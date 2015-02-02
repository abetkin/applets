import collections

class MISSING:
    pass

def as_context(obj):
    def lookup(attr):
        if isinstance(obj, collections.Mapping):
            return obj.get(attr, MISSING)
        return getattr(obj, attr, MISSING)
    return lookup
