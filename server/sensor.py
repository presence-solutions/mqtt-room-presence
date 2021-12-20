import asyncio
from server.constants import DEVICE_CHANGE_STATE_BEATS, DEVICE_CHANGE_STATE_SECONDS
import jsons
from datetime import datetime
from server.eventbus import EventBusSubscriber, subscribe, eventbus
from server.events import (
    DeviceAddedEvent, DeviceRemovedEvent, MQTTConnectedEvent, MQTTDisconnectedEvent,
    OccupancyEvent, RoomAddedEvent, RoomRemovedEvent, RoomStateChangeEvent)


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
        self.maybe_in_rooms = None

    async def update_room(self, room_id, room_state):
        now_timestamp = datetime.now().timestamp()
        current_maybe_state = self.maybe_in_rooms.get(room_id, {
            'last_state': room_state,
            'appeared_at': datetime.now().timestamp(),
            'appeared_times': 0,
        })
        self.maybe_in_rooms[room_id] = current_maybe_state
        current_maybe_state['appeared_times'] += 1

        # State is different and is OFF, start measuring the state staleness
        if not room_state and current_maybe_state['last_state'] != room_state:
            self.maybe_in_rooms[room_id] = {
                'last_state': room_state,
                'appeared_at': now_timestamp,
                'appeared_times': 0,
            }

        # The state is not changed for X seconds/bets or is ON
        # – make the state as active
        elif room_state or all([
            current_maybe_state['last_state'] == room_state,
            (now_timestamp - current_maybe_state['appeared_at']) >= DEVICE_CHANGE_STATE_SECONDS,
            current_maybe_state['appeared_times'] >= DEVICE_CHANGE_STATE_BEATS,
        ]):
            current_maybe_state['appeared_at'] = now_timestamp
            current_maybe_state['appeared_times'] = 0
            self.in_rooms[room_id] = room_state

    async def update(self, room_occupancy):
        # When the device is not detected in any rooms – clear the state
        if not room_occupancy or self.maybe_in_rooms is None:
            self.maybe_in_rooms = {}
            self.in_rooms = {}
        else:
            merged_occupancy = dict((r, False) for r, _ in self.in_rooms.items())
            merged_occupancy.update(dict((r, False) for r, _ in self.maybe_in_rooms.items()))
            merged_occupancy.update(dict((o['room'].id, o['state']) for o in room_occupancy))
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
        self.active_devices = []

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
        active_devices = [d.device for k, d in device_states.items() if d.is_in_room(self.room.id)]
        state_changed = occupied != self.state
        devices_changed = active_devices != self.active_devices

        self.state = occupied
        self.active_devices = active_devices

        if state_changed or devices_changed:
            eventbus.post(RoomStateChangeEvent(
                room=self.room,
                state=occupied,
                devices=active_devices
            ))

        if state_changed or force_publish:
            client = await self.mqtt_client()
            payload = 'ON' if occupied else 'OFF'
            await client.publish(get_room_state_topic(self.room), payload)


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
        await self.recompute_state()

    @subscribe(DeviceRemovedEvent)
    async def handle_device_removed(self, event):
        if event.device.id in self.device_states:
            del self.device_states[event.device.id]
            await self.recompute_state()

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
        if event.device.id not in self.device_states:
            return

        await self.device_states[event.device.id].update(event.room_occupancy)
        await self.recompute_state()
