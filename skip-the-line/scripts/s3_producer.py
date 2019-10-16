#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
"""A helper script that reads an object from S3, apply a schema to it
then supply it to Pulsar as a stream producer.
Here we dictate that Avro schema be used throughout the system."""
import logging
import uuid
import sys
import time

import smart_open
import pulsar
from pipeline_utils import model_class_factory, CallbackHandler


logger = logging.getLogger(__name__)


def process_request(reader, wait=False, timeout=20):
    """Read requests from a Pulsar Reader.Returns None if there is no valid command

    Requests are in the format of   `<command>:<value>`.
    Allowed commands and values are:
        STATE       PAUSE / RESUME / STOP   Signal the processor to pause, resume or exit.
        PARTITIONS  <num partitions>        Change the number of partitions
        MULT        <multiplicity>          Change the multiplicity factor
        RATE        <max rate>              Change the maximum publication rate (before
                                            multiplication of messages)
    """
    if not reader or not (reader.has_message_available() or wait):
        return
    try:
        if wait:
            timeout = None
        message = reader.read_next(timeout)
    except Exception as e:
        logger.debug('Reader timeout.  No message available. ' + str(e))
        return
    request = message.value()
    if ':' not in request:
        logger.warn('Invalud request: [%s]', request)
        return
    command, value = request.split(':', 1)
    command = command.strip().upper()
    value = value.strip()
    if not command or not value:
        logger.warn('Incomplete request: [%s]', request)
        return

    if 'STATUS'.startswith(command):
        # process status change
        value = value.upper()
        if value in ['PAUSE', 'RESUME', 'STOP']:
            return 'STAT', value
    else: # Then value must be an integer. Check that
        if not value.isdigit():
            logger.warn('Value must be an integer')
            return
        value = int(value)
        if value <= 0:
            logger.warn('Value must be positive')
            return
        
        if 'PARTITIONS'.startswith(command):
            return 'PART', value
        if 'RATE'.startswith(command):
            return 'RATE', value
        if 'MULTIPLICITY'.startswith(command):
            return 'MULT', value
    logger.warn('Unrecognized command [%s]', command)


