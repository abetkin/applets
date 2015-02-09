import unittest
from applets.base import  MISSING, StopPoint, stop_after, stop_before, \
        MethodGreenlet


class StopPointSubtest(StopPoint):
    test_case = None

    def __init__(self, func, description):
        super().__init__(func)
        self._description = description
        MethodGreenlet.stop_point.fset(self.g_current, self, append=False)

    def __call__(self, test_func):
        # TODO wrap
        if self.test_case is not None:
            subtest = self.test_case.subTest(self._description)
            self._test_func = subtest(test_func)
        else:
            self._test_func = test_func
            # self._test_func = unittest.FunctionTestCase(
            #         test_func, description=self._description)
        # return self._test_func # ?

    def switch(self, *args, _result_=MISSING, **kwargs):
        if _result_ is not MISSING:
            kwargs['_result_'] = _result_
        if self.test_case is not None:
            self._test_func(*args, **kwargs)
        else:
            def testfunc():
                self._test_func(case, *args, **kwargs)
            case = unittest.FunctionTestCase(testfunc,
                                             description=self._description)
            runner = unittest.TextTestRunner()
            runner.run(case)
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
