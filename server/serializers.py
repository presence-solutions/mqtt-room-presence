from tortoise.contrib.pydantic import pydantic_model_creator, pydantic_queryset_creator
from server import models

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
