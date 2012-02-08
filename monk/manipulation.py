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

.. attribute:: VALUE_MERGERS

    Default sequence of mergers:

    * :class:`TypeMerger`
    * :class:`DictMerger`
    * :class:`ListMerger`
    * :class:`FuncMerger`
    * :class:`AnyMerger`

"""
import types


class ValueMerger(object):
    """ Base class for value mergers.
    """
    def __init__(self, spec, value):
        self.spec = spec
        self.value = value

    def check(self):
        """ Returns ``True`` if this merger can handle given spec/value pair,
        otherwise returns ``False``.

        Subclasses must overload this method.
        """
        raise NotImplementedError  # pragma: nocover

    def process(self):
        """ Returns a merged version or `self.spec` and `self.value`.

        Subclasses must overload this method.
        """
        raise NotImplementedError  # pragma: nocover


class TypeMerger(ValueMerger):
    """ Type definition. Preserves empty values.
    Example::

        >>> TypeMerger(int, None).process()
        None
        >>> TypeMerger(int, 123).process()
        123

    """
    def check(self):
        return isinstance(self.spec, type)

    def process(self):
        # there's no default value for this key, just a restriction on type
        return self.value


class DictMerger(ValueMerger):
    """ Nested dictionary.
    Example::

        >>> DictMerger({'a': 123}, {}).process()
        {'a': 123}
        >>> DictMerger({'a': 123}, {'a': 456}).process()
        {'a': 456}

    """
    def check(self):
        return self.spec == dict or isinstance(self.spec, dict)

    def process(self):
        if self.value is not None and not isinstance(self.value, dict):
            # bogus value; will not pass validation but should be preserved
            return self.value
        return merged(self.spec or {}, self.value or {})


class ListMerger(ValueMerger):
    """ Nested list.
    """
    def check(self):
        return self.spec == list or isinstance(self.spec, list)

    def process(self):
        item_spec = self.spec[0] if self.spec else None
        if isinstance(item_spec, type):
            if self.value and len(self.spec) == 1:
                return self.value
            else:
                return []
        elif isinstance(item_spec, dict):
            # list of dictionaries
            if self.value:
                return [merged(item_spec, item) for item in self.value]
            else:
                return []
        elif item_spec == None:
            # any value is accepted as list item
            return self.value
        else:
            # probably default list item like [1]
            return self.value


class FuncMerger(ValueMerger):
    """ Default value is obtained from a function with no arguments.
    It is expected that the callable does not have side effects.
    Example::

        >>> FuncMerger(lambda: 123, None).process()
        123
        >>> FuncMerger(lambda: 123, 456).process()
        456

    """
    def check(self):
        func_types = types.FunctionType, types.BuiltinFunctionType
        return isinstance(self.spec, func_types)

    def process(self):
        if self.value is None:
            return self.spec()
        else:
            return self.value


class AnyMerger(ValueMerger):
    """ Any value from spec that can be checked for type.
    """
    def check(self):
        return True

    def process(self):
        if self.value is None:
            return self.spec
        else:
            return self.value


VALUE_MERGERS = TypeMerger, DictMerger, ListMerger, FuncMerger, AnyMerger


def merge_value(spec, value, mergers):
    """ Returns a merged value based on given spec and data, using given
    sequence of mergers.

    The mergers are expected to be subclasses of :class:`ValueMerger`.
    They are polled one by one; the first one that agrees to process given
    value is used to produce the result.

    Example::

        >>> merge_value({'a': 123}, {}, [DictMerger])
        {'a': 123}
        >>> merge_value({'a': 123}, {'a': 456}, [DictMerger])
        {'a': 456}

    """
    for merger_class in mergers:
        merger = merger_class(spec, value)
        if merger.check():
            return merger.process()
    return value


def merged(spec, data, mergers=VALUE_MERGERS):
    """ Returns a dictionary based on `spec` + `data`.

    Does not validate values. If `data` overrides a default value, it is
    trusted. The result can be validated later with
    :func:`~monk.validation.validate_structure`.

    Note that a key/value pair is added from `spec` either if `data` does not
    define this key at all, or if the value is ``None``. This behaviour may not
    be suitable for all cases and therefore may change in the future.

    You can fine-tune the process by changing the list of mergers.

    :param spec:
        `dict`. A document structure specification.
    :param data:
        `dict`. Overrides some or all default values from the spec.
    :param mergers:
        `sequence`. An ordered series of :class:`ValueMerger` subclasses.
        Default is :attr:`VALUE_MERGERS`. The mergers are passed to
        :func:`merge_value`.
    """
    result = {}

    if not isinstance(data, dict):
        raise TypeError('data must be a dictionary')

    for key in set(spec.keys() + data.keys()):
        if key in spec:
            value = merge_value(spec[key], data.get(key), mergers=mergers)
        else:
            # never mind if there are nested structures: anyway we cannot check
            # them as they aren't in the spec
            value = data[key]

        result[key] = value

    return result
