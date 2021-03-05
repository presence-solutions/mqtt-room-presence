from collections import namedtuple


class DeviceSignalEvent(namedtuple(
    'DeviceSignalEvent',
    'uuid, name, tx, rx, distance, timestamp'
)):
    pass


class HeartbeatEvent(namedtuple(
    'HeartbeatEvent',
    'device, signals, timestamp'
)):
    pass


class OccupancyEvent(namedtuple(
    'OccupancyEvent',
    'device, room'
)):
    pass


class MQTTConnectedEvent(namedtuple(
    'MQTTConnectedEvent',
    'client'
)):
    pass


class MQTTMessage(namedtuple(
    'MQTTMessage',
    'topic, payload'
)):
    pass


class DeviceAdded(namedtuple(
    'DeviceAdded',
    'device'
)):
    pass


class DeviceRemoved(namedtuple(
    'DeviceAdded',
    'device'
)):
    pass
