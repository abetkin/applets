import greenlet
from contextlib import contextmanager
# from .base import ContextGreenlet

from .util import MISSING, as_context

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
    g_current._context = ctx
    yield
    if old_ctx is MISSING:
        del g_current._context
    else:
        g_current._context = old_ctx
