from contextlib import contextmanager, ExitStack
from applets.util import case
import greenlet
from applets.base import GreenletWrapper, MISSING, StopPoint, stop_after, stop_before
from applets import from_context

class A:
    x = 3

    @GreenletWrapper
    def run(self):
        return B().walk() + 1

class B:

    def __init__(self):
        self.__b__ = True

    @GreenletWrapper
    def walk(self):
        return from_context('x')


class _stop_after(StopPoint):

    def __init__(self, func):
        super().__init__(func)
        self.__enter__()

    def get_type(self):
        return stop_after

    def __call__(self, test_func):
        self._test_func = test_func

    def switch(self, *args, _result_=MISSING, **kwargs):
        if _result_ is not MISSING:
            kwargs['_result_'] = _result_
        self._test_func(*args, **kwargs)
        return self.resume()


import unittest

class T(unittest.TestCase):

    def test(self):

        @_stop_after(B.walk)
        @self.subTest('gregerg')
        def f(obj, _result_):
            print(_result_)
            self.assertFalse(obj.__b__)

        o = A()
        ss = o.run()
