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
    use_name_as_id = fields.BooleanField()
    display_name = fields.CharField(max_length=100)
    latest_signal = fields.DatetimeField()
    current_room = fields.ForeignKeyField('models.Room', related_name='devices')
    active_prediction_model = fields.ForeignKeyField('models.PredictionModel', related_name='active_devices')

    @property
    def identifier(self):
        identifier = self.name if self.use_name_as_id else self.uuid
        return identifier or self.uuid


class Room(Base, TimestampMixin):
    name = fields.CharField(max_length=100)


class Scanner(Base, TimestampMixin):
    name = fields.CharField(max_length=100)
    uuid = fields.CharField(max_length=100)
    display_name = fields.CharField(max_length=100)
    latest_signal = fields.DatetimeField()


class PredictionModel(Base, TimestampMixin):
    display_name = fields.CharField(max_length=100)
    inputs_hash = fields.CharField(max_length=100)
    accuracy = fields.FloatField()
    model = fields.BinaryField()
    # device = fields.ForeignKeyField('models.Device', related_name='in_prediction_models')


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
