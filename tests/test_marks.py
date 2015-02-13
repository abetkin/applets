
from collections import OrderedDict

from declared import Mark as mark, DeclaredMeta
from green_context.util import case

class custom(mark):

    def __new__(cls, f):
        if callable(f):
            f = f()
        return int(f)

custom.register(int)

class MarkedApp(metaclass=DeclaredMeta):

    mark1 = mark2 = custom(1)

    @custom
    def mark3():
        return 2


case.assertSequenceEqual(
    MarkedApp._declared_marks,
    OrderedDict([('mark1', 1), ('mark2', 1), ('mark3', 2)]))
