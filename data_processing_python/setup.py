#!/usr/bin/env python
"""
Install uitilities in Xiaolei Zhu's Insight DE project. 
"""
from setuptools import setup

__title__ = "pipeline_utils"
__version__ = "0.0.1"
__status__ = "Prototype"


setup(name="pipeline_utils",
      version=__version__,
      description="A very simple yet flexible stream processing model that is free of complex frameworks",
      packages=["pipeline_utils"],
      scripts=["scripts/hash_stream.py", 'scripts/s3_producer.py', 'scripts/moving_count.py', 'scripts/transform_schema.py'],
      # test_suite="pipeline_utils",
      long_description="""This is still very much a work in progress.""",
      install_requires=['pyyaml', 'pulsar-client>=2.4.0', 'redis>=3.0.0', 'smart-open>=1.7.0']
      )


