from collections import OrderedDict
from declared import Mark, DeclaredMeta
from green_context.base import green_method, green_function, ContextAttr


from functools import reduce
from qfilters import QFilter, QuerySetFilter

from django.db.models.query import Q

class FilterMark(Mark):

    collect_into = '_declared_filters'

    def build_me(self, marks):
        if isinstance(self, Q):
            return QFilter(self)
        return self


qobj = QFilter
qsfilter = QuerySetFilter

FilterMark.register(qobj)
FilterMark.register(Q)
FilterMark.register(qsfilter)


class apply(FilterMark):
    def __init__(self, operation):
        self.op = operation


class Filter:

    _filters = ContextAttr('_declared_filters')
    queryset = ContextAttr('queryset')

    def __init__(self, queryset=None):
        if queryset is not None:
            self.queryset = queryset

    @green_method
    def filter(self):
        accumulated = []
        for name, obj in self._filters.items():
            if isinstance(obj, apply):
                self._filters[name] = reduce(obj.op, accumulated)
                while accumulated:
                    accumulated.pop().skip = True
            else:
                accumulated.append(obj)
        self.results = OrderedDict()
        queryset = self.queryset
        for name, obj in self._filters.items():
            if not getattr(obj, 'skip', None):
                self.results[name] = queryset = obj(queryset)
        return queryset
