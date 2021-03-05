from server.events import MQTTConnectedEvent, MQTTMessage
from server.eventbus import Mode, eventbus, subscribe

SCANNERS_TOPIC = 'room_presence/'


class Heartbeat:
    def __init__(self):
        print('Init heartbeat', flush=True)
        eventbus.register(self, self.__class__.__name__)

    @subscribe(on_event=MQTTConnectedEvent)
    def handle_mqtt_connect(self, event):
        self.mqtt = event.client
        self.mqtt.subscribe('{}#'.format(SCANNERS_TOPIC))

    @subscribe(on_event=MQTTMessage, thread_mode=Mode.PARALLEL)
    def handle_mqtt_message(self, event):
        if not event.topic.startswith(SCANNERS_TOPIC):
            return

        print('Message received', event, flush=True)
