"""Reduction or aggregation on the full stream"""
import logging
import time

import pulsar
from redis import Redis

from .schema_model import model_class_factory


logger = logging.getLogger(__name__)


def process_global_window(reduce_func, topic, schema,
                          output_topic, output_func, output_field, output_schema,
                          init_func=None, key_by=None, name=None, timeout=1000,
                          broker='pulsar://localhost:6650', max_records=-1,
                          state_server='localhost', state_id=1, **settings):
    """Update the state correspond to an event stream for a continuously
    sliding time window.
    """
    state = Redis(state_server, db=state_id)

    if init_func is None:
        init_func = reduce_func

    client = pulsar.Client(broker)
    Model = model_class_factory(**schema)
    avro_schema = pulsar.schema.AvroSchema(Model)
    consumer = client.subscribe(topic,
                                subscription_name=name,
                                schema=avro_schema)
    if key_by is not None and key_by not in schema:
        logger.info('key_by:     %s', key_by)
        logger.info('Schema:     %s', str(schema))
        raise KeyError('Key chosen for updating the state table is not in the schema')

    OutModel = model_class_factory(**output_schema)
    producer = client.create_producer(output_topic,
                                      schema=pulsar.schema.AvroSchema(OutModel))
    if output_field not in output_schema:
        raise KeyError('The output field is not in the schema.')
    if key_by is not None and key_by not in schema:
        raise KeyError('No field matched the `key_by` setting')
    for key in output_schema:
        if key == output_field:
            continue
        if key not in schema:
            raise KeyError('Output schema contains unknown fields')

    t0 = time.time()
    i = 0
    while i != max_records:
        try:
            message = consumer.receive(timeout)
        except Exception as e:
            logger.info('Consumer has been depleted.  Message %s', str(e))
            t0 += timeout * 1e-3
            break
        data = message.value().__dict__
        consumer.acknowledge(message)
        i += 1

        key = "___all-fields___" if key_by is None else data[key_by]
        if key in state:
            add_func(state, key, data)
        else:
            init_func(state, key, data)
        output = output_func(state, key, data)
        if output is None:
            continue
        record = {field: output if field == output_field else data[field]
                  for field in output_schema}
        producer.send(OutModel.from_dict(record))
    logger.info('Total messages processed: %d', i)
    logger.info('Average processing rate: %.2f records/s', i/(time.time()-t0))
    client.close()
