from server.events import DeviceAdded, DeviceRemoved, MQTTConnectedEvent, MQTTMessage
from server.eventbus import Mode, eventbus, subscribe

SCANNERS_TOPIC = 'room_presence/'


class DeviceTracker:
    def __init__(self, device):
        self.device = device

    def kill(self):
        pass

    def track(self):
        pass


class Heartbeat:
    def __init__(self):
        self.device_trackers = {}
        eventbus.register(self, self.__class__.__name__)

    @subscribe(on_event=DeviceAdded)
    def handle_device_added(self, event):
        self.kill_device(event)
        if event.device.uuid in self.device_trackers:
            self.device_trackers[event.device.uuid].kill()

        tracker = DeviceTracker(event.device)
        self.device_trackers[event.device.uuid] = tracker
        tracker.track()

    @subscribe(on_event=DeviceRemoved)
    def handle_device_removed(self, event):
        if event.device.uuid in self.device_trackers:
            self.device_trackers[event.device.uuid].kill()

    @subscribe(on_event=MQTTConnectedEvent)
    def handle_mqtt_connect(self, event):
        self.mqtt = event.client
        self.mqtt.subscribe('{}#'.format(SCANNERS_TOPIC))

    @subscribe(on_event=MQTTMessage, thread_mode=Mode.PARALLEL)
    def handle_mqtt_message(self, event):
        if not event.topic.startswith(SCANNERS_TOPIC):
            return
        pass
