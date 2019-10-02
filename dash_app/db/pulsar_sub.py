"""Handles subscriptions from Pulsar to retrieve metrics."""
import os
import uuid
import time
import logging


import pulsar
import pandas


BROKER = os.environ.get("PULSAR_BROKER", 'pulsar://10.0.0.16:6650')

logger = logging.getLogger(__name__)


class LatencyTracker(object):
    """Susbscribe to the metric channel to obtain realtime updates of latency info"""
    def __init__(self, broker=BROKER, topic='metric:window_ratio', name=None, cooldown=5):
        """Initialize the Latency tracker.

        Args:
            broker:     Pulsar Broker URL
            topic:      Topic where the metric data is published
            name:       Subscription name. By default a random one will be generated.
            cooldown:   Minimum amount of time between different attempts to fetch metrics
                        from the message queue."""
        logger.info('Connecting to Pulsar broker at %s', broker)
        self.client = pulsar.Client(broker)
        if name is None:
            name = str(uuid.uuid4())
        self.name = name
        self.consumer = self.client.subscribe(topic, subscription_name=name)
        self.cooldown = cooldown
        self.tip = -1e5
        self.time = []
        self.latency = []
        self.rate = []
        self.last_count = {}
        self.last_timestamp = {}

    def update_latency(self, timeout=20):
        # First check if it is time to refresh yet. 
        # No redundant updates within the specified cooldown period.
        t = time.time()
        if t <= self.tip:
            return
        self.tip = t + self.cooldown
        # Receive all new metrics from the pulsar client
        while True:
            try:
                message = self.consumer.receive(timeout)
            except Exception as e:
                break
            data = message.value()
            if isinstance(data, bytes):
                data = data.decode()
            name, counter, event_time, t = data.split(':')
            counter = int(counter)
            event_time = float(event_time)
            t = float(t)
            # Compute latency and message rate if it is not the first message
            if name in self.last_count:
                rate = (counter - self.last_count[name]) / (t - self.last_timestamp[name]) / 1000 
                latency = (t - event_time)*1000
                print(data, rate, latency)
                self.time.append(t)
                self.latency.append(latency)
                self.rate.append(rate)
            self.last_count[name] = counter
            self.last_timestamp[name] = t

