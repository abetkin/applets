from functools import wraps
from itertools import islice
from contextlib import contextmanager
from collections import Mapping
from copy import copy

from .util import Missing, ExplicitNone, threadlocal
from ._signals import pre_signal, post_signal

from .core import Context


# def ContextAttr(name, default=Missing):
#
#     def fget(self):
#         dic = self.__dict__.setdefault('_contextattrs', {})
#         context = get_context()
#         if name in dic:
#             return dic[name]
#         if default is not Missing:
#             return context.get(name, default)
#         try:
#             return context[name]
#         except KeyError:
#             raise AttributeError(name)
#
#     def fset(self, value):
#         dic = self.__dict__.setdefault('_contextattrs', {})
#         dic[name] = value
#
#     return property(fget, fset)
#




@contextmanager
def add_context(mapping):
    context = get_context()
    # TODO if empty - replace
    context.maps.insert(0, mapping)
    try:
        yield
    except Exception as ex:
        ex.gctx = copy(context)
        raise ex
    finally:
        del context.maps[0]


# g.ex

class Ex:
    pass



def get_context():
    # Usually to be called from objects as properties
    #
    context = threadlocal().setdefault('context', Context())
    return context



from blinker import signal




class ContextGrabber:

    def __init__(self, get_context_object):
        self.get_context_object = get_context_object

    def as_manager(self, *run_args, **run_kwargs):
        instance = self.get_context_object(*run_args, **run_kwargs)
        return add_context(instance)

    
    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            with self.as_manager(*args, **kwargs):
                # TODO try..except
                pre_exec.send(args=args, kwargs=kwargs)
                ret = func(*args, **kwargs)
                post_exec.send(args=args, kwargs=kwargs)
                return ret

        pre_exec = pre_signal(wrapper)
        post_exec = post_signal(wrapper)

        return wrapper


class grabctx:

    def __init__(*args, **kwargs):
        1



def grab_instance(name):
    @ContextGrabber
    def grabber(*args, **kwargs):
        return {name: args[0]}
    return grabber
