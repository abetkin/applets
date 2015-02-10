from applets.base import GreenletWrapper
from applets import from_context
from applets.testing import TestCase, TestCaseAfter, TestCaseBefore

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


class T(TestCase):

    def test(self):

        @self.stop_before(B.walk, 'walking')
        def f(obj):
            self.assertFalse(obj.__b__)

        @self.stop_after(A.run, 'running A')
        def g(a, _result_):
            self.assertNotEqual(_result_, 4)

        o = A()
        ss = o.run()

# @TestCaseBefore(B.walk, 'walking')
# def f(case, obj):
#     case.assertFalse(obj.__b__)

# @TestCaseAfter(A.run, 'running A')
# def g(case, a, _result_):
#     case.assertNotEqual(_result_, 4)

# o = A()
# ss = o.run()
