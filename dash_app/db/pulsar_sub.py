"""Handles subscriptions from Pulsar to retrieve metrics."""
import os
import uuid
import time
import logging
from collections import defaultdict


import pulsar
import pandas


BROKER = os.environ.get("PULSAR_BROKER", 'pulsar://10.0.0.16:6650')

logger = logging.getLogger(__name__)


class LatencyTracker(object):
    """Susbscribe to the metric channel to obtain realtime updates of latency info"""
    def __init__(self, broker=BROKER, topic='metric:window_ratio', name=None, cooldown=1):
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
        self.time = defaultdict(list)
        self.event_time = defaultdict(list)
        self.latency = defaultdict(list)
        self.rate = defaultdict(list)
        self.ingestion_rate = defaultdict(list)
        self.last_count = {}
        self.last_timestamp = {}
        self.last_eventtime = {}

    def update(self, timeout=20, memory=5):
        # First check if it is time to refresh yet. 
        # No redundant updates within the specified cooldown period.
        t_now = time.time()
        if t_now <= self.tip:
            return
        self.tip = t_now + self.cooldown
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
                ing_rate = (counter - self.last_count[name]) / (t - self.last_eventtime[name]) / 1000 
                latency = (t - event_time)*1000
                print(data, rate, latency)
                self.time[name].append(t)
                self.event_time[name].append(event_time)
                self.latency[name].append(latency)
                self.rate[name].append(rate)
                self.ingestion_rate[name].append(ing_rate)
                self.last_latency = latency
            self.last_count[name] = counter
            self.last_timestamp[name] = t
            self.last_eventtime[name] = event_time
        # Take the average latency and total rate of all recent data
        cutoff = t_now - memory
        latency = 0
        n = 1e-4
        rate = 0
        inrate=0
        for name in self.last_count.keys():
            if self.time[name] and self.time[name][-1] > cutoff:
                rate += self.rate[name][-1]
                inrate += self.ingestion_rate[name][-1]
                latency += self.latency[name][-1]
                n += 1
        latency /= n
        self.time['all'].append(t_now)
        self.rate['all'].append(rate)
        self.ingestion_rate['all'].append(inrate)
        self.latency['all'].append(latency)


