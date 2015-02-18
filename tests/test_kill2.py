from g_context.util import case
from g_context.base import method, pre_hook, post_hook
from g_context import context
from g_context.hooks import exit_before, exit_after

class A:
    x = 3

    @method
    def run(self):
        return B().walk() + 1

class B:

    @method
    def walk(self):
        return context['x']


class Kill(Exception):

    def __init__(self, value):
        self.value = value



with exit_after(A.run) as ex:
    o = A()
    res = o.run()


case.assertEqual(ex.ret, 4)
