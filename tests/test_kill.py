from applets.util import case
from applets.base import GreenletWrapper
from applets.handles import stop_before, stop_after
from applets import from_context

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
        with stop_after(A.run):
            with stop_before(B.walk) as stopped:
                b, = super().run()
                stopped.kill()
        return b


o = C()
res = o.run()
case.assertIsInstance(res, B)


# TODO check that handles are parent greenlets
