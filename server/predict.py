from server.eventbus import EventBusSubscriber, subscribe
from server.events import HeartbeatEvent, OccupancyEvent


class Predict(EventBusSubscriber):

    @subscribe(HeartbeatEvent)
    def handle_device_heartbeat(self, event):
        # print(event)
        pass
