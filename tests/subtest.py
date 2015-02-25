import sys
import unittest
from contextlib import ContextDecorator

import gcontext as g


class TestCase(unittest.TestCase):

    def run(self, result):
        with g.add_context({'result': result}, {'testcase': self}):
            return super().run(result)


class SubTest(unittest.TestCase):

    parent = g.ContextAttr('testcase')

    def __init__(self, description):
        super().__init__()
        self._name = '%s [%s]' % (self.parent, description)

    def __str__(self):
        return self._name

    def runTest(self):
        extype, ex, tb = sys.exc_info()
        if extype:
            raise extype.with_traceback(ex, tb)


class subtest(ContextDecorator):

    result = g.ContextAttr('result')

    def __init__(self, description):
        self._description = description

    def __enter__(self):
        self._case = SubTest(self._description)
        self._context_cm = g.add_context({'testcase': self._case})
        self._context_cm.__enter__()

    def __exit__(self, *exc_info):
        self._context_cm.__exit__(*exc_info)
        self._case.run(self.result)
        return True
