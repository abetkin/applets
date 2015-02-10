import unittest
from functools import update_wrapper
from applets.base import  MISSING, StopPoint, stop_after, stop_before


class StopPointTest(StopPoint):
    test_case = None

    def __init__(self, func, description):
        super().__init__(func)
        self._description = description

    def activate(self):
        self.stop_points.insert(0, self)

    def __call__(self, test_func):
        self._test_func = test_func
        return test_func

    def switch(self, *args, _result_=MISSING, **kwargs):
        if _result_ is not MISSING:
            kwargs['_result_'] = _result_
        if self.test_case is not None:
            subtest = self.test_case.subTest(self._description)
            subtest(self._test_func)(*args, **kwargs)
        else:
            # fallback
            def testfunc():
                self._test_func(case, *args, **kwargs)
            case = unittest.FunctionTestCase(testfunc,
                                             description=self._description)
            runner = unittest.TextTestRunner()
            runner.run(case)
        return self.resume()


class StopBefore(StopPointTest):
    def get_type(self):
        return stop_before

class StopAfter(StopPointTest):
    def get_type(self):
        return stop_after


class StopBeforeSubtest:
    def __get__(self, test, owner):
        def construct(*args, **kwargs):
            instance = StopBefore(*args, **kwargs)
            instance.test_case = test
            return instance
        update_wrapper(construct, StopBefore, updated=())
        return construct

class StopAfterSubtest:
    def __get__(self, test, owner):
        def construct(*args, **kwargs):
            instance = StopAfter(*args, **kwargs)
            instance.test_case = test
            return instance
        update_wrapper(construct, StopAfter, updated=())
        return construct


class TestCase(unittest.TestCase):
    stop_before = StopBeforeSubtest()
    stop_after = StopAfterSubtest()