def process_file(s3object, schema, broker='pulsar://localhost:6650', topic='test',
                 max_records=-1, batching=True, max_pending=5000, multiplicity=1,
                 vectorize=True, timestamp=False, partitions=None, key_by='',
                 request_topic='', max_rate=1000, service_interval=200,
                 response_time=0.2, start_position=0):
    """Read from S3 and publish to Pulsar.  It can also ingest from a local/network file
    or HDFS, if the URI of the file is supplied.

    This utility tool can create a specified schema and import data from S3 to publish to
    a given topic.  Also performs basic transformations such as timestamping and vectorizing
    arrays given in string forms.  The output can be hashed to a range of channels based
    on the contents of a specified a key field.  It also allows a maximum publication rate
    to be specifed (in messages per second), and multiplication of messages to achieve
    higher throughput.

    When a request topic is given, several of the settings can be modified through commands
    sent through this topic.  See `process_request()` for format and allowed commands.
    
    Args:
        s3object:     Address of the S3 object. i.e. s3://my-bucket/directory/some_file.json
        schema:       Schema of the s3 data
        broker:       Pulsar broker address
        topic:        Which topic to publish to
        max_records:  Maximum of records to publish.  Default is -1, meaning no limits
        batching:     Allow producer batching.
        max_pending:  Maximum number of allowed pending records in producer queue
        multiplicity: The messages are sent out this number of times for each entry in S3
        timestamp:    Timestamp the messages based on the current time. If specified, this
                      argument should contain the field name for the timestamp to live in.
                      Floating point number in seconds.
        vectorize:    If True, parse any field that is specified as an Array in the Schema,
                      but is written in S3 as a String.
        partitions:   If specified, will partition the messaged based on a key.
        key_by:       Which field to use as partition key.  The key will be hashed and messages
                      published to channels based on the key hash.
        max_rate:     Maximum publication rate per second. Before the multiplication factor.
        request_topic:      If specified, will listen to command in this topic and update settings.
        service_interval:   Interval between which the rates will be monitored and incoming
                            requests processed.
        response_time:      Minimum time interval for accepting requests.  This will increase
                            frequency of request polling if max_rate is low.
        start_position:     Start from this position, instead of the beginning.
    """
    # Create the schema model for the output topic
    Model = model_class_factory(**schema)
    avro_schema = pulsar.schema.AvroSchema(Model)

    logger.info('Initializing client and request reader.')
    # Create a Pulsar client and a group of producers
    client = pulsar.Client(broker)
    # Because partitions may change, producers are only created when needed
    producers = {}
    def get_producer(i=None):
        if i not in producers:
            if i is None:
                t = topic
            else:
                t = '{}-{}'.format(topic, i)
            logger.info('Creating producer for topic %s', t)
            producers[i] = client.create_producer(t, schema=avro_schema,
                              block_if_queue_full=True,
                              batching_enabled=batching,
                              max_pending_messages=max_pending
                          ) 
        return producers[i]

    # Create the request reader
    request_reader = None
    if request_topic:   # Initiate a request reader.
        request_reader = client.create_reader(request_topic,
                pulsar.MessageId.latest,  # Always read from the end
                schema=pulsar.schema.StringSchema(),  # Commands in plain text
                reader_name='s3_reader:'+str(uuid.uuid4())  # Unique name
            )
        logger.info('Will read request from topic [%s]', request_topic)
    # The last time a request has been processed or message rate measured
    last_stamp = t0 = time.time()
    last_i = -1
    # If the reader has been paused
    paused = False
    stopped = False

    data = None
    # Determine which fields will be vectorized
    if vectorize is True:
        vectorize = [field for field, kind in schema.items() if kind[0] == 'Array']

    # Callback handler for async producer.
    handler = CallbackHandler()

    # Calculate the interval at which control requests and max rates will be processed
    min_interval = max(1, int(response_time * max_rate))
    interval = min(service_interval, min_interval) 

    # This is for keeping track where in the file we are, for restarting
    logger.info('Starting to process %s', str(s3object))
    position = 0
    try:    # Ensure that clients are properly closed on error exit
        # Read content of the S3 object
        with smart_open.open(s3object) as f:
            # Track the current position.  This is for restarting purposes
            if start_position > 0:
                f.seek(start_position)
                position = start_position

            for i, line in enumerate(f):
                if i == max_records:
                    logger.info('Maximum number of records reached.')
                    break
                position += len(line)
                # Check if we need to check publication rates 
                if interval > 0 and i % interval == 0:
                    # First read requests
                    while True:
                        request = process_request(request_reader, wait=paused)
                        if not request and not paused:
                            break
                        command, value = request
                        logger.info('Received request {}, {} from {}'.format(command,
                                     value, request_reader.topic())) 
                        if command == 'STAT':  # Change status
                            if value == 'PAUSE':
                                if not paused:
                                    logger.info('Publication paused.')
                                    paused = True
                            elif value == 'RESUME':
                                if paused:
                                    logger.info('Publication resumed')
                                    paused = False
                                    last_i = i
                            elif value == 'STOP':
                                stopped = True
                                logger.info('Publication stopped')
                        elif command == 'PART':   # Change partitions
                            partitions = value 
                            logger.info('Number of partitions changed to %d', value)
                        elif command == 'MULT':
                            multiplicity = value
                            logger.info('Message multiplicity changed to %d', value)
                        elif command == 'RATE':
                            max_rate = value
                            logger.info('Max rate changed to %d', value)
                            min_interval = max(1, int(response_time * max_rate))
                            interval = min(service_interval, min_interval) 
                        if not paused or stopped:
                            break
                    # Now check message rate is too high
                    dt_plan = float(i - last_i) / max(max_rate, 0.1)
                    t_now = time.time()
                    dt_actual = t_now - last_stamp
                    if dt_actual < dt_plan:
                        logger.debug('Processed %d msg in %.2fs. Waiting %.3fs.',
                            i - last_i, dt_actual, dt_plan - dt_actual)
                        time.sleep(dt_plan - dt_actual)
                    last_stamp = time.time()
                    last_i = i

                if stopped:
                    break

                # Get the data from S3 and process it into proper dict form
                try:
                    data = yaml.safe_load(line)
                except yaml.parser.ParserError:
                    logger.warn('Badly formed line skipped: %s', line)
                    continue
                if vectorize:
                    for key in vectorize:
                        if isinstance(data[key], str):
                            data[key] = [entry.strip() for entry in data[key].split(',')]
                if timestamp:
                    data[timestamp] = time.time()
                # check which partition I am in 
                if partitions:
                    if key_by not in schema:
                        raise ValueError('Need to specify a proper key field for partitioning.')
                    index = hash(data[key_by]) % partitions
                    producer = get_producer(index)
                else:
                    producer = get_producer()
                for j in range(multiplicity):
                    producer.send_async(Model.from_dict(data), handler.callback)
        for producer in producers.values():
            producer.flush()
        logger.info('Last record: %s', str(data))
        logger.info("Processing rate: %.2f records/s", i * multiplicity/ (time.time()-t0))
        if handler.dropped:
            logger.info('Number of dropped messaged: %d', handler.dropped)
            logger.info('Last error result:          %s', handler.result)
    finally:
        logger.info('Exit position: %d', position)
        client.close()


if __name__ == '__main__':
    import yaml
    # If Yaml setting file is not supplied
    if len(sys.argv) < 1:
        raise RuntimeError('Did not suppy settings through yaml file')
    with open(sys.argv[1]) as f:
        settings = yaml.safe_load(f)
    if not isinstance(settings, dict):
        raise RuntimeError('Invalid settings file.')
    logging.basicConfig(level=settings.pop('logging_level', 'INFO'))

    process_file(**settings)
