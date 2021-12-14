from datetime import datetime
import dateutil
from tortoise.exceptions import DoesNotExist, IntegrityError
from server.eventbus import eventbus
from server.events import DeviceSignalEvent, LearntDeviceSignalEvent, StartRecordingSignalsEvent, StopRecordingSignalsEvent, TrainPredictionModelEvent, TrainingProgressEvent
from server.models import Device, DeviceSignal, PredictionModel, Room, Scanner
from ariadne import (
    ObjectType, ScalarType, MutationType, SubscriptionType,
    make_executable_schema, load_schema_from_path,
    snake_case_fallback_resolvers)

type_defs = load_schema_from_path('schema.graphql')

datetime_scalar = ScalarType("Datetime")
query = ObjectType("Query")
subscription = SubscriptionType()
mutation = MutationType()


@datetime_scalar.serializer
def serialize_datetime(value):
    return value.isoformat()


@datetime_scalar.value_parser
def parse_datetime_value(value):
    if value:
        return dateutil.parser.parse(value)


@datetime_scalar.literal_parser
def parse_datetime_literal(ast):
    value = str(ast.value)
    return parse_datetime_value(value)  # reuse logic from parse_value


@query.field("allDevices")
async def resolve_devices(_, info):
    return await Device.all().order_by('-created_at')


@mutation.field("addDevice")
async def resolve_add_device(_, info, input):
    try:
        return {
            "device": await Device.create(
                name=input['name'],
                uuid=input['uuid'],
                display_name=input.get('displayName', ''),
                use_name_as_id=input.get('useNameAsId', False),
                prediction_model_id=input.get('predictionModel', None)
            )
        }
    except IntegrityError:
        return {
            "error": {
                "code": "integrity_error",
                "message": "A device with the same name or UUID already exists"
            }
        }


@mutation.field("updateDevice")
async def resolve_update_device(_, info, input):
    try:
        await Device.filter(id=input['id']).update(
            name=input['name'],
            uuid=input['uuid'],
            display_name=input.get('displayName', ''),
            use_name_as_id=input.get('useNameAsId', False),
            prediction_model_id=input.get('predictionModel', None)
        )
        return {
            "device": await Device.get(id=input['id'])
        }
    except DoesNotExist:
        return {}
    except IntegrityError:
        return {
            "error": {
                "code": "integrity_error",
                "message": "A device with the same name or UUID already exists"
            }
        }


@mutation.field("removeDevice")
async def resolve_remove_device(_, info, id):
    try:
        device = await Device.get(id=id)
        await device.delete()
        return device
    except DoesNotExist:
        return None


@query.field("allRooms")
async def resolve_rooms(_, info):
    return await Room.all().order_by('-created_at')


@mutation.field("addRoom")
async def resolve_add_room(_, info, input):
    try:
        room = await Room.create(name=input['name'])

        await room.scanners.clear()
        for s in await Scanner.filter(id__in=input.get('scanners', [])):
            await room.scanners.add(s)

        return {
            "room": room
        }
    except IntegrityError:
        return {
            "error": {
                "code": "integrity_error",
                "message": "A room with the same name already exists"
            }
        }


@mutation.field("updateRoom")
async def resolve_update_room(_, info, input):
    try:
        await Room.filter(id=input['id']).update(name=input['name'])

        room = await Room.get(id=input['id'])
        await room.scanners.clear()
        for s in await Scanner.filter(id__in=input.get('scanners', [])):
            await room.scanners.add(s)

        return {
            "room": room
        }
    except DoesNotExist:
        return {}
    except IntegrityError:
        return {
            "error": {
                "code": "integrity_error",
                "message": "A room with the same name already exists"
            }
        }


@mutation.field("removeRoom")
async def resolve_remove_room(_, info, id):
    try:
        room = await Room.get(id=id)
        await room.delete()
        return room
    except DoesNotExist:
        return None


@query.field("allScanners")
async def resolve_scanner(_, info):
    return await Scanner.all().order_by('-created_at')


