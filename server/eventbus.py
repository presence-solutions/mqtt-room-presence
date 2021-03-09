from asyncio.coroutines import iscoroutine
import threading
from asyncio import create_task
from queue import Queue
from threading import Thread


class Mode:
    POSTING = 0
    COROUTINE = 3
    BACKGROUND = 1
    PARALLEL = 4
    CONCURRENT = 5


class EventBusThread(threading.Thread):
    def __init__(self, threadID, name=None, counter=None, method=None, event=None, subscriber=None):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.name = name
        self.counter = counter
        self.method = method
        self.event = event
        self.subscriber = subscriber

    def run(self):
        self.method(self.subscriber, self.event)


class EventBus:
    subscribers = {}
    pending_events = []
    event_method = {}
    method_mode = {}

    def __init__(self):
        self.common_background_thread = EventBusThread(0, "EventBusBackgroundThread", 1)
        self.queue = Queue(maxsize=0)
        self.num_threads = 10
        for worker in [lambda: self.start_workers() for i in range(self.num_threads)]:
            worker()

    def start_workers(self):
        worker = Thread(target=self.monitor_queue, args=(self.queue,))
        worker.setDaemon(True)
        worker.start()

    def monitor_queue(self, q):
        while True:
            q.get()
            q.task_done()

    def register(self, subscriber=None, subscriber_key=None):
        self.subscribers[subscriber_key] = subscriber

    def post(self, event):
        self.pending_events.append(event)
        self.execute()

    def call(self, method, with_event, in_mode, subscriber):
        coro = method(subscriber, with_event)
        if iscoroutine(coro):
            create_task(coro)

    def execute(self):
        for event in self.pending_events:
            self.pending_events.remove(event)
            if event.__class__ in self.event_method:
                for method in self.event_method[event.__class__]:
                    subscribers_with_method = filter(
                        lambda subscriber: has_instance_the_method(method, subscriber),
                        self.subscribers.values())

                    for subscriber in subscribers_with_method:
                        self.call(
                            method=method, with_event=event, in_mode=self.method_mode.get(method),
                            subscriber=subscriber)

    def addEventsWithMethods(self, event, method, thread_mode):
        self.method_mode[method] = thread_mode
        if event in self.event_method:
            subscribedMethodsForEvent = self.event_method.get(event)
            subscribedMethodsForEvent.append(method)
            for method in self.event_method.get(event):
                self.event_method[event] = subscribedMethodsForEvent
        else:
            self.event_method[event] = [method]


def has_instance_the_method(method, subscriber):
    return method.__module__ == subscriber.__module__ and method.__name__ in dir(subscriber)


def subscribe(thread_mode=Mode.POSTING, on_event=None):
    def real_decorator(function):
        eventbus.addEventsWithMethods(on_event, function, thread_mode)

        def wrapper(*args, **kwargs):
            return function(*args, **kwargs)
        return wrapper

    return real_decorator


eventbus = EventBus()
