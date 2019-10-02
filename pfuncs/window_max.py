"""Pulsar function for calculating the maximum value of a series in a time window"""
import time
from datetime import datetime, timedelta

from pulsar import Function
from pulsar.schema import AvroSchema

from pipeline_utils import model_class_factory
from redis import Redis



class WindowMax(Function):
    """a sorted list for each key is stored on redis"""
    def process(self, input, context):
        """Process the customer count and compute its maximum over a window"""
        config = context.user_config
        # Connect the redis state server
        state = Redis(config['state_server'], port=config['state_port'], db=config['state_id'])
        # Parse input message Schema
        RecordClass = model_class_factory(**config['schema'])
        record = RecordClass.decode(input)

        # Retrieve the `key` and `value` of the current input
        key = 'max:' + getattr(record, config['key_by'])
        value = getattr(record, config['value_field'])

        # Retrieve and parse the date field to compute time windows
        date_field = config.get('date_field', 'date')
        date_format = config.get('date_format', '%Y-%m-%d %H:%M:%S')
        t_last = datetime.strptime(getattr(record, date_field), date_format)
        t_start = t_last - timedelta(seconds=config['window'])
        stamp_last = t_last.timestamp()
        stamp_start = t_start.timestamp()

        # The state contains a stack of uniformly decreasing max values, with the most recent
        # value at the end.  First, pop all elements smaller than the current value
        while True:
            head = state.lpop(key)
            if head is None:
                break
            if isinstance(head, bytes):
                head = head.decode()
            t_head, value_head = head.split(':')
            if float(value_head) > value:
                state.lpush(key, head)
                break
        # Push the current value to the top of the stack
        state.lpush(key, "{}:{}".format(stamp_last, value))
        # Retire elements at the bottom that are no longer within the time window.  This is
        # actually not strictly necessary for the algorithm to work but does reduce the reading
        # cost and decreases the memory foot print.
        value_tail = value
        while True:
            tail = state.rpop(key)
            if tail is None:
                break
            if isinstance(tail, bytes):
                tail = tail.decode()
            t_tail, value_tail = tail.split(':')
            if float(t_tail) > stamp_start:
                state.rpush(key, tail)
                break
        # Encode the output message based on the proper schema and send it out
        ResultClass = model_class_factory(**config['output_schema'])
        result = ResultClass.clone_from(record)
        setattr(result, config['output_field'], type(value)(value_tail))

        # Record metrics for the function.  Default is to never record it.
        metric_period = config.get('metric_period', 0)
        timestamp_field = config.get('timestamp', None)
        if metric_period and timestamp_field:
            metric_field = 'metric:' + context.get_function_name()
            counter = state.incr(metric_field+':count')
            if counter % metric_period == 0:
                t = time.time() 
                event_time = getattr(record, timestamp_field) 
                state.lpush(metric_field, '{}:{}:{}'.format(counter, event_time, t)) 
        return result.encode() 
