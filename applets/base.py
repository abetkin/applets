from functools import wraps
import collections
import greenlet

from .util import as_context, MISSING


class Applet:

    ctx = 1

# TODO __contains__
'''
Context is an object you can get attributes from by calling it:

    >>> context('some_attr')
'''


class ListContext(list):

    _wrapped_func = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__instance__ = None

    def __bool__(self):
        # whether context is prepared
        #
        return '__instance__' not in self.__dict__

    def _set_prepared(self):
        if '__instance__' in self.__dict__:
            del self.__instance__

    def __get__(self, instance, owner):
        if instance:
            self.__instance__ = instance
        if self._wrapped_func:
            return self._wrapped_func.__get__(instance)
        return self

    def __call__(self, name):
        for obj in self:
            if not callable(obj):
                obj = as_context(obj)
            value = obj(name)
            if value is not MISSING:
                return value
        return MISSING

    def __add__(self, other):
        if not isinstance(other, list):
            other = list((other,))
        result = ListContext(self)
        result.extend(other)
        return result

    def __radd__(self, other):
        if not isinstance(other, list):
            other = list((other,))
        result = ListContext(other)
        result.extend(self)
        return result


class ContextGreenlet(greenlet.greenlet):

    def __init__(self, run, ctx):
        super().__init__(run)
        self._context = ctx

    @property
    def context(self):
        if self._context:
            return self._context
        g = self
        new = ListContext()
        while not g._context:
            obj = g._context.__instance__
            if obj is not None:
                new.append(obj)
            g = g.parent
            if not hasattr(g, '_context'):
                self._context = new + self._context
                break
        else:
            self._context = new + g._context
        self._context._set_prepared()
        return self._context

    @context.setter
    def context(self, value):
        self._context = value

    @classmethod
    def wrap(cls, func):
        ctx = ListContext()

        @wraps(func)
        def wrapper(*args, **kwargs):
            g = cls(func, ctx)
            return g.switch(*args, **kwargs)

        ctx._wrapped_func = wrapper
        return ctx
