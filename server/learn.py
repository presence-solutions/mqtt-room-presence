from datetime import datetime
import pickle
import concurrent.futures
import asyncio
import pandas as pd
import numpy as np
from server.eventbus import eventbus
from server.kalman import KalmanRSSI
from server.constants import KALMAN_Q, KALMAN_R, LONG_DELAY_PENALTY_SEC

from server.utils import calculate_inputs_hash

from sklearn import metrics
from sklearn.multiclass import OneVsRestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split

from server.eventbus import EventBusSubscriber, subscribe
from server.events import (
    DeviceRemovedEvent, DeviceSignalEvent, LearntDeviceSignalEvent, RoomRemovedEvent, StartRecordingSignalsEvent,
    StopRecordingSignalsEvent, TrainPredictionModelEvent)
from server.models import (
    DeviceSignal, PredictionModel, Scanner, LearningSession, get_rooms_scanners)


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
                        elif seconds_passed > 120:
                            room_init = True

    return pd.DataFrame(columns=sorted_scanners + ['room'], data=result_data)


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


def train_model(signals):
    data_df = prepare_training_data(signals)
    data_df.drop_duplicates(inplace=True)
    X, y = (data_df.iloc[:, :-1], data_df.room.values)
    X_train, X_test, y_train, y_test = train_test_split(X, y, stratify=y, random_state=42, test_size=0.2)
    print('Training {}, testing {}'.format(str(len(y_train)), str(len(y_test))))

    try:
        estimator = OneVsRestClassifier(LogisticRegression(
            penalty='l1', solver='liblinear', class_weight='balanced', C=0.001, max_iter=10000))
        estimator.fit(X_train, y_train)
    except Exception as e:
        return 0, None, e

    room_thresholds, accuracy = calculate_best_thresholds(estimator, X_test, y_test)
    estimator = ThresholdsBasedEstimator(estimator, room_thresholds)
    return accuracy, estimator, None


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

        print('Learned signal from {}, {}'.format(event.scanner_uuid, event.signal['rssi']))

    @subscribe(TrainPredictionModelEvent)
    async def handle_train_model(self, event):
        device = event.device
        loop = asyncio.get_running_loop()

        print('Training the model...')
        rooms, scanners = await get_rooms_scanners()
        inputs_hash = await calculate_inputs_hash(rooms, scanners)
        signals = await DeviceSignal.filter(device_id=device.id).prefetch_related('room', 'scanner', 'learning_session')

        with concurrent.futures.ThreadPoolExecutor() as pool:
            train_result = loop.run_in_executor(pool, train_model, signals)

        accuracy, model, error = (await asyncio.gather(train_result))[0]

        if error is not None:
            print('There is an error while fitting the model: ', error)
        else:
            print('Training is done! Results: {}, {}, {}'.format(accuracy, model, error))
            result = await PredictionModel.create(
                accuracy=accuracy,
                model=pickle.dumps(model),
                inputs_hash=inputs_hash,
            )
            await result.devices.add(device)
