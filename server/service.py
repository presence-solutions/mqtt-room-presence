from server.eventbus import eventbus
from server.events import DeviceAddedEvent, RegenerateHeartbeatsEvent, RoomAddedEvent, RoomRemovedEvent, StartRecordingSignalsEvent, TrainPredictionModelEvent
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
        # for room in rooms:
        #     eventbus.post(RoomRemovedEvent(room=room))

    async def init_devices(self):
        devices = await Device.all()
        for device in devices:
            eventbus.post(DeviceAddedEvent(device=device))

        # await Scanner.create(uuid="office", name="")
        # await Scanner.create(uuid="kitchen", name="")
        # await Scanner.create(uuid="lobby", name="")
        # await Scanner.create(uuid="guest", name="")
        # await Scanner.create(uuid="bathroom", name="")
        # await Scanner.create(uuid="bedroom", name="")
        # await Scanner.create(uuid="laundry", name="")
        # await Scanner.create(uuid="extra-1", name="")

        # rooms = [
        #     [await Room.create(name='Office'), 'extra-1', 'bathroom'],
        #     [await Room.create(name='Kitchen'), 'kitchen', 'office', 'guest'],
        #     [await Room.create(name='Lobby'), 'lobby', 'kitchen', 'bathroom'],
        #     [await Room.create(name='Guest'), 'guest', 'kitchen', 'office'],
        #     [await Room.create(name='Bathroom'), 'bathroom', 'lobby'],
        #     [await Room.create(name='Bedroom'), 'bedroom', 'guest', 'extra-1'],
        #     [await Room.create(name='Laundry'), 'laundry', 'lobby'],
        # ]

        # for r in rooms:
        #     room = r[0]
        #     scanners = [await Scanner.get(uuid=k) for k in r[1:]]
        #     await room.scanners.add(*scanners)

        # await Device.filter(name="Mi Smart Band 6").delete()
        # await Device.create(name="Mi Smart Band 6", uuid="ebcd027f9891")
        # await Device.create(name="Artem", uuid="FDA50693A4E24FB1AFCFC6EB07647825".lower())

        # device = await Device.get(name='Mi Smart Band 6')
        # model_device = await Device.get(name='Mi Smart Band 6')
        # room = await Room.get(name='Office')

        # await DeviceHeartbeat.filter(device=device, room=room).delete()
        # await DeviceSignal.filter(device=device, room=room).delete()

        # eventbus.post(StartRecordingSignalsEvent(
        #     device=device,
        #     room=room
        # ))

        # eventbus.post(RegenerateHeartbeatsEvent(
        #     device=device,
        # ))

        # eventbus.post(TrainPredictionModelEvent(
        #     device=model_device,
        # ))

        # pred_model = await PredictionModel.filter(devices__id=model_device.id).order_by('-created_at').first()
        # device.prediction_model = pred_model
        # await device.save()

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
