"""Reduction or aggregation on the full stream"""
import logging
import time

import pulsar
from redis import Redis

from .schema_model import model_class_factory
from .callback import CallbackHandler


logger = logging.getLogger(__name__)



def process_global_window(state, reduce_func, topic, schema,
                          output_topic, output_func, output_field, output_schema,
                          init_func=None, key_by=None, name=None, timeout=None,
                          broker='pulsar://localhost:6650', max_records=-1,
                          batching=True, max_pending=5000, initial_position='latest',
                          **settings):
    """Update the state correspond to an event stream for a continuously
    sliding time window.
    """
    if init_func is None:
        init_func = reduce_func

    client = pulsar.Client(broker)
    Model = model_class_factory(**schema)
    avro_schema = pulsar.schema.AvroSchema(Model)

    if initial_position == 'earliest':
        position = pulsar.InitialPosition.Earliest
    elif initial_position == 'latest':
        position = pulsar.InitialPosition.Lastest
    else:
        raise ValueError('Initial position must be latest or earliest.')

    consumer = client.subscribe(topic, initial_position=position,
                                subscription_name=name,
                                schema=avro_schema)
    if key_by is not None and key_by not in schema:
        logger.info('key_by:     %s', key_by)
        logger.info('Schema:     %s', str(schema))
        raise KeyError('Key chosen for updating the state table is not in the schema')

    OutModel = model_class_factory(**output_schema)
    producer = client.create_producer(output_topic, block_if_queue_full=True,
                                      batching_enabled=batching,
                                      max_pending_messages=max_pending,
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
    handler = CallbackHandler()
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
        producer.send_async(OutModel.from_dict(record), handler.callback)
    producer.flush()
    logger.info('Total messages processed: %d', i)
    logger.info('Average processing rate: %.2f records/s', i/(time.time()-t0))
    client.close()
