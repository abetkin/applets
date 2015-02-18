import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'tutorial.settings'
import django
django.setup()

from rest_framework.test import APIClient

from snippets.serializers import HyperlinkedModelSerializer
from snippets.models import Snippet

from g_context.base import add_context
from g_context.util import case
from g_context._django.filter import Filter, apply, FilterMark
import operator

from qfilters import QFilter, QuerySetFilter
from django.db.models.query import Q, QuerySet

from declared import Mark, DeclaredMeta, declare

class MyFilter(metaclass=DeclaredMeta):

    default_mark = FilterMark

    code = Q(code__contains='cod')

    @declare(FilterMark)
    def title(self):
        return Q(title='titlu')

    # style = ~Q(style='friendly')

    result = apply(operator.and_)

    def __init__(self):
        self.process_declared()


with add_context(MyFilter(), {'queryset': Snippet.objects.all()}):
    print(Filter().filter())
