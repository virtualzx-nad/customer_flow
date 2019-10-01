"""Pulsar function for calculating the maximum value of a series in a time window"""
from datetime import datetime, timedelta

from pulsar import Function
from pulsar.schema import AvroSchema

from pipeline_utils import model_class_factory
from redis import Redis



class WindowMax(Function):
    """a sorted list for each key is stored on redis"""
    def process(self, input, context):
        config = context.user_config
        state = Redis(config['state_server'], port=config['state_port'], db=config['state_id'])
        RecordClass = model_class_factory(**config['schema'])
        record = RecordClass.decode(input)
        # Retrieve the `key` of the current input
        key = 'max:' + getattr(record, config['key_by'])
        value = getattr(record, config['value_field'])
        date_field = config.get('date_field', 'date')
        date_format = config.get('date_format', '%Y-%m-%d %H:%M:%S')
        t_last = datetime.strptime(getattr(record, date_field), date_format)
        t_start = t_last - timedelta(seconds=config['window'])
        stamp_last = t_last.timestamp()
        stamp_start = t_start.timestamp()
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
        state.lpush(key, "{}:{}".format(stamp_last, value))
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
        ResultClass = model_class_factory(**config['output_schema'])
        result = ResultClass.clone_from(record)
        setattr(result, config['output_field'], type(value)(value_tail))
        return result.encode() 
