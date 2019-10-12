"""Slightly enriched Pulsar Functions that handles serialization and deserialization
based on schema provided in user config.  Also allow the user to directly write
a kernel using the user configurations and give them defaults more easily."""
import uuid
from abc import abstractmethod

from pulsar import Function

from .schema_model import model_class_factory


class SchemaFunction(Function):
    """Instead of overriding `process`, override `kernel` instead.  Inside kernel()
    the input is received as a dictionary with each field in a key/value pair

    The output is also a dictionary specifying which fields will be modified.
    Any field not in output will be cloned from input object

    Also provide an evaluation `counter` and a unique `name` for each instance.
    """
    def __init__(self, *args, **kwargs):
        """Initialize the counter and create the name field"""
        super().__init__(*args, **kwargs)
        self.counter = 0
        self.name = uuid.uuid4()

    def process(self, input, context):
        """Process the customer count and compute its maximum over a window
        then output the ratio between the current count and max

        If the input schema is missing, the message data will be directly
        passed into the kernel function.
        If the output schema is missing, the results will be returned to
        Pulsar without additional treatment.
        """
        config = dict(context.user_config)
        schema = config.pop('schema', None)
        output_schema = config.pop('output_schema', None)
        if schema:
            # Parse input message Schema
            RecordClass = model_class_factory(**schema)
            record = RecordClass.decode(input)
        else:
            raise ValueError('Schema not found in user config')

        result = self.kernel(record.__dict__, context, **config)
        self.counter += 1
        if not result:
            return

        # Output does not have a schema
        if not output_schema:
            return result

        # Encode the output message based on the proper schema and send it out
        ResultClass = model_class_factory(**output_schema)
        output = ResultClass.clone_from(record)
        for key, value in result.items():
            setattr(output, key, value)
        return output.encode()


    @abstractmethod
    def kernel(self, input, context, **config):
        """Process input message"""
        pass
