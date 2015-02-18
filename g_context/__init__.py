import greenlet
threadlocal = greenlet.getcurrent()

from .base import context
