from g_context.base import getcontext, green_function, green_method, ContextAttr
from declared import Mark, SkipMark

from rest_framework.serializers import Field, Serializer, \
    ModelSerializer
from rest_framework import serializers

@green_function
def deserialize(data=None, klass=Serializer):
    if data is None:
        data = getcontext()['request']['QUERY_PARAMS']
    s = klass()
    s._declared_fields = s._declared_fields or getcontext()['_declared_fields']
    if s.is_valid():
        return s.data
    raise Exception(s.errors)

def ContextDict(*keys):
    dic = {}

    def fget(self, ):
        if not dic:
            for key in keys:
                dic[key] = getcontext()[key]
        return dic

    def fset(self, value):
        'do nothing'
    return property(fget, fset)

class ListSerializer(serializers.ListSerializer):
    _context = ContextDict('request')

@green_function
def serialize(obj=None, klass=Serializer, **kwargs):
    if obj is None:
        obj = getcontext()['object']

    class new_class(klass):
        _context = ContextDict('request')

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._declared_fields = getcontext()['_declared_fields']

        class Meta:
            list_serializer_class = ListSerializer
    s = new_class(obj, **kwargs)
    return s.data

# add later obj to context ?

class field(Mark):

    def build_me(field, fields):
        if isinstance(field, Field) and fields_separator in fields:
            sep = fields.index(fields_separator)
            if fields.index(field) < sep:
                field.read_only = True
            else:
                field.write_only = True
        return field

class FieldsSeparator(field):
    '''
    Separator between the read-only and write-only fields.
    '''
    def build_me(field, fields):
        raise SkipMark

fields_separator = FieldsSeparator()
