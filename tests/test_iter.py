from applets.util import case
from applets.base import GreenletWrapper
from applets.handles import stop_before, stop_after
from applets import from_context, context

class A:
    x = 3

    @GreenletWrapper
    def run(self):
        return B().walk() + 1

class B:

    @GreenletWrapper
    def walk(self):
        return from_context('x')


class C(A):

    @GreenletWrapper
    def run(self):
        with stop_after(A.run) as A_run:
            with stop_before(B.walk) as stopped:
                b, = super().run()
                stopped.resume(5)
        return A_run.resumed


o = C()
res = o.run()
case.assertEqual(res, 6)


class D(A):

    @GreenletWrapper
    def run(self):
        with stop_after(A.run) as sce:
            with stop_after(B.walk):
                super().run()
        return sce.resumed

o = D()
res = o.run()
case.assertEqual(res, 4)
