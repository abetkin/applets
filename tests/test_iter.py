from g_context.util import case
from g_context.base import method, pre_hook, post_hook
from g_context import context

class A:
    x = 3

    @method
    def run(self):
        return B().walk() + 1

class B:

    @method
    def walk(self):
        return context['x']


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
