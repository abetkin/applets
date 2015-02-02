import collections
import unittest

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
