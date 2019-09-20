"""compute in a continuous event triggered sliding window"""
import logging
import time
import datetime

import pulsar
from redis import Redis

from schema_model import model_class_factory


logger = logging.getLogger(__name__)


# Helper worker functions
def incr(state, key, data):
    state.incr(key)

def decr(state, key, data):
    state.decr(key)

def output_integer(state=None, key=None):
    """Directly output the value associated with the key."""
    return int(state[key])
    
def process_time_window(add_func, remove_func, init_func, topic, schema,
                        output_topic, output_func, output_field, output_schema,
                        window=10.0, key_by=None, name=None,
                        broker='pulsar://localhost:6650', max_records=-1,
                        state_server='localhost', state_id=1,
                        date_field='date', date_format='%Y-%m-%d %H:%M:%S',
                        **settings):
    """Update the state correspond to an event stream for a continuously
    sliding time window.
    """
    state = Redis(state_server, db=state_id)

    client = pulsar.Client(broker)
    Model = model_class_factory(**schema)
    avro_schema = pulsar.schema.AvroSchema(Model)
    consumer = client.subscribe(topic,
                                subscription_name=name,
                                schema=avro_schema)
    reader = None
    if key_by is not None and key_by not in schema or date_field not in schema:
        logger.info('key_by:     %s', key_by)
        logger.info('date_field: %s', date_field)
        logger.info('Schema:     %s', str(schema))
        raise KeyError('Key chosen for updating the state table is not in the schema')

    OutModel = model_class_factory(**output_schema)
    producer = client.create_producer(output_topic,
                                      schema=pulsar.schema.AvroSchema(OutModel))

    t0 = time.time()
    i = 0
    while i != max_records:
        i += 1
        try:
            message = consumer.receive(1000)
        except Exception as e:
            logger.info('Consumer has been depleted.  Message %s', str(e))
            t0 += 1
            break
        data = message.value().__dict__
        consumer.acknowledge(message)
        key = "___all-fields___" if key_by is None else data[key_by]
        t_right = datetime.datetime.strptime(data[date_field], date_format).timestamp()
        # First time a key is encountered
        if reader is None:
            reader = client.create_reader(topic, schema=avro_schema,
                                          start_message_id=message.message_id())
            t_left = t_right
        if key in state:
            add_func(state, key, data)
        else:
            init_func(state, key, data)
        keys_changed = {key}
        key_decreased = False
        while t_left <= t_right - window and reader.has_message_available():
            message = reader.read_next()
            data = message.value().__dict__
            keyl = '___all-fields___' if key_by is None else data[key_by]
            t_left = datetime.datetime.strptime(data[date_field], date_format).timestamp()
            remove_func(state, keyl, data)
            keys_changed.add(keyl)
        for key in keys_changed:
            output = output_func(state, key)
            if output is None:
                continue
            if key_by is None:
                producer.send(OutModel.from_dict({output_field: output}))
            else:
                producer.send(OutModel.from_dict({key_by: key, output_field:output}))

    logger.info('Average processing rate: {:.2f} records/s'.format(i/(time.time()-t0)))
    client.close()


