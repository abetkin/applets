from g_context.base import getcontext

def deserialize(data=None, Serializer=1):
    data = data or getcontext()['request']['QUERY_PARAMS']
    s = Serializer()
    s._declared_fields = s._declared_fields or getcontext()['_declared_fields']
    if s.is_valid():
        return s.data
    raise Exception(s.errors)

def serialize(obj, Serializer):
    obj = obj or getcontext()['object']
    s = Serializer(obj)
    return s.data
