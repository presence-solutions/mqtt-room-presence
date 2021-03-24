from server.eventbus import eventbus
from server.events import DeviceAddedEvent, RegenerateHeartbeatsEvent, RoomAddedEvent, StartRecordingSignalsEvent, TrainPredictionModelEvent
from server.heartbeat import Heartbeat
from server.learn import Learn
from server.predict import Predict
from server.sensor import Sensor
from server.models import Device, DeviceHeartbeat, DeviceSignal, PredictionModel, Room, Scanner


class Service:
    def __init__(self) -> None:
        self.hearbeat = Heartbeat()
        self.learn = Learn()
        self.predict = Predict()
        self.sensor = Sensor()

    async def init_rooms(self):
        rooms = await Room.all()
        for room in rooms:
            eventbus.post(RoomAddedEvent(room=room))

    async def init_devices(self):
        devices = await Device.all()
        for device in devices:
            eventbus.post(DeviceAddedEvent(device=device))

        # await Room.create(name='Office')
        # await Room.create(name='Kitchen')
        # await Room.create(name='Lobby')
        # await Room.create(name='Guest')
        # await Room.create(name='Bathroom')
        # await Room.create(name='Bedroom')
        # await Room.create(name='Laundry')
        # # await Scanner.create(uuid="office", name="")
        # await Scanner.create(uuid="kitchen", name="")
        # await Scanner.create(uuid="lobby", name="")
        # await Scanner.create(uuid="guest", name="")
        # await Scanner.create(uuid="bathroom", name="")
        # await Scanner.create(uuid="bedroom", name="")
        # await Scanner.create(uuid="laundry", name="")
        # await Scanner.create(uuid="extra-1", name="")
        # # await Device.create(name="room-assistant companion", uuid="40978e03b915", use_name_as_id=True)
        # await Device.create(name="Mi Smart Band 4", uuid="cf4ffda76286")
        # await Device.create(name="Mi Smart Band 5", uuid="C0090A1B234D".lower())
        # # await Device.create(name="iPhone (Anna)", uuid="4debad57eb66", use_name_as_id=True)
        # # await Device.filter(name="Artem").delete()
        # await Device.create(name="Artem", uuid="FDA50693A4E24FB1AFCFC6EB07647825".lower())

        device = await Device.get(name='Artem')

        # await DeviceHeartbeat.filter(device_id=(await Device.get(name='Mi Smart Band 4')).id).delete()
        # await DeviceSignal.filter(device_id=(await Device.get(name='Mi Smart Band 4')).id).delete()

        # eventbus.post(StartRecordingSignalsEvent(
        #     device=device,
        #     room=await Room.get(name='Lobby')
        # ))

        # eventbus.post(RegenerateHeartbeatsEvent(
        #     device=device,
        # ))

        # eventbus.post(TrainPredictionModelEvent(
        #     device=device,
        # ))

        # pred_model = await PredictionModel.filter(devices__id=device.id).order_by('-created_at').first()
        # device.prediction_model = pred_model
        # await device.save()

        # 215 46.153149 583 2021-03-19 07:01:05.189796+00:00

        # print(await DeviceHeartbeat.filter(room_id=(await Room.get(name='Bathroom')).id, id__lt=583).update(room_id=(await Room.get(name='Lobby')).id))

        # print(await DeviceSignal.filter(room_id=(await Room.get(name='Bathroom')).id, id__lt=1781).update(room_id=(await Room.get(name='Lobby')).id))

        # print(await DeviceSignal.filter(room_id=(await Room.get(name='Lobby')).id))

        # heartbeats = await DeviceHeartbeat.filter(room_id=(await Room.get(name='Bathroom')).id).order_by('created_at')
        # for i, h in enumerate(heartbeats):
        #     # if h.id < 863:
        #     diff = (heartbeats[i].created_at - heartbeats[i-1].created_at).total_seconds()
        #     print(i, diff, h.id, heartbeats[i].created_at)


async def start_service(app):
    service = Service()
    app['service'] = service
    await service.init_devices()
    await service.init_rooms()
