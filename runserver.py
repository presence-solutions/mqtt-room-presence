from os import name
from server.server import socketio, app
from server.models import Device, Scanner, Session

session = Session()
session.add(Scanner(uuid="office", name=""))
session.add(Scanner(uuid="office_2", name=""))
session.add(Scanner(uuid="office_3", name=""))
session.add(Device(name="Mi Smart Band 4", uuid="cf4ffda76286"))
session.commit()

socketio.run(app, host='0.0.0.0', port=5000, use_reloader=False, debug=True)
