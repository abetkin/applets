import greenlet
# from .base import ContextGreenlet

from .util import MISSING

def get_from_context(name):
    context = greenlet.getcurrent().context
    value = context(name)
    if value is MISSING:
        raise AttributeError(name)
