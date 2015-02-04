from applets.util import case
import greenlet
from applets.base import GreenletWrapper, stop_before
from applets import get_from_context, context

class A:
    x = 3

    @GreenletWrapper
    def run(self):
        return B().walk() + 1

class B:

    @GreenletWrapper
    def walk(self):
        return get_from_context('x')


class C(A):

    @GreenletWrapper
    def run(self):
        with stop_before(B.walk) as stopped:
            res = super().run()
            return stopped.resume(5)



o = C()
case.assertEqual(o.run(), 6)
