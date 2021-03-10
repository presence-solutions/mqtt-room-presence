from server.events import DeviceAddedEvent, DeviceRemovedEvent
from server.eventbus import eventbus
from tortoise.signals import post_delete, post_save
from tortoise.models import Model
from tortoise import fields, Tortoise


class Base(Model):
    class Meta:
        abstract = True

    id = fields.IntField(pk=True)


class TimestampMixin():
    created_at = fields.DatetimeField(null=True, auto_now_add=True)
    updated_at = fields.DatetimeField(null=True, auto_now=True)


class DeviceHeartbeat(Base, TimestampMixin):
    device = fields.ForeignKeyField('models.Device', related_name='heartbeats')
    room = fields.ForeignKeyField('models.Room', related_name='heartbeats')
    signals = fields.JSONField()


class Device(Base, TimestampMixin):
    name = fields.CharField(max_length=100)
    uuid = fields.CharField(max_length=100)
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
    name = fields.CharField(max_length=100)


class Scanner(Base, TimestampMixin):
    name = fields.CharField(max_length=100)
    uuid = fields.CharField(max_length=100, default='')
    display_name = fields.CharField(max_length=100, default='')
    latest_signal = fields.DatetimeField(null=True)


class PredictionModel(Base, TimestampMixin):
    display_name = fields.CharField(max_length=100)
    inputs_hash = fields.CharField(max_length=100)
    accuracy = fields.FloatField(default=0)
    model = fields.BinaryField(null=True)
    devices = fields.ManyToManyField(
        'models.Device', related_name='used_by_models', through='model_device')


@post_save(Device)
async def emit_device_added(sender, instance, created, using_db, update_fields):
    eventbus.post(DeviceAddedEvent(device=instance))


@post_delete(Device)
async def emit_device_removed(sender, instance, using_db):
    eventbus.post(DeviceRemovedEvent(device=instance))


async def init_db(app):
    await Tortoise.init(db_url="sqlite://:memory:", modules={"models": ["server.models"]})
    await Tortoise.generate_schemas()


async def close_db(app):
    await Tortoise.close_connections()
