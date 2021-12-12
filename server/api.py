import dateutil
from tortoise.exceptions import DoesNotExist, IntegrityError
from server.models import Device, Room, Scanner
from ariadne import (
    ObjectType, ScalarType, MutationType, make_executable_schema, load_schema_from_path,
    snake_case_fallback_resolvers)

type_defs = load_schema_from_path('schema.graphql')

datetime_scalar = ScalarType("Datetime")
query = ObjectType("Query")
device = ObjectType("Device")
room = ObjectType("Room")
scanner = ObjectType("Scanner")
mutation = MutationType()


@datetime_scalar.serializer
def serialize_datetime(value):
    return value.isoformat()


@datetime_scalar.value_parser
def parse_datetime_value(value):
    # dateutil is provided by python-dateutil library
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
            )
        }
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
        return {
            "room": await Room.create(name=input['name'])
        }
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
        return {
            "scanner": await Scanner.create(uuid=input['uuid'], name='')
        }
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


resolvers = [
    datetime_scalar,
    device, room, scanner,
    query, mutation,
    snake_case_fallback_resolvers
]
schema = make_executable_schema(type_defs, resolvers)
