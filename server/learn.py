from server.eventbus import subscribe, eventbus, Mode
from server.events import HeartbeatEvent, StartRecordingSignals, StopRecordingSignals
from server.models import DeviceHeartbeat, Session


class Learn:
    def __init__(self):
        self.recording_room = None
        self.recording_device = None
        self.db_session = Session()
        eventbus.register(self, self.__class__.__name__)

    @subscribe(on_event=StartRecordingSignals)
    def handle_start_recording(self, event):
        self.recording_room = event.room
        self.recording_device = event.device

    @subscribe(on_event=StopRecordingSignals)
    def handle_stop_recording(self, event):
        self.recording_room = None
        self.recording_device = None

    @subscribe(thread_mode=Mode.BACKGROUND, on_event=HeartbeatEvent)
    def handle_device_heartbeat(self, event):
        if (not event.signals
                or not self.recording_room
                or not self.recording_device
                or event.device != self.recording_device):
            return

        self.db_session.add(DeviceHeartbeat(
            device_id=event.device.id,
            room_id=self.recording_room.id,
            signals=event.signals,
        ))
        self.db_session.commit()
