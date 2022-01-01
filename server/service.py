from server.eventbus import eventbus
from server.events import DeviceAddedEvent, RoomAddedEvent
from server.heartbeat import Heartbeat
from server.learn import Learn
from server.models import Device, Room
from server.predict import Predict
from server.sensor import Sensor


class Service:
    def __init__(self) -> None:
        self.hearbeat = Heartbeat()
        # self.learn = Learn()
        # self.predict = Predict()
        # self.sensor = Sensor()

    async def init_rooms(self):
        rooms = await Room.all()
        for room in rooms:
            eventbus.post(RoomAddedEvent(room=room))

    async def init_devices(self):
        devices = await Device.all()
        for device in devices:
            eventbus.post(DeviceAddedEvent(device=device))


async def start_service():
    service = Service()
    await service.init_devices()
    await service.init_rooms()
