import greenlet
from functools import wraps

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

