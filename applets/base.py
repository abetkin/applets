from functools import wraps
import collections
from contextlib import contextmanager
import greenlet

from .util import as_context, MISSING
from .handles import HandleBefore, HandleAfter


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

def from_context(name):
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
    '''Wrapper for methods and functions.'''

    __self__ = None

    def __init__(self, func):
        self.__func__ = func

    @property
    def raw(self):
        return self.__func__.__get__(self.__self__)

    def __get__(self, instance, owner):
        if instance is not None:
            self.__self__ = instance
            return self
        return self.__func__

    def __call__(self, *args, **kwargs):
        g = MethodGreenlet(self)
        g.get_context()
        if self.__self__ is not None:
            args = (self.__self__,) + args
        return g.switch(*args, **kwargs)


class MethodGreenlet(greenlet.greenlet):
    ''''''

    def __init__(self, method):
        super().__init__(method.__func__)
        self._method = method
        # all_handles attribute is for optimization purposes
        self.all_handles = dict(
                (p, p) for p in getattr(self.parent, '_handles', ()))
        self.all_handles.update(
                getattr(self.parent, 'all_handles', ()))

    @property
    def __instance__(self):
        return self._method.__self__

    @property
    def __func__(self):
        return self._method.__func__

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

    def __repr__(self):
        return 'MethodGreenlet: %s' % self.__instance__.__class__.__name__ \
                if self.__instance__ is not None else '-'

    def run(self, *args, **kwargs):
        result = MISSING
        handle = self.all_handles.get((HandleBefore, self.__func__))
        if handle and handle.is_active():
            handle.g_stopped = self
            result = handle._switch(*args, **kwargs)
        if result is MISSING:
            # *
            result = self.__func__(*args, **kwargs)
            # *
        handle = self.all_handles.get((HandleAfter, self.__func__))
        if handle and handle.is_active():
            handle.g_stopped = self # or just take current ?
            switched = handle._switch(*args, _result_=result, **kwargs)
            if switched is not MISSING:
                result = switched
        return result
