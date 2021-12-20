import asyncio
import logging

from server.events import (
    DeviceAddedEvent, DeviceRemovedEvent, DeviceSignalEvent, HeartbeatEvent, MQTTConnectedEvent, MQTTMessageEvent,
    StartRecordingSignalsEvent)
from server.eventbus import EventBusSubscriber, eventbus, subscribe
from server.kalman import KalmanRSSI
from datetime import datetime
from server.constants import (
    SCANNERS_TOPIC, LONG_DELAY_PENALTY_SEC, HEARTBEAT_COLLECT_PERIOD_SEC, KALMAN_R, KALMAN_Q, TURN_OFF_DEVICE_SEC)


def normalize_uuid(uuid: str):
    return uuid.replace(':', '').lower()


def normalize_scanner_payload(payload):
    return {
        'name': payload.get('name', ''),
        'uuid': normalize_uuid(payload.get('uuid', '')),
        'rssi': int(payload.get('rssi', '-100')),
        'when': payload.get('when', datetime.now().timestamp()),
    }


class UnfilteredRSSI():
    def __init__(self) -> None:
        self.x = -100

    def filter(self, x):
        self.x = x
        return x


class HeratbeatGenerator:
    def __init__(
        self, scanners=None, kalman=None, silent_scanner_penalty=None, long_delay=None,
        turn_off_delay=None, device=None
    ) -> None:
        scanners = scanners or []
        self.values = dict(zip(scanners, [-100] * len(scanners)))
        self.last_change = dict(zip(scanners, [0] * len(scanners)))
        self.last_signal = dict(zip(scanners, [0] * len(scanners)))
        self.appeared = dict(zip(scanners, [True] * len(scanners)))
        self.silent_scanner_penalty = silent_scanner_penalty
        self.turn_off_delay = turn_off_delay
        self.long_delay = long_delay
        self.filters = {} if kalman is not None else None
        self.kalman = kalman
        self.device = device

    def process(self, signals, time, period):
        silent_scanners = set(self.values.keys())

        for s in signals:
            scanner = s['scanner']
            silent_scanners -= set([scanner])

            if scanner not in self.filters:
                if self.kalman:
                    self.filters[scanner] = KalmanRSSI(R=self.kalman[0], Q=self.kalman[1])
                else:
                    self.filters[scanner] = UnfilteredRSSI()

            self.values[scanner] = self.filters[scanner].filter(s['rssi'])
            self.appeared[scanner] = True
            self.last_change[scanner] = s['when']
            self.last_signal[scanner] = s['when']

        for scanner in self.values.keys():
            last_change_delay = time - self.last_change[scanner]
            last_signal_delay = time - self.last_signal[scanner]

            if self.silent_scanner_penalty is not None and scanner in silent_scanners:
                penalty_signal = max(self.values.get(scanner, -100) - self.silent_scanner_penalty, -100)
                self.values[scanner] = self.filters[scanner].filter(penalty_signal)
                self.last_change[scanner] = time
                logging.info('%s scanner %s silent scanner penalty', repr(self.device), scanner)

            if self.turn_off_delay is not None and last_signal_delay >= self.turn_off_delay:
                self.values[scanner] = self.filters[scanner].reset(-100.0)
                self.last_change[scanner] = time
                self.last_signal[scanner] = time
                logging.info('%s scanner %s turn off penalty', repr(self.device), scanner)

            elif self.long_delay is not None and last_change_delay >= self.long_delay:
                self.values[scanner] = self.filters[scanner].filter(-100)
                self.last_change[scanner] = time
                logging.info('%s scanner %s long delay penalty', repr(self.device), scanner)

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
        self.gen = HeratbeatGenerator(
            long_delay=LONG_DELAY_PENALTY_SEC, kalman=(KALMAN_R, KALMAN_Q),
            turn_off_delay=TURN_OFF_DEVICE_SEC, device=self.device)

    async def next_cycle(self):
        try:
            await asyncio.sleep(HEARTBEAT_COLLECT_PERIOD_SEC)
            self.create_heartbeat()
            self.track()
        except Exception as e:
            logging.error(e)

    def create_heartbeat(self, timestamp=None):
        timestamp = timestamp or datetime.now().timestamp()
        signals = self.collected_signals
        self.collected_signals = []
        heartbeat = self.gen.process(
            signals, timestamp, HEARTBEAT_COLLECT_PERIOD_SEC)

        if heartbeat != self.last_heartbeat and len(heartbeat) > 0:
            self.last_heartbeat = heartbeat
            final_heartbeat = heartbeat if max(heartbeat.values()) > -99.0 else None
            self.send_heartbeat_event(HeartbeatEvent(
                device=self.device, signals=final_heartbeat, timestamp=timestamp))

    def send_heartbeat_event(self, event):
        eventbus.post(event)

    def send_device_signal(self, scanner_uuid, signal):
        eventbus.post(DeviceSignalEvent(device=self.device, signal=signal, scanner_uuid=scanner_uuid))


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
