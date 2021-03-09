from datetime import datetime
from aiohttp import web


async def time_api():
    return web.json_response({'time': datetime.now()})


def setup_routes(app):
    app.router.add_get('/api/time', time_api)
