import gcontext as g

class Factorial:
    def __init__(self, n=None):
        if n is not None:
           self.n = n

    n = g.ContextAttr('n')
    result = g.ContextAttr('result', 1)

    @g.method
    def get(self):
        if self.n:
            self.result *= self.n
            self.n -= 1
            return Factorial().get()
        return self.result

from util import case

for i in range(5):
    case.assertEqual(Factorial(5).get(), 120)
