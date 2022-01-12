from datetime import datetime
import pickle

import pandas as pd
import numpy as np
from itertools import product
from server.eventbus import eventbus
from server.constants import MOVING_AVERAGE_WINDOW
from server.utils import calculate_inputs_hash, run_in_executor
from joblib import Parallel, delayed

from sklearn.base import clone as clone_estimator
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import SelectorMixin
from sklearn.base import BaseEstimator

from server.eventbus import EventBusSubscriber, subscribe
from server.events import (
    DeviceRemovedEvent, DeviceSignalEvent, LearntDeviceSignalEvent, RoomRemovedEvent, StartRecordingSignalsEvent,
    StopRecordingSignalsEvent, TrainPredictionModelEvent, TrainingProgressEvent)
from server.models import (
    DeviceSignal, PredictionModel, Scanner, LearningSession, get_rooms_scanners)


def select_random_delay(signal_row, rssi_bin_scanner_data):
    try:
        return rssi_bin_scanner_data.loc[(signal_row['scanner'], signal_row['rssi_bin']), 'delay'].sample(n=1)[0]
    except KeyError:
        return 5.0


@run_in_executor
def threaded_prepare_training_data(signals):
    # Prepare the dataframe with signals
    data_df = pd.DataFrame([{
        'rssi': x.rssi,
        'scanner': x.scanner.uuid,
        'room': x.room.id,
        'when_ts': x.created_at.timestamp(),
        'position': str(x.learning_session.id),
    } for x in signals])
    data_df.set_index('position', inplace=True)
    data_df['session_length'] = data_df.groupby(['position'])['when_ts'].apply(lambda x: x.max() - x.min())
    data_df.reset_index(inplace=True)
    data_df.set_index(['position', 'scanner'], inplace=True)
    data_df['session_scanner_freq'] = data_df.groupby(['position', 'scanner'])\
        .apply(lambda x: len(x) / x.iloc[0]['session_length'])
    data_df['session_scanner_signals'] = data_df.groupby(['position', 'scanner']).apply(lambda x: len(x))
    data_df.reset_index(inplace=True)
    data_df.set_index('position', inplace=True)
    data_df['session_scanner_freq_norm'] = data_df.groupby(['position'])['session_scanner_freq']\
        .apply(lambda x: (x / x.max()))
    data_df.reset_index(inplace=True)

    # Upsample data for each individual scanner-position and select only the most
    # active scanners in each position
    upsampled_data_df = []
    pos_scan_df = data_df.groupby(['position', 'scanner']).agg(
        session_length=('session_length', 'min'),
        scanner_freq=('session_scanner_freq', 'min'),
        scanner_freq_norm=('session_scanner_freq_norm', 'min'),
        scanner_signals=('session_scanner_signals', 'min'))

    for position in data_df['position'].unique():
        position_signals_df = data_df.loc[data_df['position'] == position]
        most_active_scanners = pos_scan_df.loc[position].sort_values('scanner_freq', ascending=False).iloc[:4]
        upsampled_scanner_df = []

        for scanner in most_active_scanners.index:
            scanner_df = position_signals_df.loc[position_signals_df['scanner'] == scanner]
            scanner_stat = pos_scan_df.loc[(position, scanner)]

            # Ignore scanners with only 4 signals or with signals frequency significantly lower
            # than the frequency of the most active scanner
            if scanner_stat['scanner_signals'] < 4 or scanner_stat['scanner_freq_norm'] < 0.2:
                continue

            scanner_df = scanner_df.sample(n=400, replace=True, ignore_index=True)
            upsampled_scanner_df.append(scanner_df[['rssi', 'when_ts', 'scanner', 'position', 'room']])

        upsampled_scanner_df = pd.concat(upsampled_scanner_df)
        upsampled_data_df.append(upsampled_scanner_df)

    # Smooth the upsampled data to reduce the noise a little bit
    upsampled_data_df = pd.concat(upsampled_data_df).reset_index()
    upsampled_data_df['index'] = upsampled_data_df.groupby(['scanner', 'position']).cumcount()
    upsampled_data_df['rssi_smoothed'] = upsampled_data_df.groupby(['scanner', 'position'])['rssi']\
        .rolling(MOVING_AVERAGE_WINDOW).mean().reset_index((0, 1))['rssi'].round()
    upsampled_data_df.dropna(inplace=True)

    # Generate all possible heartbeats for each position. We use 4 scanners maximum for each position
    # and smoothed RSSI for each scanner rounded to a whole number so there are not so many
    # combinations of signal levels from each scanner, hence we can generate all of them for training the model
    heartbeats_df = []
    for position in upsampled_data_df['position'].unique():
        position_df = upsampled_data_df.loc[upsampled_data_df['position'] == position]
        active_scanners = position_df['scanner'].unique()
        unique_scanner_rssi = [
            position_df.loc[position_df['scanner'] == scanner]['rssi_smoothed'].unique().tolist()
            for scanner in active_scanners
        ]
        position_heartbeats_df = pd.DataFrame(data=product(*unique_scanner_rssi), columns=active_scanners)
        position_heartbeats_df['_room'] = position_df.iloc[0]['room']
        position_heartbeats_df['_position'] = position
        heartbeats_df.append(position_heartbeats_df)

    heartbeats_df = pd.concat(heartbeats_df)[[*upsampled_data_df['scanner'].unique(), '_room', '_position']]
    heartbeats_df.fillna(-100, inplace=True)
    heartbeats_df.drop_duplicates(inplace=True)

    return heartbeats_df


