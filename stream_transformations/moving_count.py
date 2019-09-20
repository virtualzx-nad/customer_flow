import logging
import sys

import yaml

from time_window import process_time_window, incr, decr, output_integer

if len(sys.argv) < 1:
    raise ArgumentError('Did not suppy settings through yaml file')
with open(sys.argv[1]) as f:
    settings = yaml.safe_load(f)

logging.basicConfig(level=settings.get('logging_level', 'INFO'))
logger = logging.getLogger(__name__)
process_time_window(incr, decr, incr, output_func=output_integer, **settings)