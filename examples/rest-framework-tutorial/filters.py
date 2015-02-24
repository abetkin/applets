import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'tutorial.settings'
import django
django.setup()
class qobj:

    def __init__(self, qobj):
        self.qobj = qobj

    def filter(self, qs):
        return qs.filter(self.qobj)

    def __repr__(self):
        pairs = ['%s=%s' % item for item in self.qobj.children]
        return 'Q: %s' % ', '.join(pairs)

    def build(mark, *args):
        if isinstance(mark, Q):
            return qobj(mark)
        return mark
import abc
from declared import Mark, Declared

from django.db.models.query import Q

class qsfilter(Mark):

    collect_into = '_declared_filters'

    def __init__(self, func):
        self.func = func

    def filter(self, queryset):
        return self.func(queryset)

    def build(mark, *args):
        if isinstance(mark, Q):
            return qobj(mark)
        return mark

qsfilter.register(Q)
from declared import DeclaredMeta

@qsfilter.register
class FiltersDeclaredMeta(DeclaredMeta, abc.ABCMeta):
    def __repr__(cls):
        return 'filters declared'
    objects = g.ContextAttr('queryset')


import gcontext as g
from declared import DeclaredMeta

@qsfilter.register
class FiltersDeclaredMeta(DeclaredMeta, abc.ABCMeta):
    def __repr__(cls):
        return 'filters declared'
    objects = g.ContextAttr('queryset')


from functools import reduce

class FiltersDeclared(metaclass=FiltersDeclaredMeta):
    default_mark = qsfilter

    @classmethod
    def filter(cls):
        raise NotImplementedError()




class ReduceFilters(FiltersDeclared):
    # operation = None
    _declared_filters = None

    @classmethod
    def filter(cls, queryset):
        filters = [f.filter(queryset) for f in cls._declared_filters.values()]
        if filters:
            return reduce(cls.operation, filters)
        return queryset

import operator

class qand(ReduceFilters):
    operation = operator.and_
class qor(ReduceFilters):
    operation = operator.or_
class K(qor):


    a = Q(owner__isnull=True)
    b = Q(code='esferf')

    class c(qand):
        c = Q(code='codu')
        d = Q(title='titlu')
K._declared_filters
K.filter(Snippet.objects.all())
class CascadeFilter(FiltersDeclared):

    @classmethod
    def filter(cls, objects=None):
        if objects is None:
            objects = cls.objects
        for f in cls._declared_filters.values():
            objects = f.filter(objects)
        return objects
class Cascade(CascadeFilter):

    a = Q(code='codu')

    @qsfilter # description
    def b(queryset):
        if queryset.exists():
            return (queryset[0],)
        return queryset
Cascade._declared_filters
with g.add_context({'queryset': Snippet.objects.all()}):
    print(Cascade.filter())
