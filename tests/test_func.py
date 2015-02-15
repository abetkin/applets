from g_context.base import green_method, green_function
from g_context.handles import handler_before, handler_after
from g_context import getcontext
from g_context.util import case

class A:
    x = 3

    @green_method
    def run(self):
        return B().walk() + 1

class B:

    @green_method
    def walk(self):
        return getcontext()['x']


@green_function
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
