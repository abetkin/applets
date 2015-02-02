# coding: utf-8
from applets.base import ContextGreenlet
from applets import get_from_context
class A:
    a = 1

    # context = (to set)

    @ContextGreenlet.wrap
    def run(self):
        return B().run()

class B:

    @ContextGreenlet.wrap
    def run(self):
        return get_from_context('a')
o = A()
print(o.run())
