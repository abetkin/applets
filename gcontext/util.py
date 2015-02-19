import greenlet

threadlocal = greenlet.getcurrent()

def threadlocal():
    gcurrent = greenlet.getcurrent()
    return gcurrent.__dict__.setdefault('_gcontext', {})

class Missing:
    pass

class ExplicitNone:
    pass
