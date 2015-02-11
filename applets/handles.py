import types
from contextlib import ContextDecorator
import greenlet

from .util import MISSING, BoundArguments, ExplicitNone


# TODO __repr__
class Handle:

    g_stopped = None
    # handle_type = not_implemented

    def __init__(self, stop_func):
        self.func = stop_func
        if not isinstance(self.func, types.FunctionType):
            try:
                self.func = self.func.__func__
            except AttributeError:
                self.func = self.func.fget
        self.g_current = greenlet.getcurrent()
        self.activate()

    @property
    def handles(self):
        return self.g_current.__dict__.setdefault('_handles', [])

    def activate(self):
        self.handles.append(self)

    def is_active(self):
        if self.handles:
            return self.handles[-1] == self

    def switch(self, *args, _result_=MISSING, **kwargs):
        raise NotImplementedError()

    def _switch(self, *args, **kwargs):
        self.g_stopped = greenlet.getcurrent()
        try:
            return self.switch(*args, **kwargs)
        finally:
            self.handles.remove(self)

    def __hash__(self):
        return hash((self.handle_type, self.func))

    def __eq__(self, other):
        if isinstance(other, tuple):
            return other == (self.handle_type, self.func)
        if isinstance(other, Handle):
            return self.func is other.func \
                    and self.handle_type is other.handle_type


class HandleAfter:
    pass

class HandleBefore:
    pass

# rename ?
class InteractiveHandle(Handle, ContextDecorator):

    resumed = MISSING

    def resume(self, result=MISSING):
        assert self.resumed is MISSING, "Already resumed"
        if self.g_stopped:
            self.resumed = self.g_stopped.switch(result)
            return self.resumed

    def switch(self, *args, _result_=MISSING, **kwargs):
        arguments = BoundArguments(self.func, *args, **kwargs)
        return self.g_current.switch(arguments)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        if exc[0]:
            raise exc[0].with_traceback(exc[1], exc[2])
        if self.resumed is MISSING:
            self.resume()

    def kill(self):

        def to_kill(g=self.g_stopped):
            while g is not None and g != self.g_current:
                yield g
                g = g.parent
        for g in reversed(list(to_kill())):
            g.throw()
        # TODO check that handles are parent greenlets


class stop_before(InteractiveHandle):
    handle_type = HandleBefore

class stop_after(InteractiveHandle):
    handle_type = HandleAfter

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


class FunctionHandle(Handle):
    # via decorating a function

    def __call__(self, handler_func):
        self.handler_func = handler_func
        return handler_func

    def activate(self):
        self.handles.insert(0, self)

    def switch(self, *args, _result_=MISSING, **kwargs):
        if _result_ is not MISSING:
            kwargs['_result_'] = _result_
        ret = self.handler_func(*args, **kwargs)
        if ret is None:
            ret = MISSING
        elif ret is ExplicitNone:
            ret = None
        return ret

class handler_before(FunctionHandle):
    handle_type = HandleBefore

class handler_after(FunctionHandle):
    handle_type = HandleAfter


def resume(value=MISSING):
    g_current = greenlet.getcurrent()
    handles = getattr(g_current, '_handles', None)
    assert handles, "Nothing to resume"
    return handles[-1].resume(value)


def resume_all():
    g_current = greenlet.getcurrent()
    value = None
    while getattr(g_current, '_handles', None):
        value = resume()
    return value
