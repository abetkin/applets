# coding: utf-8
from applets.base import Greenlet
from applets import from_context, context
from applets.util import case

class A:
    a = 1

    @Greenlet
    def run(self):
        return B().run()


class B:

    @Greenlet
    def run(self):
        return from_context('a')


o = A()
case.assertEqual(o.run(), 1)

with context({'a': 2}):
    case.assertEqual(B().run(), 2)
    case.assertEqual(A().run(), 1)
