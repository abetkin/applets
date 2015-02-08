import unittest
from applets.base import  MISSING, StopPoint, stop_after, stop_before


class StopPointSubtest(StopPoint):
    test_case = None

    def __init__(self, func, *subtest_args, **subtest_kwargs):
        super().__init__(func)
        self.subtest_args = subtest_args
        self.subtest_kwargs = subtest_kwargs
        self.__enter__()

    def __call__(self, test_func):
        # TODO wrap
        subtest = self.test_case.subTest(
                *self.subtest_args, **self.subtest_kwargs)
        self._test_func = subtest(test_func)

    def switch(self, *args, _result_=MISSING, **kwargs):
        if _result_ is not MISSING:
            kwargs['_result_'] = _result_
        self._test_func(*args, **kwargs)
        return self.resume()
        # TODO try...finally


class StopBeforeSubTest(StopPointSubtest):
    def get_type(self):
        return stop_before

class StopAfterSubTest(StopPointSubtest):
    def get_type(self):
        return stop_after


class StopBefore:

    def __get__(self, test, owner):
        def construct(*args, **kwargs):
            instance = StopBeforeSubTest(*args, **kwargs)
            instance.test_case = test
            return instance
        # wrap
        return construct

class StopAfter:

    def __get__(self, test, owner):
        def construct(*args, **kwargs):
            instance = StopAfterSubTest(*args, **kwargs)
            instance.test_case = test
            return instance
        # wrap
        return construct


class TestCase(unittest.TestCase):
    stop_before = StopBefore()
    stop_after = StopAfter()
