import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'tutorial.settings'
import django
django.setup()

from rest_framework.test import APIClient

from snippets.serializers import HyperlinkedModelSerializer
from g_context.handles import stop_after, stop_before, \
        handler_after, handler_before, resume
from g_context.base import green_method, green_function
from g_context.util import case


# @handler_before(HyperlinkedModelSerializer.is_valid)
# def f(*args, **kw):
#     '''import IPython
#     IPython.embed()'''

# stop_after(HyperlinkedModelSerializer.errors)
stop_after(HyperlinkedModelSerializer.data)

class Client(APIClient):
    @green_function
    def get(self, *args, **kwargs):
        return super().get(*args, **kwargs)

    @green_function
    def post(self, *args, **kwargs):
        return super().post(*args, **kwargs)

cl = Client()
cl.login(username='vitalii', password='root')
resp = cl.post('/snippets/', {'title': 'titlu', 'code': 'codu'})
# import IPython
# IPython.embed()
case.assertIsInstance(resp, dict)
resp = resume()
print(resp.data)
