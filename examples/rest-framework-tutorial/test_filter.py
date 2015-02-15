import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'tutorial.settings'
import django
django.setup()

from rest_framework.test import APIClient

from snippets.serializers import HyperlinkedModelSerializer
from snippets.models import Snippet
from g_context.handles import stop_after, stop_before, \
        handler_after, handler_before, resume
from g_context.base import green_method, green_function, context
from g_context.util import case
from g_context._django.filter import Filter, qobj, qsfilter, apply, FilterMark
import operator

from qfilters import QFilter, QuerySetFilter
from django.db.models.query import Q, QuerySet

from declared import Mark, DeclaredMeta

class MyFilter(metaclass=DeclaredMeta):

    default_mark = FilterMark

    code = Q(code__contains='cod')

    title = Q(title='titlu')

    # style = ~Q(style='friendly')

    result = apply(operator.and_)


with context(MyFilter, {'queryset': Snippet.objects.all()}):
    print(Filter().filter())
