import logging
from aiohttp import web
from server.mqtt import setup_mqtt
from server.socketio import socketio
from server.service import start_service
from server.api import setup_routes
from server.models import init_db, close_db
from server.config.base import Config

logging.basicConfig(level=logging.INFO)

app = web.Application()
app['config'] = Config

setup_routes(app)
socketio.attach(app)

app.on_startup.append(init_db)
app.on_startup.append(start_service)
app.on_startup.append(setup_mqtt)
app.on_cleanup.append(close_db)
