
from collections import ChainMap

import operator as op
from functools import reduce

class Context(ChainMap):

    def __missing__(self):
        # use anonymous instances
        raise NotImplementedError


class GrabbedContext(dict):

    def __init__(self, *args, _grabber_=None, **kwargs):
        self._grabber_ = _grabber_
        super().__init__(*args, **kwargs)

    def __hash__(self, ):
        ret = reduce(op.add, [hash(k) for k in self])
        ret += hash(self._identity_)
        return ret


class Literal(str):

    def __getattr__(self, attr):
        if not self:
            value = attr
        else:
            value = '.'.join((self, attr))
        return self.__class__(value)

literal = Literal()