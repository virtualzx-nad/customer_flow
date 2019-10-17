"""Pulsar function for calculating the maximum value of a series in a time window
And use this to calculate the ratio between the current value and the max.
"""
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta

from pipeline_utils import SchemaFunction



class WindowRatio(SchemaFunction):
    """a sorted list for each key is stored on redis"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = defaultdict(deque)

    def kernel(self, data, context, key_by,
               value_field='value', output_field='crowd_ratio', max_output='max_count',
               date_field='date', date_format='%Y-%m-%d %H:%M:%S', window=1000,
               metric_period=0, metric_topic='metric:window_ratio', timestamp=None):
        """Process the customer count and compute its maximum over a window
        then output the ratio between the current count and max"""
        # Retrieve the `key` and `value` of the current input
        key = data[key_by] 
        value = data[value_field] 

        # Retrieve and parse the date field to compute time windows
        if date_format:
            t_last = datetime.strptime(data[date_field], date_format)
            stamp_last = t_last.timestamp()
        else:
            stamp_last = data[date_field]
        t_start = t_last - timedelta(seconds=window)
        stamp_start = t_start.timestamp()

        # The state contains a deque of uniformly decreasing max values, with the most recent
        # value at the end.  First, pop all elements smaller than the current value
        state = self.state[key]
        while state:
            t_head, value_head = state[0]
            if value_head > value:
                break
            state.popleft()
        # Push the current value to the top of the stack
        state.appendleft((stamp_last, value))
        # Retire elements at the bottom that are no longer within the time window.  This is
        # actually not strictly necessary for the algorithm to work but does reduce the reading
        # cost and decreases the memory foot print.
        value_tail = value
        while state:
            t_tail, value_tail = state.pop()
            if t_tail > stamp_start and t_tail <= stamp_last:
                state.append((t_tail, value_tail))
                break

        # Record metrics for the function.  Default is to never record it.
        if metric_period and timestamp and self.counter % metric_period == 0:
                t = time.time() 
                event_time = data[timestamp] 
                message = '{}:{}:{}:{}'.format(self.name, self.counter, event_time, t)
                context.publish(metric_topic, message, 
                                message_conf={'event_timestamp': int(stamp_last * 1000)})
        result = {output_field: value/(value_tail + 1)}
        if max_output:
            result[max_output] = value_tail
        return result 
