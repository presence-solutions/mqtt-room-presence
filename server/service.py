from server.heartbeat import Heartbeat
from server.learn import Learn
from server.predict import Predict
from server.sensor import Sensor


class Service:
    def __init__(self) -> None:
        self.hearbeat = Heartbeat()
        self.learn = Learn()
        self.predict = Predict()
        self.sensor = Sensor()
