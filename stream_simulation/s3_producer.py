#!/usr/bin/env python
# -*- encoding: utf-8 -*-
"""A helper script that reads an object from S3, apply a schema to it
then supply it to Pulsar as a stream producer.
Here we dictate that Avro schema be used throughout the system."""
import logging
import sys
import time

import smart_open
from smart_open.smart_open_lib import Uri
import pulsar
from schema_model import model_class_factory


def process_file(s3object, schema, broker='pulsar://localhost:6650', topic='test',
                 max_lines=-1):
    Model = model_class_factory(**schema)
    client = pulsar.Client(broker)
    producer = client.create_producer(topic, schema=pulsar.schema.AvroSchema(Model))
    i0 = 0
    t0 = time.time()
    for i, line in enumerate(smart_open.open(s3object)):
        if i == max_lines:
            break
        t = time.time()
        if t > t0 + 1:
            print("Processing speed: %.2f records/s" % ((i-i0) / (t-t0)))
            t0 = t
            i0 = i
        producer.send(Model.from_dict(yaml.safe_load(line)))
    client.close()

if __name__ == '__main__':
    import yaml
    # If Yaml setting file is not supplied
    if len(sys.argv) < 1:
        raise ArgumentError('Did not suppy settings through yaml file')
    with open(sys.argv[1]) as f:
        settings = yaml.safe_load(f)
    logging.basicConfig(level=settings.pop('level', 'INFO'))
    process_file(**settings)
