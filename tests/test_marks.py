
from collections import OrderedDict

from declared import Mark as mark, DeclaredMeta
from green_context.util import case

class custom(mark):

    collect_into = '_declared_numbers'

    def build(self):
        if self.source_function:
            return int(self.source_function())
        return int(self.value)


class MarkedApp(metaclass=DeclaredMeta):

    mark1 = mark2 = custom(value=1)

    @custom()
    def mark3():
        return 2

case.assertSequenceEqual(
    MarkedApp._declared_numbers,
    OrderedDict([('mark1', 1), ('mark2', 1), ('mark3', 2)]))
