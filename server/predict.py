import asyncio
import pickle
import concurrent.futures
from server.eventbus import eventbus
from server.models import get_rooms_scanners
from server.utils import calculate_inputs_hash, create_x_data_row
from server.eventbus import EventBusSubscriber, subscribe
from server.events import DeviceAddedEvent, DeviceRemovedEvent, HeartbeatEvent, OccupancyEvent


def predict_presence(algorithm, data):
    return algorithm[0], algorithm[1].predict([data])


class Predict(EventBusSubscriber):

    def __init__(self):
        super().__init__()
        self.prediction_models = {}

    @subscribe(DeviceAddedEvent)
    async def handle_device_added(self, event):
        model = await event.device.prediction_model
        if not model:
            return

        self.prediction_models[event.device.id] = (pickle.loads(model.model), model.inputs_hash)

    @subscribe(DeviceRemovedEvent)
    def handle_device_removed(self, event):
        del self.prediction_models[event.device.id]

    @subscribe(HeartbeatEvent)
    async def handle_device_heartbeat(self, event):
        if event.device.id not in self.prediction_models:
            return

        if not event.signals:
            eventbus.post(OccupancyEvent(device_id=event.device.id, room_id=None))
            return

        loop = asyncio.get_running_loop()
        algorithms, inputs_hash = self.prediction_models[event.device.id]
        rooms, scanners = await get_rooms_scanners()
        curr_inputs_hash = await calculate_inputs_hash(rooms=rooms, scanners=scanners)

        if inputs_hash != curr_inputs_hash:
            return

        with concurrent.futures.ThreadPoolExecutor() as pool:
            def run_predict_coroutine(algorithm, data):
                return loop.run_in_executor(pool, predict_presence, algorithm, data)

            x_data = await create_x_data_row(event.signals, scanners=scanners)
            results = [run_predict_coroutine(a, x_data) for a in algorithms if a[0] == 'Neural Net']

        results = await asyncio.gather(*results)
        eventbus.post(OccupancyEvent(device_id=event.device.id, room_id=results[0][1][0]))

        # # print(results)
        # def results_group_fn(x): return x[1][0]
        # sorted_results = sorted(results, key=results_group_fn)
        # counted_results = [(k, len(list(g))) for k, g in groupby(sorted_results, key=results_group_fn)]
        # room_id, matches = max(counted_results, key=lambda x: x[1])

        # if matches >= quorum_count:
        #     eventbus.post(OccupancyEvent(device_id=event.device.id, room_id=room_id))
