#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""A helper script that reads an object from S3, apply a schema to it
then supply it to Pulsar as a stream producer.
Here we dictate that Avro schema be used throughout the system."""
import logging
import sys
import time

import smart_open
import pulsar
from pipeline_utils import model_class_factory, CallbackHandler


def process_file(s3object, schema, broker='pulsar://localhost:6650', topic='test',
                 max_records=-1, batching=True, max_pending=5000, vectorize=True):
    Model = model_class_factory(**schema)
    client = pulsar.Client(broker)
    producer = client.create_producer(topic, schema=pulsar.schema.AvroSchema(Model),
                                      block_if_queue_full=True,
                                      batching_enabled=batching,
                                      max_pending_messages=max_pending)
    t0 = time.time()
    data = None
    # Determine which fields will be vectorized
    if vectorize is True:
        vectorize = [field for field, kind in schema.items() if kind[0] == 'Array']
    # Callback handler for async producer.
    handler = CallbackHandler()
    for i, line in enumerate(smart_open.open(s3object)):
        if i == max_records:
            break
        data = yaml.safe_load(line)
        if vectorize:
            for key in vectorize:
                if isinstance(data[key], str):
                    data[key] = [entry.strip() for entry in data[key].split(',')]
        producer.send_async(Model.from_dict(data), handler.callback)
    producer.flush()
    logger.info('Last record: %s', str(data))
    logger.info("Processing rate: %.2f records/s", i / (time.time()-t0))
    if handler.dropped:
        logger.info('Number of dropped messaged: %d', handler.dropped)
        logger.info('Last error result:          %s', handler.result)
    client.close()

if __name__ == '__main__':
    import yaml
    # If Yaml setting file is not supplied
    if len(sys.argv) < 1:
        raise ArgumentError('Did not suppy settings through yaml file')
    with open(sys.argv[1]) as f:
        settings = yaml.safe_load(f)
    logging.basicConfig(level=settings.pop('level', 'INFO'))
    logger = logging.getLogger(__name__)

    process_file(**settings)
