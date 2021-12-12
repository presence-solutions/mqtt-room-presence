import dateutil
from tortoise.exceptions import DoesNotExist
from server.models import Device
from ariadne import (
    ObjectType, ScalarType, MutationType, make_executable_schema, load_schema_from_path,
    snake_case_fallback_resolvers)

type_defs = load_schema_from_path('schema.graphql')

datetime_scalar = ScalarType("Datetime")
query = ObjectType("Query")
device = ObjectType("Device")
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
    except Exception:
        # TODO: handle creation errors
        return {
            "error": {
                "code": "unexpected_exception",
                "message": "Unxepected exception"
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


resolvers = [query, mutation, device, snake_case_fallback_resolvers]
schema = make_executable_schema(type_defs, resolvers)
