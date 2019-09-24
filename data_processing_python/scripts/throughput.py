#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""Simple throughput test.  Just publish one message repeatedly.""" 
import logging
import sys
import time

import pulsar
import yaml


def test_message(message, broker='pulsar://localhost:6650', topic='test',
                 max_records=10000):
    message_size = sys.getsizeof(message)
    logger.info('Throughput test message: %s  (%d bytes)', message, message_size)
    message_size /= 1048576.
    client = pulsar.Client(broker)
    producer = client.create_producer(topic)
    t0 = time.time()
    for i in range(max_records):
        producer.send(message.encode('utf-8'))
    dt = time.time()-t0
    logger.info("Message rate: %10.5f records/s", max_records / dt)
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
