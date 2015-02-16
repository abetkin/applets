from g_context.base import getcontext, green_function, green_method, ContextAttr
from declared import Mark, SkipMark

from rest_framework.serializers import Field, Serializer, \
    ModelSerializer
from rest_framework import serializers

def serializer_class(baseclass):

    class ListSerializer(serializers.ListSerializer):
        _context = ContextDict('request')

    class Serializer(baseclass):
        _context = ContextDict('request')

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._declared_fields = getcontext()['_declared_fields']

        class Meta:
            list_serializer_class = ListSerializer

    return Serializer


@green_function
def deserialize(data=None, klass=Serializer):
    # TODO
    if data is None:
        data = getcontext()['request'].QUERY_PARAMS
    new_class = serializer_class(klass)
    s = new_class(data=data)
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
        pass
    return property(fget, fset)


@green_function
def serialize(obj=None, klass=Serializer, **kwargs):
    if obj is None:
        obj = getcontext()['object']
    new_class = serializer_class(klass)
    s = new_class(obj, **kwargs)
    return s.data

# add later obj to context ?

class field(Mark):

    collect_into = '_declared_fields'

    def build_me(field, fields, owner):
        if isinstance(field, Field) and fields_separator in fields:
            sep = fields.index(fields_separator)
            read_only = fields.index(field) < sep
            field.read_only = read_only
            field.write_only = not read_only
        return field


field.register(Field)

class FieldsSeparator(field):
    '''
    Separator between the read-only and write-only fields.
    '''
    def build_me(field, fields, owner):
        raise SkipMark

fields_separator = FieldsSeparator()
