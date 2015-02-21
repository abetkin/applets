# Examples

The examples collection.

---

## subTest

An example from the domain of application testing. In the standard
library there is nice `unittest` package. It used to have, however, two annoyingly missing features:
running subtests and dropping into debugger on failures. Now there is only one since
the first problem were successfully solved in 3.4 release.

Lets be for a moment `unittest` authors and try to implement this "subtest" feature
using `gcontext`. For those who haven't read that part of `unittest` documentation,
this is what the original looks like:

    class MyTest(unittest.TestCase):
        def test(self):
            with self.subTest('this will fail'):
                self.assertTrue(False)

Here is the proposed solution. The tests are run with the result argument, that is
created by a test runner. To make subtests use the same result their parent does
we push it into the context. Also we push `{'testcase': self}`: subtests should know
their parents.

    import gcontext as g

    class TestCase(unittest.TestCase):

        def run(self, result):
            with g.add_context({'result': result, 'testcase': self}):
                return super().run(result)

Here is our subtest class:

    class SubTest(unittest.TestCase):

        parent = g.ContextAttr('testcase')

        def __init__(self, description):
            super().__init__()
            self._name = '%s [%s]' % (self.parent, description)

        def __str__(self):
            return self._name

        def runTest(self):
            extype, ex, tb = sys.exc_info()
            if extype:
                raise extype.with_traceback(ex, tb)

It's `runTest` does almost nothing: the actual testing code will be run inside the `subTest`
context manager. It just reraises the last exception that will now be caught by
`TestCase.run`. Now namely the context manager:


    class subTest(ContextDecorator):

        result = g.ContextAttr('result')

        def __init__(self, description):
            self._description = description

        def __enter__(self):
            self._case = SubTest(self._description)
            self._context_cm = g.add_context({'testcase': self._case})
            self._context_cm.__enter__()

        def __exit__(self, *exc_info):
            self._context_cm.__exit__(*exc_info)
            self._case.run(self.result)
            return True


All subtests also push `{'testcase': self}` to make a hierarchy.

Now, how is this `subTest` different from the original?                  
First, our subtests are nested,
while in the original version they are not (we benefit from this fact only in `__str__` function).
Also and they are not required to be accessed
from the testcase instance, which allows to write things like

    class TC(TestCase):

        @subTest('a method')
        def amethod(self):
            self.assertTrue(False)

        def test(self):
            with subTest('hierarchy'):
                with subTest('is honored'):
                    self.assertFalse(True)
            afunction()
            self.amethod()

    def case():
        return g.get_context()['testcase']

    @subTest('a function')
    def afunction():
        case().assertEqual(1 + 1, 2)

*Note:* This is just an example, it doesn't have any real advantages for writing unit tests.

---
