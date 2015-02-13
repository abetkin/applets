from copy import copy
from collections import OrderedDict
from abc import ABCMeta

class Mark(metaclass=ABCMeta):

    collect_into = '_declared_marks'



class DeclaredMeta(type):
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

        klass = type.__new__(cls, name, bases, namespace)
        cls._add_all(marks_dict, klass)
        return klass

    @classmethod
    def _add_all(mcls, marks_dict, klass):
        for key, mark in marks_dict.items():
            collect_into = getattr(mark, 'collect_into', Mark.collect_into)
            if callable(collect_into):
                collect_into = collect_into()
            if not collect_into in klass.__dict__:
                setattr(klass, collect_into, OrderedDict([(key, mark)]))
            else:
                getattr(klass, collect_into)[key] = mark
