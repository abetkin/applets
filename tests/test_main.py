# coding: utf-8
from g_context.base import method, function, pre_hook, post_hook
from g_context.base import context, add_context
from g_context.util import case

class A:
    a = 1

    @method
    def run(self):
        return B().run()


class B:
    a= 54

    @method
    def run(self):
        return context['a']

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
