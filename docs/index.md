# gcontext

The global context in use.

---

## Overview

**gcontext** is based on the idea of using the  **threadlocal context**, mostly to address the challenges of writing the traditional
web applications.

The idea of using threadlocals is not new
([flask](http://flask.pocoo.org) is a well-known example). New is the way (actually, two ways) to use them:

#### Attribute lookup

Instances chain that is formed by the global context is used for sequential attribute lookup. 

#### Dynamic pre- and post-execution hooks

Wrapped callables are supplemented with pre- and post-execution hooks that are looked in another global (threadlocal) object. 


---------

Besides being an illustration, the package aims to be 100% tested and production-ready (this part is not true yet).

---------

#### Applied to web development

Though the concept is not related to web, I see it's application mostly there. Why?

The development of web applications has it's specifics. The code there is organized into functions (callables)
that are the handlers for different urls and usually are called views. That callables usually are greatly isolated from each other,
and in most cases this is for the better. Also, usually the development process results in adding new urls, not modifying the logic of existing ones.
This makes those handlers-views some kind of "throw-away" code.

The author's personal experience with web development is
as a developer of backend API with `django` and `django-rest-framework`. Speaking of the latter, many times I found the heavy
Tom Christie's framework staying in my way and felt that something is wrong with it. Although the declarative approach is sometimes
very neat. Not that I chose wrong tools: I have used other frameworks too. And speaking of `django`, it is very nice, I like it.
(Well, with the except for it's testing facilities. Again, they try to enforce logic-heavy "good practises" when it's a throw-away type of activity:
testing).

Still, I have this impression that objects aggregation can be done better and that having some kind of global context can make things easier.

---------

Warning: Only **Python 3** is supported yet.
    
---------

The codebase is **very small** (~300 SLOC), so there will be no API reference, just the narrative documentation.

--------

## The "global" context

There is a "global" context object that represents a stack of objects. It is global in a
sense that it is global to a thread, being actually a threadlocal. Now, that object can be used as
a mapping: an attribute is looked up in the objects stack sequentially starting from it's top.

That object will be called the context and can be retrieved with `gcontext.get_context()`

The objects are pushed and popped from the stack with the help of context managers,
of which the simplest is `add_context`:

    import gcontext as g

    with g.add_context({'name': 'John'})
        print('Hello, %s' % g.get_context()['name'])

The package also provides decorators for callables (methods in the most typical case)
that wrap similar context manager
that can push into the context their arguments (usually we are interested in the bound instance: the first positional argument).
These decorators are instances of `GrabContextWrapper` and use internally the
context manager similar to `add_context`. Let's see the `method` decorator in action:

    class Parent:
        def __init__(self, params):
            self.params = params

        @g.method
        def do_smth(self):
            return Child().will_do_this()

    class Child:
        @g.method
        def will_do_this(self):
            print('I can use %s' % g.get_context()['params'])
            
    >>> Parent('parameters'}).do_smth()
    I can use parameters

Now `Child` can access parent attributes from the context.

Notice that the child's method is also decorated with `g.method`. That is because `g.method` works more complex than `add_context`:
it sets the last added element as pending, and it will be missing from `get_context()` until the next entering in a context modifying 
manager.

This is done to prevent the namespace pollution: it wouldn't be great if an object could access it's own attributes
from the context. In that case you won't be able to write things like

    class Child:
        @property
        def params(self):
            return g.get_context()['params'])

You would get "recursion depth exceeded" error: `params` attribute will be accessed in cycle. In current implementation it is safe.
Actually, there is a
convenience function for such things - `ContextAttr`, that returns a property:

```python
params = g.ContextAttr('params')
```

The property is writable, but the written value won't reflect in the context.
The context is read-only (as a mapping).


----

## Examples

