from server import models
from server import serializers


async def get_devices(app):
    tourpy = await serializers.DeviceListView.from_queryset(models.Device.all())
    return serializers.pydantic_response(tourpy)


async def get_rooms(app):
    tourpy = await serializers.RoomListView.from_queryset(models.Room.all())
    return serializers.pydantic_response(tourpy)


async def get_scanners(app):
    tourpy = await serializers.ScannerListView.from_queryset(models.Scanner.all())
    return serializers.pydantic_response(tourpy)


def setup_routes(app):
    app.router.add_get('/api/device', get_devices)
    app.router.add_get('/api/room', get_rooms)
    app.router.add_get('/api/scanner', get_scanners)
