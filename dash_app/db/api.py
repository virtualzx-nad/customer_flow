import os

from redis import Redis


HOST = os.environ.get("REDIS_HOST", 'localhost')


redis = Redis(HOST)



def get_latency():
    return float(redis.get('latency'))


def get_processing_rate():
    return float(redis.get('processing_rate')) / 1000