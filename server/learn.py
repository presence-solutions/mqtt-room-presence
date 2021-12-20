from datetime import datetime
import pickle

import pandas as pd
import numpy as np
from server.eventbus import eventbus
from server.kalman import KalmanRSSI
from server.constants import KALMAN_Q, KALMAN_R, LONG_DELAY_PENALTY_SEC, TURN_OFF_DEVICE_SEC

from server.utils import calculate_inputs_hash, run_in_executor

from sklearn import metrics
from sklearn.multiclass import OneVsOneClassifier
from sklearn.pipeline import Pipeline
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.feature_selection import SelectorMixin
from sklearn.base import BaseEstimator

from server.eventbus import EventBusSubscriber, subscribe
from server.events import (
    DeviceRemovedEvent, DeviceSignalEvent, LearntDeviceSignalEvent, RoomRemovedEvent, StartRecordingSignalsEvent,
    StopRecordingSignalsEvent, TrainPredictionModelEvent, TrainingProgressEvent)
from server.models import (
    DeviceSignal, PredictionModel, Scanner, LearningSession, get_rooms_scanners)


@run_in_executor
def threaded_prepare_training_data(signals):
    used_data_df = pd.DataFrame([{
        'rssi': x.rssi,
        'scanner': x.scanner.id,
        'room': x.room.id,
        'when': np.datetime64(x.created_at),
        'position': x.learning_session.id,
    } for x in signals])

    sorted_rooms = sorted(used_data_df['room'].unique())
    sorted_scanners = sorted(used_data_df['scanner'].unique())
    session_dur_df = used_data_df.groupby(['room', 'position'])\
        .agg(when_min=('when', 'min'), when_max=('when', 'max'), signals=('when', 'count'))
    session_dur_df['when_diff'] = np.round(
        (session_dur_df['when_max'] - session_dur_df['when_min']) / np.timedelta64(1, 's'))
    session_dur_df['frequency'] = session_dur_df['signals'] / session_dur_df['when_diff']
    filters = dict([(s, KalmanRSSI(R=KALMAN_R, Q=KALMAN_Q)) for s in sorted_scanners])
    off_signals_history = dict([(s, 0) for s in sorted_scanners])
    delay_signals_history = dict([(s, 0) for s in sorted_scanners])
    result_data = []

    for _ in range(10):
        for room in np.random.choice(sorted_rooms, len(sorted_rooms), replace=False):
            room_init = False
            seconds_passed = 0
            positions = used_data_df[used_data_df['room'] == room]['position'].unique()
            for _ in range(3):
                for position in np.random.choice(positions, len(positions), replace=False):
                    signals_per_sec = session_dur_df.loc[(room, position), 'frequency']
                    signals = used_data_df[(used_data_df['room'] == room) & (used_data_df['position'] == position)]
                    signals = signals.sample(n=min(len(signals), 300), replace=True)

                    for _, row in signals.iterrows():
                        seconds_passed += 1 / signals_per_sec
                        off_signals_history[row['scanner']] = 0
                        delay_signals_history[row['scanner']] = 0
                        filters[row['scanner']].filter(row['rssi'])
                        data_row = [np.round(filters[s].lastMeasurement() or -100, decimals=1) for s in sorted_scanners]

                        for s in sorted_scanners:
                            off_signals_history[s] += 1
                            delay_signals_history[s] += 1
                            if off_signals_history[s] > (TURN_OFF_DEVICE_SEC / signals_per_sec):
                                off_signals_history[s] = 0
                                filters[s].reset(-100.0)
                            elif delay_signals_history[s] > (LONG_DELAY_PENALTY_SEC / signals_per_sec):
                                delay_signals_history[s] = 0
                                filters[s].filter(-100.0)

                        if room_init:
                            result_data.append(data_row + [room])
                        elif seconds_passed > 60:
                            room_init = True

    result_data = pd.DataFrame(columns=sorted_scanners + ['room'], data=result_data)
    result_data.drop_duplicates(inplace=True)
    X, y = (result_data.iloc[:, :-1], result_data.room.values)
    return X, y


@run_in_executor
def threaded_train_model(X, y):
    try:
        estimator = OneVsOneClassifier(Pipeline([
            ('select', SelectHighestMean()),
            ('scale', StandardScaler()),
            ('classification', RandomForestClassifier(n_estimators=10, class_weight='balanced', n_jobs=-1))
        ]), n_jobs=-1)
        estimator.fit(X, y)
        accuracy = metrics.recall_score(y, estimator.predict(X), average='micro')
        estimator = PresenceEstimator(estimator)
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
    X, y = await threaded_prepare_training_data(signals)

    report_training_progress(
        device=device,
        status_code="dataset_ready",
        message="The dataset is generated, training {}".format(str(len(y))),
    )
    return X, y


async def train_model(device, X, y):
    report_training_progress(
        device=device,
        status_code="training_started",
        message="Starting to train the model"
    )

    accuracy, model, error = await threaded_train_model(X, y)

    report_training_progress(
        device=device,
        status_code="training_finished",
        message="The model training is finished, accuracy {}".format(str(accuracy))
    )

    return accuracy, model, error


class PresenceEstimator:
    def __init__(self, estimator) -> None:
        self.estimator = estimator

    def predict(self, data_row):
        pred_result = self.estimator.predict(data_row)
        return dict((r, 1) for r in pred_result)


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
        training_data = await prepare_training_data(device)
        accuracy, model, error = await train_model(device, *training_data)

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
