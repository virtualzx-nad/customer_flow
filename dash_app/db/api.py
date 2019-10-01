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


def get_latency():
    latency = redis.get('metric:latency')
    if latency is None:
        return
    return float(latency)


def get_processing_rate():
    rate= redis.get('metric:processing_rate')
    if rate is None:
        return
    return float(rate) / 1000


def get_categories():
    return {entry.decode().split(':')[1]: entry.decode()
            for entry in redis.smembers('catalog:categories')}

def get_occupancy(business_id):
    """Compute the occupancy of a business id"""
    max_occ = redis.lindex('max:'+business_id, -1)
    if max_occ is None:
        return 0, 1
    if isinstance(max_occ, bytes):
        max_occ = max_occ.decode()
    max_occ = int(max_occ.split(':')[1])
    occ = redis.llen('count:'+business_id)
    return occ, max_occ

def get_info_near(longitude, latitude, radius, unit='km', max_results=10000, max_shown=10000, category='geo:Restaurants'):
    """Retrieve businesses near a particular coordinate and their occupancy"""
    t0 = time.time()
    nearby = redis.georadius(category, longitude, latitude, radius,
                             count=max_results,
                             unit=unit, withcoord=True)
    #print('Redis returned %d entries' % len(nearby))
    if len(nearby) > max_shown:
        nearby = sample(nearby, max_shown)
    t1 = time.time()
    labels, latitudes, longitudes, ratio, sizes = [], [], [], [], []
    for data, (lon, lat) in nearby:
        business_id, name = map(literal_eval, data.decode().split('||'))
        occ, max_occ = get_occupancy(business_id)
        if not occ:
            continue
        longitudes.append(lon)
        latitudes.append(lat)
        ratio.append(occ/max_occ)
        sizes.append(math.sqrt(max_occ) * 2)
        labels.append('{}\n{}/{}'.format(name, occ, max_occ))
    t2=time.time()
    df = pd.DataFrame({'label': labels, 'latitude':latitudes, 'longitude':longitudes, 'ratio':ratio, 'size':sizes})
    t3=time.time()
    print('Redis:{:7.2f} Occ:{:7.2f} DF:{:7.2f} n={}'.format(t1-t0, t2-t1, t3-t2, len(df)))
    return df
