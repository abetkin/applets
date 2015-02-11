
from collections import OrderedDict

from applets.marks import Mark as mark, CollectMarksMeta
from applets.util import case

class custom(mark):

    collect_into = 'numbers'

    def build(self):
        if self.source_function:
            return int(self.source_function())
        return int(self.value)


class MarkedApp(metaclass=CollectMarksMeta):

    mark1 = mark2 = custom(value=1)

    @custom()
    def mark3():
        return 2

case.assertSequenceEqual(
    MarkedApp._collected['numbers'],
    OrderedDict([('mark1', 1), ('mark2', 1), ('mark3', 2)]))
