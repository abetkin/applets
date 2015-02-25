from functools import wraps
from itertools import islice
from contextlib import contextmanager
from collections import Mapping
from copy import copy

from .util import Missing, ExplicitNone, threadlocal
from .hooks import pre_hook, post_hook, Hook


def ContextAttr(name, default=Missing):

    def fget(self):
        dic = self.__dict__.setdefault('_contextattrs', {})
        context = get_context()
        if name in dic:
            return dic[name]
        if default is not Missing:
            return context.get(name, default)
        try:
            return context[name]
        except KeyError:
            raise AttributeError(name)

    def fset(self, value):
        dic = self.__dict__.setdefault('_contextattrs', {})
        dic[name] = value

    return property(fget, fset)


@contextmanager
def add_context(*objects):
    added = 0
    context = _raw_context()
    for obj in objects:
        if context.push(obj):
            added += 1
    context.pending = False
    yield
    for i in range(added):
        context.pop()


@Mapping.register
class ObjectsStack:
    def __init__(self, objects=None):
        self._objects = objects or []

    @property
    def objects(self):
        return self._objects

    def __copy__(self):
        return self.__class__(self.objects)

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
            return self.objects == other.objects

    def __ne__(self, other):
        return not (self == other)

    def push(self, obj):
        if obj is not None and obj not in self._objects:
            self._objects.insert(0, obj)
            return True

    def pop(self):
        self._objects.pop(0)


class PendingObjectContext(ObjectsStack):

    pending = False

    @property
    def parent(self):
        if not self.pending:
            return self
        objects = islice(self.objects, 1, None)
        return self.__class__(tuple(objects))

def _raw_context():
    return threadlocal().setdefault('context', PendingObjectContext())

def get_context():
    '''
    Return parent context.
    '''
    return _raw_context().parent


class GrabContextWrapper:

    def __init__(self, get_context_object):
        self.get_context_object = get_context_object

    @contextmanager
    def as_manager(self, *run_args, **run_kwargs):
        context = _raw_context()
        was_pending = context.pending
        instance = self.get_context_object(*run_args, **run_kwargs)
        added = context.push(instance) # whether was added successfully
        context.pending = added
        yield
        if added:
            context.pop()
        context.pending = was_pending


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
