import unittest
from functools import wraps
from collections import deque
from .util import  threadlocal

hooks_deque = threadlocal.hooks_deque = deque()
hooks_dict = threadlocal.hooks_dict = dict()

class Hook:

    def __init__(self, func, hook_func=None):
        self.func = func
        if hook_func:
            self.hook_func = hook_func

    @classmethod
    def lookup(cls, hook):
        if hook in hooks_dict:
            return hooks_dict[hook]
        if hooks_deque and hook == hooks_deque[-1]:
            return hooks_deque[-1]

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

    def execute(self, *args, **kwargs):
        return self.hook_func(*args, **kwargs)

    def __enter__(self):
        hooks_dict[self] = self

    def __exit__(self, *exc):
        if exc[0]:
            raise exc[0].with_traceback(exc[1], exc[2])
        del hooks_dict[self]

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


class OrderedHook(Hook):

    def execute(self, *args, **kwargs):
        hooks_deque.rotate(1)
        return self.hook_func(*args, **kwargs)

    def __enter__(self):
        hooks_deque.append(self)

    def __exit__(self, *exc):
        if exc[0]:
            raise exc[0].with_traceback(exc[1], exc[2])
        hooks_deque.remove(self)


class TestCaseHook(OrderedHook):
    test_case = None
    _hook_func = None

    def __init__(self, func, description=None, hook_func=None):
        super().__init__(func, hook_func=hook_func)
        self._description = description

    @property
    def hook_func(self):
        return self._hook_func

    @hook_func.setter
    def hook_func(self, func):
        subtest = self.test_case.subTest(self._description)
        func = subtest(func)
        # check
        hooks_deque.appendleft(self) # add but don't make active

        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            hooks_deque.remove(self)

        self._hook_func = wrapper


class SubTest:

    def __init__(self, type):
        self.type = type

    def __get__(self, test, owner):
        def construct(*args, **kwargs):
            instance = TestCaseHook(*args, **kwargs)
            instance.type = self.type
            instance.test_case = test
            return instance
        return construct


class TestCase(unittest.TestCase):
    stop_before = SubTest(pre_hook)
    stop_after = SubTest(post_hook)
