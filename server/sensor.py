import asyncio
from server.constants import DEVICE_CHANGE_STATE_TIMES
import jsons
from server.eventbus import EventBusSubscriber, subscribe
from server.events import (
    DeviceAddedEvent, DeviceRemovedEvent, MQTTConnectedEvent, MQTTDisconnectedEvent,
    OccupancyEvent, RoomAddedEvent, RoomRemovedEvent)


def get_room_topic(room):
    return 'homeassistant/binary_sensor/room_{}_occupancy/config'.format(room.id)\
        .replace(' ', '_').lower()


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
        self.in_rooms = {}
        self.new_rooms = None

    async def update_room(self, room_id, room_state):
        if self.in_rooms.get(room_id, False) == room_state:
            self.new_rooms[room_id] = (room_state, 1)
            return

        print('Maybe device {} state in room {} is {}?'.format(self.device.name, room_id, room_state))

        maybe_room_state = self.new_rooms.get(room_id, (room_state, 1))

        if maybe_room_state[0] == room_state:
            maybe_room_state = (room_state, maybe_room_state[1] + 1)
        else:
            maybe_room_state = (room_state, 1)

        if maybe_room_state[1] >= DEVICE_CHANGE_STATE_TIMES:
            maybe_room_state = (maybe_room_state[0], 1)
            self.in_rooms[room_id] = maybe_room_state[0]

            print('Device {} changed state in room {} to {}'.format(self.device.name, room_id, maybe_room_state[0]))

        self.new_rooms[room_id] = maybe_room_state

    async def update(self, room_occupancy):
        if self.new_rooms is None:
            self.new_rooms = {}
            self.in_rooms = dict(room_occupancy)
        else:
            merged_occupancy = dict((r, False) for r, v in self.in_rooms.items())
            merged_occupancy.update(dict((r, False) for r, v in self.new_rooms.items()))
            merged_occupancy.update(room_occupancy)
            results = (self.update_room(r, s) for r, s in merged_occupancy.items())
            await asyncio.gather(*results)

    def is_in_room(self, room_id):
        return self.in_rooms.get(room_id, False)


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
            'state_topic': get_room_state_topic(self.room),
            'unique_id': 'room_occupancy.{}.{}'.format(
                self.room.id, self.room.name).replace(' ', '_').lower(),
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
        self.reconfigure_on_connect = False

    async def recompute_state(self):
        update_results = [t.recompute_state(self.device_states) for k, t in self.room_trackers.items()]
        await asyncio.gather(*update_results)

    @subscribe(MQTTConnectedEvent)
    async def handle_mqtt_connect(self, event):
        if self.reconfigure_on_connect:
            for _, tracker in self.room_trackers.items():
                await tracker.configure()
                await tracker.recompute_state(self.device_states, force_publish=True)

    @subscribe(MQTTDisconnectedEvent)
    def handle_mqtt_disconnect(self, event):
        self.reconfigure_on_connect = True

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
        if event.room.id in self.room_trackers:
            tracker = self.room_trackers[event.room.id]
            del self.room_trackers[event.room.id]
        else:
            tracker = RoomTracker(event.room, self.mqtt_client)
        await tracker.remove()

    @subscribe(OccupancyEvent)
    async def handle_device_occupancy(self, event):
        if event.device_id not in self.device_states:
            return

        await self.device_states[event.device_id].update(event.room_occupancy)
        await self.recompute_state()
