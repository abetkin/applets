from functools import wraps
import collections
from contextlib import contextmanager, ContextDecorator
import greenlet

from .util import as_context, MISSING, BoundArguments


class Applet:

    ctx = 1

# TODO __contains__
'''
Context is an object you can get attributes from by calling it:

    >>> context('some_attr')
'''

class ListContext(list):

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


###########

def from_context(name):
    context = greenlet.getcurrent().context
    value = context(name)
    if value is not MISSING:
        return value
    raise AttributeError(name)

@contextmanager
def context(ctx):
    if isinstance(ctx, type) or not callable(ctx): # FIXME ?
        ctx = as_context(ctx)
    g_current = greenlet.getcurrent()
    old_ctx = getattr(g_current, 'context', MISSING)
    g_current.context = ctx
    yield
    if old_ctx is MISSING:
        del g_current.context
    else:
        g_current.context = old_ctx


class GreenletWrapper:
    '''Wrapper for methods and functions.'''

    __self__ = None

    def __init__(self, func):
        self.__func__ = func

    @property
    def raw(self):
        return self.__func__.__get__(self.__self__)

    def __get__(self, instance, owner):
        if instance is not None:
            self.__self__ = instance
            return self
        return self.__func__

    def __call__(self, *args, **kwargs):
        g = MethodGreenlet(self)
        g.get_context()
        if self.__self__ is not None:
            args = (self.__self__,) + args
        return g.switch(*args, **kwargs)


class MethodGreenlet(greenlet.greenlet):
    ''''''

    def __init__(self, method):
        super().__init__(method.__func__)
        self._method = method
        # all_stop_points attribute is for optimization purposes
        self.all_stop_points = getattr(self.parent, 'all_stop_points', {})

    @property
    def stop_point(self):
        if getattr(self, '_stop_points', None):
            return self._stop_points[-1]

    @stop_point.setter
    def stop_point(self, value, append=True):
        stop_points = self.__dict__.setdefault('_stop_points', [])
        if append:
            stop_points.append(value)
        else:
            stop_points.insert(0, value)
        self.__dict__.setdefault('all_stop_points', {})[value] = value

    @stop_point.deleter
    def stop_point(self):
        del self._stop_points[-1]

    @property
    def __instance__(self):
        return self._method.__self__

    @property
    def __func__(self):
        return self._method.__func__

    def get_context(self):
        if hasattr(self, 'context'):
            return self.context
        g = self
        new = ListContext()
        while g is not None:
            if hasattr(g, 'context'):
                new = new + g.context
                break
            if getattr(g, '__instance__', None) is not None:
                new.append(g.__instance__)
            g = g.parent
        self.context = new
        return new

    def __repr__(self):
        return 'MethodGreenlet: %s' % self.__instance__.__class__.__name__ \
                if self.__instance__ is not None else '-'

    # TODO probably move listening logic out
    def run(self, *args, **kwargs):
        result = MISSING
        stop_point = (stop_before, self.__func__)
        stop_point = self.all_stop_points.get(stop_point)
        if stop_point and stop_point == \
                MethodGreenlet.stop_point.fget(stop_point.g_current):
            stop_point.g_stopped = self
            result = stop_point._switch(*args, **kwargs)
        if result is MISSING:
            result = self.__func__(*args, **kwargs)

        stop_point = (stop_after, self.__func__)
        stop_point = self.all_stop_points.get(stop_point)
        if stop_point and stop_point == \
                MethodGreenlet.stop_point.fget(stop_point.g_current):
            stop_point.g_stopped = self
            switched = stop_point._switch(*args, _result_=result, **kwargs)
            if switched is not MISSING:
                result = switched
        return result


class StopPoint(ContextDecorator):

    g_stopped = None

    def __init__(self, stop_func):
        self.func = stop_func
        self.g_current = greenlet.getcurrent()

    def resume(self, result=MISSING):
        self._clear()
        return self.g_stopped.switch(result)

    def _switch(self, *args, _result_=MISSING, **kwargs):
        self._args = args
        self._kwargs = kwargs
        self._result_ = _result_
        return self.switch(*args, _result_=_result_, **kwargs)

    def switch(self, *args, _result_=MISSING, **kwargs):
        arguments = BoundArguments(self.func, *args, **kwargs)
        return self.g_current.switch(arguments)

    def __enter__(self):
        MethodGreenlet.stop_point.fset(self.g_current, self)
        return self

    def __exit__(self, *exc):
        if exc[0]:
            raise exc[0].with_traceback(exc[1], exc[2])
        self._clear()

    def _clear(self):
        if MethodGreenlet.stop_point.fget(self.g_current) == self:
            MethodGreenlet.stop_point.fdel(self.g_current)

    def get_type(self):
        return self.__class__

    def kill(self):
        g = self.g_stopped
        if g is None:
            return
        while g != self.g_current:
            if g: g.throw()
            g = g.parent

    def __hash__(self):
        return hash((self.get_type(), self.func))

    def __eq__(self, other):
        if isinstance(other, tuple):
            return other == (self.get_type(), self.func)
        if isinstance(other, StopPoint):
            return self.func is other.func \
                    and self.get_type() is other.get_type()


class stop_before(StopPoint):
    pass

class stop_after(StopPoint):

    def __init__(self, *_args, args=False, **_kwargs):
        self.include_arguments = args  # whether to include call arguments
                                       # too in the switched value or just
                                       # the return value
        super().__init__(*_args, **_kwargs)

    def switch(self, *args, _result_=MISSING, **kwargs):
        if not self.include_arguments:
            return self.g_current.switch(_result_)
        arguments = BoundArguments(self.func, *args, **kwargs)
        return self.g_current.switch(_result_, arguments)
