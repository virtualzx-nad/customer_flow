"""Pulsar functions for establish a geospatial index in the redis server
using the coordinates specified in a topic.  Any repeated occurance of a
key will be considered an update and old records will be overwritten"""
from pipeline_utils import SchemaFunction 
from redis import Redis


class StoreGeoIndex(SchemaFunction):
    """Pulsar function for storing geospatial information to redis"""
    def kernel(self, data, context, key_fields,
               latitude_field='latitude', longitude_field='longitude',
               group_by='__all__', group_catalog=None,
               redis_server='10.0.0.24', redis_port=6379, redis_id=1):
        """Create geospatial index in Redis from messages of an input topic

        Args:
            data:       Input message in a dict
            context:    Pulsar Functions context object
            key_fields: Which fields to flatten and save to the key field in Redis
            latitude_field:  Which field contains the latitude data
            longitude_field: Which field contains the longitude data
            group_by:   When specified, multiple geospatial index tables will be
                        created in Redis based on values in this field.  Note that
                        if this field is an Array, the message will be registered in
                        each elements."""
        lat = data[latitude_field]
        lon = data[longitude_field]
        if not isinstance(key_fields, (tuple, list)):
            key_fields = [key_fields]
        keys = [data[key_field] for key_field in key_fields]
        decoded = [repr(key.decode()) if isinstance(key, bytes) else repr(key) for key in keys]
        # Determine which groups this entry belongs to
        if group_by == '__all__':
            groups = ['geo:__all__']
        else:
            group_names = data[group_by] 
            if group_names is None:
                group_names = ['__unknown__']
            elif isinstance(group_names, str):
                group_names = [group_names]
            groups = ['geo:' + name for name in group_names] 

        # Connect to redis server
        redis = Redis(redis_server, port=redis_port, db=redis_id)

        # If `group_catalog` option is specified, store the catalog of all existing categories
        # in this field on redis 
        if group_catalog:
            redis.sadd(group_catalog, *groups)

        # Update the entry location for each groups that it belongs to.
        for group in groups:
            redis.geoadd(group, lon, lat, '||'.join(decoded))
