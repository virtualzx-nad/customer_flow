from pulsar import Function
from pulsar.schema import AvroSchema

from pipeline_utils import model_class_factory
from redis import Redis

class WindowCount(Function):
    """a sorted list for each key is stored on redis
    """
    def __init__(self):
    def process(self, input, context):
        config = context.user_config
        state = Redis(config['state_server'], port=config['state_port'], db=config['state_id'])
        key_by = config['key_by'] 
        RecordClass = model_class_factory(**config['schema'])
        record = RecordClass.decode(input) 
