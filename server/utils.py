import asyncio
from server.models import get_rooms_scanners
from sklearn import preprocessing
import functools


def normalize_data_row(x_data_rows):
    # return x_data_rows
    return preprocessing.normalize([x_data_rows], norm='l2')[0]


def normalize_rssi_value(rssi):
    """
    Change RSSI value to be more suitable for ML algorithms.
    The current version is based on the idea that the lower
    value of the neuron the less significant that neuron is.
    When we have no data and RSSI is -100 this function
    will convert it to 0 which will kind of deactivate the neuron.
    It gives a better result for NN classifier and do not impact too much
    the other classifiers.
    """
    return (rssi + 108) / (108 - 59)


def create_x_data_row(signals, scanners):
    X_data_row = []
    for scanner in scanners:
        signal = signals.get(scanner.uuid, {})
        X_data_row.append(normalize_rssi_value(signal.get('filtered_rssi', -100)))

    return normalize_data_row(X_data_row)


async def calculate_inputs_hash(rooms=None, scanners=None):
    if not scanners or not rooms:
        rooms, scanners = await get_rooms_scanners()

    sorted_rooms = sorted(str(r.id) for r in rooms)
    sorted_scanners = sorted(str(s.id) for s in scanners)
    id_str = '.'.join((sorted_rooms + ['|'] + sorted_scanners))

    return id_str


def run_in_executor(f):
    @functools.wraps(f)
    def inner(*args, **kwargs):
        loop = asyncio.get_running_loop()
        return loop.run_in_executor(None, lambda: f(*args, **kwargs))

    return inner