I really wanted to illustrate it first with a non-web example, and I have found one.
Only it turned out to be a little longer than I expected, so I will not place it here. It is [available](examples.md#subTest) from the Examples section.

-----

The second example is regarding the [django-rest-framework](http://www.django-rest-framework.org/). Surprisingly, 
its serialization utilities also use a context. It is a dictionary that logically nested objects pass to each other's `__init__`
method. For example, the `request` object is looked up in the context when it's needed.
What if we could just feed it our context?

    class MySerializer(serializers.Serializer):
        _context = property(lambda self: g.get_context(),
                            lambda self, value: None)

And it works like magic. The implied result from this is that you can use serializers just if
there were `serialize()` and `deserialize()` functions.
You only define fields with a class because it's less verbose than with an `OrderedDict`.
Logically it's a function (of course, in the assumption that we decided to add `request` to "global" context).

Let's make those functions:

    class SerializerError(Exception):
        pass

    class MySerializer(serializers.Serializer):
        
        @classmethod
        def serialize(cls, obj=None):
            if obj is None:
                obj = get_context()['object']
            serializer = cls(obj)
            capture = g.method.as_manager # adds the first passed argument to context
            with capture(serializer):
                return serializer.data
        
        @classmethod
        def deserialize(cls, data=None):
            if data is None:
                data = get_context()['request'].QUERY_PARAMS
            serializer = cls(data=data)
            capture = g.method.as_manager
            with capture(serializer):
                if serializer.is_valid():
                    return serializer.data
                raise SerializerError(serializer.errors)

Actually, capturing the serializer instance with `g.method.as_manager` is not required. I just noticed
that logically nested into the serializer objects (like fields) have that `parent` attribute. Now they can access parent from the context.       
That is the interface I would like to see for serialization: the two classmethods above.

There is a [continuation](examples.md#django-filters-enhanced)  to this in the Examples section:
there you can find similar classes for filter declaration and the implementation of similar classmethods.

--------

## Testing and the interactive shell

Being able to provide context to methods makes possible using from the interactive shell objects that
you couldn't before. For example, you are not required to depend on the request object:

    class Aclass:
        request = g.ContextAttr('request', None)

        @property
        def data(self):
            if self.request is None:
                return g.get_context()['request_data']
            return self.request.QUERY_PARAMS

And then you can write:

```python
with g.add_context({'request_data': {'name': 'John',
                                     'age': '30'}}):
    # ...
    
```

This also can make the testing easier, because it allows running code units isolated
from each other.

Remember it's a mixed blessing though. If abused, it can make your code, inversely, hardly testable,
that will show unreproducible behaviour. The usual precautions for using global variables apply.

---

## The context isolation

Though context modifying managers should guarantee the proper context cleanup even in case of errors,
I think it's required, that, say, handling of two different http requests could be fundamentally isolated,
i.e. would belong to different threadlocals. Speaking of http requests processing, they are usually executed
either in separate threads or processes, so their contexts will be isolated.

Threadlocals in `gcontext` internally rely on [greenlet](http://greenlet.readthedocs.org): `get_context()` calls
`greenlet.getcurrent()` (that will return a different object for different threads).

So, it's enough to execute code in two separate greenlets to garantee they have isolated contexts.

----------

## Pre- and post-execution hooks

We have reached to the second feature of `gcontext`: one can decorate a function and make it aware of the pre- and post-execution hooks.

Now, before the execution, callable will check the threadlocal context and if there is a hook it will execute it, the
same will it do after the execution. Those hooks have access to the function arguments and (for post-hooks) the result value.
If hook's returned value is not `None`, it will overwrite the value returned by the wrapped callable. If a pre-hook returns such a value, the original
the original callable won't get executed.

Now, the point: those decorators that make callables aware of pre- and post-hooks, and the ones that push callable's
attributes into the context - are the same thing: `GrabContextWrapper` instances like `g.method`. The reason for that is the methods that provide context
to others, are usually more important than others - the ones that we likely would want to set hooks for, therefore there is no
need for two decorators.

Let's see an example:

    from itertools import count, islice
    import gcontext as g

    class Counter:

        def __init__(self):
            self._counter = islice(count(), 10)

        def __iter__(self):
            return self

        @g.function
        def __next__(self):
            return next(self._counter)


    def upper_bound(value):
        @g.post_hook(Counter.__next__)
        def hook(counter, ret):
            return ret % value
        return hook

    with upper_bound(5):
        for i in Counter():
            print(i)
 
It prints numbers from 0 to 4 and then once again. Note that we've decorated `__next__` with `g.function`
so it will add nothing to context, but we could use `g.method` as well.

`gcontext` knows about two types of hooks: **unordered** and **ordered** ones. By default hooks are unordered and are maintained with a dict.
But sometimes you want to force their order: for example, in a testcase hooks may represent just some assertions and you want an error to be raised
if the test hooks order differs from the expected.

An example for this:

    from random import randint
    import gcontext as g

    class Egg:
        __init__ = g.function(object.__init__)

    class Chicken:
        @g.function
        def __init__(self, color):
            self.color = color

        def lay_eggs(self):
            return [Egg() for i in range(randint(1, 4))]


    class Test(g.TestCase):

        def test(self):

            @self.stop_before(Egg.__init__, 'Waiting for an egg')
            def _egg(egg):
                pass

            @self.stop_after(Chicken.__init__, 'Waiting for a chicken')
            def _chicken(chicken, color, ret=None):
                '%s chicken' % chicken.color
                self.assertIs(ret, None)

            Chicken('yellow').lay_eggs()

This test fails when being run with `unittest`: it complains that `_chicken` hook hadn't been executed.
Apparently, the actual order of things differs from the expected...            
`stop_before` and `stop_after` are `unittest` subtests
(regular ones, if you've read the first example, forget it).

*Note:* Dynamic hooks are a powerful mechanism, that, of course, was not designed just to define  pre- and post-execution
logic. You can do that with usual wrappers, or with inheritance. Still, they are absolutely usable for that purposes:

```python
with post_hook(func, hook_func):
    main()
```

You can also regard those hooks as breakpoints that can be used not only for debugging. Indeed, they can 
raise an exception and pass any data with it. `g.exit_before` and `g.exit_after` are the examples of those:

```python
with g.exit_after(some_callable) as exc:
    some_scenario()
print('callable returned %s' % exc.ret)
send_scenario_the_other_way()
```

What is the motivation behind all this?

The idea is to make some functions "special". In the most cases they are methods, bound to their instances. 
Suppose such an instance with the respective method to be a logical unit of an application (or of an url handler,
if speaking about web applications).
The examples of such units may be authorization, serialization, filtering. 
In `django-rest-framework` all these are represented with instances of separate classes, so kind of are regarded as separate units anyway.

The hooks provide access to these "application units". `exit_*` hooks may be seen as some primitive form of interaction with them.
Although, there hasn't been (yet) any work done in `gcontext` regarding facilities for the interactive work (using in the interactive python shells).

But for now you can write:

    with exit_after(InterestingUnit.main) as ex: 
        test_client.post('/some/url')

    >>> print('Unit %s returned %s ' % (ex.args[0], ex.ret))
   
---------

And for the final words..

##  New kind of "Browsable API"

What is written below is just some food for thought, it doesn't have any specific implementation in `gcontext`.

Probably, you know this [feature](http://www.django-rest-framework.org/topics/browsable-api/) of `django-rest-framework`, that is called "browsable interface". Except for some introspecting capabilities
like extracting docstrings, it acts like a `curl`-like tool with a web interface. But, unlike `curl`-like tools, since that browsable interface logic was mixed into the framework's
base code, hypothetically you can get an unrelated to the browsable interface functionality break because of it.
I didn't track in detail how much things changed with the 3.0 release, but as I understand, there were no fundamental changes.

What if that "api browser" could browse to an url and a specific application unit (like `test_client` did in the snippet above), that contains heavy and the principal logic for that
url? Yes, it will be a python object, so what? [ipython](www.ipython.org), for example, has rich tools to interact with such objects from the
web interface. Such objects can have an html representation, be interacted with from javascript, and hypothetically can be usable not only for developers.

Let me give you a real life example. Suppose an API url has a complicated queryset filtering logic, with a quite long specs defining the desired
behavior. Besides that everything is trivial. I have a filtering class that does all the logic.
As a developer, I would like to have a quick access to the instance of that class, and to it's methods from the interactive shell.
That would really be a "big win".

In `django` we have the admin interface, that is built for the content managers (and other managers), but is used by everyone. Why not to have
such a "developer interface" that hopefully some time will be usable by other people?
