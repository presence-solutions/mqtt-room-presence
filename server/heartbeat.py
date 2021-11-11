import asyncio

from server.events import (
    DeviceAddedEvent, DeviceRemovedEvent, DeviceSignalEvent, HeartbeatEvent, MQTTConnectedEvent, MQTTMessageEvent,
    StartRecordingSignalsEvent)
from server.eventbus import EventBusSubscriber, eventbus, subscribe
from server.kalman import KalmanRSSI
from datetime import datetime
from server.constants import (
    SCANNERS_TOPIC, OFF_ON_DELAY_SEC, HEARTBEAT_COLLECT_PERIOD_SEC)


def normalize_uuid(uuid: str):
    return uuid.replace(':', '').lower()


def normalize_scanner_payload(payload):
    return {
        'name': payload.get('name', ''),
        'uuid': normalize_uuid(payload.get('uuid', '')),
        'rssi': int(payload.get('rssi', '-100')),
        'when': payload.get('when', datetime.now().timestamp()),
    }


class HeratbeatGenerator:
    def __init__(self, scanners=None, kalman=None, penalty=None, off_on_delay=None) -> None:
        scanners = scanners or []
        self.values = dict(zip(scanners, [-100] * len(scanners)))
        self.delay = dict(zip(scanners, [0] * len(scanners)))
        self.last_time = dict(zip(scanners, [0] * len(scanners)))
        self.appeared = dict(zip(scanners, [False] * len(scanners)))
        self.penalty = penalty
        self.off_on_delay = off_on_delay
        self.filters = {} if kalman is not None else None
        self.kalman = kalman

    def process(self, signals, time, period):
        silent_scanners = set(self.values.keys())

        for s in signals:
            scanner = s['scanner']
            if self.kalman:
                if scanner not in self.filters:
                    self.filters[scanner] = KalmanRSSI(R=self.kalman[0], Q=self.kalman[1])
                self.values[scanner] = self.filters[scanner].filter(s['rssi'])
            else:
                self.values[scanner] = s['rssi']

            self.appeared[scanner] = True
            self.last_time[scanner] = s['when']

            silent_scanners -= set([scanner])

        for scanner in self.values.keys():
            if self.appeared.get(scanner, False):
                self.delay[scanner] = time - self.last_time[scanner]
            else:
                self.delay[scanner] += period

        if self.penalty is not None and self.penalty > 0:
            for scanner in silent_scanners:
                if self.values[scanner] > -100:
                    self.values[scanner] -= self.penalty
                    self.values[scanner] = max(self.values[scanner], -100)
                if self.filters:
                    self.filters[scanner].filter(self.values[scanner])

        if self.off_on_delay is not None and self.off_on_delay > 0:
            for scanner in silent_scanners:
                if self.delay[scanner] >= self.off_on_delay and self.values[scanner] > -100:
                    self.values[scanner] = -100
                if self.filters:
                    self.filters[scanner].filter(self.values[scanner])

        return self.create_heartbeat(signals, time)

    def create_heartbeat(self, signals, time):
        return dict(self.values)


class DeviceTracker:
    def __init__(self, device):
        self.device = device
        self.coroutine = None
        self.reset_generator()

    @subscribe(StartRecordingSignalsEvent)
    def handle_start_recording(self, event):
        self.reset_generator()

    def stop(self):
        if self.coroutine:
            self.coroutine.cancel()
            self.coroutine = None
        self.reset_generator()

    def track(self):
        self.coroutine = asyncio.create_task(self.next_cycle())

    def process_signal(self, scanner_uuid, signal):
        self.collected_signals.append({
            'scanner': scanner_uuid,
            'rssi': signal['rssi'],
            'when': float(signal['when'])
        })
        self.send_device_signal(scanner_uuid, signal)

    def reset_generator(self):
        self.collected_signals = []
        self.last_heartbeat = None
        self.gen = HeratbeatGenerator(off_on_delay=OFF_ON_DELAY_SEC)

    async def next_cycle(self):
        await asyncio.sleep(HEARTBEAT_COLLECT_PERIOD_SEC)
        self.create_heartbeat()
        self.track()

    def create_heartbeat(self, timestamp=None):
        timestamp = timestamp or datetime.now().timestamp()
        signals = self.collected_signals
        self.collected_signals = []
        heartbeat = self.gen.process(
            signals, timestamp, HEARTBEAT_COLLECT_PERIOD_SEC)

        if heartbeat != self.last_heartbeat and len(heartbeat) > 0:
            self.last_heartbeat = heartbeat
            final_heartbeat = heartbeat if max(heartbeat.values()) > -100 else None
            self.send_heartbeat_event(HeartbeatEvent(
                device=self.device, signals=final_heartbeat, timestamp=timestamp))

    def send_heartbeat_event(self, event):
        eventbus.post(event)

    def send_device_signal(self, scanner_uuid, signal):
        print('Processed signal from {} / {}, rssi {}'.format(
            self.device.name, scanner_uuid, signal['rssi']))

        eventbus.post(DeviceSignalEvent(device=self.device, signal=signal, scanner_uuid=scanner_uuid))


class SimulatedDeviceTracker(DeviceTracker):
    def __init__(self, device):
        super().__init__(device)
        self.heartbeats = []

    def stop(self):
        super().stop()
        self.heartbeats = []

    def track(self):
        pass

    def send_heartbeat_event(self, event):
        if event.signals is not None:
            self.heartbeats.append(event.signals)

    def send_device_signal(self, scanner_uuid, signal):
        pass


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
