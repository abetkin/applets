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


class Kill(Exception):

    def __init__(self, value):
        self.value = value


class C(A):

    @method
    def run(self):
        @post_hook(B.walk)
        def stop(*args, ret=None):
            raise Kill(ret)

        with stop:
            try:
                super().run()
            except Kill as e:
                return e.value + 1


o = C()
res = o.run()
case.assertEqual(res, 4)
