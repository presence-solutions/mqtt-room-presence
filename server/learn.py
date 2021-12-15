from datetime import datetime
import pickle

import pandas as pd
import numpy as np
from server.eventbus import eventbus
from server.kalman import KalmanRSSI
from server.constants import KALMAN_Q, KALMAN_R, LONG_DELAY_PENALTY_SEC

from server.utils import calculate_inputs_hash, run_in_executor

from sklearn import metrics
from sklearn.multiclass import OneVsRestClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split

from server.eventbus import EventBusSubscriber, subscribe
from server.events import (
    DeviceRemovedEvent, DeviceSignalEvent, LearntDeviceSignalEvent, RoomRemovedEvent, StartRecordingSignalsEvent,
    StopRecordingSignalsEvent, TrainPredictionModelEvent, TrainingProgressEvent)
from server.models import (
    DeviceSignal, PredictionModel, Scanner, LearningSession, get_rooms_scanners)


@run_in_executor
def prepare_training_data(signals):
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
    signals_history = dict([(s, 0) for s in sorted_scanners])
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
                    signals = signals.sample(min(len(signals), 200))

                    for _, row in signals.iterrows():
                        seconds_passed += 1 / signals_per_sec
                        signals_history[row['scanner']] = 0
                        filters[row['scanner']].filter(row['rssi'])
                        data_row = [filters[s].lastMeasurement() or -100 for s in sorted_scanners]

                        for s in sorted_scanners:
                            signals_history[s] += 1
                            if signals_history[s] > (LONG_DELAY_PENALTY_SEC / signals_per_sec):
                                signals_history[s] = 0
                                filters[s].filter(-100)

                        if room_init:
                            result_data.append(data_row + [room])
                        elif seconds_passed > 60:
                            room_init = True

    result_data = pd.DataFrame(columns=sorted_scanners + ['room'], data=result_data)
    result_data.drop_duplicates(inplace=True)
    X, y = (result_data.iloc[:, :-1], result_data.room.values)
    return train_test_split(X, y, stratify=y, random_state=42, test_size=0.2)


def calculate_best_thresholds(estimator, X, y):
    pred_probas = estimator.predict_proba(X)
    sorted_rooms = estimator.classes_
    pred_probas_df = pd.DataFrame(
        [dict(list(zip(sorted_rooms, r)) + [('_room', y[i])]) for i, r in enumerate(pred_probas)])
    room_thresholds = {}
    beta = 12  # recall is more important than precision
    scores = []

    for _, room in enumerate(sorted_rooms):
        y_true = [1 if x else 0 for x in pred_probas_df['_room'] == room]
        y_pred = list(pred_probas_df[room])
        precision, recall, thresholds = metrics.precision_recall_curve(y_true, y_pred)
        beta_squared = beta ** 2
        fscore = ((1 + beta_squared) * precision * recall) / (beta_squared * precision + recall)
        ix = np.argmax(fscore)
        room_thresholds[room] = thresholds[ix]
        scores.append(fscore[ix])
        print('%s - Best Threshold=%f, F-Score=%.3f, Precision=%.3f, Recall=%.3f' % (
            room, thresholds[ix], fscore[ix], precision[ix], recall[ix]))

    return room_thresholds, np.mean(scores)


@run_in_executor
def train_model(X_train, X_test, y_train, y_test):
    try:
        estimator = OneVsRestClassifier(RandomForestClassifier(
            n_estimators=10, class_weight='balanced', n_jobs=-1))
        estimator.fit(X_train, y_train)
    except Exception as e:
        return 0, None, e

    room_thresholds, accuracy = calculate_best_thresholds(estimator, X_test, y_test)
    estimator = ThresholdsBasedEstimator(estimator, room_thresholds)
    return accuracy, estimator, None


def report_training_progress(**kwargs):
    eventbus.post(TrainingProgressEvent(**{
        "is_final": False,
        "is_error": False,
        "prediction_model": None,
        **kwargs
    }))


async def looped_prepare_training_data(device):
    report_training_progress(
        device=device,
        status_code="generating_dataset",
        message="Prepearing the training dataset"
    )

    signals = await DeviceSignal.filter(device_id=device.id).prefetch_related('room', 'scanner', 'learning_session')
    X_train, X_test, y_train, y_test = await prepare_training_data(signals)

    report_training_progress(
        device=device,
        status_code="dataset_ready",
        message="The dataset is generated, training {}, testing {}".format(str(len(y_train)), str(len(y_test)))
    )
    return X_train, X_test, y_train, y_test


async def looped_train_model(device, X_train, X_test, y_train, y_test):
    report_training_progress(
        device=device,
        status_code="training_started",
        message="Starting to train the model"
    )

    accuracy, model, error = await train_model(X_train, X_test, y_train, y_test)

    report_training_progress(
        device=device,
        status_code="training_finished",
        message="The model training is finished, accuracy {}".format(str(accuracy))
    )

    return accuracy, model, error


class ThresholdsBasedEstimator:
    def __init__(self, estimator, thresholds) -> None:
        self.estimator = estimator
        self.thresholds = thresholds

    def predict_proba(self, data_row):
        pred_result = list(zip(self.estimator.classes_, self.estimator.predict_proba(data_row)[0]))
        max_pred_result = max(pred_result, key=lambda x: x[1])
        pred_result = [r for r in pred_result if r[1] >= self.thresholds[r[0]]]
        pred_result = [max_pred_result] if not pred_result else pred_result
        return [dict(pred_result)]


class Learn(EventBusSubscriber):
    def __init__(self):
        super().__init__()
        self.recording_room = None
        self.recording_device = None
        self.learning_session = None

    @subscribe(StartRecordingSignalsEvent)
    async def handle_start_recording(self, event):
        self.recording_room = event.room
        self.recording_device = event.device
        self.learning_session = await LearningSession.create(
            room_id=event.room.id, device_id=event.device.id)

    @subscribe(StopRecordingSignalsEvent)
    def handle_stop_recording(self, event):
        self.recording_room = None
        self.recording_device = None
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

        eventbus.post(LearntDeviceSignalEvent(device_signal=device_signal))

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
        training_data = await looped_prepare_training_data(device)
        accuracy, model, error = await looped_train_model(device, *training_data)

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
