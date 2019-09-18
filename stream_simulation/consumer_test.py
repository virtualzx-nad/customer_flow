# Consumer test.  Do character counts
import logging
import sys

import pulsar
import yaml

from schema_model import model_class_factory


if len(sys.argv) < 1:
    raise ArgumentError('Did not suppy settings through yaml file')
with open(sys.argv[1]) as f:
    settings = yaml.safe_load(f)
logging.basicConfig(level=settings.get('level', 'INFO'))

Model = model_class_factory(**settings['schema'])
print(Model.schema())

client = pulsar.Client('pulsar://localhost:6650')



consumer = client.subscribe('test-topic', subscription_name='consumer1', schema=pulsar.schema.AvroSchema(Model))

while True:
    message = consumer.receive(1000)
    data = message.value()
    # print("Received message for: %s" % data.name)
    consumer.acknowledge(message)
client.close()
