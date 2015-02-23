import operator
from django.contrib.auth.models import User
from rest_framework import permissions
from rest_framework import renderers
from rest_framework import viewsets, generics
from rest_framework.decorators import detail_route
from rest_framework.response import Response
from rest_framework import serializers
from snippets.models import Snippet
from snippets.permissions import IsOwnerOrReadOnly
from snippets.serializers import SnippetSerializer, UserSerializer


from gcontext import method, add_context, get_context
from gcontext._django.serialize import serialize, deserialize, field, \
        fields_separator
from gcontext._django.filter import Filter, FilterMark, apply
from declared import DeclaredMeta, declare

from django.db.models.query import Q

class SnippetViewSet(viewsets.ModelViewSet):
    """
    This endpoint presents code snippets.

    The `highlight` field presents a hyperlink to the hightlighted HTML
    representation of the code snippet.

    The **owner** of the code snippet may update or delete instances
    of the code snippet.

    Try it yourself by logging in as one of these four users: **amy**, **max**,
    **jose** or **aziz**.  The passwords are the same as the usernames.
    """
    queryset = Snippet.objects.all()
    serializer_class = SnippetSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)

    @detail_route(renderer_classes=(renderers.StaticHTMLRenderer,))
    def highlight(self, request, *args, **kwargs):
        snippet = self.get_object()
        return Response(snippet.highlighted)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class UserViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This endpoint presents the users in the system.

    As you can see, the collection of snippet instances owned by a user are
    serialized using a hyperlinked representation.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class DeclaredFields(metaclass=DeclaredMeta):
    default_mark = field


class MyFilter(Filter, DeclaredFields):

    @property
    def filters(self):
        return self._declared_filters

    @method
    def __init__(self, qs=None):
        super().__init__(qs)
        self.process_declared()


    title = serializers.CharField()
    code = serializers.CharField()

    @declare(FilterMark) # rename: Filter
    def qtitle(self):
        return Q(title=self.params['title'])

    @declare(FilterMark)
    def qcode(self):
        return Q(code=self.params['code'])

    result = apply(operator.and_)

    _params = None

    @property
    def params(self):
        if self._params is None:
            self._params = deserialize()
        return self._params

from gcontext._django.views import ContextDispatch

class SnippetsList(ContextDispatch, generics.ListAPIView, DeclaredFields):

    queryset = Snippet.objects.all()

    owner = serializers.ReadOnlyField(source='owner.username')
    _________ = fields_separator
    highlight = serializers.HyperlinkedIdentityField(view_name='snippet-highlight', format='html')

    def get(self, request):
        import ipdb
        with ipdb.launch_ipdb_on_exception():
            self.object = list(MyFilter().filter())
            return Response(serialize(many=True))

snippets_list = SnippetsList.as_view()
