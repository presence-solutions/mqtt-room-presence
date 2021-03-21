from server.models import get_rooms_scanners


async def create_x_data_row(signals, scanners=None):
    if not scanners:
        rooms, scanners = await get_rooms_scanners()

    X_data_row = []
    for scanner in scanners:
        signal = signals.get(scanner.uuid, {})
        X_data_row.append(signal.get('filtered_rssi', -100))

    return X_data_row


async def calculate_inputs_hash(rooms=None, scanners=None):
    if not scanners or not rooms:
        rooms, scanners = await get_rooms_scanners()

    sorted_rooms = sorted(str(r.id) for r in rooms)
    sorted_scanners = sorted(str(s.id) for s in scanners)
    id_str = '.'.join((sorted_rooms + ['|'] + sorted_scanners))

    return id_str
