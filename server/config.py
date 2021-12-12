from starlette.config import Config
from starlette.datastructures import Secret

config = Config('.env')

SECRET_KEY = config('SECRET_KEY', cast=Secret)
MQTT_BROKER_URL = config('MQTT_BROKER_URL', cast=str)
MQTT_BROKER_PORT = config('MQTT_BROKER_PORT', cast=int, default=1883)
MQTT_USERNAME = config('MQTT_USERNAME', cast=str)
MQTT_PASSWORD = config('MQTT_PASSWORD', cast=Secret)
DATABASE_URI = config('DATABASE_URI', cast=Secret, default='sqlite://data.sqlite3')

TORTOISE_ORM = {
    "connections": {
        "default": str(DATABASE_URI)
    },
    "apps": {
        "models": {
            "models": ["server.models", "aerich.models"],
            "default_connection": "default",
        },
    },
}
