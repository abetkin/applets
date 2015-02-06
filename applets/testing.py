from functools import wraps
from .base import stop_before, stop_after

def break_before(where):
    with stop_before(where):
        1
    def decorate(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            1
    return decorate
