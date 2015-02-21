# gcontext

The global context in use.

---

## Overview

The goal of `gcontext` is to illustrate the concept of a **global context** (actually, threadlocal).

The idea of using threadlocals is not new
(e.g. `flask` has them), new is the way to use them. Actually, two ways: firstly, global "nested" context is used for **attribute lookup**.
Secondly, it allows **setting pre- and post-execution hooks dynamically** for the respectively decorated callables.

Besides being an illustration, the package aims to be 100% tested and production-ready (this part is not true yet). 

Though the concept is not related to web, I see it's application mostly there. Why?
Well, the development of web applications has it's specifics. The code there is organized into functions (callables)
that are the handlers for different urls and usually are called views. That callables usually are greatly isolated from each other,
and in most cases this is for the better. Also usually development process results in adding new urls, not modifying the logic of existing ones. This makes those handlers-views some kind of "throw-away" code. Of course, it's not the only thing specific to web development.

The author's personal experience with web development is
as a developer of the backend API with `django` and `django-rest-framework`. Speaking of the latter, many times I found the heavy
Tom Christie's framework staying in my way and felt that something is wrong with it. Although the declarative approach is sometimes
very neat. Not that I chose wrong tools: I have used other frameworks too. And speaking of `django`, it is very nice, I like it.
(Well, with the except for it's testing facilities. Again, they try to enforce logic-heavy "good practises" when it's a throw-away type of activity:
testing). 


The codebase is **very small** (~300 SLOC), so there will be no API reference, just the narrative documentation.

-----------

## The "global" context

There is a "global" context object that represents a stack of objects. It is global in
sense that it is a threadlocal, i.e. is global to a thread. Now, we'll use that object as
a mapping: an attribute is looked up in the objects starting from the top of the stack.

That object will be called the context and can be retrieved with `gcontext.get_context()`

The objects are pushed and popped from the stack with the help of context managers,
of which the simplest is `add_context`: it just pushes (temporarily) objects in the context:

    import gcontext as g

    @g.add_context({'name': 'John'})
    def hello():
        print('Hello %s' % g.get_context()['name'])

The package also provides decorators for callables (methods in the most typical case)
that can push into the context their arguments (usually we are interested in the bound instance).
These decorators are instances of `GrabContextWrapper` and use internally the
context manager similar to `add_context`. Let's see `method` decorator in action:

    class Parent:
        def __init__(self, params):
            self.params = params

        @g.method
        def do_smth(self):
            return Child().will_do_this()

    class Child:
        def will_do_this(self):
            print('I can use %s' % g.get_context()['params'])

Now child can access parent attributes from the context. `Parent` instances, however,
also see in the context their own attributes - not very
good: it's an unneeded namespace pollution. That's why there exists the notion of
parent context. The logic behind this is simple: the last added element
remains pending until the next entering in such context manager.

Actually, the parent context is what you get with `get_context`. So, the code above will not
work:

```python
>>> Parent('some data'}).do_smth()
Key Error: 'params'
```

That's because `will_do_this` is on the the same context "nesting level" as `do_smth`.
Let's make the child method execute in the child context:

    class Child:

        @g.method
        def will_do_this(self):
            print('I can use %s' % g.get_context()['params'])

    >>> Parent('parameters'}).do_smth()
    I can use parameters

The context namespace doesn't get polluted, e.g. you can write:

    class Child:
        @property
        def params(self):
            return g.get_context()['params'])

Though `params` property accesses `params` attribute from context, you don't get the "recursion depth exceeded" error.
Actually, the package provides a
convenience function `ContextAttr` that returns a property:

```python
params = g.ContextAttr('params')
```

The property is writable, but the written value won't reflect in the context.
The context is read-only (as a mapping).


----

## Examples

I really wanted to illustrate it firstly with non-web example, but it turned out to be a little longer than I expected.
You can find it in the **[Examples](examples.md)** section (it goes first).

The first example will be from the non-web domain. Let's take a look at the `unittest` package.

The second example is regarding [django-rest-framework](http://www.django-rest-framework.org/). Surprisingly, 
its serialization utilities also use a context. It is a dictionary that logically nested objects pass to each other's `__init__`
method. For example, the `request` object is looked up in the context when it's needed.
What if we could just feed it our context?

    class MySerializer(serializers.Serializer):
        _context = property(lambda self: g.get_context(),
                            lambda self, value: None)

And it works just like magic. The implied result from this is that you can use serializers just if
there were `serialize()` and `deserialize()` functions.
You only define fields with a class because it's less verbose than with an `OrderedDict`.
Logically it's a function (of course, in the assumption that we decided to make `request` object "global").

Let's make those functions:

    class SerializerError(Exception):
        pass

    _context = property(lambda self: g.get_context(), lambda self, value: None)

    class ListSerializer(serializers.ListSerializer):
        _context = _context
        
    class MySerializer(serializers.Serializer):
        _context = _context
        
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
            
        class Meta:
            list_serializer_class = ListSerializer

Actually, capturing the serializer instance with `g.method.as_manager` is not required. I just noticed
that logically nested into the serializer objects (like fields) have that `parent` attribute. Now they can access parent from the context.       
That is the interface I would like to see for serialization: the two classmethods above.

---

## Pre- and post-execution hooks
