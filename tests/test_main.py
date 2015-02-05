# coding: utf-8
from applets.base import GreenletWrapper
from applets import from_context, context
from applets.util import case

class A:
    a = 1

    @GreenletWrapper
    def run(self):
        return B().run()


class B:

    @GreenletWrapper
    def run(self):
        return from_context('a')


o = A()
case.assertEqual(o.run(), 1)

with context({'a': 2}):
    case.assertEqual(B().run(), 2)
    case.assertEqual(A().run(), 1)
