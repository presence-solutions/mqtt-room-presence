from server.eventbus import subscribe, eventbus, Mode
from server.events import MQTTConnectedEvent, OccupancyEvent


class Sensor:
    def __init__(self):
        eventbus.register(self, self.__class__.__name__)

    @subscribe(on_event=MQTTConnectedEvent)
    def handle_mqtt_connect(self, event):
        print('connected', flush=True)

    @subscribe(on_event=OccupancyEvent)
    def handle_device_occupancy(self, event):
        pass
