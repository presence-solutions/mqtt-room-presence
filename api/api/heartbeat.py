from pyeventbus3.pyeventbus3 import PyBus, subscribe, Mode


class Heartbeat:
    def __init__(self):
        self.bus = PyBus.Instance()
        self.bus.register(self, self.__class__.__name__)
