import os
import collections
import unittest
import inspect

class MISSING:
    pass

def as_context(obj):
    def lookup(attr):
        if isinstance(obj, collections.Mapping):
            return obj.get(attr, MISSING)
        return getattr(obj, attr, MISSING)
    return lookup

class Case(unittest.TestCase):

    def runTest(self):
        pass

case = Case('runTest')


class ArgumentsDict:
    '''
    OrderedDict from *args and **kwargs:
    returns values, not keys, when is iterated over.
    '''

    def __init__(self, function, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self.signature = inspect.signature(function)
        self.bound_args = self.signature.bind(*args, **kwargs).arguments


    def __dir__(self):
        return self.signature.parameters.keys()

    def __repr__(self):
        return super().__repr__() # FIXME

    def __iter__(self):
        for name, parameter in self.signature.parameters.items():
            yield self.bound_args.get(name, parameter.default)

    def __getitem__(self, name):
        value = self.bound_args.get(name, MISSING)
        if value is not MISSING:
            return value
        value = self.signature.parameters.get(name, MISSING)
        if value is not MISSING:
            return value
        return KeyError(name)
