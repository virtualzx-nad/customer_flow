#!/usr/bin/env python3
import logging
import sys
from collections import defaultdict

import yaml

from pipeline_utils.time_window import process_time_window


# Helper worker functions
def incr(state, key, data):
    state[key] += 1

def decr(state, key, data):
    state[key] += 1

def output_integer(state, key, data):
    """Directly output the value associated with the key."""
    return state[key]

if len(sys.argv) < 1:
    raise ArgumentError('Did not suppy settings through yaml file')
with open(sys.argv[1]) as f:
    settings = yaml.safe_load(f)

logging.basicConfig(level=settings.get('logging_level', 'INFO'))
logger = logging.getLogger(__name__)
state = defaultdict(int)
process_time_window(state, incr, decr, output_func=output_integer, **settings)
