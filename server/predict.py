from server.eventbus import subscribe, eventbus, Mode
from server.events import HeartbeatEvent, OccupancyEvent


class Predict:
    def __init__(self):
        eventbus.register(self, self.__class__.__name__)

    @subscribe(thread_mode=Mode.PARALLEL, on_event=HeartbeatEvent)
    def handle_device_heartbeat(self, event):
        print('predicting...', event)
        # eventbus.post(OccupancyEvent())
