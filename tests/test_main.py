# coding: utf-8
from gcontext import method, function, pre_hook, post_hook
from gcontext import get_context, add_context, ContextAttr
from util import case

class A:
    a = 1

    @method
    def run(self):
        return B().run()


class B:
    a= 54

    @method
    def run(self):
        return get_context().parent['a']

o = A()
case.assertEqual(o.run(), 1)

with add_context({'a': 2}):
    case.assertEqual(B().run(), 2)


@post_hook(A.run)
def post(o, ret):
    case.assertEqual(ret, 1)

@pre_hook(B.run)
def pre(obj):
    case.assertIsInstance(obj, B)

with post, pre:
    o = A()
    case.assertEqual(o.run(), 1)
