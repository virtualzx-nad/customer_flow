"""Pulsar functions for establish a geospatial index in the redis server
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
        key_fields = config.get('key_field', '__raw__')
        if not isinstance(key_fields, (tuple, list)):
            key_fields = [key_fields]
        keys = [getattr(record, key_field) for key_field in key_fields]
        decoded = [repr(key.decode()) if isinstance(key, bytes) else repr(key) for key in keys]
        group_field = config.get('group_by', '__all__')
        if group_field == '__all__':
            groups = ['geo:__all__']
        else:
            group_names = getattr(record, group_field)
            if group_names is None:
                group_names = ['__unknown__']
            elif isinstance(group_names, str):
                group_names = [group_names]
            groups = ['geo:' + name for name in group_names] 

        redis = Redis(config['redis_server'], port=config['redis_port'], db=config['redis_id'])

        # If `group_catalog` option is specified, store the catalog of all existing categories
        # in this field on redis 
        catalog = config.get('group_catalog', None)
        if catalog:
            redis.sadd(catalog, *groups)

        # Update the entry location for each groups that it belongs to.
        for group in groups:
            redis.geoadd(group, lon, lat, '||'.join(decoded))