@mutation.field("addScanner")
async def resolve_add_scanner(_, info, input):
    try:
        scanner = await Scanner.create(
            uuid=input['uuid'],
            display_name=input.get('displayName', ''),
            name=''
        )

        await scanner.used_in_rooms.clear()
        for r in await Room.filter(id__in=input.get('usedInRooms', [])):
            await scanner.used_in_rooms.add(r)

        return {
            "scanner": scanner
        }
    except IntegrityError:
        return {
            "error": {
                "code": "integrity_error",
                "message": "A scanner with the same UUID already exists"
            }
        }


@mutation.field("updateScanner")
async def resolve_update_scanner(_, info, input):
    try:
        await Scanner.filter(id=input['id']).update(
            uuid=input['uuid'],
            display_name=input.get('displayName', ''),
        )

        scanner = await Scanner.get(id=input['id'])
        await scanner.used_in_rooms.clear()
        for r in await Room.filter(id__in=input.get('usedInRooms', [])):
            await scanner.used_in_rooms.add(r)

        return {
            "scanner": scanner
        }
    except DoesNotExist:
        return {}
    except IntegrityError:
        return {
            "error": {
                "code": "integrity_error",
                "message": "A scanner with the same UUID already exists"
            }
        }


@mutation.field("removeScanner")
async def resolve_remove_scanner(_, info, id):
    try:
        scanner = await Scanner.get(id=id)
        await scanner.delete()
        return scanner
    except DoesNotExist:
        return None


@query.field("allPredictionModels")
async def resolve_prediction_models(_, info):
    return await PredictionModel.all().order_by('-created_at')


@mutation.field("removePredictionModel")
async def resolve_remove_prediction_model(_, info, id):
    try:
        prediction_model = await PredictionModel.get(id=id)
        await prediction_model.delete()
        return prediction_model
    except DoesNotExist:
        return None


@mutation.field("startSignalsRecording")
async def resolve_start_signals_recording(_, info, room, device):
    try:
        eventbus.post(StartRecordingSignalsEvent(
            device=await Device.get(id=device),
            room=await Room.get(id=room)
        ))
        return {}
    except DoesNotExist:
        return {
            "error": {
                "code": "does_not_exist",
                "message": "Given room or device does not exist"
            }
        }


@mutation.field("stopSignalsRecording")
async def resolve_stop_signals_recording(_, info):
    eventbus.post(StopRecordingSignalsEvent())
    return {}


@mutation.field("startModelTraining")
async def resolve_start_model_training(_, info, device):
    try:
        eventbus.post(TrainPredictionModelEvent(device=await Device.get(id=device)))
        return {}
    except DoesNotExist:
        return {
            "error": {
                "code": "does_not_exist",
                "message": "Given device does not exist"
            }
        }


@subscription.source("deviceSignal")
async def source_device_signal(_, info, device=None, scanner=None):
    async with eventbus.subscribe(DeviceSignalEvent) as subscriber:
        async for event in subscriber:
            try:
                scanner_obj = await Scanner.get(uuid=event.scanner_uuid)
            except DoesNotExist:
                scanner_obj = Scanner(uuid=event.scanner_uuid, unknown=True)

            if all([
                not device or event.device.id == int(device),
                not scanner or scanner_obj.id == int(scanner)
            ]):
                signal_datetime = datetime.fromtimestamp(event.signal['when'])
                yield DeviceSignal(
                    room=None,
                    learning_session=None,
                    device=event.device,
                    scanner=scanner_obj,
                    rssi=int(event.signal['rssi']),
                    created_at=signal_datetime,
                    updated_at=signal_datetime,
                )


@subscription.source("learntSignal")
async def resolve_learnt_signal_sub(_, info):
    async with eventbus.subscribe(LearntDeviceSignalEvent) as subscriber:
        async for event in subscriber:
            yield event.device_signal


@subscription.field("learntSignal")
@subscription.field("deviceSignal")
def resolve_subscription_device_signal(signal, info, **kwargs):
    return signal


@subscription.source("modelTrainingProgress")
async def resolve_model_training_progress_sub(_, info, device):
    async with eventbus.subscribe(TrainingProgressEvent) as subscriber:
        async for event in subscriber:
            if event.device.id == int(device):
                yield {"progress": event}


@subscription.field("modelTrainingProgress")
def resolve_model_training_progress(event, info, **kwargs):
    return event


resolvers = [
    datetime_scalar,
    query, mutation, subscription,
    snake_case_fallback_resolvers
]
schema = make_executable_schema(type_defs, resolvers)
