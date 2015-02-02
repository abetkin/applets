# coding: utf-8
from applets.base import ContextGreenlet
from applets import get_from_context, context
from applets.util import case

class A:
    a = 1

    @ContextGreenlet.wrap
    def run(self):
        return B().run()


class B:

    @ContextGreenlet.wrap
    def run(self):
        return get_from_context('a')


o = A()
case.assertEqual(o.run(), 1)

with context({'a': 2}):
    case.assertEqual(B().run(), 2)
