import uvicorn
from server.server import app

uvicorn.run(app, host='0.0.0.0', port=5000)
