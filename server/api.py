from datetime import datetime
from aiohttp import web


async def time_api(app):
    return web.json_response({'time': 122})


def setup_routes(app):
    app.router.add_get('/api/time', time_api)
