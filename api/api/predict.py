from pyeventbus3.pyeventbus3 import PyBus, subscribe, Mode
from events import HeartbeatEvent, OccupancyEvent


class Predict:
    def __init__(self):
        self.bus = PyBus.Instance()
        self.bus.register(self, self.__class__.__name__)

    @subscribe(threadMode=Mode.GREENLET, onEvent=HeartbeatEvent)
    def handleDeviceHeartbeat(self, event):
        self.bus.post(OccupancyEvent())
