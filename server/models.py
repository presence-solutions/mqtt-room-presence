from server.events import DeviceAddedEvent, DeviceRemovedEvent
from server.eventbus import eventbus
from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, ForeignKey, Table, Float,
    LargeBinary, Boolean, JSON, event)
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql.functions import func


engine = create_engine('sqlite:///:memory:', echo=True)
Session = sessionmaker(bind=engine)


class Base(object):
    @declared_attr
    def __tablename__(cls):
        return cls.__name__.lower()

    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


Base = declarative_base(cls=Base)


device_predict_association_table = Table(
    'device_predict_association', Base.metadata,
    Column('device_id', Integer, ForeignKey('device.id')),
    Column('model_id', Integer, ForeignKey('predictionmodel.id'))
)

room_predict_association_table = Table(
    'room_predict_association', Base.metadata,
    Column('room_id', Integer, ForeignKey('room.id')),
    Column('model_id', Integer, ForeignKey('predictionmodel.id'))
)

scanner_predict_association_table = Table(
    'scanner_predict_association', Base.metadata,
    Column('scanner_id', Integer, ForeignKey('scanner.id')),
    Column('model_id', Integer, ForeignKey('predictionmodel.id'))
)


class DeviceHeartbeat(Base):
    device_id = Column(Integer, ForeignKey('device.id'))
    device = relationship('Device')
    room_id = Column(Integer, ForeignKey('room.id'))
    room = relationship('Room')
    signals = Column(JSON)


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


Base.metadata.create_all(engine)


@event.listens_for(Device, 'after_insert')
def emit_device_added(mapper, connection, target):
    eventbus.post(DeviceAddedEvent(device=target))


@event.listens_for(Device, 'after_delete')
def emit_device_removed(mapper, connection, target):
    eventbus.post(DeviceRemovedEvent(device=target))


async def init_db(app):
    pass


async def close_db(app):
    pass
