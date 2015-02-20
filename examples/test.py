from subtest import TestCase, subtest
import gcontext as g

class TC(TestCase):



    def test(self):

        with subtest('AAA'):
            with subtest('BBB'):
                self.assertFalse(1)
        func()

def case():
    return g.get_context()['testcase']

@subtest('description')
def func():
    case().assertTrue(0)
