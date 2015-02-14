from functools import wraps
from contextlib import contextmanager
import greenlet

from .util import MISSING
from .handles import HandleBefore, HandleAfter

from collections import ChainMap, Mapping


def getcontext():
    return greenlet.getcurrent().context

def ContextAttr(name, default=MISSING):

    def fget(self):
        context = getcontext()
        if default is not MISSING:
            return context.get(name, default)
        return context[name]

    def fset(self, value):
        context = getcontext()
        context[name] = value

    return property(fget, fset)


@contextmanager
def context(ctx):
    g_current = greenlet.getcurrent()
    old_ctx = getattr(g_current, 'context', MISSING)
    if isinstance(old_ctx, ChainMap): # TODO test
        old_ctx.maps.insert(0, ctx)
        yield
        old_ctx.maps.remove(ctx)
        return
    g_current.context = ctx
    yield
    if old_ctx is MISSING:
        del g_current.context
    else:
        g_current.context = old_ctx

# TODO def replace_context() ?

class ChainObjects(ChainMap):

    def __missing__(self, key):
        for obj in self.objects:
            result = getattr(obj, key, MISSING)
            if result is not MISSING:
                return result
        raise KeyError(key)

# rename ?
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

    @property
    def context(self):
        if hasattr(self, '_context'):
            return self._context
        obj = self.__self__
        objects = []
        def maps():
            g = self.parent
            while g is not None and not hasattr(g, 'context'):
                g = g.parent
            if g is None:
                return
            if isinstance(g.context, ChainObjects):
                objects.extend(g.context.objects)
                if obj is not None and obj not in objects:
                    objects.insert(0, obj)
                    yield obj.__dict__
                    yield obj.__class__.__dict__
                yield from g.context.maps[1:]
            else:
                assert isinstance(g.context, Mapping)
                if obj is not None:
                    objects.insert(0, obj)
                    yield obj.__dict__
                    yield obj.__class__.__dict__
                yield g.context
        self._context = ChainObjects({}, *maps())
        self._context.objects = objects
        return self._context

    @context.setter
    def context(self, value):
        self._context = value

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
