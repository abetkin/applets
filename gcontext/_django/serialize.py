from gcontext import get_context, function, method, ContextAttr
from declared import Mark, SkipMark

from rest_framework.serializers import Field, Serializer, \
    ModelSerializer
from rest_framework import serializers

_context = property(lambda self: get_context(), lambda self, value: None)

def serializer_class(baseclass):

    class ListSerializer(serializers.ListSerializer):
        _context = _context

    class Serializer(baseclass):
        _context = _context

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self._declared_fields = get_context()['_declared_fields']

        class Meta:
            list_serializer_class = ListSerializer

    return Serializer


@function
def deserialize(data=None, klass=Serializer):
    # TODO
    if data is None:
        data = get_context()['request'].QUERY_PARAMS
    new_class = serializer_class(klass)
    s = new_class(data=data)
    if s.is_valid():
        return s.data
    raise Exception(s.errors)


@function
def serialize(obj=None, klass=Serializer, **kwargs):
    if obj is None:
        obj = get_context()['object']
    new_class = serializer_class(klass)
    s = new_class(obj, **kwargs)
    return s.data

# add later obj to context ?

class field(Mark):

    collect_into = '_declared_fields'

    @classmethod
    def __subclasshook__(cls, C):
        if issubclass(C, serializers.Field):
            return True
        return NotImplemented

    def build(field, fields, owner):
        if isinstance(field, Field) and fields_separator in fields:
            sep = fields.index(fields_separator)
            read_only = fields.index(field) < sep
            field.read_only = read_only
            field.write_only = not read_only
        return field


# field.register(Field)

class FieldsSeparator(field):
    '''
    Separator between the read-only and write-only fields.
    '''
    def build(field, fields, owner):
        raise SkipMark

fields_separator = FieldsSeparator()
