from contextlib import contextmanager

class Exit(Exception):
    
    def __init__(self):
        1
        # func, args, kwargs

# Ex ??


def _stop_now():
    1

@contextmanager
def stop_at(func):
    try:
        yield ex # ??
    except Exception as ex:
        1

def stop_after(func):
    1