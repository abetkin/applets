from gcontext.base import method, get_context
from gcontext.hooks import TestCase

class A:
    x = 3

    @method
    def run(self):
        return B().walk() + 1

class B:

    def __init__(self):
        self.__b__ = True

    @method
    def walk(self):
        return get_context()['x']


class T(TestCase):

    def test(self):

        @self.stop_before(B.walk, 'walking')
        def f(obj):
            self.assertFalse(obj.__b__)

        @self.stop_after(A.run, 'running A')
        def g(a, ret):
            self.assertNotEqual(ret, 4)

        o = A()
        self.assertEqual(o.run(), 4)
