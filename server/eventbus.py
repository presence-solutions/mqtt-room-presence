import asyncio
from asyncio.coroutines import iscoroutine
from asyncio.events import AbstractEventLoop
from asyncio.futures import Future
from asyncio.queues import Queue
from collections import namedtuple
import inspect


class EventBus:
    event_method = {}

    def post(self, event):
        results = []
        methods = self.event_method.get(event.__class__, {})
        for method, decriptor in methods.items():
            instances, with_instance = decriptor

            if not with_instance:
                results.append(self.call(method=method, with_event=event, subscriber=None))
            else:
                for instance in instances:
                    results.append(self.call(method=method, with_event=event, subscriber=instance))

        return_fut = asyncio.get_running_loop().create_future()
        results_fut = asyncio.gather(*results)
        results_fut.add_done_callback(lambda x: return_fut.set_result(True))
        return return_fut

    def call(self, method, with_event, subscriber):
        result = method(subscriber, with_event) if subscriber else method(with_event)
        if iscoroutine(result):
            return result
        else:
            fut = asyncio.get_running_loop().create_future()
            fut.set_result(result)
            return fut

    def register_instance_subscribers(self, instance, methods, on_event=None):
        for method in methods:
            method_event = method._subscriber if not on_event else on_event
            self.event_method[method_event][method][0].add(instance)

    def remove_instance_subscribers(self, instance, methods, on_event=None):
        for method in methods:
            method_event = method._subscriber if not on_event else on_event
            self.event_method[method_event][method][0].remove(instance)

    def add_subscriber_method(self, on_event, method, with_instance):
        descriptor = (set(), with_instance)
        if on_event in self.event_method:
            self.event_method[on_event][method] = descriptor
        else:
            self.event_method[on_event] = {method: descriptor}

    def remove_subscriber_method(self, on_event, method):
        if on_event in self.event_method:
            self.event_method[on_event].pop(method)

    def subscribe(self, on_event):
        return AsyncEventsIterator(self, on_event)


class AsyncEventsIterator():
    eventbus: EventBus
    on_event: namedtuple
    loop: AbstractEventLoop
    future_event: Future

    def __init__(self, eventbus, on_event):
        self.on_event = on_event
        self.eventbus = eventbus
        self.loop = asyncio.get_running_loop()
        self.queue = Queue()
        self.stopped = False

    async def event_receiver(self, event):
        if not self.stopped:
            self.queue.put_nowait(event)

    def __aiter__(self):
        return self

    async def __anext__(self):
        next_event = await self.queue.get()
        if next_event:
            return next_event
        else:
            raise StopAsyncIteration

    async def __aenter__(self):
        self.eventbus.add_subscriber_method(self.on_event, self.event_receiver, False)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.stop()

    def stop(self):
        if not self.stopped:
            self.stopped = True
            self.eventbus.remove_subscriber_method(self.on_event, self.event_receiver)
            self.queue.put_nowait(None)


class EventBusMetaclass(type):
    def __new__(metacls, name, bases, namespace, **kwds):
        result = type.__new__(metacls, name, bases, dict(namespace))
        result._subscribers = [value for value in namespace.values() if hasattr(value, '_subscriber')]
        return result


class EventBusSubscriber(metaclass=EventBusMetaclass):
    def __init__(self):
        eventbus.register_instance_subscribers(self, self._subscribers)

    def __del__(self):
        eventbus.remove_instance_subscribers(self, self._subscribers)


def subscribe(on_event):
    def real_decorator(function):
        def wrapper(*args, **kwargs):
            return function(*args, **kwargs)

        wrapper._subscriber = on_event
        spec = inspect.signature(function)
        with_instance = len(spec.parameters) == 2

        eventbus.add_subscriber_method(on_event, wrapper, with_instance)

        return wrapper

    return real_decorator


eventbus = EventBus()
