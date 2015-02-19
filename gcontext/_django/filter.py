from collections import OrderedDict
from declared import Mark, DeclaredMeta
from gcontext import method, function, ContextAttr


from functools import reduce
from qfilters import QFilter, QuerySetFilter

from django.db.models.query import Q

class FilterMark(Mark):

    collect_into = '_declared_filters'

    def build_me(self, marks, owner):
        if isinstance(self, Q):
            return QFilter(self)
        return self


qobj = FilterMark.register(QFilter)
qsfilter = FilterMark.register(QuerySetFilter)

FilterMark.register(Q)


class apply(FilterMark):
    def __init__(self, operation):
        self.op = operation


class Filter:
    filters = ContextAttr('_declared_filters')
    queryset = ContextAttr('queryset')

    def __init__(self, queryset=None):
        if queryset is not None:
            self.queryset = queryset

    @method
    def filter(self):
        accumulated = []
        for name, obj in self.filters.items():
            if isinstance(obj, apply):
                self.filters[name] = reduce(obj.op, accumulated)
                while accumulated:
                    accumulated.pop().skip = True
            else:
                accumulated.append(obj)
        self.results = OrderedDict()
        queryset = self.queryset
        for name, obj in self.filters.items():
            if not getattr(obj, 'skip', None):
                self.results[name] = queryset = obj(queryset)
        return queryset
