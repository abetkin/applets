from copy import copy
from collections import OrderedDict
from abc import ABCMeta

class Mark(metaclass=ABCMeta):

    collect_into = 'marks'

    def __init__(self, **kwargs):
        self.source_function = None
        self.__dict__.update(kwargs)

    def __call__(self, f):
        self.source_function = f
        return self

    def build(self):
        '''
        Construct an instance from Mark. You should override this.
        '''
        return self

    @classmethod
    def _add_all(cls, marks_dict, klass):
        for key, mark in marks_dict.items():
            build = getattr(klass, 'build_mark', None)
            if build:
                build = build(mark)
            if build is None:
                build = getattr(mark, 'build', None)
                if build:
                    build = build()
            # if build is not None:
            #     mark = build

            # check if klass defines collect_marks_into
            collect_into = getattr(klass, 'collect_marks_into', None)
            if callable(collect_into):
                collect_into = collect_into(mark)
            if collect_into is None:
                collect_into = getattr(mark, 'collect_into', Mark.collect_into)
                if callable(collect_into):
                    collect_into = collect_into()
            _dict = klass._collected.setdefault(collect_into, OrderedDict())
            _dict[key] = build or mark


class CollectMarksMeta(type):
    '''
    The metaclass collects `Mark` instances from the classdict
    and then removes from the class namespace.
    '''

    @classmethod
    def __prepare__(metacls, name, bases, **kwds):
        return OrderedDict()

    def __new__(cls, name, bases, namespace):
        marks_dict = OrderedDict()
        for key, obj in namespace.items():
            if not isinstance(obj, Mark):
                continue
            # make clones if necessary so that all marks
            # were different objects
            if obj in marks_dict.values():
                obj = copy(obj)
            marks_dict[key] = obj

        # clear the namespace
        for _name in marks_dict:
            del namespace[_name]

        namespace['_collected'] = {}
        klass = type.__new__(cls, name, bases, namespace)
        Mark._add_all(marks_dict, klass)
        return klass
