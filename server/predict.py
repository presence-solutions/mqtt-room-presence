import pickle
import pandas as pd
from server.eventbus import eventbus
from server.models import get_rooms_scanners
from server.utils import calculate_inputs_hash, run_in_executor
from server.eventbus import EventBusSubscriber, subscribe
from server.events import DeviceAddedEvent, DeviceRemovedEvent, HeartbeatEvent, OccupancyEvent


@run_in_executor
def predict_presence(estimator, data_row):
    return estimator.predict_proba(data_row)[0]


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
        # No prediction model registered for a device
        if event.device.id not in self.prediction_models:
            return

        # No signals provided – the device is out
        if not event.signals:
            eventbus.post(OccupancyEvent(
                device=event.device.id,
                room_occupancy={},
                signals=None,
            ))
            return

        estimator, inputs_hash = self.prediction_models[event.device.id]
        rooms, scanners = await get_rooms_scanners()
        curr_inputs_hash = await calculate_inputs_hash(rooms=rooms, scanners=scanners)
        rooms_map = dict((r.id, r) for r in rooms)

        # The inputs are different than expected by the model
        if inputs_hash != curr_inputs_hash:
            # TODO: rise some visible error for this
            return

        # Predict presence in a separate thread
        scanner_uuids = [s.uuid for s in scanners]
        default_heartbeat = dict(zip(scanner_uuids, [-100] * len(scanner_uuids)))
        data = pd.DataFrame([{**default_heartbeat, **event.signals}])
        result = await predict_presence(estimator, data)
        result = [{
            "room": rooms_map[k],
            "state": True,
            "proba": result[k],
        } for k in result.keys()]

        eventbus.post(OccupancyEvent(
            device=event.device,
            room_occupancy=result,
            signals=data.iloc[0].to_dict(),
        ))
