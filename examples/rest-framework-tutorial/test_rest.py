import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'tutorial.settings'
import django
django.setup()

from rest_framework.test import APIClient

from snippets.serializers import HyperlinkedModelSerializer
from applets.handles import stop_after, stop_before, \
        handler_after, handler_before, resume
from applets.base import Greenlet
from applets.util import case


# @handler_before(HyperlinkedModelSerializer.is_valid)
# def f(*args, **kw):
#     '''import IPython
#     IPython.embed()'''

stop_after(HyperlinkedModelSerializer.is_valid)

cl = APIClient()
cl.login(username='vitalii', password='root')
resp = Greenlet(cl.post)('/snippets/', {'title': 'titlu', 'code': 'codu'})

case.assertEqual(resp, True)
resp = resume()
print(resp.data)
