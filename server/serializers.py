import pydantic
from tortoise.contrib.pydantic import pydantic_model_creator, pydantic_queryset_creator
from server import models
from aiohttp import web
from typing import Dict, Optional


DeviceView = pydantic_model_creator(models.Device)
DeviceListView = pydantic_queryset_creator(models.Device)

DeviceHeartbeatView = pydantic_model_creator(models.DeviceHeartbeat)
DeviceHeartbeatListView = pydantic_queryset_creator(models.DeviceHeartbeat)

ScannerView = pydantic_model_creator(models.Scanner)
ScannerListView = pydantic_queryset_creator(models.Scanner)

Room_Pydantic = pydantic_model_creator(models.Room)
RoomListView = pydantic_queryset_creator(models.Room)

PredictionModelView = pydantic_model_creator(models.PredictionModel)
PredictionModelListView = pydantic_queryset_creator(models.PredictionModel)


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
