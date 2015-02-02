import greenlet
from functools import wraps
import IPython

frame = None

def green(f):
    @wraps(f)
    def wrapper(*args, **kw):
        import sys
        global frame
        frame = sys._getframe()
        g = greenlet.greenlet(f)
        return g.switch(*args, **kw)
    return wrapper

g = greenlet.getcurrent()

class A:

    @green
    def run(self, a):
        import ipdb
        ipdb.set_trace()
        assert greenlet.getcurrent().parent is g
        return a

if __name__ == '__main__':
    o = A()
    o.run(3)
