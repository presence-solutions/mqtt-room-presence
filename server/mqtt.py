import asyncio
import jsons
from asyncio_mqtt import Client, MqttError
from server import config
from server.eventbus import eventbus
from server.events import MQTTConnectedEvent, MQTTDisconnectedEvent, MQTTMessageEvent
from contextlib import AsyncExitStack


async def connect_mqtt():
    async with AsyncExitStack() as stack:
        tasks = set()
        stack.push_async_callback(cancel_tasks, tasks)

        # Connect to the MQTT broker
        client = Client(
            hostname=str(config.MQTT_BROKER_URL), port=config.MQTT_BROKER_PORT,
            username=str(config.MQTT_USERNAME), password=str(config.MQTT_PASSWORD))

        await stack.enter_async_context(client)

        # Take all messages and emit them to the event bus
        messages = await stack.enter_async_context(client.unfiltered_messages())
        task = asyncio.create_task(emit_messages(messages))
        tasks.add(task)

        # Subscribe to topic(s)
        # Note that we subscribe *after* starting the message
        # loggers. Otherwise, we may miss retained messages.
        eventbus.post(MQTTConnectedEvent(client=client))

        # Wait for everything to complete (or fail due to, e.g., network
        # errors)
        await asyncio.gather(*tasks)


async def emit_messages(messages):
    async for message in messages:
        eventbus.post(MQTTMessageEvent(
            topic=message.topic,
            payload=jsons.loads(message.payload.decode())
        ))


async def cancel_tasks(tasks):
    for task in tasks:
        if task.done():
            continue
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


async def start_mqtt():
    reconnect_interval = 3
    while True:
        try:
            await connect_mqtt()
        except MqttError as error:
            eventbus.post(MQTTDisconnectedEvent())
            print(f'Error "{error}". Reconnecting in {reconnect_interval} seconds.')
        finally:
            await asyncio.sleep(reconnect_interval)


async def setup_mqtt():
    asyncio.create_task(start_mqtt())
