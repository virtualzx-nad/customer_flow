"""Handles connection with the Redis server"""
import os
import logging
from ast import literal_eval
from random import sample
import math
import time
from datetime import datetime

import pandas as pd
import redis


logger = logging.getLogger(__name__)


class RedisConnector(object):
    """Handles connection to redis"""
    def __init__(self, host=None, port=None, db=None):
        self.connect(host, port, db)

    def connect(self, host=None, port=None, db=None):
        """Connect to redis"""
        if host is None:
            host = os.environ.get("REDIS_HOST", 'localhost')
        if port is None:
            port = os.environ.get("REDIS_PORT", 6379)
        if db is None:
            db = os.environ.get("REDIS_DB_INDEX", 1)
        self.client = redis.Redis(host, port=port, db=db, decode_responses=True)
        try:
            self.client.ping()
            self.connected = True
        except redis.exceptions.ConnectionError:
            logger.warn('Cannot connect to redis.', exc_info=True)
            self.connected = False
        self.category_refresh = time.time()
        self.categories = {}
        self.timestamp = 0

    def get_categories(self, cooldown=30):
        """Retrieve all business categories."""
        t = time.time()
        if t >  self.category_refresh and self.connected:
            self.categories = {entry.split(':')[1]: entry
                    for entry in self.client.smembers('catalog:categories')}
            self.category_refresh = t + cooldown
        return self.categories

    def get_info_near(self, longitude, latitude, radius,
                      unit='km', max_results=10000, max_shown=1000, category='geo:Restaurants'):
        """Retrieve businesses near a particular coordinate and their occupancy"""
        if not self.connected:
            return None
        t0 = time.time()
        cutoff = self.timestamp - 1e8
        nearby = self.client.georadius(category, longitude, latitude, radius,
                                 count=max_results,
                                 unit=unit, withcoord=True)
        #print('Redis returned %d entries' % len(nearby))
        if len(nearby) > max_shown:
            nearby = sample(nearby, max_shown)
        t1 = time.time()
        labels, latitudes, longitudes, ratios, sizes = [], [], [], [], []
        for data, (lon, lat) in nearby:
            business_id, name = map(literal_eval, data.split('||'))
            entry = self.client.hget('crowd_ratio', business_id)
            if entry is None:
                continue
            if '||' not in entry:
                continue
            ratio, stamp, max_count = entry.split('||')
            max_count = int(max_count)
            if max_count < 2: 
                continue
            ratio = float(ratio)
            stamp = datetime.strptime(stamp , '%Y-%m-%d %H:%M:%S').timestamp()
            if abs(self.timestamp - stamp) < 60:
                self.timestamp = max(self.timestamp, stamp)
            else:
                self.timestamp = stamp
            longitudes.append(lon)
            latitudes.append(lat)
            ratios.append(ratio)
            labels.append('{}\n{:.2f}% of {}'.format(name, ratio*100, max_count))
            sizes.append(2+math.sqrt(float(max_count)))
        t2=time.time()
        df = pd.DataFrame({'label': labels, 'latitude':latitudes, 'longitude':longitudes, 'ratio':ratios, 'size': sizes})
        t3=time.time()
        print('Redis:{:7.2f} Occ:{:7.2f} DF:{:7.2f} n={}'.format(t1-t0, t2-t1, t3-t2, len(df)))
        return df