@run_in_executor
def threaded_train_model(heartbeats_df):
    try:
        X_train_idx_df = heartbeats_df.set_index(['_room', '_position']).sort_index()
        position_estimators = {}
        train_scores = []
        binary_estimator = Pipeline([
            ('select', SelectHighestMean()),
            ('classification', RandomForestClassifier(n_estimators=5, class_weight='balanced', n_jobs=-1))
        ])

        for room in X_train_idx_df.index.get_level_values('_room').unique():
            for position in X_train_idx_df.loc[(room,)].index.unique():
                pos_mask = (heartbeats_df['_room'] != room) | (heartbeats_df['_position'] == position)
                X_pos_train_raw = heartbeats_df[pos_mask].copy()
                X_pos_train = X_pos_train_raw.iloc[:, :-2]
                y_pos_train = X_pos_train_raw['_position'] == position

                estimator = clone_estimator(binary_estimator)
                position_estimators[(room, position)] = estimator
                estimator.fit(X_pos_train, y_pos_train)
                train_scores.append(estimator.score(X_pos_train, y_pos_train))

        scanners_list = heartbeats_df.columns[:-2].tolist()
        estimator = EnsambledPresenceEstimator(position_estimators, scanners_list)
        accuracy = np.mean(train_scores)
    except Exception as e:
        return 0, None, e

    return accuracy, estimator, None


def report_training_progress(**kwargs):
    eventbus.post(TrainingProgressEvent(**{
        "is_final": False,
        "is_error": False,
        "prediction_model": None,
        **kwargs
    }))


async def prepare_training_data(device):
    report_training_progress(
        device=device,
        status_code="generating_dataset",
        message="Prepearing the training dataset"
    )

    signals = await DeviceSignal.filter(device_id=device.id).prefetch_related('room', 'scanner', 'learning_session')
    heartbeats = await threaded_prepare_training_data(signals)

    report_training_progress(
        device=device,
        status_code="dataset_ready",
        message="The dataset is generated, training {}".format(str(len(heartbeats))),
    )
    return heartbeats


async def train_model(device, heartbeats):
    report_training_progress(
        device=device,
        status_code="training_started",
        message="Starting to train the model"
    )

    accuracy, model, error = await threaded_train_model(heartbeats)

    report_training_progress(
        device=device,
        status_code="training_finished",
        message="The model training is finished, accuracy {}".format(str(accuracy))
    )

    return accuracy, model, error


def _predict_single_room_position(rows, estimator, key):
    return key[0], key[1], estimator.predict_proba(rows)[:, 1]


def _get_best_prediction(x):
    preds = x['predictions'].to_numpy()
    preds = np.concatenate(preds).reshape(len(preds), len(preds[0]))
    return pd.Series(preds.max(axis=0))


class EnsambledPresenceEstimator:
    def __init__(self, estimators, scanners_list) -> None:
        self.estimators = estimators
        self.scanners_list = scanners_list

    def predict(self, data_row):
        data_row = data_row[self.scanners_list].round()
        pred_res = Parallel(n_jobs=-1)(
            delayed(_predict_single_room_position)(data_row, estimator, key)
            for key, estimator in self.estimators.items()
        )
        pred_res = pd.DataFrame(data=pred_res, columns=['room', 'position', 'predictions'])\
            .groupby(['room']).apply(_get_best_prediction).T
        prediction = pred_res.iloc[0]
        return prediction[prediction > 0].to_dict()


