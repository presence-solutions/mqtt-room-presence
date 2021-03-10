import pydantic
from datetime import datetime
from aiohttp import web
from server import models
from server import serializers
from typing import Dict, Optional


def pydantic_response(
    data: pydantic.BaseModel,
    *,
    status: int = 200,
    reason: Optional[str] = None,
    headers: Optional[Dict] = None,
    content_type: str = "application/json",
) -> web.Response:
    return web.Response(
        text=data.json(),
        body=None,
        status=status,
        reason=reason,
        headers=headers,
        content_type=content_type,
    )


async def get_devices(app):
    tourpy = await serializers.DeviceListView.from_queryset(models.Device.all())
    return pydantic_response(tourpy)


async def get_rooms(app):
    tourpy = await serializers.RoomListView.from_queryset(models.Room.all())
    return pydantic_response(tourpy)


async def get_scanners(app):
    tourpy = await serializers.ScannerListView.from_queryset(models.Scanner.all())
    return pydantic_response(tourpy)


def setup_routes(app):
    app.router.add_get('/api/device', get_devices)
    app.router.add_get('/api/room', get_rooms)
    app.router.add_get('/api/scanner', get_scanners)
