import eventlet
import logging
from flask import Flask
from server.mqtt import mqtt
from server.socketio import socketio
from server.service import Service
from server.api import api

eventlet.monkey_patch()
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.config.from_object('server.config.base.Config')
app.register_blueprint(api)

mqtt.init_app(app)
socketio.init_app(app)
service = Service()
