"""compute in a continuous event triggered sliding window"""
import logging
import sys
import time
import datetime

import pulsar
import yaml

from schema_model import model_class_factory
from redis import Redis

def inc(state, data):
    return int(state) + 1

def dec(state, data):
    return int(state) - 1

def process_window(settings, add_func, remove_func, default_state):
    state = Redis(settings['state_server'], db=settings['state_id'])

    client = pulsar.Client(settings['broker'])
    schema = settings['schema']
    Model = model_class_factory(**schema)
    avro_schema = pulsar.schema.AvroSchema(Model)
    consumer = client.subscribe(settings['topic'],
                                subscription_name=settings['name'],
                                schema=avro_schema)
    reader = None
    key_by = settings['key_by']
    date_field = settings['date_field']
    if key_by not in schema or date_field not in schema:
        logger.info('key_by:     %s', key_by)
        logger.info('date_field: %s', date_field)
        logger.info('Schema:     %s', str(schema))
        raise KeyError('Key chosen for updating the state table is not in the schema')

    window = settings['window']
    date_format = settings['date_format']
    max_records = settings['max_records']
    t0 = time.time()
    i = 0
    while i != max_records:
        i += 1
        try:
            message = consumer.receive(500)
        except Exception as e:
            logger.error(str(e))
            break
        data = message.value().__dict__
        consumer.acknowledge(message)
        key = data[key_by]
        t_right = datetime.datetime.strptime(data[date_field], date_format).timestamp()
        # First time a key is encountered
        if reader is None:
            reader = client.create_reader(settings['topic'],
                                          start_message_id=message.message_id(), schema=avro_schema)
            t_left = t_right
        if key in state:
            s_key = state[key]
        else:
            s_key = default_state
        state[key] = add_func(s_key, data)
        while t_left <= t_right - window and reader.has_message_available():
            message = reader.read_next()
            data = message.value().__dict__
            keyl = data[key_by]
            t_left = datetime.datetime.strptime(data[date_field], date_format).timestamp()
            state[keyl] = remove_func(state[keyl], data)
        s = int(state[key])
        if s > 10:
            logger.info('Business %s has %d checkins at %12.2f', data['business_id'], s, t_right)

    print('Average processing rate: {:.2f} records/s'.format(i/(time.time()-t0)))
    client.close()

if __name__ == '__main__':
    if len(sys.argv) < 1:
        raise ArgumentError('Did not suppy settings through yaml file')
    with open(sys.argv[1]) as f:
        settings = yaml.safe_load(f)

    logging.basicConfig(level=settings.get('logging_level', 'INFO'))
    logger = logging.getLogger(__name__)
    process_window(settings, inc, dec, 0)

