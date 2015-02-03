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


###########

def get_from_context(name):
    context = greenlet.getcurrent().context
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


class GreenletWrapper:
    '''A wrapper for methods.'''

    __self__ = None

    def __init__(self, func):
        self.__func__ = func

        @wraps(func)
        def wrapper(*args, **kwargs):
            g = MethodGreenlet(self)
            g.get_context()
            return g.switch(*args, **kwargs)

        self._wrapper_func = wrapper

    @property
    def raw(self):
        return self.__func__.__get__(self.__self__)

    def __get__(self, instance, owner):
        if instance:
            self.__self__ = instance
        return self

    def __call__(self, *args, **kwargs):
        method = self._wrapper_func.__get__(self.__self__)
        return method(*args, **kwargs)


class MethodGreenlet(greenlet.greenlet):

    def __init__(self, method):
        '''method is a `GreenletWrapper` instance
        '''
        self._method = method
        super().__init__(method.__func__)

    @property
    def __instance__(self):
        return self._method.__self__

    def get_context(self):
        if hasattr(self, 'context'):
            return self.context
        g = self
        new = ListContext()
        while g is not None:
            if hasattr(g, 'context'):
                new = new + g.context
                break
            if getattr(g, '__instance__', None) is not None:
                new.append(g.__instance__)
            g = g.parent
        self.context = new
        return new
