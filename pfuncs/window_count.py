from datetime import datetime, timedelta

from pulsar import Function
from pulsar.schema import AvroSchema

from pipeline_utils import model_class_factory
from redis import Redis

class WindowCount(Function):
    """a sorted list for each key is stored on redis"""
    def process(self, input, context):
        config = context.user_config
        state = Redis(config['state_server'], port=config['state_port'], db=config['state_id'])
        RecordClass = model_class_factory(**config['schema'])
        record = RecordClass.decode(input)
        # Retrieve the `key` of the current input
        key = 'count:' + getattr(record, config['key_by'])
        date_field = config.get('date_field', 'date')
        date_format = config.get('date_format', '%Y-%m-%d %H:%M:%S')
        t_last = datetime.strptime(getattr(record, date_field), date_format)
        stamp_last = t_last.timestamp()
        stamp_start = stamp_last - config['window'] 
        state.lpush(key, stamp_last)
        while True:
            tail = state.rpop(key)
            if tail is None:
                break
            if float(tail) > stamp_start:
                state.rpush(key, tail)
                break
        ResultClass = model_class_factory(**config['output_schema'])
        result = ResultClass.clone_from(record)
        setattr(result, config['output_field'], state.llen(key))
        return result.encode() 
