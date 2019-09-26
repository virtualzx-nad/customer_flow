from pulsar import schema


type_map = {
    'Boolean': schema.Boolean,
    'Integer': schema.Integer,
    'Long': schema.Long,
    'Float': schema.Float,
    'Double': schema.Double,
    'Bytes': schema.Bytes,
    'String': schema.String,
    'Array': schema.Array,
    'Map': schema.Map
}
def model_class_factory(**definition):
    """Given a schema definition, returns the model class of that schema

    Args:
        keyword arguments:  Schema definition. Keys are
            field names and values are the type of the field

    Returns:
        RecordModel: A class definition that conforms to the schema, with
            method `from_dict` that converts 
    For example, the schema definition may be
        {name: String,  dob: String, grades: [Array, Float]}

    It will result in a class definition of

        class RecordModel(Record):
            name = String()
            dob = String()
            grads = Array(Float())

    All Pulsar supported schema types are supported:
        Boolean, Integer, Long, Float, Double, Bytes, String, Array, Map

    If a list is supplied, the field is a compounded field. Note that the last
    elements in a list cannot be Array or Map, and the other elements must be
    an Array or Map, because these are the only collection types.

    e.g. [Array, Map, Integer] is an array of dictionaries with integer values.

    It does not support Enum or subRecord classes at the moment.
    """
    class RecordModel(schema.Record):
        env = locals()
        key = value = None
        for key, value in definition.items():
            if isinstance(value, (list, tuple)):
                value = list(reversed(value))
                env[key] = type_map[value[0]]()
                for v in value[1:]:
                    env[key] = type_map[v](env[key])
            else:
                env[key] = type_map[value]()
        del env, key, value

        @classmethod
        def from_dict(cls, kwargs):
            filtered = {key: value for key, value in kwargs.items() if key in cls.__dict__}
            return cls(**filtered)

        @classmethod
        def decode(cls, raw):
            """Decode a row binary string to an RecordModel object"""
            return schema.AvroSchema(cls).decode(raw.encode('utf-8'))

    return RecordModel

