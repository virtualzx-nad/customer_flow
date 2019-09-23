import logging
import sys

import yaml
from redis import Redis

from pipeline_utils.global_window import process_global_window


if len(sys.argv) < 1:
    raise ArgumentError('Did not suppy settings through yaml file')
with open(sys.argv[1]) as f:
    settings = yaml.safe_load(f)

name = settings['name']
group_by = settings['group_by']
rank_by = settings['rank_by']
reverse = settings['reverse']

def update_ranking(state, key, data):
    """use Ordered Sets from Redis to do the ranking"""
    if group_by is None:
        group = name
    else:
        group = data[group_by]
    state.zadd(group, {key: data[rank_by]})

def output_ranking(state, key, data):
    if group_by is None:
        group = name
    else:
        group = data[group_by]
    if reverse:
        return int(state.zrevrank(group, key)) + 1
    else:
        return int(state.zrank(group, key)) + 1

logging.basicConfig(level=settings.get('logging_level', 'INFO'))
logger = logging.getLogger(__name__)
state = Redis(settings['state_server'], db=settings['state_id'])
process_global_window(state, update_ranking, output_func=output_ranking, **settings)