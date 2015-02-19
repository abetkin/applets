import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'tutorial.settings'
import django
django.setup()

from rest_framework.test import APIClient

from snippets.serializers import HyperlinkedModelSerializer
from snippets.models import Snippet

from gcontext import add_context, method, function, get_context
from gcontext._django.filter import Filter, apply, FilterMark
import operator

from django.db.models.query import Q, QuerySet

from declared import Mark, DeclaredMeta, declare

class MyFilter(Filter, metaclass=DeclaredMeta):

    default_mark = FilterMark

    code = Q(code__contains='cod')

    style = Q(style='friendly')

    @declare(FilterMark)
    def title(self):
        return self.queryset.exclude(title='titl')

    result = apply(operator.and_)


    def __init__(self):
        super().__init__()
        self.process_declared()


with add_context({'queryset': Snippet.objects.all()}): # TODO pending ?
    print(MyFilter().filter())
