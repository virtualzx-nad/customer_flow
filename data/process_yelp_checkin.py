"""A processor for Yelp checkin data.
The data is ordered by business instead of time, and within each
business all check in times are aggregated to one string.  This
needs to be preprocessed and sorted by time to simulate stream data.
"""
import logging
import sys
import time
import datetime

import smart_open
from redis import Redis
import yaml

# If Yaml setting file is not supplied
if len(sys.argv) < 1:
    raise ArgumentError('Did not suppy settings through yaml file')
with open(sys.argv[1]) as f:
    settings = yaml.safe_load(f)
logging.basicConfig(level=settings.pop('logging_level', 'INFO'))
logger = logging.getLogger(__name__)

cache = Redis(settings['caching_server'])
t0 = time.time()
data = None
i = 0
max_records = settings['max_records']
for i, line in enumerate(smart_open.open(settings['s3object'])):
    if i == max_records:
        break
    data = yaml.safe_load(line)
    business_id = data['business_id']
    # Granuarity of timestamp data is only down to seconds. Here we
    # Add a small appendix according to the hash of business ID to add a jitter
    # that is evenly distributed between integer seconds.
    appendix = hash(business_id) % 1000000 * 0.000001
    dates = data['date'].split(', ')
    record = {}
    for date_time_str in dates:
        t = datetime.datetime.strptime(date_time_str, '%Y-%m-%d %H:%M:%S').timestamp()
        t += appendix
        record["{'date': '%s', 'business_id': '%s'}" % (date_time_str, business_id)] = t
    cache.zadd('timestamp', record)
n = cache.zcard('timestamp')
logger.info('Processed %d check-in data in %d businesses', n, i)
logger.info("Processing speed: %.2f entries/s", n / (time.time()-t0))

filename = settings['output']
logger.info('Saving records to %s', filename)
pointer = 0
block_size = settings['block_size']
with open(filename, 'w+') as f:
    for start in range(0, n, block_size):
        end = min(n, start + block_size)
        segment = cache.zrange('timestamp', start, end-1)
        logger.debug('Saving segment %d to %d (len=%d)', start, end, len(segment))
        for record in segment:
            f.write('{:s}\n'.format(record.decode()))


