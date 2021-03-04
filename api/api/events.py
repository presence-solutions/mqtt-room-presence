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
