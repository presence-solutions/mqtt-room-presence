import time
from flask import Flask
from heartbeat import Heartbeat
from learn import Learn
from predict import Predict
from sensor import Sensor

app = Flask(__name__)
heartbeat = Heartbeat()
learn = Learn()
predict = Predict()
sensor = Sensor()


@app.route('/api/time')
def get_current_time():
    return {'time': time.time()}
