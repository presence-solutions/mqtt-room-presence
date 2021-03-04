from pyeventbus3.pyeventbus3 import PyBus, subscribe, Mode
from events import OccupancyEvent


class Sensor:
    def __init__(self):
        self.bus = PyBus.Instance()
        self.bus.register(self, self.__class__.__name__)

    @subscribe(threadMode=Mode.GREENLET, onEvent=OccupancyEvent)
    def handleDeviceOccupancy(self, event):
        pass