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
            pass

        @self.stop_after(A.run, 'running A')
        def g(a, ret):
            self.assertEqual(ret, 4)

        o = A()
        self.assertEqual(o.run(), 4)

# subTest example #

from subtest import TestCase, subtest
import gcontext as g

class TC(TestCase):

    def test(self):

        with subtest('AAA'):
            with subtest('BBB'):
                self.assertFalse(0)
        func()

def case():
    return g.get_context()['testcase']

@subtest('description')
def func():
    case().assertTrue(1)
