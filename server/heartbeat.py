import eventlet
from server.events import DeviceAdded, DeviceRemoved, HeartbeatEvent, MQTTConnectedEvent, MQTTMessage
from server.eventbus import Mode, eventbus, subscribe
from server.kalman import KalmanRSSI
from datetime import datetime

SCANNERS_TOPIC = 'room_presence/'
DEFAULT_TX_POWER = -72
MAX_SIGNAL_BEATS_AGE = 2
HEARTBEAT_COLLECT_PERIOD_SEC = 0.5
HEARTBEAT_SIGNAL_WAIT_SEC = 60
MAX_DISTANCE = 30
KALMAN_R = 0.08
KALMAN_Q = 15


def calculate_rssi_distance(signal):
    measuredPower = signal.get('txPower', DEFAULT_TX_POWER)
    measuredPower = measuredPower * -1 if measuredPower > 0 else measuredPower
    ratio = signal['rssi'] / measuredPower

    if ratio < 1:
        return round(pow(ratio, 10), 1)

    return round(0.89976 * pow(ratio, 7.7095) + 0.111, 1)


def prepare_heratbeat(signals, latest_beat):
    final_signals = {}
    for key, value in signals.items():
        distance = value['distance']
        if distance > MAX_DISTANCE or (latest_beat - value['beat_idx']) > MAX_SIGNAL_BEATS_AGE:
            distance = MAX_DISTANCE
        final_signals[key] = distance
    return final_signals


class DeviceTracker:
    WAIT_FOR_SIGNAL = 1
    COLLECTING_DATA = 2

    def __init__(self, device):
        self.device = device
        self.state = None
        self.greenlet = None
        self.latest_signals = {}
        self.rssi_filters = {}
        self.beat_counter = 0

    def stop(self):
        self.state = None
        self.latest_signals = {}
        self.rssi_filters = {}
        self.beat_counter = 0
        if self.greenlet:
            eventlet.kill(self.greenlet)

    def track(self):
        self.state = DeviceTracker.WAIT_FOR_SIGNAL
        self.greenlet = eventlet.spawn_n(self.wait_for_signal)

    def process_signal(self, scanner_uuid, signal):
        if self.state == DeviceTracker.WAIT_FOR_SIGNAL:
            eventlet.kill(self.greenlet)
            self.state = DeviceTracker.COLLECTING_DATA
            self.greenlet = eventlet.spawn_after(HEARTBEAT_COLLECT_PERIOD_SEC, self.send_heartbeat)
            self.beat_counter += 1

        signal['beat_idx'] = self.beat_counter
        self.latest_signals[scanner_uuid] = self.filter_signal(scanner_uuid, signal)

    def filter_signal(self, scanner_uuid, signal):
        scanner_filter = self.rssi_filters.get(scanner_uuid)
        filtered_signal = dict(signal)

        if not scanner_filter:
            scanner_filter = KalmanRSSI(R=KALMAN_R, Q=KALMAN_Q)
            self.rssi_filters[scanner_uuid] = scanner_filter

        filtered_signal['rssi'] = scanner_filter.filter(filtered_signal['rssi'])
        filtered_signal['distance'] = calculate_rssi_distance(filtered_signal)

        return filtered_signal

    def wait_for_signal(self):
        eventlet.sleep(HEARTBEAT_SIGNAL_WAIT_SEC)
        eventbus.post(HeartbeatEvent(
            device=self.device, signals=None, timestamp=datetime.now()))
        self.track()

    def send_heartbeat(self):
        if self.state != DeviceTracker.COLLECTING_DATA:
            return

        heartbeat_signals = prepare_heratbeat(self.latest_signals, self.beat_counter)
        self.track()

        eventbus.post(HeartbeatEvent(
            device=self.device, signals=heartbeat_signals, timestamp=datetime.now()))


class Heartbeat:
    def __init__(self):
        self.device_trackers = {}
        eventbus.register(self, self.__class__.__name__)

    @subscribe(on_event=DeviceAdded, thread_mode=Mode.PARALLEL)
    def handle_device_added(self, event):
        if event.device.uuid in self.device_trackers:
            self.device_trackers[event.device.uuid].stop()

        tracker = DeviceTracker(event.device)
        self.device_trackers[event.device.uuid] = tracker
        tracker.track()

    @subscribe(on_event=DeviceRemoved)
    def handle_device_removed(self, event):
        if event.device.uuid in self.device_trackers:
            self.device_trackers[event.device.uuid].stop()
            del self.device_trackers[event.device.uuid]

    @subscribe(on_event=MQTTConnectedEvent)
    def handle_mqtt_connect(self, event):
        self.mqtt = event.client
        self.mqtt.subscribe('{}#'.format(SCANNERS_TOPIC))

    @subscribe(on_event=MQTTMessage)
    def handle_mqtt_message(self, event):
        if not event.topic.startswith(SCANNERS_TOPIC):
            return

        device_uuid = event.payload.get('uuid')
        if device_uuid in self.device_trackers:
            self.device_trackers[device_uuid].process_signal(
                event.topic.split('/')[1],
                event.payload
            )
