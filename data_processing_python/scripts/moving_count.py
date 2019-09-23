import logging
import sys

import yaml

from pipeline_utils.time_window import process_time_window, incr, decr, output_integer

# Helper worker functions
def incr(state, key, data):
    state.incr(key)

def decr(state, key, data):
    state.decr(key)

def output_integer(state, key, data):
    """Directly output the value associated with the key."""
    return int(state[key])

if len(sys.argv) < 1:
    raise ArgumentError('Did not suppy settings through yaml file')
with open(sys.argv[1]) as f:
    settings = yaml.safe_load(f)

logging.basicConfig(level=settings.get('logging_level', 'INFO'))
logger = logging.getLogger(__name__)
process_time_window(incr, decr, incr, output_func=output_integer, **settings)