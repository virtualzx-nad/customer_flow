# -*- encoding: utf-8 -*-
"""A helper script that reads an object from S3, apply a schema to it
then supply it to Pulsar as a stream producer.
Here we dictate that Avro schema be used throughout the system."""
import logging
import sys
import time

import smart_open
import pulsar
from schema_model import model_class_factory


def process_file(s3object, schema, broker='pulsar://localhost:6650', topic='test',
                 max_records=-1):
    Model = model_class_factory(**schema)
    client = pulsar.Client(broker)
    producer = client.create_producer(topic, schema=pulsar.schema.AvroSchema(Model))
    t0 = time.time()
    data = None
    for i, line in enumerate(smart_open.open(s3object)):
        if i == max_records:
            break
        data = yaml.safe_load(line)
        producer.send(Model.from_dict(data))
    logger.info('Last record: %s', str(data))
    logger.info("Processing speed: %.2f records/s", i / (time.time()-t0))
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
