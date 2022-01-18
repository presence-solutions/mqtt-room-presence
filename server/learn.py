from datetime import datetime
import pickle

import pandas as pd
import numpy as np
from server.heartbeat import HeratbeatGenerator
from server.eventbus import eventbus
from server.constants import KALMAN_Q, KALMAN_R, LONG_DELAY_PENALTY_SEC, TURN_OFF_DEVICE_SEC
from server.utils import calculate_inputs_hash, run_in_executor

from sklearn.pipeline import Pipeline
from sklearn.feature_selection import SelectorMixin
from sklearn.preprocessing import StandardScaler
from sklearn.base import BaseEstimator
from sklearn.multiclass import OneVsRestClassifier
from sklearn.neighbors import KNeighborsClassifier

from server.eventbus import EventBusSubscriber, subscribe
from server.events import (
    DeviceRemovedEvent, DeviceSignalEvent, LearntDeviceSignalEvent, RoomRemovedEvent, StartRecordingSignalsEvent,
    StopRecordingSignalsEvent, TrainPredictionModelEvent, TrainingProgressEvent)
from server.models import (
    DeviceSignal, PredictionModel, Scanner, LearningSession, get_rooms_scanners)


def select_scanner_delay(signal_row, rssi_bin_scanner_data):
    try:
        delay = rssi_bin_scanner_data.loc[(signal_row['scanner'], signal_row['rssi_bin']), 'delay']\
            .sample(n=1).iloc[0]
    except KeyError:
        delay = 5.0
    return delay if delay > 0 else 5.0


def upscale_signals_data(data_df, rounds=2):
    data_df = data_df.copy().sort_values('when_ts')
    data_df['rssi_bin'] = pd.cut(data_df['rssi'], np.arange(-100, 0, 5))
    data_df['delay'] = data_df.groupby(['scanner', 'position'], as_index=False)['when_ts']\
        .rolling(window=2).apply(lambda x: x.iloc[1] - x.iloc[0])['when_ts']
    data_df['delay'].fillna(0, inplace=True)

    upscaled_data_df = []
    rssi_bins_data_df = data_df.set_index(['scanner', 'rssi_bin']).sort_index()
    data_df = data_df.set_index(['position']).sort_index()

    for pos in data_df.index.unique():
        pos_df = data_df.loc[pos].reset_index()
        new_session_time = pos_df['when_ts'].max()
        session_dur = pos_df['when_ts'].max() - pos_df['when_ts'].min()
        upscaled_data_df.append(pos_df)
        rounds_to_gen = int(np.ceil((TURN_OFF_DEVICE_SEC * rounds) / session_dur))

        for i in range(rounds_to_gen):
            sampled_df = pos_df.sample(n=int(len(pos_df)), replace=False, ignore_index=True)
            sampled_df['delay'] = sampled_df.apply(select_scanner_delay, axis=1, args=(rssi_bins_data_df,))
            sampled_df['when_ts'] = sampled_df.groupby('scanner')['delay'].transform(pd.Series.cumsum)
            sampled_df['when_ts'] += new_session_time
            sampled_df['position'] = pos
            new_session_time = sampled_df['when_ts'].max()
            upscaled_data_df.append(sampled_df)

    upscaled_data_df = pd.concat(upscaled_data_df).reset_index().sort_values('when_ts')
    upscaled_data_df['delay'] = upscaled_data_df\
        .groupby(['position', 'scanner'], as_index=False)['when_ts'].rolling(window=2)\
        .apply(lambda x: x.iloc[1] - x.iloc[0])['when_ts']
    upscaled_data_df['delay'].fillna(0, inplace=True)
    return upscaled_data_df


def generate_data_new(data_df, rounds=3):
    gen = HeratbeatGenerator(
        long_delay=LONG_DELAY_PENALTY_SEC, turn_off_delay=TURN_OFF_DEVICE_SEC,
        kalman=(KALMAN_R, KALMAN_Q), device=None, logging=False)

    positions = data_df['position'].unique()
    scanners = data_df['scanner'].unique()
    data_df = data_df.set_index('position').sort_values('when_ts')
    default_heartbeat = dict(zip(scanners, [-100] * len(scanners)))
    result_data = []
    time_shift = 0
    last_processed_time = None
    prev_room = None
    room_init = False
    seconds_passed = 0

    for _ in range(rounds):
        for position in np.random.choice(positions, len(positions), replace=False):
            signals_df = data_df.loc[position].reset_index()
            first_signal = signals_df.iloc[0]
            room = first_signal['room']
            seconds_passed = seconds_passed if room == prev_room else 0
            room_init = room == prev_room
            prev_room = room
            time_shift = last_processed_time - first_signal['when_ts'] if last_processed_time else time_shift
            curr_time = first_signal['when_ts'] + time_shift

            for _, row in signals_df.iterrows():
                seconds_passed += row['when_ts'] + time_shift - curr_time
                curr_time = row['when_ts'] + time_shift
                next_signals = gen.process(
                    [{'rssi': row['rssi'], 'when': curr_time, 'scanner': row['scanner']}], curr_time)
                data_row = pd.Series({**default_heartbeat, **next_signals}).round(decimals=1)
                data_row['_room'] = room

                if room_init:
                    result_data.append(data_row)
                elif seconds_passed > 60:
                    room_init = True

            last_processed_time = curr_time

    result_data = pd.DataFrame(data=result_data)
    result_data.drop_duplicates(inplace=True)
    return result_data


@run_in_executor
def threaded_prepare_training_data(signals):
    data_df = pd.DataFrame([{
        'rssi': x.rssi,
        'scanner': x.scanner.uuid,
        'room': x.room.id,
        'when_ts': x.created_at.timestamp(),
        'position': str(x.learning_session.id),
    } for x in signals])

    return generate_data_new(upscale_signals_data(data_df, 2), 3)


@run_in_executor
def threaded_train_model(heartbeats_df):
    try:
        room_classifier = OneVsRestClassifier(Pipeline([
            ('select', SelectHighestMean(max_features=100, min_value=-95)),
            ('scale', StandardScaler()),
            ('classification', KNeighborsClassifier(3))
        ]))

        X, y = heartbeats_df.iloc[:, :-2], heartbeats_df._room
        room_classifier.fit(X, y)
        accuracy = room_classifier.score(X, y)
        scanners_list = heartbeats_df.columns[:-2].tolist()
        estimator = KNNPresenceEstimator(room_classifier, scanners_list)
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


class KNNPresenceEstimator:
    def __init__(self, estimator, scanners_list) -> None:
        self.estimator = estimator
        self.scanners_list = scanners_list

    def predict(self, data_row):
        data_row = data_row[self.scanners_list]
        prediction = self.estimator.predict_proba(data_row)[0]
        prediction_classes = list(zip(self.estimator.classes_, prediction))
        pred_result = [r for r in prediction_classes if r[1] > 0]
        return dict(pred_result)


class SelectHighestMean(SelectorMixin, BaseEstimator):
    def __init__(self, max_features=4, min_value=-92) -> None:
        super().__init__()
        self.max_features = max_features
        self.min_value = min_value

    def fit(self, X, y):
        self.means_ = np.mean(X[y == 1], axis=0)
        return self

    def _more_tags(self):
        return {'requires_y': True}

    def _get_support_mask(self):
        mask = np.zeros(self.means_.shape, dtype=bool)
        sorted_indexes = np.argsort(self.means_, kind="mergesort")
        mask[sorted_indexes[-self.max_features:]] = 1
        mask[self.means_ <= self.min_value] = 0
        mask[sorted_indexes[-1:]] = 1
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
