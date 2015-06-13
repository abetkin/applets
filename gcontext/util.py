import greenlet
from functools import wraps

import collections

threadlocal = greenlet.getcurrent()

def threadlocal():
    gcurrent = greenlet.getcurrent()
    return gcurrent.__dict__.setdefault('_gcontext', {})

class Missing:
    pass

class ExplicitNone:
    pass


def lazyattr(name):
    def decorator(method):
        @wraps(method)
        def getter(self, *args, **kwargs):
            if not hasattr(self, name):
                setattr(self, name, method(self, *args, **kwargs))
            return getattr(self, name)
        return property(getter)
    return decorator


def get_attribute(obj, dotted_attr):
    attrs = dotted_attr.split('.')
    for attr in attrs:
        if obj is None:
            return None
        try:
            if isinstance(obj, collections.Mapping):
                obj = obj[attr]
            else:
                obj = getattr(obj, attr)
