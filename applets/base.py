from functools import wraps
import collections
from contextlib import contextmanager
import greenlet

from .util import as_context, MISSING


class Applet:

    ctx = 1

# TODO __contains__
'''
Context is an object you can get attributes from by calling it:

    >>> context('some_attr')
'''


class ListContext(list):

    _wrapped_func = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__instance__ = None

    def __bool__(self):
        # whether context is prepared
        #
        return '__instance__' not in self.__dict__

    def _set_prepared(self):
        if '__instance__' in self.__dict__:
            del self.__instance__

    def __get__(self, instance, owner):
        if instance:
            self.__instance__ = instance
        if self._wrapped_func:
            return self._wrapped_func.__get__(instance)
        return self

    def __call__(self, name):
        for obj in self:
            if not callable(obj):
                obj = as_context(obj)
            value = obj(name)
            if value is not MISSING:
                return value
        return MISSING

    def __add__(self, other):
        if not isinstance(other, list):
            other = list((other,))
        result = ListContext(self)
        result.extend(other)
        return result

    def __radd__(self, other):
        if not isinstance(other, list):
            other = list((other,))
        result = ListContext(other)
        result.extend(self)
        return result

    @classmethod
    def evaluate(cls):
        g = greenlet.getcurrent()
        new = ListContext()
        while not g.context:
            obj = g.context.__instance__
            if obj is not None:
                new.append(obj)
            g = g.parent
            if not hasattr(g, 'context'):
                break
        else:
            new = new + g.context
        new._set_prepared()
        return new

###########

def get_from_context(name):
    context = greenlet.getcurrent().context
    # AttributeError ?
    if not context:
        context = greenlet.getcurrent().context = ListContext.evaluate()
    value = context(name)
    if value is not MISSING:
        return value
    raise AttributeError(name)

@contextmanager
def context(ctx):
    if isinstance(ctx, type) or not callable(ctx): # FIXME ?
        ctx = as_context(ctx)
    g_current = greenlet.getcurrent()
    old_ctx = getattr(g_current, 'context', MISSING)
    g_current.context = ctx
    yield
    if old_ctx is MISSING:
        del g_current.context
    else:
        g_current.context = old_ctx


def in_greenlet(func):
    ctx = ListContext()

    @wraps(func)
    def wrapper(*args, **kwargs):
        g = greenlet.greenlet(func)
        g.context = ctx
        return g.switch(*args, **kwargs)

    ctx._wrapped_func = wrapper
    return ctx
