from flask import Blueprint
from datetime import datetime

api = Blueprint('API', __name__)


@api.route('/api/time')
def time_api():
    return {'time': datetime.now()}
