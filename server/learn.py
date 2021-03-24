import pickle
import concurrent.futures
import asyncio
from server.heartbeat import SimulatedDeviceTracker, normalize_scanner_payload
from server.constants import LEARNING_WARMUP_DELAY
from server.utils import calculate_inputs_hash, create_x_data_row

from sklearn.model_selection import train_test_split
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
from server.models import DeviceSignal, PredictionModel, DeviceHeartbeat, Room, Scanner, get_rooms_scanners


async def prepare_training_data(device):
    heartbeats = await DeviceHeartbeat.filter(device_id=device.id)
    rooms, scanners = await get_rooms_scanners()
    inputs_hash = await calculate_inputs_hash(rooms, scanners)

    if set(r.id for r in rooms) != set(h.room_id for h in heartbeats):
        raise Exception('Not every room covered with data')

    X_data = []
    y_data = []
    for heartbeat in heartbeats:
        X_data_row = await create_x_data_row(heartbeat.signals, scanners)
        y_data_row = heartbeat.room_id
        X_data.append(X_data_row)
        y_data.append(y_data_row)

    return X_data, y_data, inputs_hash


def train_model(name, clf, X_train, y_train, X_test, y_test):
    try:
        print('learning {}'.format(name))
        algorithm = clf.fit(X_train, y_train)
        score = clf.score(X_test, y_test)
        print('finished {}'.format(name))
        return name, algorithm, score, None
    except Exception as e:
        return name, None, None, e


async def warmup_learning_process():
    """
    Wait when we receive signals from multiple scanners, to have
    as complete heartbeat as possible for a currently learning room
    """
    print('Warming up the brain... {} seconds'.format(LEARNING_WARMUP_DELAY))
    await asyncio.sleep(LEARNING_WARMUP_DELAY)
    print('Alright! Lets learn!')


async def regenerate_heartbeats(device, room):
    device_tracker = SimulatedDeviceTracker(device)
    signals = await DeviceSignal.filter(device_id=device.id, room_id=room.id)\
        .order_by('created_at').prefetch_related('scanner')

    for s in signals:
        device_tracker.process_signal(
            scanner_uuid=s.scanner.uuid, signal=normalize_scanner_payload({'rssi': s.rssi}),
            signal_timestamp=s.created_at)

    new_heartbeats = [DeviceHeartbeat(
        device_id=device.id,
        room_id=room.id,
        signals=h.signals,
    ) for h in device_tracker.heartbeats]

    await DeviceHeartbeat.filter(device_id=device.id, room_id=room.id).delete()
    await DeviceHeartbeat.bulk_create(new_heartbeats)


class Learn(EventBusSubscriber):
    def __init__(self):
        super().__init__()
        self.recording_room = None
        self.recording_device = None
        self.warmup_coroutine = None

    @subscribe(StartRecordingSignalsEvent)
    def handle_start_recording(self, event):
        self.recording_room = event.room
        self.recording_device = event.device
        self.warmup_coroutine = asyncio.create_task(warmup_learning_process())

    @subscribe(StopRecordingSignalsEvent)
    def handle_stop_recording(self, event):
        self.recording_room = None
        self.recording_device = None
        self.warmup_coroutine = None

    @subscribe(RegenerateHeartbeatsEvent)
    async def handle_regenerate_heartbeats(self, event):
        print('Regenerating heartbeats')
        rooms = await Room.all()
        for r in rooms:
            await regenerate_heartbeats(event.device, r)
            print('Room {} regenerated'.format(r.name))

    def is_learning_started(self, device):
        return (self.warmup_coroutine
                and self.warmup_coroutine.done()
                and self.recording_room
                and self.recording_device == device)

    @subscribe(DeviceSignalEvent)
    async def handle_device_signal(self, event):
        if not event.signal or not self.is_learning_started(event.device):
            return

        scanner = await Scanner.filter(uuid=event.scanner_uuid).first()
        if not scanner:
            print('There is no scanner in the database with UUID: {}'.format(event.scanner_uuid))
            return

        await DeviceSignal.create(
            device_id=event.device.id,
            room_id=self.recording_room.id,
            scanner_id=scanner.id,
            rssi=event.signal['rssi'],
            filtered_rssi=event.signal['filtered_rssi'],
        )

        print('Learned signal from {}, {}, {}'.format(
            event.scanner_uuid, event.signal['filtered_rssi'], event.signal['rssi']))

    @subscribe(HeartbeatEvent)
    async def handle_device_heartbeat(self, event):
        if not event.signals or not self.is_learning_started(event.device):
            return

        learned_heartbeats = await DeviceHeartbeat.filter(
            device_id=event.device.id, room_id=self.recording_room.id).count()
        print('Learned heartbeats: {}'.format(learned_heartbeats + 1))

        await DeviceHeartbeat.create(
            device_id=event.device.id,
            room_id=self.recording_room.id,
            signals=event.signals,
        )

    @subscribe(TrainPredictionModelEvent)
    async def handle_train_model(self, event):
        print('The training started')

        device = event.device
        loop = asyncio.get_running_loop()
        X, y, inputs_hash = await prepare_training_data(event.device)
        X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)

        print('Prepared a training set')

        classifiers = {
            "Nearest Neighbors": KNeighborsClassifier(3),
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
                return loop.run_in_executor(pool, train_model, name, clf, X_train, y_train, X_test, y_test)

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