class PresenceEstimator:
    def __init__(self, estimator, thresholds) -> None:
        self.estimator = estimator
        self.thresholds = thresholds

    def predict(self, data_row):
        prediction = self.estimator.decision_function(data_row)[0]
        prediction_classes = np.array(list(zip(self.estimator.classes_, prediction)))

        max_pred_result = prediction_classes[np.argsort(prediction)[-3:]]
        pred_result = [r for r in prediction_classes if r[1] >= self.thresholds[r[0]] * 0.9]
        pred_result = max_pred_result if not pred_result else pred_result

        return dict(pred_result)


class SelectHighestMean(SelectorMixin, BaseEstimator):
    """
    Use only the scanners with the highest mean and ignore
    those where the mean is worse than -90
    """
    def fit(self, X, y):
        self.means_ = np.mean(X[y == 1], axis=0)
        return self

    def _more_tags(self):
        return {'requires_y': True}

    def _get_support_mask(self):
        highest_indexes = np.argsort(self.means_, kind="mergesort")
        mask = np.zeros(self.means_.shape, dtype=bool)
        mask[highest_indexes[-4:]] = 1
        mask[self.means_ < -90] = 0
        mask[highest_indexes[-1:]] = 1
        return mask


class Learn(EventBusSubscriber):
    def __init__(self):
        super().__init__()
        self.recording_room = None
        self.recording_device = None
        self.learning_stats = {}
        self.learning_session = None

    @subscribe(StartRecordingSignalsEvent)
    async def handle_start_recording(self, event):
        self.recording_room = event.room
        self.recording_device = event.device
        self.learning_stats = {}
        self.learning_session = await LearningSession.create(
            room_id=event.room.id, device_id=event.device.id)

    @subscribe(StopRecordingSignalsEvent)
    def handle_stop_recording(self, event):
        self.recording_room = None
        self.recording_device = None
        self.learning_stats = {}
        self.learning_session = None

    @subscribe(DeviceRemovedEvent)
    def handle_device_removed(self, event):
        if event.device == self.recording_device:
            self.handle_stop_recording(None)
            eventbus.post(StopRecordingSignalsEvent())

    @subscribe(RoomRemovedEvent)
    def handle_room_removed(self, event):
        if event.room == self.recording_room:
            self.handle_stop_recording(None)
            eventbus.post(StopRecordingSignalsEvent())

    def is_learning_started(self, device):
        return self.recording_room and self.recording_device == device

    @subscribe(DeviceSignalEvent)
    async def handle_device_signal(self, event):
        if not self.is_learning_started(event.device):
            return

        scanner = await Scanner.filter(uuid=event.scanner_uuid).first()
        if not scanner:
            # TODO: notify the client about it somehow
            print('There is no scanner in the database with UUID: {}'.format(event.scanner_uuid))
            return

        signal_datetime = datetime.fromtimestamp(event.signal['when'])
        device_signal = await DeviceSignal.create(
            device=event.device,
            room=self.recording_room,
            learning_session=self.learning_session,
            scanner=scanner,
            rssi=event.signal['rssi'],
            created_at=signal_datetime,
            updated_at=signal_datetime,
        )

        _, scanners = await get_rooms_scanners()
        scanner_signals = self.learning_stats.get(event.scanner_uuid, 0)
        self.learning_stats[event.scanner_uuid] = scanner_signals + 1
        scanners_to_wait = min(len(scanners), 3)
        is_enough = sum(len(self.learning_stats[k]) >= 20 for k in self.learning_stats.keys()) >= scanners_to_wait
        is_enough = is_enough or sum(len(self.learning_stats[k]) >= 100 for k in self.learning_stats.keys()) >= 1

        eventbus.post(LearntDeviceSignalEvent(device_signal=device_signal, is_enough=is_enough))

    @subscribe(TrainPredictionModelEvent)
    async def handle_train_model(self, event):
        device = event.device

        report_training_progress(
            device=device,
            status_code="started",
            message="Training of the model has been started"
        )

        rooms, scanners = await get_rooms_scanners()
        inputs_hash = await calculate_inputs_hash(rooms, scanners)
        heartbeats = await prepare_training_data(device)
        accuracy, model, error = await train_model(device, heartbeats)

        if error is not None:
            report_training_progress(
                device=device,
                status_code="failed",
                is_final=True,
                is_error=True,
                message="Failed to train the model, reason: {}".format(str(error))
            )
        else:
            result = await PredictionModel.create(
                accuracy=accuracy,
                model=pickle.dumps(model),
                inputs_hash=inputs_hash,
            )
            await result.devices.add(device)

            report_training_progress(
                device=device,
                status_code="success",
                is_final=True,
                prediction_model=result,
                message="Successfully finished the prediction model creation"
            )
