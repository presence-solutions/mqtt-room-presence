from aiohttp import web
from server.server import app
from server.models import Device, Scanner, Session, Room
from server.events import StartRecordingSignalsEvent
from server.eventbus import eventbus

session = Session()
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

web.run_app(app)
