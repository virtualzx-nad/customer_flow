#!/usr/bin/env python3
"""Compute mean and variance on the fly"""
import logging
import sys
from collections import defaultdict

import yaml

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
    state[0][key] += 1
    state[1][key] += value
    state[2][key] += value * value

def decr(state, key, data):
    global field
    value = data[field]
    state[0][key] -= 1
    state[1][key] -= value
    state[2][key] -= value * value

def output_mean_variance(state, key, data):
    """Returns the mean and variance for the key"""
    n = state[0][key]
    if not n:
        return None, None
    sum_val = state[1][key]
    mean = sum_val / n
    sum_sq = state[2][key]
    variance = sum_sq - mean * mean
    return mean, variance


process_time_window(state, incr, decr, output_func=output_mean_variance, **settings)
