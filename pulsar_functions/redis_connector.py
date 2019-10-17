"""A Pulsar connector to Redis"""
import time
from datetime import datetime, timedelta

from redis import Redis

from pipeline_utils import SchemaFunction


class RedisConnector(SchemaFunction):
    """a sorted list for each key is stored on redis"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis = None
        self.redis_port = None
        self.redis_host = None
        self.redis_db = None

    def kernel(self, data, context, key_by, value_field, prefix='', group_by=None,
               host='10.0.0.24', port=6379, db=1):
        """Persist data to Redis

        Args:
            data:       dict containing input message data
            context:    Pulsar Context object
            key_by:     The data in this field will be used to determine the key
            value_field:    The data in this field will be stored to Redis
            group_by:   If specified, the results will be saved in a hash instead
                        of as top level key/value pairs in Redis. The value in
                        this field determines the name of the hash
            prefix:     If specified, the hash name will be prefixed by this string
            host:       Redis service URL
            port:       Port for the Redis server
            db:         Redis database index"""
        # Create redis connection
        if self.redis is None or (host, port, db) != (self.redis_host, self.redis_port, self.redis_db):
            self.redis = Redis(host, port=port, db=db)
            self.redis_host = host
            self.redis_port = port
            self.redis_db = db
        redis = self.redis

        # Retrieve the `key` and `value` of the current input
        key = data[key_by] 
        if isinstance(value_field, (list, tuple)):
            value = '||'.join([str(data[field]) for field in value_field])
        else:
            value = data[value_field] 

        # Identify group names and store them to redis
        if group_by:
            if isinstance(str, group_by):
                redis.hset(prefix + data[group_by], key, value)
            else:
                for group in data[group_by]:
                    redis.hset(prefix + group, key, value)
        elif prefix:
            redis.hset(prefix, key, value)
        else:
            redis.set(key, value)

