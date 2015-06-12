
from collections import ChainMap

class Context(ChainMap):
    
    def __missing__(self):
        # use anonymous instances
        raise NotImplementedError