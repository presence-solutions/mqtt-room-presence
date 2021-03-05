from server.eventbus import eventbus
from server.events import DeviceAdded
from server.heartbeat import Heartbeat
from server.learn import Learn
from server.predict import Predict
from server.sensor import Sensor
from server.models import Session, Device


class Service:
    def __init__(self) -> None:
        self.hearbeat = Heartbeat()
        self.learn = Learn()
        self.predict = Predict()
        self.sensor = Sensor()

        self.init_devices()

    def init_devices(self):
        session = Session()
        devices = session.query(Device).all()

        for device in devices:
            eventbus.post(DeviceAdded(device=device))


def start_service(app):
    pass
