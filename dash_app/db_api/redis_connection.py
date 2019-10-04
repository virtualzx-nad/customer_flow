"""Handles connection with the Redis server"""
import os
from ast import literal_eval
from random import sample
import math
import time

import pandas as pd
from redis import Redis


HOST = os.environ.get("REDIS_HOST", 'localhost')
PORT = os.environ.get("REDIS_PORT", 'localhost')
DB_INDEX = os.environ.get("REDIS_DB_INDEX", 'localhost')

redis = Redis(HOST, port=PORT, db=DB_INDEX)

def get_categories():
    return {entry.decode().split(':')[1]: entry.decode()
            for entry in redis.smembers('catalog:categories')}

def get_info_near(longitude, latitude, radius, unit='km', max_results=10000, max_shown=1000, category='geo:Restaurants'):
    """Retrieve businesses near a particular coordinate and their occupancy"""
    t0 = time.time()
    nearby = redis.georadius(category, longitude, latitude, radius,
                             count=max_results,
                             unit=unit, withcoord=True)
    #print('Redis returned %d entries' % len(nearby))
    if len(nearby) > max_shown:
        nearby = sample(nearby, max_shown)
    t1 = time.time()
    labels, latitudes, longitudes, ratios = [], [], [], []
    for data, (lon, lat) in nearby:
        business_id, name = map(literal_eval, data.decode().split('||'))
        ratio = redis.hget('crowd_ratio', business_id)
        if ratio is None:
            continue
        ratio = float(ratio)
        longitudes.append(lon)
        latitudes.append(lat)
        ratios.append(ratio)
        labels.append('{}\ncrowd: {}'.format(name, ratio))
    t2=time.time()
    df = pd.DataFrame({'label': labels, 'latitude':latitudes, 'longitude':longitudes, 'ratio':ratios})
    t3=time.time()
    print('Redis:{:7.2f} Occ:{:7.2f} DF:{:7.2f} n={}'.format(t1-t0, t2-t1, t3-t2, len(df)))
    return df
