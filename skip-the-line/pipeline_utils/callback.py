"""Callback handler for async senders"""
import pulsar


class CallbackHandler(object):
    """Handles async callbacks. Also record how many messages have been
    sent successfully and store the error messages"""
    def __init__(self):
        self.dropped = 0
        self.result = None

    def callback(self, res, msg):
        if res == pulsar.Result.Ok:
            return
        self.dropped += 1
        self.result = str(res)
