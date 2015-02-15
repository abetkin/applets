import unittest
from functools import update_wrapper, wraps
from g_context.base import  Missing
from g_context.handles import FunctionHandle, HandleBefore, HandleAfter


class TestCaseHandle(FunctionHandle):
    test_case = None

    def __init__(self, func, description):
        super().__init__(func)
        self._description = description

    def switch(self, *args, _result_=Missing, **kwargs):
        if _result_ is not Missing:
            kwargs['_result_'] = _result_
        if self.test_case is not None:
            subtest = self.test_case.subTest(self._description)
            subtest(self.handler_func)(*args, **kwargs)
        else:
            # fallback
            @wraps(self.handler_func)
            def testfunc():
                self.handler_func(case, *args, **kwargs)
            case = unittest.FunctionTestCase(testfunc,
                                             description=self._description)
            runner = unittest.TextTestRunner()
            runner.run(case)
        return Missing


class TestCaseBefore(TestCaseHandle):
    handle_type = HandleBefore

class TestCaseAfter(TestCaseHandle):
    handle_type = HandleAfter


class SubTestBefore:
    def __get__(self, test, owner):
        def construct(*args, **kwargs):
            instance = TestCaseBefore(*args, **kwargs)
            instance.test_case = test
            return instance
        update_wrapper(construct, TestCaseBefore, updated=())
        return construct

class SubTestAfter:
    def __get__(self, test, owner):
        def construct(*args, **kwargs):
            instance = TestCaseAfter(*args, **kwargs)
            instance.test_case = test
            return instance
        update_wrapper(construct, TestCaseAfter, updated=())
        return construct


class TestCase(unittest.TestCase):
    stop_before = SubTestBefore()
    stop_after = SubTestAfter()
