from server import config
from server.events import DeviceAddedEvent, DeviceRemovedEvent, RoomAddedEvent, RoomRemovedEvent
from server.eventbus import eventbus
from tortoise.signals import Signals, post_delete, post_save
from tortoise.models import Model
from tortoise import fields, Tortoise
from async_lru import alru_cache


class Base(Model):
    class Meta:
        abstract = True

    id = fields.IntField(pk=True)


class TimestampMixin():
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    updated_at = fields.DatetimeField(null=True, auto_now=True)


class LearningSession(Base, TimestampMixin):
    device = fields.ForeignKeyField('models.Device', related_name='learning_sessions')
    room = fields.ForeignKeyField('models.Room', related_name='learning_sessions')


class DeviceSignal(Base, TimestampMixin):
    learning_session = fields.ForeignKeyField('models.LearningSession', related_name='signals', null=True)
    device = fields.ForeignKeyField('models.Device', related_name='signals')
    room = fields.ForeignKeyField('models.Room', related_name='signals')
    scanner = fields.ForeignKeyField('models.Scanner', related_name='signals')
    rssi = fields.FloatField(default=0)
    filtered_rssi = fields.FloatField(default=0)


class Device(Base, TimestampMixin):
    name = fields.CharField(max_length=100, unique=True)
    uuid = fields.CharField(max_length=100, unique=True)
    use_name_as_id = fields.BooleanField(default=False)
    display_name = fields.CharField(max_length=100, default='')
    latest_signal = fields.DatetimeField(null=True)
    current_room = fields.ForeignKeyField('models.Room', related_name='devices', null=True)
    prediction_model = fields.ForeignKeyField('models.PredictionModel', related_name='used_by_devices', null=True)


    @property
    def identifier(self):
        identifier = self.name if self.use_name_as_id else self.uuid
        return identifier or self.uuid


class Room(Base, TimestampMixin):
    name = fields.CharField(max_length=100, unique=True)
    scanners = fields.ManyToManyField(
        'models.Scanner', related_name='used_in_rooms', through='room_scanner')

    class Meta:
        ordering = ["id"]

class Scanner(Base, TimestampMixin):
    uuid = fields.CharField(max_length=100, unique=True)
    display_name = fields.CharField(max_length=100, default='')
    latest_signal = fields.DatetimeField(null=True)

    class Meta:
        ordering = ["id"]


class PredictionModel(Base, TimestampMixin):
    display_name = fields.CharField(max_length=100, default='')
    inputs_hash = fields.CharField(max_length=100)
    accuracy = fields.FloatField(default=0)
    model = fields.BinaryField(null=True)
    devices = fields.ManyToManyField(
        'models.Device', related_name='used_by_models', through='model_device')


@alru_cache
async def get_rooms_scanners():
    rooms = await Room.all()
    scanners = await Scanner.all()
    return rooms, scanners


async def clear_rooms_scanners_cache(sender, instance, created, using_db, update_fields):
    get_rooms_scanners.cache_clear()


Room.register_listener(Signals.post_save, clear_rooms_scanners_cache)
Room.register_listener(Signals.post_delete, clear_rooms_scanners_cache)
Scanner.register_listener(Signals.post_save, clear_rooms_scanners_cache)
Scanner.register_listener(Signals.post_delete, clear_rooms_scanners_cache)


@post_save(Device)
async def emit_device_added(sender, instance, created, using_db, update_fields):
    eventbus.post(DeviceAddedEvent(device=instance))


@post_delete(Device)
async def emit_device_removed(sender, instance, using_db):
    eventbus.post(DeviceRemovedEvent(device=instance))


@post_save(Room)
async def emit_room_added(sender, instance, created, using_db, update_fields):
    eventbus.post(RoomAddedEvent(room=instance))


@post_delete(Room)
async def emit_room_removed(sender, instance, using_db):
    eventbus.post(RoomRemovedEvent(room=instance))


async def init_db():
    await Tortoise.init(config.TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def close_db():
    await Tortoise.close_connections()
