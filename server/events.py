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


class MQTTMessageEvent(namedtuple(
    'MQTTMessage',
    'topic, payload'
)):
    pass


class DeviceAddedEvent(namedtuple(
    'DeviceAdded',
    'device'
)):
    pass


class DeviceRemovedEvent(namedtuple(
    'DeviceAdded',
    'device'
)):
    pass


class StartRecordingSignalsEvent(namedtuple(
    'StartRecordingSignals',
    'device, room'
)):
    pass


class StopRecordingSignalsEvent():
    pass


class TrainPredictionModelEvent(namedtuple(
    'TrainPredictionModel',
    'device'
)):
    pass


class TrainingProgressEvent(namedtuple(
    'TrainingProgressEvent',
    'device, message, is_error, is_final'
)):
    pass
