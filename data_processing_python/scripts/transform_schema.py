#!/usr/bin/env python3
"""Consumer test.  Do character counts"""
import logging
import sys
import time
from pprint import pprint

import pulsar
import yaml

from pipeline_utils.schema_model import model_class_factory


if __name__ == '__main__':
    if len(sys.argv) < 1:
        raise ArgumentError('Did not suppy settings through yaml file')
    with open(sys.argv[1]) as f:
        settings = yaml.safe_load(f)
    logging.basicConfig(level=settings.get('level', 'INFO'))

# Construct the source and target schemas
source_schema = settings['source_schema']
SourceModel = model_class_factory(**source_schema)
target_schema = settings['target_schema']
TargetModel = model_class_factory(**target_schema)

# Construct schema mapping.  Default is for the same name
schema_map = settings['schema_map']
for key, target_definition in target_schema.items():
    if key in schema_map:
        source_key = schema_map[key]
    else:
        schema_map[key] = key
        source_key = key
    source_definition = source_schema.get(source_key, 'undefined')
    if  source_definition != target_definition:
        raise TypeError('Source and target schema mismatch. '
                       '{}: {} => {}: {}'.format(
                           source_key, source_definition,
                           key, target_definition
                       ))

client = pulsar.Client(settings['broker'])

consumer = client.subscribe(settings['source_topic'],
                            subscription_name=settings['name'],
                            schema=pulsar.schema.AvroSchema(SourceModel))
producer = client.create_producer(settings['target_topic'],
                                  schema=pulsar.schema.AvroSchema(TargetModel))

t0 = time.time()
for i in range(settings['max_records']):
    message = consumer.receive(1000)
    source_data = message.value()
    consumer.acknowledge(message)
    target_data = {target_key: getattr(source_data, source_key)
                   for target_key, source_key in schema_map.items()}
    producer.send(TargetModel.from_dict(target_data))
logging.info('Average processing rate: %.2f records/s', i/(time.time()-t0))
client.close()
