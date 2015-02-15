from functools import wraps
from contextlib import contextmanager
import greenlet

from .util import MISSING
from .handles import HandleBefore, HandleAfter

from collections import ChainMap, Mapping


def getcontext():
    # FIXME AttributeError
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
def context(*objects):
    g_current = greenlet.getcurrent()
    old_ctx = getattr(g_current, 'context', None)
    objects = list(objects)
    if isinstance(old_ctx, ChainObjects):
        objects.extend(old_ctx.objects)
    elif old_ctx is not None:
        objects.append(old_ctx)
    g_current.context = ChainObjects(*objects)
    yield g_current.context
    if old_ctx is None:
        del g_current.context
    else:
        g_current.context = old_ctx

# TODO def replace_context() ?

class ChainObjects:

    def __init__(self, *objects):
        self.objects = []
        def maps():
            for obj in objects:
                if obj is None or obj in self.objects:
                    continue
                self.objects.append(obj)
                if isinstance(obj, Mapping):
                    yield obj
                    continue
                yield obj.__dict__
                if not isinstance(obj, type):
                    yield obj.__class__.__dict__
        self._chainmap = ChainMap({}, *maps())

    # TODO repr

    def __getitem__(self, key):
        for mapping in self._chainmap.maps:
            try:
                return mapping[key]
            except KeyError:
                pass
        return self.__missing__(key)

    def __setitem__(self, key, value):
        self._chainmap[key] = value

    def __delitem__(self, key):
        del self._chainmap[key]

    def __bool__(self):
        return bool(self.objects)

    def get(self, key, default=None):
        return self[key] if key in self else default

    def __contains__(self, key):
        return key in self._chainmap # TODO search objects ?

    def __iter__(self):
        yield from self.objects

    def __len__(self):
        return len(self.objects)

    def __eq__(self, other):
        if isinstance(other, ChainObjects):
            return self.objects == other.objects

    def __ne__(self, other):
        return not (self == other)

    def __missing__(self, key):
        for obj in self.objects:
            result = getattr(obj, key, MISSING)
            if result is not MISSING:
                return result
        raise KeyError(key)

    def new_child(self, obj):
        return self.__class__(obj, *self.objects)


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

    def _new_context(self):
        g = self.parent
        while g is not None and not hasattr(g, 'context'):
            g = g.parent
        if g is None:
            return ChainObjects()
        assert isinstance(g.context, ChainObjects)
        obj = g.__self__ if isinstance(g, MethodGreenlet) else None
        return g.context.new_child(obj)

    @property
    def context(self):
        if not hasattr(self, '_context'):
            self._context = self._new_context()
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
