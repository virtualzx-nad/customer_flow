import os

from redis import Redis


HOST = os.environ.get("REDIS_HOST", 'localhost')


redis = Redis(HOST, db=3)



def get_latency():
    return float(redis.get('metric:latency'))


def get_processing_rate():
    return float(redis.get('metric:processing_rate')) / 1000


def get_info_near(longitude, latitude, radius, unit='km'):
    nearby = redis.georadius('geo:__all__', longitude, latitude, radius,
                             unit=unit, withcoord=True)
    ids, latitudes, longitudes = [], [], []
    for business_id, (lon, lat) in nearby:
        ids.append(business_id.decode())
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
