#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""Simple throughput test.  Just publish one message repeatedly.""" 
import logging
import sys
import time
from functools import partial

import pulsar
import yaml

from pipeline_utils import CallbackHandler


def test_message(message, broker='pulsar://localhost:6650', topic='test',
                 max_records=100000, batching=True, max_pending=10000):

    message_size = sys.getsizeof(message)
    logger.info('Throughput test message: %s  (%d bytes)', message, message_size)
    message_size /= 1048576.
    message = message.encode('utf-8')
    client = pulsar.Client(broker)
    producer = client.create_producer(topic, block_if_queue_full=True,
                                      batching_enabled=batching,
                                      max_pending_messages=max_pending)
    handler = CallbackHandler()
    t0 = time.time()
    for i in range(max_records):
        producer.send_async(message, callback=handler.callback) 
    producer.flush()
    dt = time.time()-t0
    logger.info("Message rate: %10.5f records/s", max_records / dt)
    if handler.dropped:
        logger.info("Dropped messages:  %d", handler.dropped)
        logger.info("Last result:       %s", handler.result)
    logger.info("Throughput:   %10.5f MB/s", max_records * message_size / dt)
    client.close()

if __name__ == '__main__':
    import yaml
    # If Yaml setting file is not supplied
    if len(sys.argv) < 1:
        raise ArgumentError('Did not suppy settings through yaml file')
    with open(sys.argv[1]) as f:
        settings = yaml.safe_load(f)
    logging.basicConfig(level=settings.pop('log_level', 'INFO'))
    logger = logging.getLogger(__name__)

    test_message(**settings)
