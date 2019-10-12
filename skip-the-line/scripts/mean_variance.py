#!/usr/bin/env python3
"""Compute mean and variance on the fly"""
import logging
import sys
from collections import defaultdict

import yaml
from redis import Redis

from pipeline_utils.time_window import process_time_window


if len(sys.argv) < 1:
    raise ArgumentError('Did not suppy settings through yaml file')
with open(sys.argv[1]) as f:
    settings = yaml.safe_load(f)

logging.basicConfig(level=settings.get('logging_level', 'INFO'))
logger = logging.getLogger(__name__)

# State tables for:  count, sum and sum of squares in the window
state = defaultdict(int), defaultdict(float), defaultdict(float)
field = settings['value_field']

# Helper worker functions
def incr(state, key, data):
    global field
    value = data[field]
    state.hincrby('count', key, 1)
    state.hincrbyfloat('sum', key, value)
    state.hincrbyfloat('sumsq', key, value * value)

def decr(state, key, data):
    global field
    value = data[field]
    state.hincrby('count', key, -1)
    state.hincrbyfloat('sum', key, -value)
    state.hincrbyfloat('sumsq', key, -value * value)

def output_mean_variance(state, key, data):
    """Returns the mean and variance for the key"""
    n = int(state.hget('count', key))
    if not n:
        return None, None
    sum_val = float(state.hget('sum', key))
    mean = sum_val / n
    sum_sq = float(state.hget('sumsq', key)) 
    variance = sum_sq - mean * mean
    return mean, variance

state = Redis(settings['state_server'], port=settings['state_port'], db=settings['state_id'])

process_time_window(state, incr, decr, output_func=output_mean_variance, **settings)
