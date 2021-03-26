from collections import namedtuple


class DeviceSignalEvent(namedtuple(
    'DeviceSignalEvent',
    'device, signal, scanner_uuid'
)):
    pass


class HeartbeatEvent(namedtuple(
    'HeartbeatEvent',
    'device, signals, timestamp'
)):
    async def as_dict(self):
        from server.serializers import DeviceView
        result = self._asdict()
        result['device'] = (await DeviceView.from_tortoise_orm(result['device'])).dict()
        return result


class OccupancyEvent(namedtuple(
    'OccupancyEvent',
    'device_id, room_occupancy'
)):
    pass


class MQTTConnectedEvent(namedtuple(
    'MQTTConnectedEvent',
    'client'
)):
    pass


class MQTTDisconnectedEvent(namedtuple(
    'MQTTDisconnectedEvent',
    ''
)):
    pass


class MQTTMessageEvent(namedtuple(
    'MQTTMessage',
    'topic, payload'
)):
    pass


class DeviceAddedEvent(namedtuple(
    'DeviceAddedEvent',
    'device'
)):
    pass


class DeviceRemovedEvent(namedtuple(
    'DeviceRemovedEvent',
    'device'
)):
    pass


class RoomAddedEvent(namedtuple(
    'RoomAddedEvent',
    'room'
)):
    pass


class RoomRemovedEvent(namedtuple(
    'RoomRemovedEvent',
    'room'
)):
    pass


class StartRecordingSignalsEvent(namedtuple(
    'StartRecordingSignals',
    'device, room'
)):
    pass


class StopRecordingSignalsEvent():
    pass


class RegenerateHeartbeatsEvent(namedtuple(
    'RegenerateHeartbeatsEvent',
    'device'
)):
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
    async def as_dict(self):
        from server.serializers import DeviceView
        result = self._asdict()
        result['device'] = (await DeviceView.from_tortoise_orm(result['device'])).dict()
        return result
