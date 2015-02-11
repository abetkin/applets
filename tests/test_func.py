from applets.base import Greenlet
from applets.handles import handler_before, handler_after
from applets import from_context
from applets.util import case

class A:
    x = 3

    @Greenlet
    def run(self):
        return B().walk() + 1

class B:

    @Greenlet
    def walk(self):
        return from_context('x')


@Greenlet
def some_func():

    @handler_before(B.walk)
    def f(obj):
        case.assertIsInstance(obj, B)

    @handler_after(A.run)
    def g(a, _result_):
        case.assertEqual(_result_, 4)

    o = A()
    o.run()


some_func()
