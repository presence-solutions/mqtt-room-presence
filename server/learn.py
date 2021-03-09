import time
from threading import Thread
import functools

from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.neighbors import KNeighborsClassifier
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, AdaBoostClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis

from server.constants import MAX_DISTANCE
from server.eventbus import subscribe, eventbus, Mode
from server.events import (
    HeartbeatEvent, StartRecordingSignalsEvent, StopRecordingSignalsEvent, TrainPredictionModelEvent, TrainingProgressEvent)
from server.models import Room, Scanner, DeviceHeartbeat, Session


def timeout(timeout):
    def deco(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            res = [Exception('function [%s] timeout [%s seconds] exceeded!' % (
                func.__name__, timeout))]

            def newFunc():
                try:
                    res[0] = func(*args, **kwargs)
                except Exception as e:
                    res[0] = e
            t = Thread(target=newFunc)
            t.daemon = True
            try:
                t.start()
                t.join(timeout)
            except Exception as je:
                raise je
            ret = res[0]
            if isinstance(ret, BaseException):
                raise ret
            return ret
        return wrapper
    return deco


def prepare_training_data(device):
    session = Session()
    heartbeats = session.query(DeviceHeartbeat).filter(device_id=device.id)
    rooms = session.query(Room)
    scanners = session.query(Scanner).order_by(Scanner.id)

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


@timeout(10)
def train(clf, x, y):
    return clf.fit(x, y)


class Learn:
    def __init__(self):
        self.recording_room = None
        self.recording_device = None
        self.db_session = Session()
        eventbus.register(self, self.__class__.__name__)

    @subscribe(on_event=StartRecordingSignalsEvent)
    def handle_start_recording(self, event):
        self.recording_room = event.room
        self.recording_device = event.device

    @subscribe(on_event=StopRecordingSignalsEvent)
    def handle_stop_recording(self, event):
        self.recording_room = None
        self.recording_device = None

    @subscribe(thread_mode=Mode.BACKGROUND, on_event=HeartbeatEvent)
    def handle_device_heartbeat(self, event):
        if (not event.signals
                or not self.recording_room
                or not self.recording_device
                or event.device != self.recording_device):
            return

        self.db_session.add(DeviceHeartbeat(
            device_id=event.device.id,
            room_id=self.recording_room.id,
            signals=event.signals,
        ))
        self.db_session.commit()

    @subscribe(thread_mode=Mode.COROUTINE, on_event=TrainPredictionModelEvent)
    def handle_train_model(self, event):
        device = event.device
        X, y = prepare_training_data(event.device)
        X_train, X_test, y_train, y_test = train_test_split(X, y, random_state=0)

        algorithms = {}
        accuracies = {}
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

        def log_progress(message, **kwargs):
            print(message)
            eventbus.post(TrainingProgressEvent(device=device, message=message, **kwargs))

        for name, clf in classifiers.items():
            t2 = time.time()
            log_progress("learning {}".format(name))
            try:
                algorithms[name] = train(clf, X_train, y_train)
                accuracies[name] = algorithms[name].score(X_test, y_test)
                log_progress("learned {}, accuracy {}, in {:d} ms".format(
                    name, accuracies[name], int(1000 * (t2 - time.time()))))
            except Exception as e:
                log_progress("{} {}".format(name, str(e)), is_error=True)
