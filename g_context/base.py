from functools import wraps
from contextlib import contextmanager

from .util import Missing, ExplicitNone

from collections import Mapping
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
        if context.add_child(obj):
            added += 1
    yield
    for i in range(added):
        context.objects.pop()


# TODO def replace_context() ?

@Mapping.register
class ObjectsChain:

    pending = None

    def __init__(self, *objects):
        self.objects = []
        for obj in objects:
            if obj is None or obj in self.objects:
                continue
            self.objects.append(obj)
        self._dic = {}

    def __repr__(self):
        return 'Chain ' + repr(self.objects)

    def __getitem__(self, key):
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
        if isinstance(other, ObjectsChain):
            return self.objects == other.objects

    def __ne__(self, other):
        return not (self == other)

    def add_child(self, obj):
        '''
        if self.pendind:
            pending = self.pending
            self.pending = obj
            self.add_child(pending)
        if obj is not None and obj not in self.objects:
            self.objects.insert(0, obj)
            return True'''

context = threadlocal.context = ObjectsChain()
threadlocal.hooks = []

class ContextWrapper:

    def __init__(self, instance_arg=0):
        self.instance_arg = instance_arg

    def _get_instance(self, *run_args, **run_kwargs):
        if self.instance_arg is None:
            return
        try:
            index = int(self.instance_arg)
        except TypeError:
            return self.run_kwargs[self.instance_arg]
        else:
            return self.run_args[index]

    @contextmanager
    def as_manager(self, *run_args, **run_kwargs):
        instance = self._get_instance(*run_args, **run_kwargs)
        added = context.add_child(instance)
        yield
        if added:
            context.objects.pop(0)

    def run(self, *args, **kwargs):
        result = None
        hook = threadlocal.hooks[-1] if threadlocal.hooks else None
        if hook == (pre_hook, self.wrapper):
            result = hook.hook_func(*args, **kwargs)
        if result is None:
            # *
            result = self.func(*args, **kwargs)
            # *
        elif result is ExplicitNone:
            result = None
        if hook == (post_hook, self.wrapper):
            ret = hook.hook_func(*args, ret=result, **kwargs)
            if ret is ExplicitNone:
                result = None
            elif ret is not None:
                result = ret
        return result


    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            self.run_args = args
            self.run_kwargs = kwargs
            with self.as_manager(*args, **kwargs):
                return self.run(*args, **kwargs)
        self.func = func
        self.wrapper = wrapper
        return wrapper


function = ContextWrapper(None)
method = ContextWrapper()


class Hook:

    def __init__(self, func, hook_func=None):
        self.func = func
        self.hook_func = hook_func

    def __call__(self, hook_func):
        self.hook_func = hook_func

    def __enter__(self):
        threadlocal.hooks.append(self)

    def __exit__(self, *exc):
        if exc[0]:
            raise exc[0].with_traceback(exc[1], exc[2])
        threadlocal.hooks.pop()

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
