from server.events import DeviceAddedEvent, DeviceRemovedEvent, StartRecordingSignalsEvent
from server.eventbus import eventbus
from tortoise.models import Model
from tortoise import fields


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


class Device(Base):
    name = Column(String)
    uuid = Column(String)
    use_name_as_id = Column(Boolean)
    display_name = Column(String)
    latest_signal = Column(DateTime)
    current_room_id = Column(Integer, ForeignKey('room.id'))
    current_room = relationship('Room', back_populates='devices')
    active_prediction_model_id = Column(Integer, ForeignKey('predictionmodel.id'))
    active_prediction_model = relationship('PredictionModel')
    prediction_models = relationship(
        "PredictionModel",
        secondary=device_predict_association_table,
        back_populates="devices")

    @property
    def identifier(self):
        identifier = self.name if self.use_name_as_id else self.uuid
        return identifier or self.uuid


class Room(Base):
    name = Column(String)
    devices = relationship('Device', back_populates='current_room')
    prediction_models = relationship(
        "PredictionModel",
        secondary=room_predict_association_table,
        back_populates="rooms")


class Scanner(Base):
    uuid = Column(String)
    name = Column(String)
    display_name = Column(String)
    latest_signal = Column(DateTime)
    prediction_models = relationship(
        "PredictionModel",
        secondary=scanner_predict_association_table,
        back_populates="scanners")


class PredictionModel(Base):
    display_name = Column(String)
    inputs_hash = Column(String)
    accuracy = Column(Float)
    model = Column(LargeBinary)
    devices = relationship(
        "Device",
        secondary=device_predict_association_table,
        back_populates="prediction_models")
    rooms = relationship(
        "Room",
        secondary=room_predict_association_table,
        back_populates="prediction_models")
    scanners = relationship(
        "Scanner",
        secondary=scanner_predict_association_table,
        back_populates="prediction_models")


@event.listens_for(Device, 'after_insert')
def emit_device_added(mapper, connection, target):
    eventbus.post(DeviceAddedEvent(device=target))


@event.listens_for(Device, 'after_delete')
def emit_device_removed(mapper, connection, target):
    eventbus.post(DeviceRemovedEvent(device=target))


async def init_db(app):
    engine = create_async_engine("sqlite:///:memory:", echo=True)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    # expire_on_commit=False will prevent attributes from being expired
    # after commit.
    async_session = sessionmaker(
        engine, expire_on_commit=False, class_=AsyncSession
    )

    app['db'] = async_session

    async with async_session() as session:
        session.add(Room(name='Office'))
        session.add(Scanner(uuid="office", name=""))
        session.add(Scanner(uuid="kitchen", name=""))
        session.add(Scanner(uuid="lobby", name=""))
        # session.add(Device(name="room-presence", uuid="40978e03b915"))
        # session.add(Device(name="Mi Smart Band 4", uuid="cf4ffda76286"))
        session.add(Device(name="iPhone (Anna)", uuid="4debad57eb66", use_name_as_id=True))
        session.commit()

        eventbus.post(StartRecordingSignalsEvent(
            device=session.query(Device).first(),
            room=session.query(Room).first()
        ))


async def close_db(app):
    pass
