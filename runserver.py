from server.server import socketio, app
from server.models import Device, Scanner, Session, Room
from server.events import StartRecordingSignals
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

eventbus.post(StartRecordingSignals(
    device=session.query(Device).first(),
    room=session.query(Room).first()
))

socketio.run(app, host='0.0.0.0', port=5000, use_reloader=False, debug=True)
# {"id":"4debad57eb66","uuid":"4debad57eb66","rssi":-86,"name":"iPhone (Anna)","txPower":12,"distance":3533415}
