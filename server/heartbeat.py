import asyncio
from server.events import DeviceAddedEvent, DeviceRemovedEvent, DeviceSignalEvent, HeartbeatEvent, MQTTConnectedEvent, MQTTMessageEvent
from server.eventbus import EventBusSubscriber, eventbus, subscribe
from server.kalman import KalmanRSSI
from datetime import datetime
from server.constants import (
    SCANNERS_TOPIC, DEFAULT_TX_POWER, HEARTBEAT_COLLECT_PERIOD_SEC,
    HEARTBEAT_SIGNAL_WAIT_SEC, KALMAN_R, KALMAN_Q, SCANNER_WAIT_TIMEOUT_SEC)


def prepare_heratbeat(signals, latest_beat):
    final_signals = {}
    current_timestamp = datetime.now()

    for key, value in signals.items():
        if (current_timestamp - value['timestamp']).total_seconds() > SCANNER_WAIT_TIMEOUT_SEC:
            final_signals[key] = {
                'filtered_rssi': -100,
                'raw_rssi': -100,
            }
        else:
            final_signals[key] = {
                'filtered_rssi': value['filtered_rssi'],
                'raw_rssi': value['raw_rssi'],
            }

    return final_signals


def normalize_uuid(uuid: str):
    return uuid.replace(':', '').lower()


def normalize_tx_power(tx_power: str or int):
    return -abs(int(tx_power))


def normalize_scanner_payload(payload):
    return {
        'name': payload.get('name', ''),
        'uuid': normalize_uuid(payload.get('uuid', '')),
        'rssi': int(payload.get('rssi', '-100')),
        'txPower': normalize_tx_power(payload.get('txPower', DEFAULT_TX_POWER)),
    }


class DeviceTracker:
    WAIT_FOR_SIGNAL = 1
    COLLECTING_DATA = 2

    def __init__(self, device):
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
        signal = self.filter_signal(scanner_uuid, signal)
        self.latest_signals[scanner_uuid] = signal

        eventbus.post(DeviceSignalEvent(device=self.device, signal=signal, scanner_uuid=scanner_uuid))

    def filter_signal(self, scanner_uuid, signal):
        scanner_filter = self.rssi_filters.get(scanner_uuid)
        filtered_signal = dict(signal)

        if not scanner_filter:
            scanner_filter = KalmanRSSI(R=KALMAN_R, Q=KALMAN_Q)
            self.rssi_filters[scanner_uuid] = scanner_filter

        filtered_signal['raw_rssi'] = filtered_signal['rssi']
        filtered_signal['filtered_rssi'] = scanner_filter.filter(filtered_signal['rssi'])
        filtered_signal['timestamp'] = datetime.now()

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


class Heartbeat(EventBusSubscriber):
    def __init__(self):
        super().__init__()
        self.device_trackers = {}

    @subscribe(DeviceAddedEvent)
    def handle_device_added(self, event):
        if event.device.identifier in self.device_trackers:
            self.device_trackers[event.device.identifier].stop()

        tracker = DeviceTracker(event.device)
        self.device_trackers[event.device.identifier] = tracker
        tracker.track()

    @subscribe(DeviceRemovedEvent)
    def handle_device_removed(self, event):
        if event.device.identifier in self.device_trackers:
            self.device_trackers[event.device.identifier].stop()
            del self.device_trackers[event.device.identifier]

    @subscribe(MQTTConnectedEvent)
    async def handle_mqtt_connect(self, event):
        await event.client.subscribe('{}#'.format(SCANNERS_TOPIC))

    @subscribe(MQTTMessageEvent)
    def handle_mqtt_message(self, event):
        if not event.topic.startswith(SCANNERS_TOPIC):
            return

        payload = normalize_scanner_payload(event.payload)
        tracker = (
            self.device_trackers.get(payload['uuid'])
            or self.device_trackers.get(payload['name'])
        )

        if tracker:
            tracker.process_signal(
                event.topic.split('/')[1],
                payload
            )
