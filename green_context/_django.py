from operator import and_, or_
from collections import OrderedDict
from functools import partial, wraps
from green_context.marks import Mark, CollectMarksMeta
from green_context.base import ContextAttr, green_method

from rest_framework import serializers

from django.db.models.query import Q, QuerySet

class qsfilter(Mark):
    '''
    Django queryset filter.
    '''
    collect_into = '_filters'

class qobj(Mark):
    collect_into = '_filters'

class make_qs(Mark):
    collect_into = '_filters'

    def __init__(self, source='objects', operation=and_, **kwargs):
        super().__init__(source=source, operation=operation, **kwargs)

class filterfunc(Mark):
    collect_into = '_filters'


from functools import reduce



class FilteringUnit(metaclass=CollectMarksMeta):

    objects = ContextAttr('objects')

    def _process_pending_filters(self, source='objects', target='objects', operation=and_):
        if not self.pending_filters:
            return
        base_qs = self.results[source]
        assert isinstance(base_qs, QuerySet)
        self.results[target] = reduce(operation, [f(base_qs) for f in self.pending_filters])
        self.pending_filters = []

    @green_method # ??
    def main(self):
        self.results = OrderedDict()
        self.results['objects'] = self.objects
        self.pending_filters = []

        for obj_name, obj in self._filters.items():
            if isinstance(obj, qsfilter):
                @wraps(obj.source_function)
                def _filter(qs, obj=obj):
                    return obj.source_function(self, qs)
                self.pending_filters.append(_filter)
                continue
            if isinstance(obj, qobj):
                @wraps(obj.source_function)
                def _filter(qs, obj=obj):
                    q_obj = obj.source_function(self)
                    return qs.filter(q_obj)
                self.pending_filters.append(_filter)
                continue
            if isinstance(obj, make_qs):
                self._process_pending_filters(obj.source, obj_name, obj.operation)
                assert not obj.source_function
                continue
            if isinstance(obj, filterfunc):
                self._process_pending_filters()
                qs = self.results[obj.source]
                self.results[obj_name] = obj.source_function(self, qs)
                continue
        self._process_pending_filters()

        return self.results['objects']
#         q = reduce(self.operation, self._q_objects)
