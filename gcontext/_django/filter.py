from collections import OrderedDict
from declared import Mark, DeclaredMeta
from gcontext import method, function, ContextAttr


from functools import reduce

from django.db.models.query import Q, QuerySet

class FilterMark(Mark):

    collect_into = '_declared_filters'

FilterMark.register(Q)
# FilterMark.register(QuerySet)


class apply(FilterMark):
    def __init__(self, operation):
        self.op = operation


class Filter:
    _declared_filters = ContextAttr('_declared_filters')
    queryset = ContextAttr('queryset')

    def __init__(self, queryset=None):
        self.results = {}
        if queryset is not None:
            self.queryset = queryset

    @method
    def filter(self):
        filters = self._declared_filters
        queryset = self.queryset

        accumulated = []
        for name, obj in filters.items():
            if not isinstance(obj, apply):
                accumulated.append(obj)
                assert isinstance(obj, (Q, QuerySet))
                continue
            qobjects = list(filter(lambda o: isinstance(o, Q), accumulated))
            if qobjects:
                for qobj in qobjects:
                    accumulated.remove(qobj)
                queryset = queryset.filter(reduce(obj.op, qobjects))
            if accumulated:
                accumulated.append(queryset)
                queryset = reduce(obj.op, accumulated)
            self.results[name] = queryset
        return queryset
