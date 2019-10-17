"""Count the number of events in a time window"""
from collections import defaultdict, deque
from datetime import datetime, timedelta

from pipeline_utils import SchemaFunction


class WindowCount(SchemaFunction):
    """a sorted list for each key is stored on redis"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.state = defaultdict(deque)

    def kernel(self, record, context, key_by,
               date_field='date', date_format='%Y-%m-%d %H:%M:%S',
               window=1000, output_field='count'):
        """Count the number of instances inside of a time window from
        the current event

        Args:
            record:   A dictionary containing the input message fields
            context:  The Pulsar Functions context object
            key_by:   The name of the key field, by which items will be counted
            date_field:  Which field to parse for date information
            date_format: If specified, the format string used to parse the date
                      info. If this is None, the date field should contain a
                      numericl timestamp
            window:   Window length in seconds
            output_field:  Which field the output will be saved to

        Returns:
            The event count in the specified window will be returned in the key
            specified by output_field
            """
        # Retrieve the `key` of the current input
        key = record[key_by] 
        # Retrieve the real time stamp
        if date_format is None:
            stamp_last = record[date_field]
        else:
            t_last = datetime.strptime(record[date_field], date_format)
            stamp_last = t_last.timestamp()
        stamp_start = stamp_last - window 
        # Update the list of timestamps falling inside of the window
        state = self.state[key]
        state.appendleft(stamp_last)
        while state:
            tail = state.pop()
            if tail > stamp_start and tail <= stamp_last:
                state.append(tail)
                break
        return {output_field: len(state)}
