from server.eventbus import eventbus
from server.events import DeviceAddedEvent
from server.heartbeat import Heartbeat
from server.learn import Learn
from server.predict import Predict
from server.sensor import Sensor
from server.models import Device


class Service:
    def __init__(self) -> None:
        self.hearbeat = Heartbeat()
        self.learn = Learn()
        self.predict = Predict()
        self.sensor = Sensor()

    async def init_devices(self):
        devices = await Device.all()

        for device in devices:
            eventbus.post(DeviceAddedEvent(device=device))


async def start_service(app):
    service = Service()
    app['service'] = service
    await service.init_devices()
