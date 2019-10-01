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

ALL_POINTS = redis.georadius('geo:Restaurants',-77.946, 43.126, 1000,
                             unit='mi', withcoord=True)
ACTIVE = set([])
PARTITIONS = 60


def initialize():
    print('Total number of establishments: ', len(ALL_POINTS))
    for i in range(PARTITIONS):
        refresh_active(i)
    print('Done initializing')

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


def refresh_active(n_intervals):
    t0 = time.time()
    partition = n_intervals % PARTITIONS
    for i in range(partition, len(ALL_POINTS),PARTITIONS):
        label, (lon, lat) = ALL_POINTS[i]
        business_id, name = map(literal_eval, label.decode().split('||'))
        max_occ = redis.lindex('max:'+business_id, -1)
        if max_occ is None:
            continue
        if isinstance(max_occ, bytes):
            max_occ = max_occ.decode()
        max_occ = int(max_occ.split(':')[1])
        if max_occ > 1:
            ACTIVE.add(i)
    # print("Active establishments: ", len(ACTIVE), ' t=', time.time()-t0)
 

def get_info_active():
    t0=time.time()
    labels, latitudes, longitudes, ratio, sizes = [], [], [], [], []
    for i in list(ACTIVE):
        data, (lon, lat) = ALL_POINTS[i]
        business_id, name = map(literal_eval, data.decode().split('||'))
        occ, max_occ = get_occupancy(business_id)
        longitudes.append(lon)
        latitudes.append(lat)
        ratio.append(occ/max_occ)
        sizes.append(math.sqrt(max_occ) * 2)
        labels.append('{}\n{}/{}'.format(name, occ, max_occ))
    t1=time.time()
    df = pd.DataFrame({'label': labels, 'latitude':latitudes, 'longitude':longitudes, 'ratio':ratio, 'size':sizes})
    t2=time.time()
    # print('ACTIVE Occ:{:7.2f} DF:{:7.2f} n={}'.format(t1-t0, t2-t1, len(df)))
    return df
    
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
        if not occ or max_occ == 1:
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
