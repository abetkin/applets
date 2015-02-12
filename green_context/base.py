from functools import wraps
from contextlib import contextmanager
import greenlet

from .util import as_context, MISSING
from .handles import HandleBefore, HandleAfter

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

def from_context(name, default=MISSING):
    context = greenlet.getcurrent().context
    value = context(name)
    if value is not MISSING:
        return value
    if default is MISSING:
        raise AttributeError(name)
    return default

@contextmanager
def context(ctx):
    if isinstance(ctx, type) or not callable(ctx): # FIXME ?
        ctx = as_context(ctx)
    g_current = greenlet.getcurrent()
    old_ctx = getattr(g_current, 'context', MISSING)
    if isinstance(old_ctx, ListContext): # TODO test
        old_ctx.insert(0, ctx)
        yield
        old_ctx.remove(ctx)
        return
    g_current.context = ctx
    yield
    if old_ctx is MISSING:
        del g_current.context
    else:
        g_current.context = old_ctx

# TODO def replace_context() ?


def ContextAttr(name, default=MISSING):
    def fget(self):
        self.__dict__.setdefault('_context_attributes', {})
        if name in self._context_attributes:
            return self._context_attributes[name]
        return from_context(name, default)

    def fset(self, value):
        self.__dict__.setdefault('_context_attributes', {})
        self._context_attributes[name] = value

    return property(fget, fset)


class Greenlet:
    '''Wrapper for methods and functions.'''

    def __init__(self, instance_arg=0):
        self.instance_arg = instance_arg

    def _get_instance(self, *args, **kwargs):
        if self.instance_arg is None:
            return
        try:
            index = int(self.instance_arg)
        except TypeError:
            return kwargs[self.instance_arg]
        else:
            return args[index]

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            instance = self._get_instance(*args, **kwargs)
            g = MethodGreenlet(wrapper, instance)
            g.get_context()
            return g.switch(*args, **kwargs)
        return wrapper

green_function = Greenlet(None)
green_method = Greenlet()


class MethodGreenlet(greenlet.greenlet):
    ''''''

    def __init__(self, func, instance=None):
        self._wrapper_func = func
        self.__self__ = instance
        super().__init__(self.__func__)
        # all_handles attribute is for optimization purposes
        self.all_handles = dict(
                (p, p) for p in getattr(self.parent, '_handles', ()))
        self.all_handles.update(
                getattr(self.parent, 'all_handles', ()))
    @property
    def __func__(self):
        return self._wrapper_func.__wrapped__

    def get_context(self):
        if hasattr(self, 'context'):
            return self.context
        g = self
        new = ListContext()
        while g is not None:
            if hasattr(g, 'context'):
                new = new + g.context
                break
            if getattr(g, '__self__', None) is not None:
                new.append(g.__self__)
            g = g.parent
        self.context = new
        return new

    def __repr__(self):
        return 'MethodGreenlet: %s' % self.__self__.__class__.__name__ \
                if self.__self__ is not None else '-'

    def run(self, *args, **kwargs):
        result = MISSING
        handle = self.all_handles.get((HandleBefore, self._wrapper_func))
        if handle and handle.is_active():
            result = handle._switch(*args, **kwargs)
        if result is MISSING:
            # *
            result = self.__func__(*args, **kwargs)
            # *
        handle = self.all_handles.get((HandleAfter, self._wrapper_func))
        if handle and handle.is_active():
            switched = handle._switch(*args, _result_=result, **kwargs)
            if switched is not MISSING:
                result = switched
        return result
