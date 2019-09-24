#!/usr/bin/env python3
"""Hash a message stream into multiple streams based on a key.
(Equivalent to Flink KeyBy)"""
import logging
import sys
import time

import pulsar
import yaml

from pipeline_utils.schema_model import model_class_factory


if len(sys.argv) < 1:
    raise ArgumentError('Did not suppy settings through yaml file')
with open(sys.argv[1]) as f:
    settings = yaml.safe_load(f)

logging.basicConfig(level=settings.get('logging_level', 'INFO'))
logger = logging.getLogger(__name__)

# Connect the consumer, i.e. stream to be splitted.
client = pulsar.Client(settings['broker'])
Model = model_class_factory(**settings['schema'])
avro_schema = pulsar.schema.AvroSchema(Model)
consumer = client.subscribe(settings['topic'], schema=avro_schema,
                            subscription_name=settings['name'],
                            consumer_type=pulsar.ConsumerType.Shared)

# Connect the producers for each substream
partitions = settings['partitions']
shift = settings['shift']
format_str = settings['topic_format']
producers = [client.create_producer(format_str.format(index + shift),
                                    schema=avro_schema)
             for index in range(partitions)]

# Start hashing streams!!!!
max_records = settings['max_records']
key_by = settings['key_by']
timeout = settings['timeout']
t0 = time.time()
i = 0
while i != max_records:
    try:
        message = consumer.receive(timeout)
    except Exception as e: 
        logger.info('Source stream timeout. '+ str(e))
        t0 += timeout * 0.001
        break
    data = message.value()
    consumer.acknowledge(message)
    i += 1
    key = getattr(data, key_by)
    index = hash(key) % partitions
    producers[index].send(data)
logger.info('Total messages processed: %d', i)
logger.info('Average processing rate: %.2f records/s', i/(time.time()-t0))
client.close()

