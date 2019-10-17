from pulsar import Function
from pulsar.schema import AvroSchema

from pipeline_utils import get_record


class HashStream(Function):
    def process(self, input, context):
        config = context.user_config
        RecordClass = model_class_factory(**config['schema'])
        record = RecordClass.decode(input) 
        key_by = config['key_by']
        partitions = config['partitions']
        shift = config['shift']
        format_str = config['topic_format']
        key = getattr(record, key_by)
        index = hash(key) % partitions
        out_topic = format_str.format(index + shift)
        context.publish(out_topic, input)
        return
