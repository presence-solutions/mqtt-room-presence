from aiohttp import web
from server.server import app

web.run_app(app, port=5000)
