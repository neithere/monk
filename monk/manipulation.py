# -*- coding: utf-8 -*-
#
#    Monk is a lightweight schema/query framework for document databases.
#    Copyright © 2011  Andrey Mikhaylenko
#
#    This file is part of Monk.
#
#    Monk is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Monk is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with Monk.  If not, see <http://gnu.org/licenses/>.
"""
Data manipulation
=================
"""
import types


class ValueMerger(object):
    def __init__(self, spec, value, orig_value):
        self.spec = spec
        self.value = value
        self.orig_value = orig_value

    def check(self):
        return False

    def process(self):
        return self.value


class TypeMerger(ValueMerger):
    def check(self):
        if isinstance(self.value, type):
            return True

    def process(self):
        # there's no default value for this key, just a restriction on type
        return None


class DictMerger(ValueMerger):
    def check(self):
        if isinstance(self.value, dict) and \
            (self.spec == dict or isinstance(self.spec, dict)):
            return True

    def process(self):
        return merged(self.spec or {}, self.value)


class ListMerger(ValueMerger):
    def check(self):
        if isinstance(self.value, list) and \
            (self.spec == list or isinstance(self.spec, list)):
            return True

    def process(self):
        item_spec = self.spec[0] if self.spec else None
        if isinstance(item_spec, type):
            return []
        elif isinstance(item_spec, dict):
            # list of dictionaries
            # FIXME `value` was prematurely merged, refactor this
            value = self.orig_value or []
            return [merged(item_spec, item) for item in value]
        elif item_spec == None:
            # any value is accepted as list item
            return self.value
        else:
            # probably default list item like [1]
            return self.value


class FuncMerger(ValueMerger):
    def check(self):
        func_types = types.FunctionType, types.BuiltinFunctionType
        if isinstance(self.spec, func_types):
            return True

    def process(self):
        # default value is obtained from a function with no arguments;
        # (It is expected that the callable does not have side effects)
        if hasattr(self.value, '__call__'):
            # FIXME this is unreliable: the value may be already
            # a result of calling the function from spec which, in
            # turn, can be callable. Instead of checking for __call__
            # we should check if the value was obtained from data or
            # from the spec. This is problematic at the moment because
            # nested structures are simply assigned to `value` if
            # `value` is None or is not in the data, and *then* the
            # structure is recursively merged (at which point the
            # information on the source of given chunk of data is lost)
            return self.value()
        else:
            return self.value


VALUE_MERGERS = TypeMerger, DictMerger, ListMerger, FuncMerger


def merge_value(spec, value):
    orig_value = value
    value = spec if value is None else value
    for merger_class in VALUE_MERGERS:
        merger = merger_class(spec, value, orig_value)
        if merger.check():
            return merger.process()
    # some value from spec that can be checked for type
    return value


def merged(spec, data, value_processor=None):
    """ Returns a dictionary based on `spec` + `data`.

    Does not validate values. If `data` overrides a default value, it is
    trusted. The result can be validated later with
    :func:`~monk.validation.validate_structure`.

    Note that a key/value pair is added from `spec` either if `data` does not
    define this key at all, or if the value is ``None``. This behaviour may not
    be suitable for all cases and therefore may change in the future.

    :param spec:
        `dict`. A document structure specification.
    :param data:
        `dict`. Overrides some or all default values from the spec.
    """
    result = {}

    for key in set(spec.keys() + data.keys()):
        if key in spec:
            value = merge_value(spec[key], data.get(key))
        else:
            # never mind if there are nested structures: anyway we cannot check
            # them as they aren't in the spec
            value = data[key]

        if value_processor:
            value = value_processor(value)

        result[key] = value

    return result
