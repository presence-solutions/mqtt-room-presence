import pickle
import concurrent.futures
import asyncio

from server.heartbeat import SimulatedDeviceTracker, normalize_scanner_payload
from server.constants import HEARTBEAT_COLLECT_PERIOD_SEC, LEARNING_WARMUP_DELAY_SEC
from server.utils import calculate_inputs_hash, create_x_data_row

from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis

from server.eventbus import EventBusSubscriber, subscribe
from server.events import (
    DeviceSignalEvent, HeartbeatEvent, RegenerateHeartbeatsEvent, StartRecordingSignalsEvent,
    StopRecordingSignalsEvent, TrainPredictionModelEvent)
from server.models import (
    DeviceSignal, PredictionModel, DeviceHeartbeat, Scanner, LearningSession, get_rooms_scanners)


async def prepare_training_data(device):
    heartbeats = await DeviceHeartbeat.filter(device_id=device.id)
    rooms, scanners = await get_rooms_scanners()
    inputs_hash = await calculate_inputs_hash(rooms, scanners)

    if set(r.id for r in rooms) != set(h.room_id for h in heartbeats):
        raise Exception('Not every room covered with data')

    X_data = []
    y_data = []
    for heartbeat in heartbeats:
        X_data_row = create_x_data_row(heartbeat.signals, scanners)
        y_data_row = heartbeat.room_id
        X_data.append(X_data_row)
        y_data.append(y_data_row)

    return X_data, y_data, inputs_hash


def train_model(name, clf, X, y):
    try:
        print('learning {}'.format(name))
        algorithm = clf.fit(X, y)
        score = clf.score(X, y)
        print('finished {}'.format(name))
        return name, algorithm, score, None
    except Exception as e:
        return name, None, None, e


async def warmup_learning_process():
    """
    Wait when we receive signals from multiple scanners, to have
    as complete heartbeat as possible for a currently learning room
    """
    print('Warming up the brain... {} seconds'.format(LEARNING_WARMUP_DELAY_SEC))
    await asyncio.sleep(LEARNING_WARMUP_DELAY_SEC)
    print('Alright! Lets learn!')


async def regenerate_heartbeats(device):
    sessions = await LearningSession.filter(device=device).prefetch_related('room')

    for session in sessions:
        signals = await DeviceSignal.filter(learning_session=session).prefetch_related('scanner')
        start_time = min(signals, key=lambda x: x.created_at.timestamp()).created_at.timestamp()
        end_time = max(signals, key=lambda x: x.created_at.timestamp()).created_at.timestamp()
        period = HEARTBEAT_COLLECT_PERIOD_SEC
        tracker = SimulatedDeviceTracker(device=device)
        last_signal_index = 0

        for curr_time in range(int(start_time + period - 1), int(end_time + period), period):
            for i in range(last_signal_index, len(signals)):
                signal_ts = signals[i].timestamp()
                if signal_ts > curr_time - period and signal_ts <= curr_time:
                    tracker.process_signal(signals[i].scanner.uuid, normalize_scanner_payload({
                        'uuid': signals[i].scanner.uuid,
                        'rssi': signals[i].rssi,
                        'when': signal_ts,
                    }))
                else:
                    last_signal_index = i
                    break

            tracker.create_heartbeat(timestamp=curr_time)

        new_heartbeats = [DeviceHeartbeat(
            device_id=device.id,
            room_id=session.room.id,
            learning_session_id=session.id,
            signals=signals,
        ) for signals in tracker.heartbeats]

        await DeviceHeartbeat.filter(
            device_id=device.id, room_id=session.room.id, learning_session_id=session.id).delete()
        await DeviceHeartbeat.bulk_create(new_heartbeats)


class Learn(EventBusSubscriber):
    def __init__(self):
        super().__init__()
        self.recording_room = None
        self.recording_device = None
        self.warmup_coroutine = None
        self.learning_session = None

    @subscribe(StartRecordingSignalsEvent)
    async def handle_start_recording(self, event):
        self.recording_room = event.room
        self.recording_device = event.device
        self.learning_session = await LearningSession.create(
            room_id=event.room.id, device_id=event.device.id)
        self.warmup_coroutine = asyncio.create_task(warmup_learning_process())

    @subscribe(StopRecordingSignalsEvent)
    def handle_stop_recording(self, event):
        self.recording_room = None
        self.recording_device = None
        self.warmup_coroutine = None
        self.learning_session = None

    @subscribe(RegenerateHeartbeatsEvent)
    async def handle_regenerate_heartbeats(self, event):
        print('Regenerating heartbeats...')
        await regenerate_heartbeats(event.device)
        print('Regenerated!')

    def is_learning_started(self, device):
        return (self.warmup_coroutine
                and self.warmup_coroutine.done()
                and self.recording_room
                and self.recording_device == device)

    @subscribe(DeviceSignalEvent)
    async def handle_device_signal(self, event):
        scanner = await Scanner.filter(uuid=event.scanner_uuid).first()
        if not scanner:
            print('There is no scanner in the database with UUID: {}'.format(event.scanner_uuid))
            return

        await DeviceSignal.create(
            device_id=event.device.id,
            room_id=self.recording_room.id,
            learning_session_id=self.learning_session.id,
            scanner_id=scanner.id,
            rssi=event.signal['rssi'],
            created_at=event.signal['when'],
            updated_at=event.signal['when'],
        )

        print('Learned signal from {}, {}'.format(event.scanner_uuid, event.signal['rssi']))

    @subscribe(HeartbeatEvent)
    async def handle_device_heartbeat(self, event):
        if not event.signals or not self.is_learning_started(event.device):
            return

        await DeviceHeartbeat.create(
            device_id=event.device.id,
            room_id=self.recording_room.id,
            learning_session_id=self.learning_session.id,
            signals=event.signals,
        )

        count = await DeviceHeartbeat.filter(
            device_id=event.device.id, room_id=self.recording_room.id,).count()

        print('Learned heartbeats: {}'.format(count))

    @subscribe(TrainPredictionModelEvent)
    async def handle_train_model(self, event):
        print('The training started')

        device = event.device
        loop = asyncio.get_running_loop()
        X, y, inputs_hash = await prepare_training_data(event.device)

        print('Prepared a training set')

        classifiers = {
            "Nearest Neighbors": KNeighborsClassifier(5),
            "Linear SVM": SVC(kernel="linear", C=0.025, probability=True),
            "RBF SVM": SVC(gamma=2, C=1, probability=True),
            "Decision Tree": DecisionTreeClassifier(max_depth=5),
            "Random Forest": RandomForestClassifier(
                max_depth=5, n_estimators=10, max_features=1),
            "Neural Net": MLPClassifier(alpha=1, max_iter=1000),
            "AdaBoost": AdaBoostClassifier(),
            "Naive Bayes": GaussianNB(),
            "QDA": QuadraticDiscriminantAnalysis()
        }

        print('Run training of the models')

        with concurrent.futures.ThreadPoolExecutor() as pool:
            def run_train_coroutine(name, clf):
                return loop.run_in_executor(pool, train_model, name, clf, X, y)

            train_coros = [run_train_coroutine(name, clf) for name, clf in classifiers.items()]

        results = await asyncio.gather(*train_coros)
        top_five = sorted(results, key=lambda x: x[2], reverse=True)
        model = [(data[0], data[1], data[2]) for data in top_five]

        print('Training is done! Results: {}'.format(model))

        result = await PredictionModel.create(
            accuracy=model[0][2],
            model=pickle.dumps(model),
            inputs_hash=inputs_hash,
        )
        await result.devices.add(device)
