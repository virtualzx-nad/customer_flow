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

def get_info_near(longitude, latitude, radius, unit='km', max_results=10000, random=False, category='geo:Restaurants'):
    """Retrieve businesses near a particular coordinate and their occupancy"""
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

    ids, latitudes, longitudes, ratio, max_occupancy = [], [], [], [], []
    for data, (lon, lat) in nearby:
        business_id, name = map(literal_eval, data.decode().split('||'))
        longitudes.append(lon)
        latitudes.append(lat)
        occ, max_occ = get_occupancy(business_id)
        ratio.append(occ/max_occ)
        max_occupancy.append(max_occ + 2)
        ids.append('{}\n{}/{}'.format(name, occ, max_occ))

    return dict(
            type="scattermapbox",
            lon=longitudes,
            lat=latitudes,
            text=ids,
            name='nearby_business',
            marker=dict(size=max_occupancy, color=ratio, colorscale='Jet',
                        showscale=True, cmax=1.0, cmin=0.0)
        )
