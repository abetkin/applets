import unittest
from functools import wraps
from g_context.base import  threadlocal, Hook, pre_hook, post_hook

# TODO always return None ?

class TestCaseHook(Hook):
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
        threadlocal.hooks.appendleft(self) # add but don't make active

        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            threadlocal.hooks.remove(self)

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
