import asyncio
from server.events import DeviceAddedEvent, DeviceRemovedEvent, HeartbeatEvent, MQTTConnectedEvent, MQTTMessageEvent
from server.eventbus import Mode, eventbus, subscribe
from server.kalman import KalmanRSSI
from datetime import datetime
from server.constants import (
    SCANNERS_TOPIC, DEFAULT_TX_POWER, MAX_SIGNAL_BEATS_AGE, HEARTBEAT_COLLECT_PERIOD_SEC,
    HEARTBEAT_SIGNAL_WAIT_SEC, MAX_DISTANCE, KALMAN_R, KALMAN_Q)


def calculate_rssi_distance(signal):
    measuredPower = DEFAULT_TX_POWER  # signal.get('txPower', DEFAULT_TX_POWER)
    ratio = signal['filtered_rssi'] / measuredPower

    if ratio < 1:
        return round(pow(ratio, 10), 1)

    return round(0.89976 * pow(ratio, 7.7095) + 0.111, 1)


def prepare_heratbeat(signals, latest_beat):
    final_signals = {}
    for key, value in signals.items():
        distance = value['distance']
        if distance > MAX_DISTANCE or (latest_beat - value['beat_idx']) > MAX_SIGNAL_BEATS_AGE:
            distance = MAX_DISTANCE

        final_signals[key] = {
            'distance': distance,
            'filtered_rssi': value['filtered_rssi'],
            'raw_rssi': value['raw_rssi'],
        }

    return final_signals


class DeviceTracker:
    WAIT_FOR_SIGNAL = 1
    COLLECTING_DATA = 2

    def __init__(self, device):
        print('here', device)
        self.device = device
        self.state = None
        self.coroutine = None
        self.latest_signals = {}
        self.rssi_filters = {}
        self.beat_counter = 0

    def stop(self):
        self.state = None
        self.latest_signals = {}
        self.rssi_filters = {}
        self.beat_counter = 0
        if self.coroutine:
            self.coroutine.cancel()

    def track(self):
        self.state = DeviceTracker.WAIT_FOR_SIGNAL
        self.coroutine = asyncio.create_task(self.wait_for_signal())

    def process_signal(self, scanner_uuid, signal):
        if self.state == DeviceTracker.WAIT_FOR_SIGNAL:
            self.coroutine.cancel()
            self.beat_counter += 1
            self.state = DeviceTracker.COLLECTING_DATA
            self.coroutine = asyncio.create_task(self.send_heartbeat())

        signal['beat_idx'] = self.beat_counter
        self.latest_signals[scanner_uuid] = self.filter_signal(scanner_uuid, signal)

    def filter_signal(self, scanner_uuid, signal):
        scanner_filter = self.rssi_filters.get(scanner_uuid)
        filtered_signal = dict(signal)

        if not scanner_filter:
            scanner_filter = KalmanRSSI(R=KALMAN_R, Q=KALMAN_Q)
            self.rssi_filters[scanner_uuid] = scanner_filter

        filtered_signal['raw_rssi'] = filtered_signal['rssi']
        filtered_signal['filtered_rssi'] = scanner_filter.filter(filtered_signal['rssi'])
        filtered_signal['distance'] = calculate_rssi_distance(filtered_signal)

        return filtered_signal

    async def wait_for_signal(self):
        await asyncio.sleep(HEARTBEAT_SIGNAL_WAIT_SEC)
        eventbus.post(HeartbeatEvent(
            device=self.device, signals=None, timestamp=datetime.now()))
        self.track()

    async def send_heartbeat(self):
        await asyncio.sleep(HEARTBEAT_COLLECT_PERIOD_SEC)

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

    @subscribe(on_event=DeviceAddedEvent)
    def handle_device_added(self, event):
        if event.device.identifier in self.device_trackers:
            self.device_trackers[event.device.identifier].stop()

        tracker = DeviceTracker(event.device)
        self.device_trackers[event.device.identifier] = tracker
        tracker.track()

    @subscribe(on_event=DeviceRemovedEvent)
    def handle_device_removed(self, event):
        if event.device.identifier in self.device_trackers:
            self.device_trackers[event.device.identifier].stop()
            del self.device_trackers[event.device.identifier]

    @subscribe(on_event=MQTTConnectedEvent)
    async def handle_mqtt_connect(self, event):
        await event.client.subscribe('{}#'.format(SCANNERS_TOPIC))

    @subscribe(on_event=MQTTMessageEvent)
    def handle_mqtt_message(self, event):
        if not event.topic.startswith(SCANNERS_TOPIC):
            return

        device_uuid = event.payload.get('uuid')
        device_name = event.payload.get('name')
        tracker = self.device_trackers.get(device_uuid) or self.device_trackers.get(device_name)

        if tracker:
            tracker.process_signal(
                event.topic.split('/')[1],
                event.payload
            )
