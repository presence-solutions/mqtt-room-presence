from server.eventbus import eventbus
from server.events import DeviceAddedEvent, StartRecordingSignalsEvent
from server.heartbeat import Heartbeat
from server.learn import Learn
from server.predict import Predict
from server.sensor import Sensor
from server.models import Device, Room, Scanner


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

        await Room.create(name='Office')
        await Scanner.create(uuid="office", name="")
        await Scanner.create(uuid="kitchen", name="")
        await Scanner.create(uuid="lobby", name="")
        # await Device.create(name="room-presence", uuid="40978e03b915")
        await Device.create(name="Mi Smart Band 4", uuid="cf4ffda76286")
        # await Device.create(name="iPhone (Anna)", uuid="4debad57eb66", use_name_as_id=True)

        eventbus.post(StartRecordingSignalsEvent(
            device=await Device.first(),
            room=await Room.first()
        ))


async def start_service(app):
    service = Service()
    app['service'] = service
    await service.init_devices()
