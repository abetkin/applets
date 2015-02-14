from green_context.util import case
from green_context.base import green_method
from green_context.handles import stop_before, stop_after
from green_context import getcontext, context

class A:
    x = 3

    @green_method
    def run(self):
        return B().walk() + 1

class B:

    @green_method
    def walk(self):
        return getcontext()['x']


class C(A):

    @green_method
    def run(self):
        with stop_after(A.run) as A_run:
            with stop_before(B.walk) as stopped:
                ret = super().run()
                b, = ret
                stopped.resume(5)
        return A_run.resumed


o = C()
res = o.run()
case.assertEqual(res, 6)


class D(A):
    # x = 5

    @green_method
    def run(self):
        with stop_after(A.run) as sce:
            with stop_after(B.walk):
                super().run()
        return sce.resumed

o = D()
res = o.run()
case.assertEqual(res, 4)
