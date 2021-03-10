from server.eventbus import EventBusSubscriber, subscribe
from server.events import MQTTConnectedEvent, OccupancyEvent


class Sensor(EventBusSubscriber):

    @subscribe(MQTTConnectedEvent)
    def handle_mqtt_connect(self, event):
        print('connected', flush=True)

    @subscribe(OccupancyEvent)
    def handle_device_occupancy(self, event):
        pass
