import os
from ast import literal_eval
from random import sample


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


def get_info_near(longitude, latitude, radius, unit='km', max_results=10000, random=False, category='geo:Restaurants'):
    if random:
        nearby = redis.georadius(category, longitude, latitude, radius,
                                 unit=unit, withcoord=True)
    else:
        nearby = redis.georadius(category, longitude, latitude, radius,
                                 unit=unit, withcoord=True, sort='ASC')

    if len(nearby) > max_results:
        if random:
            nearby = sample(nearby, max_results)
        else:
            nearby = nearby[:max_results]

    ids, latitudes, longitudes = [], [], []
    for data, (lon, lat) in nearby:
        business_id, name = map(literal_eval, data.decode().split('||'))
        ids.append(name)
        longitudes.append(lon)
        latitudes.append(lat)

    return dict(
            type="scattermapbox",
            lon=longitudes,
            lat=latitudes,
            text=ids,
            name='nearby_business',
            marker=dict(size=3, opacity=0.6)
        )
