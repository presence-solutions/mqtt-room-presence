import socketio as sio
from server.eventbus import subscribe
from server.events import HeartbeatEvent, TrainingProgressEvent

socketio = sio.AsyncServer(async_mode='aiohttp')


@subscribe(TrainingProgressEvent)
async def handle_training_progress(event):
    await socketio.emit('training_progress', event._asdict())


@subscribe(HeartbeatEvent)
async def handle_heartbeat(event):
    await socketio.emit('heartbeat', await event.as_dict())
