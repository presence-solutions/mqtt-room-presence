from collections import namedtuple
import logging


class DeviceSignalEvent(namedtuple(
    'DeviceSignalEvent',
    'device, signal, scanner_uuid'
)):
    log_level = logging.DEBUG


class LearntDeviceSignalEvent(namedtuple(
    'LearntDeviceSignalEvent',
    'device_signal, is_enough'
)):
    log_level = logging.DEBUG


class HeartbeatEvent(namedtuple(
    'HeartbeatEvent',
    'device, signals, timestamp'
)):
    log_level = logging.DEBUG


class OccupancyEvent(namedtuple(
    'OccupancyEvent',
    'device, room_occupancy, signals, prediction_model'
)):
    log_level = logging.INFO


class MQTTConnectedEvent(namedtuple(
    'MQTTConnectedEvent',
    'client'
)):
    log_level = logging.INFO


class MQTTDisconnectedEvent(namedtuple(
    'MQTTDisconnectedEvent',
    'error, reconnect_interval'
)):
    log_level = logging.INFO


class MQTTMessageEvent(namedtuple(
    'MQTTMessage',
    'topic, payload'
)):
    log_level = logging.DEBUG


class DeviceAddedEvent(namedtuple(
    'DeviceAddedEvent',
    'device'
)):
    log_level = logging.INFO


class DeviceRemovedEvent(namedtuple(
    'DeviceRemovedEvent',
    'device'
)):
    log_level = logging.INFO


class RoomAddedEvent(namedtuple(
    'RoomAddedEvent',
    'room'
)):
    log_level = logging.INFO


class RoomRemovedEvent(namedtuple(
    'RoomRemovedEvent',
    'room'
)):
    log_level = logging.INFO


class RoomStateChangeEvent(namedtuple(
    'RoomStateChangeEvent',
    'room, state, devices'
)):
    log_level = logging.INFO


class StartRecordingSignalsEvent(namedtuple(
    'StartRecordingSignals',
    'device, room'
)):
    log_level = logging.INFO


class StopRecordingSignalsEvent():
    log_level = logging.INFO


class TrainPredictionModelEvent(namedtuple(
    'TrainPredictionModel',
    'device'
)):
    log_level = logging.INFO


class TrainingProgressEvent(namedtuple(
    'TrainingProgressEvent',
    'device, status_code, message, prediction_model, is_error, is_final'
)):
    log_level = logging.INFO
