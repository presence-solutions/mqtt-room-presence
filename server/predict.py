import asyncio
import pickle
import concurrent.futures
import pandas as pd
from server.eventbus import eventbus
from server.models import get_rooms_scanners
from server.utils import calculate_inputs_hash
from server.eventbus import EventBusSubscriber, subscribe
from server.events import DeviceAddedEvent, DeviceRemovedEvent, HeartbeatEvent, OccupancyEvent


def predict_presence(estimator, data):
    return estimator.predict(data)[0]


class Predict(EventBusSubscriber):

    def __init__(self):
        super().__init__()
        self.prediction_models = {}

    @subscribe(DeviceAddedEvent)
    async def handle_device_added(self, event):
        if not event.device.prediction_model:
            return

        model = await event.device.prediction_model

        if not model and event.device.id in self.prediction_models:
            del self.prediction_models[event.device.id]
        else:
            self.prediction_models[event.device.id] = (pickle.loads(model.model), model.inputs_hash)

    @subscribe(DeviceRemovedEvent)
    def handle_device_removed(self, event):
        del self.prediction_models[event.device.id]

    @subscribe(HeartbeatEvent)
    async def handle_device_heartbeat(self, event):
        if event.device.id not in self.prediction_models:
            return

        if not event.signals:
            eventbus.post(OccupancyEvent(device_id=event.device.id, room_occupancy=[]))
            return

        loop = asyncio.get_running_loop()
        estimator, inputs_hash = self.prediction_models[event.device.id]
        rooms, scanners = await get_rooms_scanners()
        curr_inputs_hash = await calculate_inputs_hash(rooms=rooms, scanners=scanners)

        if inputs_hash != curr_inputs_hash:
            return

        with concurrent.futures.ThreadPoolExecutor() as pool:
            scanner_uuids = [s.uuid for s in scanners]
            default_heartbeat = dict(zip(scanner_uuids, [-100] * len(scanner_uuids)))
            data = pd.DataFrame([{**default_heartbeat, **event.signals}])
            result = loop.run_in_executor(pool, predict_presence, estimator, data)

        selected_room = (await asyncio.gather(result))[0]
        result = {selected_room: True}
        room = next((r for r in rooms if r.id == selected_room), None)

        print('Prediction for {}: {}'.format(event.device.name, room.name))
        eventbus.post(OccupancyEvent(device_id=event.device.id, room_occupancy=result))
