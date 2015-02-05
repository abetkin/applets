from functools import wraps
import collections
from contextlib import contextmanager, ContextDecorator
import greenlet

from .util import as_context, MISSING, ArgumentsDict


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

def get_from_context(name):
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

    def _get_waiting_greenlet(self, *stop_point):
        # look for a waiting greenlet but return not the
        # greenlet itself but the respective `StopPoint` instance.
        #
        g = self
        while g is not None:
            stop_points = getattr(g, 'stop_points', None)
            if stop_points:
                stop = stop_points[-1]
                if stop == stop_point:
                    stop.g_stopped = self
                    return stop
            g = g.parent

    def __repr__(self):
        return 'MethodGreenlet: %s' % self.__instance__.__class__.__name__ \
                if self.__instance__ is not None else '-'

    def run(self, *args, **kwargs):
        back = MISSING
        waiting = self._get_waiting_greenlet(stop_before, self.__func__)
        if waiting:
            forth = waiting.transform(self.__func__, *args, **kwargs)
            back = waiting.g_current.switch(forth)
        if back is MISSING:
            result = self.__func__(*args, **kwargs)
        else:
            result = back

        waiting = self._get_waiting_greenlet(stop_after, self.__func__)
        if waiting:
            forth = waiting.transform(self.__func__, *args, _result_=result,
                                      **kwargs)
            back = waiting.g_current.switch(forth)
            if back is not MISSING:
                result = back
        return result


class StopPoint(ContextDecorator):

    g_stopped = None

    def __init__(self, stop_func):
        self.func = stop_func
        self.g_current = greenlet.getcurrent()

    def resume(self, result=MISSING): # TODO
        self._clear()
        return self.g_stopped.switch(result)

    def transform(self, func, *args, **kwargs):
        '''Transform the value that is switched from the stopped greenlet.
        '''
        return ArgumentsDict(func, *args, **kwargs)

    def __enter__(self):
        stop_points = self.g_current.__dict__.setdefault('stop_points', [])
        stop_points.append(self)
        return self

    def __exit__(self, *exc):
        self._clear()

    def kill(self):
        g = self.g_stopped
        if g is None:
            return
        while g != self.g_current:
            if g: g.throw()
            g = g.parent

    def _clear(self):
        stop_points = self.g_current.stop_points
        if stop_points and stop_points[-1] == self:
            stop_points.pop()

    def __hash__(self, other):
        return hash((self.__class__, self.func))

    def __eq__(self, other):
        if self.__class__ != type(other):
            if isinstance(other, tuple):
                return other == (self.__class__, self.func)
        return self.func == getattr(other, 'func', MISSING)


class stop_before(StopPoint):
    pass

class stop_after(StopPoint):

    def __init__(self, *_args,
                 args=False, # whether to include arguments in switched value
                 **_kwargs):
        self.include_arguments = args
        super().__init__(*_args, **_kwargs)

    def transform(self, func, *args, _result_=MISSING, **kwargs):
        if not self.include_arguments:
            return _result_
        arguments = super().transform(func, *args, **kwargs)
        return _result_, arguments
