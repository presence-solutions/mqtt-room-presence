from asyncio import create_task
from asyncio.coroutines import iscoroutine
import inspect


class EventBus:
    event_method = {}

    def post(self, event):
        methods = self.event_method.get(event.__class__, {})
        for method, decriptor in methods.items():
            instances, with_instance = decriptor

            if not with_instance:
                self.call(method=method, with_event=event, subscriber=None)
            else:
                for instance in instances:
                    self.call(method=method, with_event=event, subscriber=instance)

    def call(self, method, with_event, subscriber):
        coro = method(subscriber, with_event) if subscriber else method(with_event)
        if iscoroutine(coro):
            create_task(coro)

    def register_instance_subscribers(self, instance, methods):
        for method in methods:
            event = method._subscriber
            self.event_method[event][method][0].add(instance)

    def remove_instance_subscribers(self, instance, methods):
        for method in methods:
            event = method._subscriber
            self.event_method[event][method][0].remove(instance)

    def add_subscriber_method(self, event, method, with_instance):
        descriptor = (set(), with_instance)
        if event in self.event_method:
            self.event_method[event][method] = descriptor
        else:
            self.event_method[event] = { method: descriptor }


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
