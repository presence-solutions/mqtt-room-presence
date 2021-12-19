from ariadne.asgi import GraphQL
from starlette.applications import Starlette
from server.mqtt import setup_mqtt
from server.service import start_service
from server.models import init_db, close_db
from server.api import schema

app = Starlette(
    on_startup=[init_db, setup_mqtt, start_service],
    on_shutdown=[close_db],
    debug=True
)
app.mount("/graphql", GraphQL(schema, debug=True))
