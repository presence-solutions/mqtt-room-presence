import time
import concurrent.futures
import asyncio

from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis

from server.constants import MAX_DISTANCE
from server.eventbus import subscribe, eventbus
from server.events import (
    HeartbeatEvent, StartRecordingSignalsEvent, StopRecordingSignalsEvent, TrainPredictionModelEvent, TrainingProgressEvent)
from server.models import Room, Scanner, DeviceHeartbeat


async def prepare_training_data(device):
    heartbeats = await DeviceHeartbeat.filter(device_id=device.id)
    rooms = await Room.all()
    scanners = await Scanner.all()

    if set(r.id for r in rooms) != set(h.room_id for h in heartbeats):
        raise Exception('Not every room covered with data')

    X_data = []
    y_data = []
    for heartbeat in heartbeats:
        X_data_row = []
        y_data_row = heartbeat.room_id

        signals = heartbeat.signals
        for scanner in scanners:
            signal = signals.get(scanner.uuid, {})
            X_data_row.append(signal.get('distance', MAX_DISTANCE))

        X_data.append(X_data_row)
        y_data.append(y_data_row)

    return X_data, y_data


def log_progress(device, message, **kwargs):
    print(message)
    eventbus.post(TrainingProgressEvent(device=device, message=message, **kwargs))


def train_model(device, name, clf, X_train, y_train):
    t2 = time.time()
    log_progress(device, "learning {}".format(name))
    try:
        algorithm = clf.train(X_train, y_train)
        log_progress(device, "learned {}, in {:d} ms".format(name, int(1000 * (t2 - time.time()))))
        return name, algorithm
    except Exception as e:
        log_progress("{} {}".format(name, str(e)), is_error=True)
        return name, None


class Learn:
    def __init__(self):
        self.recording_room = None
        self.recording_device = None
        eventbus.register(self, self.__class__.__name__)

    @subscribe(on_event=StartRecordingSignalsEvent)
    def handle_start_recording(self, event):
        self.recording_room = event.room
        self.recording_device = event.device

    @subscribe(on_event=StopRecordingSignalsEvent)
    def handle_stop_recording(self, event):
        self.recording_room = None
        self.recording_device = None

    @subscribe(on_event=HeartbeatEvent)
    async def handle_device_heartbeat(self, event):
        if (not event.signals
                or not self.recording_room
                or not self.recording_device
                or event.device != self.recording_device):
            return

        await DeviceHeartbeat.create(
            device_id=event.device.id,
            room_id=self.recording_room.id,
            signals=event.signals,
        )

    @subscribe(on_event=TrainPredictionModelEvent)
    async def handle_train_model(self, event):
        device = event.device
        loop = asyncio.get_running_loop()
        X, y = await prepare_training_data(event.device)
        X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)

        classifiers = {
            "Nearest Neighbors": KNeighborsClassifier(3),
            "Linear SVM": SVC(kernel="linear", C=0.025, probability=True),
            "RBF SVM": SVC(gamma=2, C=1, probability=True),
            "Decision Tree": DecisionTreeClassifier(max_depth=5),
            "Random Forest": RandomForestClassifier(
                max_depth=5, n_estimators=10, max_features=1),
            "Neural Net": MLPClassifier(alpha=1),
            "AdaBoost": AdaBoostClassifier(),
            "Naive Bayes": GaussianNB(),
            "QDA": QuadraticDiscriminantAnalysis()
        }

        with concurrent.futures.ThreadPoolExecutor() as pool:
            def run_train_coroutine(name, clf):
                return loop.run_in_executor(pool, train_model, device, name, clf, X_train, y_train)

            train_coros = [run_train_coroutine(name, clf) for name, clf in classifiers.items()]

        await asyncio.gather(*train_coros)

