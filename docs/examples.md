# Examples

The examples collection.

---

## Subtest feature

In the standard
library there is nice `unittest` package. It used to have, however, two annoyingly missing features:
running subtests and dropping into debugger on failures. Now there is only one since
the first problem was successfully solved in 3.4 release.

Lets try to reimplement this "subtest" feature
using `gcontext`. For those who haven't read that part of `unittest` documentation,
this is what the original looks like:

    class MyTest(unittest.TestCase):
        def test(self):
            with self.subTest('this will fail'):
                self.assertTrue(False)

Here is the proposed solution. We want subtests to use the same test result their parent does so
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

Now, how this `subTest` is different from the original?                  
First, our subtests are nested,
while in the original version they are not (we benefit from this fact only in `__str__` function).
Also, they are not required to be accessed
from the testcase instance, which allows us to write things like

    class TC(TestCase):

        @subTest('a method')
        def amethod(self):
            self.assertTrue(False)

        def test(self):
            with subTest('hierarchy'):
                with subTest('is honoured'):
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

## "Django filters" enhanced

No, we won't fork django. It will be an "enhanced" version compared to ["Django Filters"](http://abetkin.github.io/declared/examples/#django-filters)
example from the **[declared](http://abetkin.github.io/declared/)**
package. Enhanced is put within the quotation marks because it can turn otherwise if used excessively without need.

In "Django Filters" we have written base classes for filters declaration that can be nested. A filter there is a callable that takes
iterable (a queryset) as a parameter and returns iterable. Let's modify that example, so that it will take queryset from the context
if it's not specified:

    @qsfilter.register
    class FiltersDeclaredMeta(DeclaredMeta, abc.ABCMeta):
        def __repr__(cls):
            return ', '.join(cls._declared_filters.keys())
        
        objects = g.ContextAttr('queryset')

We have added `objects` property to the metaclass so it will be accessible from the filter's class.

Now we can use it in filters' implementations:

    class CascadeFilter(DeclaredFilters):
        @classmethod
        def filter(cls, objects=None):
            if objects is None:
                objects = cls.objects
            for f in cls._declared_filters.values():
                objects = f.filter(objects)
            return objects
    
    class ReduceFilters(DeclaredFilters):
        @classmethod
        def filter(cls, objects=None):
            if objects is None:
                objects = cls.objects
            filters = [f.filter(objects) for f in cls._declared_filters.values()]
            if filters:
                return reduce(cls.operation, filters)
            return objects

Notice the fallback to `cls.objects` if the queryset wasn't passed.

Actually, the queryset is less global than, say, the request object, so the property should not be used often.
The ability to call such routines without arguments should be used in corner cases, when they are hardly accessible and
the routine plays secondary, accesory role. Like in the example below:  

    from declared import declare
    from django.db.models import Q

    class MyFilters(Filter):

        class Fields(Serializer):
            text = CharField()
            title = CharField()

        def __init__(self):
            self.params = self.Fields.deserialize()
            self.process_declared()
        
        @declare()
        def text(self):
            return Q(text__icontains=self.params['text'])
        
We have used `Serializer` class to deserialize `Filter` arguments. It's very convenient that it's `deserialize` function can take no arguments.

Likewise, filtering can play such auxiliary role somewhere else. And the ability to use `queryset` attribute set, say, on the view
can be very convenient.