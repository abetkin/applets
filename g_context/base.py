from functools import wraps
from contextlib import contextmanager

from .util import Missing, ExplicitNone

from collections import Mapping, deque
import threading


threadlocal = threading.local()


def ContextAttr(name, default=Missing):

    def fget(self):
        if default is not Missing:
            return context.get(name, default)
        return context[name]

    def fset(self, value):
        context[name] = value

    return property(fget, fset)


@contextmanager
def add_context(*objects):
    context
    added = 0
    for obj in objects:
        if context.push(obj):
            added += 1
    yield
    for i in range(added):
        context.pop()


# TODO def replace_context() ?

@Mapping.register
class ObjectsStack:

    pending = None

    def __init__(self):
        self._objects = []
        self._dic = {}

    @property
    def objects(self):
        return self._objects[1:] if self.pending else self._objects

    def __repr__(self):
        return repr(self.objects)

    def __getitem__(self, key):
        if isinstance(key, int):
            # a bit of user-friendly interface
            return self.objects[key]
        if key in self._dic:
            return self._dic[key]
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
        self._dic[key] = value

    def __delitem__(self, key):
        del self._dic[key]

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
        self._objects.pop()


context = threadlocal.context = ObjectsStack()
threadlocal.hooks = deque()


class ContextWrapper:

    def __init__(self, instance_arg=0):
        self.instance_arg = instance_arg

    def _get_instance(self, *run_args, **run_kwargs):
        if self.instance_arg is None:
            return
        try:
            index = int(self.instance_arg)
        except TypeError:
            return run_kwargs[self.instance_arg]
        else:
            return run_args[index]

    @contextmanager
    def as_manager(self, *run_args, **run_kwargs):
        instance = self._get_instance(*run_args, **run_kwargs)
        added = context.push(instance)
        yield
        if added:
            context.pop()

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.as_manager(*args, **kwargs):
                result = None
                hooks = threadlocal.hooks
                if hooks and hooks[-1] == (pre_hook, wrapper):
                    result = hooks[-1].hook_func(*args, **kwargs)
                    hooks.rotate(1)
                if result is None:
                    # * our function *
                    result = func(*args, **kwargs)
                    # * * * * * * *  *
                elif result is ExplicitNone:
                    result = None
                if hooks and hooks[-1] == (post_hook, wrapper):
                    ret = hooks[-1].hook_func(*args, ret=result, **kwargs)
                    hooks.rotate(1)
                    if ret is ExplicitNone:
                        result = None
                    elif ret is not None:
                        result = ret
                return result

        return wrapper


function = ContextWrapper(None)
method = ContextWrapper()


class Hook:

    def __init__(self, func, hook_func=None):
        self.func = func
        if hook_func:
            self.hook_func = hook_func

    def __repr__(self):
        hook_type = {
            pre_hook: 'pre',
            post_hook: 'post',
        }[self.type]
        hook_name = self.hook_func.__name__ # FIXME can be any callable
        return '%s: %s %s' % (hook_name, hook_type, self.func)

    def __call__(self, hook_func):
        self.hook_func = hook_func
        return self

    def __enter__(self):
        threadlocal.hooks.append(self)

    def __exit__(self, *exc):
        if exc[0]:
            raise exc[0].with_traceback(exc[1], exc[2])
        threadlocal.hooks.remove(self)

    def __hash__(self):
        return hash((self.type, self.func))

    def __eq__(self, other):
        if isinstance(other, tuple):
            return other == (self.type, self.func)
        if isinstance(other, Hook):
            return self.func is other.func and self.type is other.type


class pre_hook(Hook):
    pass
pre_hook.type = pre_hook

class post_hook(Hook):
    pass
post_hook.type = post_hook
