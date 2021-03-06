import json
from flask_mqtt import Mqtt
from server.eventbus import eventbus
from server.events import MQTTConnectedEvent, MQTTMessage

mqtt = Mqtt()


@mqtt.on_connect()
def handle_mqtt_connect(*args, **kwargs):
    eventbus.post(MQTTConnectedEvent(*args, **kwargs))


@mqtt.on_message()
def handle_mqtt_message(client, userdata, message):
    eventbus.post(MQTTMessage(
        topic=message.topic,
        payload=json.loads(message.payload.decode())
    ))
