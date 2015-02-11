import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'tutorial.settings'
import django
django.setup()

from rest_framework.test import APIClient

from snippets.serializers import HyperlinkedModelSerializer
from applets.handles import stop_after, stop_before, \
        handler_after, handler_before, resume
from applets.base import green_method, green_function
from applets.util import case


# @handler_before(HyperlinkedModelSerializer.is_valid)
# def f(*args, **kw):
#     '''import IPython
#     IPython.embed()'''

stop_after(HyperlinkedModelSerializer.errors)
# stop_after(HyperlinkedModelSerializer.data)

cl = APIClient()
cl.login(username='vitalii', password='root')
resp = green_function(cl.post)('/snippets/', {'title': 'titlu', 'code': 'codu'})
# import IPython
# IPython.embed()
case.assertEqual(dict(resp), {})
resp = resume()
print(resp.data)
