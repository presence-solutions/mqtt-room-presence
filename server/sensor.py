import asyncio
from server.constants import DEVICE_CHANGE_STATE_TIMES
import jsons
from server.models import Device
from server.eventbus import EventBusSubscriber, subscribe
from server.events import DeviceAddedEvent, DeviceRemovedEvent, MQTTConnectedEvent, MQTTDisconnectedEvent, OccupancyEvent, RoomAddedEvent, RoomRemovedEvent


def get_room_topic(room):
    return 'homeassistant/binary_sensor/room_{}_occupancy/config'.format(room.id)


def get_room_config_topic(room):
    return '{}/config'.format(get_room_topic(room))


def get_room_state_topic(room):
    return '{}/state'.format(get_room_topic(room))


class MQTTClientHolder(EventBusSubscriber):
    def __init__(self):
        super().__init__()
        self.create_mqtt_future()

    def create_mqtt_future(self):
        loop = asyncio.get_running_loop()
        self.mqtt_client = loop.create_future()

    @subscribe(MQTTConnectedEvent)
    def handle_mqtt_connect(self, event):
        self.mqtt_client.set_result(event.client)

    @subscribe(MQTTDisconnectedEvent)
    def handle_mqtt_disconnect(self, event):
        self.create_mqtt_future()

    def __call__(self, *args, **kwds):
        return self.mqtt_client


class DeviceState:
    def __init__(self, device):
        self.device = device
        self.current_room_id = device.current_room_id
        self.new_room_id = None
        self.new_room_counter = 1

    async def update(self, new_room_id):
        if new_room_id == self.current_room_id:
            return

        if new_room_id == self.new_room_id:
            self.new_room_counter += 1
        else:
            self.new_room_id = new_room_id
            self.new_room_counter = 1

        if self.new_room_counter >= DEVICE_CHANGE_STATE_TIMES or (not self.current_room_id and self.new_room_id):
            self.current_room_id = self.new_room_id
            self.new_room_id = None
            self.new_room_counter = 0

            await Device.filter(id=self.device.id).update(current_room_id=self.current_room_id)
            print('Device {} is in {}'.format(self.device.name, self.current_room_id))

    def is_in_room(self, room_id):
        return self.current_room_id == room_id


class RoomTracker(EventBusSubscriber):
    def __init__(self, room, mqtt_client):
        super().__init__()
        self.room = room
        self.mqtt_client = mqtt_client
        self.state = False

    async def configure(self):
        client = await self.mqtt_client()
        payload = jsons.dumps({
            'name': '{} Room Occupancy'.format(self.room.name),
            'device_class': 'occupancy',
            'state_topic': get_room_state_topic(self.room)
        })
        await client.publish(get_room_config_topic(self.room), payload)

    async def remove(self):
        client = await self.mqtt_client()
        await client.publish(get_room_config_topic(self.room), '')

    async def recompute_state(self, device_states, force_publish=False):
        occupied = any(d.is_in_room(self.room.id) for k, d in device_states.items())
        if occupied == self.state and not force_publish:
            return

        self.state = occupied

        client = await self.mqtt_client()
        payload = 'ON' if occupied else 'OFF'
        await client.publish(get_room_state_topic(self.room), payload)

        print('Room {} turned to {}'.format(self.room.name, payload))


class Sensor(EventBusSubscriber):
    def __init__(self):
        super().__init__()
        self.room_trackers = {}
        self.device_states = {}
        self.mqtt_client = MQTTClientHolder()

    async def recompute_state(self):
        update_results = [t.recompute_state(self.device_states) for k, t in self.room_trackers.items()]
        await asyncio.gather(*update_results)

    @subscribe(DeviceAddedEvent)
    async def handle_device_added(self, event):
        self.device_states[event.device.id] = DeviceState(event.device)

    @subscribe(DeviceRemovedEvent)
    async def handle_device_removed(self, event):
        if event.device.id in self.device_states:
            del self.device_states[event.device.id]

    @subscribe(RoomAddedEvent)
    async def handle_room_added(self, event):
        tracker = RoomTracker(event.room, self.mqtt_client)
        self.room_trackers[event.room.id] = tracker
        await tracker.configure()
        await tracker.recompute_state(self.device_states, force_publish=True)

    @subscribe(RoomRemovedEvent)
    async def handle_room_removed(self, event):
        tracker = self.room_trackers[event.room.id]
        del self.room_trackers[event.room.id]
        await tracker.remove()

    @subscribe(OccupancyEvent)
    async def handle_device_occupancy(self, event):
        if event.device_id not in self.device_states:
            return

        await self.device_states[event.device_id].update(event.room_id)
        await self.recompute_state()
