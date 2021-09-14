import pickle
import concurrent.futures
import asyncio
import pandas as pd
import numpy as np

from server.heartbeat import SimulatedDeviceTracker, normalize_scanner_payload
from server.constants import HEARTBEAT_COLLECT_PERIOD_SEC, LEARNING_WARMUP_DELAY_SEC
from server.utils import calculate_inputs_hash

from sklearn import metrics
from sklearn.ensemble import RandomForestClassifier
from sklearn.multiclass import OneVsRestClassifier

from server.eventbus import EventBusSubscriber, subscribe
from server.events import (
    DeviceSignalEvent, HeartbeatEvent, RegenerateHeartbeatsEvent, StartRecordingSignalsEvent,
    StopRecordingSignalsEvent, TrainPredictionModelEvent)
from server.models import (
    DeviceSignal, PredictionModel, DeviceHeartbeat, Scanner, LearningSession, get_rooms_scanners)


async def prepare_training_data(device):
    heartbeats = await DeviceHeartbeat.filter(device_id=device.id).prefetch_related('room')
    rooms, scanners = await get_rooms_scanners()
    inputs_hash = await calculate_inputs_hash(rooms, scanners)

    if set(r.id for r in rooms) != set(h.room_id for h in heartbeats):
        raise Exception('Not every room covered with data')

    scanners = [s.uuid for s in scanners]
    default_heartbeat = dict(zip(scanners, [-100] * len(scanners)))
    heartbeats_df = pd.DataFrame([{**default_heartbeat, **h.signals, 'room': h.room.id} for h in heartbeats])
    heartbeats_df.drop_duplicates(inplace=True)
    heartbeats_target = heartbeats_df.room.values
    heartbeats_data = heartbeats_df.iloc[:, :-1]

    return heartbeats_data, heartbeats_target, inputs_hash


def weighted_f_score(y_true, y_pred, *, average='micro', verbose=False):
    scores = np.array(metrics.fbeta_score(y_true, y_pred, beta=10, average=None))
    if verbose:
        print(scores)
    if average is not None:
        return scores.mean() - 4 * scores.std()
    return scores


def train_model(X, y):
    try:
        super_scoring = metrics.make_scorer(weighted_f_score)
        estimator = OneVsRestClassifier(RandomForestClassifier(n_jobs=-1))
        estimator.fit(X, y)
        score = super_scoring(estimator, X, y)
        return estimator, score, None
    except Exception as e:
        return None, None, e


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
        to_skip = LEARNING_WARMUP_DELAY_SEC
        period = HEARTBEAT_COLLECT_PERIOD_SEC
        signals = await DeviceSignal.filter(learning_session=session).prefetch_related('scanner')
        start_time = min(signals, key=lambda x: x.created_at.timestamp()).created_at.timestamp()
        end_time = max(signals, key=lambda x: x.created_at.timestamp()).created_at.timestamp()
        tracker = SimulatedDeviceTracker(device=device)
        last_signal_index = 0

        for curr_time in range(int(start_time + period - 1), int(end_time + period), period):
            for i in range(last_signal_index, len(signals)):
                signal_ts = signals[i].created_at.timestamp()
                if signal_ts > curr_time - period and signal_ts <= curr_time:
                    tracker.process_signal(signals[i].scanner.uuid, normalize_scanner_payload({
                        'uuid': signals[i].scanner.uuid,
                        'rssi': signals[i].rssi,
                        'when': signal_ts,
                    }))
                else:
                    last_signal_index = i
                    break

            if to_skip > 0:
                to_skip -= period
            else:
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

    def is_learning_started(self, device, warm=True):
        return ((not warm or (self.warmup_coroutine and self.warmup_coroutine.done()))
                and self.recording_room
                and self.recording_device == device)

    @subscribe(DeviceSignalEvent)
    async def handle_device_signal(self, event):
        if not self.is_learning_started(event.device, warm=False):
            return

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
        print('Run training of the models')

        with concurrent.futures.ThreadPoolExecutor() as pool:
            train_result = loop.run_in_executor(pool, train_model, X, y)

        train_result = (await asyncio.gather(train_result))[0]

        if train_result[2] is not None:
            print('There is an error while fitting the model: ', train_result[2])
        else:
            print('Training is done! Results: {}'.format(train_result))
            result = await PredictionModel.create(
                accuracy=train_result[1],
                model=pickle.dumps(train_result[0]),
                inputs_hash=inputs_hash,
            )
            await result.devices.add(device)
