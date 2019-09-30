"""Pulsar functions for establish a geospatial index in the state server
using the coordinates specified in a topic.  Any repeated occurance of a
key will be considered an update and old records will be overwritten"""
from pulsar import Function
from pulsar.schema import AvroSchema

from pipeline_utils import model_class_factory
from redis import Redis


class StoreGeoIndex(Function):
    """Pulsar function for storing geospatial information to redis"""
    def process(self, input, context):
        config = context.user_config
        RecordClass = model_class_factory(**config['schema'])
        record = RecordClass.decode(input) 
        lat = getattr(record, config.get('latitude_field', 'latitude'))
        lon = getattr(record, config.get('longitude_field', 'longitude'))
        key = getattr(record, config['key_field'])
        group_field = config.get('group_by', '__all__')
        if group_field == '__all__':
            group = 'geo:__all__' 
        else:
            group = 'geo:' + getattr(record, group_field) 

        state = Redis(config['state_server'], port=config['state_port'], db=config['state_id'])
        result = state.geoadd(group, lon, lat, key)
        if result != 1:
            return 'State server returned ' + str(result)
