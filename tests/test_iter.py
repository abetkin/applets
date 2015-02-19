from util import case
from gcontext.base import method, pre_hook, post_hook
from gcontext import get_context

class A:
    x = 3

    @method
    def run(self):
        return B().walk() + 1

class B:

    @method
    def walk(self):
        return get_context()['x']


class C(A):

    def incr(self, *args, ret=None):
        return ret + 2

    @method
    def run(self):
        with post_hook(B.walk, self.incr):
            return super().run()


o = C()
res = o.run()
case.assertEqual(res, 6)
