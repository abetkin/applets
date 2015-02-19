from functools import wraps
from contextlib import contextmanager
from collections import Mapping

from .util import Missing, ExplicitNone, threadlocal
from .hooks import pre_hook, post_hook, Hook


def ContextAttr(name, default=Missing):
    dic = {}

    def fget(self):
        context = get_context()
        if name in dic:
            return dic[name]
        if default is not Missing:
            return context.get(name, default)
        return context[name]

    def fset(self, value):
        dic[name] = value

    return property(fget, fset)


@contextmanager
def add_context(*objects):
    added = 0
    context = get_context()
    for obj in objects:
        if context.push(obj):
            added += 1
    context.pending = False
    yield
    for i in range(added):
        context.pop()


@Mapping.register
class ObjectsStack:

    pending = None

    def __init__(self, objects=None):
        self._objects = objects or []

    def __copy__(self):
        return self.__class__(self.objects)

    @property
    def objects(self):
        return self._objects[1:] if self.pending else self._objects

    def __repr__(self):
        return repr(self.objects)

    def __getitem__(self, key):
        if isinstance(key, int):
            # a bit of user-friendly interface
            return self.objects[key]
        for obj in self.objects:
            try:
                if isinstance(obj, Mapping):
                    return obj[key]
                return getattr(obj, key)
            except (KeyError, AttributeError):
                pass
        return self.__missing__(key)

    def __missing__(self, key):
        raise KeyError(key)

    def __setitem__(self, key, value):
        raise NotImplementedError()

    def __delitem__(self, key):
        raise NotImplementedError()

    def __bool__(self):
        return bool(self.objects)

    def get(self, key, default=None):
        return self[key] if key in self else default

    def __contains__(self, key):
        try:
            self[key]
            return True
        except KeyError:
            pass

    def __iter__(self):
        yield from self.objects

    def __len__(self):
        return len(self.objects)

    def __eq__(self, other):
        if isinstance(other, ObjectsStack):
            return self._objects == other._objects \
                    and bool(self.pending) == bool(other.pending)

    def __ne__(self, other):
        return not (self == other)

    def push(self, obj):
        if obj is not None and obj not in self.objects:
            self._objects.insert(0, obj)
            self.pending = True
        else:
            self.pending = False
        return self.pending # the success of the operation

    def pop(self):
        self._objects.pop(0)

def get_context():
    return threadlocal().setdefault('context', ObjectsStack())

class GrabContextWrapper:

    def __init__(self, get_context_object):
        self.get_context_object = get_context_object

    @contextmanager
    def as_manager(self, *run_args, **run_kwargs):
        instance = self.get_context_object(*run_args, **run_kwargs)
        added = get_context().push(instance)
        yield
        if added:
            get_context().pop()


    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.as_manager(*args, **kwargs):
                result = None
                hook = Hook.lookup((pre_hook, wrapper))
                if hook:
                    result = hook.execute(*args, **kwargs)
                if result is None:
                    # * wrapped function *
                    result = func(*args, **kwargs)
                    # * * * * *  * * * * *
                elif result is ExplicitNone:
                    result = None
                hook = Hook.lookup((post_hook, wrapper))
                if hook:
                    ret = hook.execute(*args, ret=result, **kwargs)
                    if ret is ExplicitNone:
                        result = None
                    elif ret is not None:
                        result = ret
                return result

        return wrapper


@GrabContextWrapper
def function(*args, **kwargs):
    return None

@GrabContextWrapper
def method(*args, **kwargs):
    return args[0]
