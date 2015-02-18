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

# stop_after(A.run)
# stop_before(B.run)

# o = A()
# o.run()
# # case.assertEqual(resume(), 1)
# # case.assertEqual(resume(), 1)
# case.assertEqual(resume_all(), 1)
