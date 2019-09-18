# Consumer test.  Do character counts
import logging
import sys
import time

import pulsar
import yaml

from schema_model import model_class_factory


if len(sys.argv) < 1:
    raise ArgumentError('Did not suppy settings through yaml file')
with open(sys.argv[1]) as f:
    settings = yaml.safe_load(f)
logging.basicConfig(level=settings.get('level', 'INFO'))

Model = model_class_factory(**settings['schema'])

client = pulsar.Client('pulsar://localhost:6650')



reader = client.create_reader('test-topic', start_message_id=pulsar.MessageId.earliest,
                                reader_name='reading_counter', schema=pulsar.schema.AvroSchema(Model))

t0 = time.time()
counter = 0
while reader.has_message_available():
    message = reader.read_next()
    data = message.value()
    # print("Received message for: %s" % data.name)
    counter += 1
print("Processing rate %5.2f records/s" % (counter / (time.time()-t0)))
client.close()
