from functools import wraps
import collections
from contextlib import contextmanager, ContextDecorator
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

    def __init__(self, method, # stop_before=None, stop_after=None
                ):
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

    def _check(self, stop_where='stop_before'):
        g = self
        func = self.__func__
        while g is not None:
            if getattr(g, stop_where, None) == func:
                return g
            g = g.parent

    def __repr__(self):
        return 'MethodGreenlet: %s' % self.__instance__.__class__.__name__ \
                if self.__instance__ is not None else '-'

    def run(self, *args, **kwargs):
        waiting = self._check('stop_before')
        result = MISSING
        if waiting:
            waiting.paused_greenlet = self
            result = waiting.switch(self.__instance__, kwargs) # TODO
        if result is MISSING:
            result = self.__func__(*args, **kwargs)

        waiting = self._check('stop_after')
        if waiting:
            waiting.paused_greenlet = self
            switched = waiting.switch(result, kwargs) # TODO
            # if switched is not MISSING:
            #     result = switched
        return result


class stop_at(ContextDecorator):

    ATTRIBUTE = None

    def __init__(self, where, kill=True):
        self.func = where
        self.kill_on_exit = kill
        self.g_current = greenlet.getcurrent()

    def __enter__(self):
        try:
            self.old_value = getattr(self.g_current, self.ATTRIBUTE)
        except AttributeError:
            pass
        setattr(self.g_current, self.ATTRIBUTE, self.func)
        return self

    def __exit__(self, *exc):
        self._reset_old_value()
        if self.kill_on_exit:
            self._kill()

    def _kill(self):
        paused = getattr(self.g_current, 'paused_greenlet', None)
        if paused is None:
            return
        del self.g_current.paused_greenlet
        while paused != self.g_current:
            if paused:
                paused.throw()
            paused = paused.parent

    def resume(self, result=MISSING): # TODO
        self._reset_old_value()
        paused = self.g_current.paused_greenlet
        del self.g_current.paused_greenlet
        return paused.switch(result)

    def _reset_old_value(self):
        if hasattr(self, 'old_value'):
            setattr(self.g_current, self.ATTRIBUTE, self.old_value)
            del self.old_value
        try:
            delattr(self.g_current, self.ATTRIBUTE)
        except: pass


class stop_before(stop_at):
    ATTRIBUTE = 'stop_before'

class stop_after(stop_at):
    ATTRIBUTE = 'stop_after'
