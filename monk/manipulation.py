# -*- coding: utf-8 -*-
#
#    Monk is an unobtrusive data modeling, manipulation and validation library.
#    Copyright © 2011—2013  Andrey Mikhaylenko
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

    * :class:`ExplicitDefaultMerger`
    * :class:`TypeMerger`
    * :class:`DictMerger`
    * :class:`ListMerger`
    * :class:`FuncMerger`
    * :class:`AnyMerger`

"""
from monk import compat
from monk.schema import canonize


__all__ = [
    # mergers
    'ValueMerger', 'TypeMerger', 'DictMerger', 'ListMerger', 'FuncMerger',
    'AnyMerger', 'ExplicitDefaultMerger',
    # functions
    'merge_value', 'merged',
    # helpers
    'unfold_list_of_dicts', 'unfold_to_list'
]


class ValueMerger(object):
    """ Base class for value mergers.
    """
    def __init__(self, spec, value):
        self.spec = canonize(spec)
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


class ExplicitDefaultMerger(ValueMerger):
    """ Rule. Uses defaults, if any.
    Example::

        >>> TypeMerger(int, None).process()
        None
        >>> TypeMerger(int, 123).process()
        123

    """
    def check(self):
        return self.spec.default

    def process(self):
        if self.value is None:
            return self.spec.default
        else:
            return self.value


class AnyMerger(ValueMerger):
    """ The "any value" merger.

    Example::

        >>> AnyMerger(None, None).process()
        None
        >>> AnyMerger(None, 123).process()
        123

    """
    def check(self):
        return (self.spec.datatype is None
            and self.spec.default is None
            and not self.spec.inner_spec)

    def process(self):
        # there's no default value for this key, just a restriction on type
        return self.value


class TypeMerger(ValueMerger):
    """ Type definition. Preserves empty values.
    Example::

        >>> TypeMerger(int, None).process()
        None
        >>> TypeMerger(int, 123).process()
        123

    """
    def check(self):
        return self.spec.datatype is not None

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
        return self.spec.datatype == dict

    def process(self):
        if self.value is not None and not isinstance(self.value, dict):
            # bogus value; will not pass validation but should be preserved
            return self.value
        return merged(self.spec.inner_spec or {}, self.value or {})


class ListMerger(ValueMerger):
    """ Nested list.
    """
    def check(self):
        return self.spec.datatype == list

    def process(self):
        item_spec = self.spec.inner_spec or None
        item_rule = canonize(item_spec)

        if not self.value:
            return []

        if item_rule.datatype is None:
            # any value is accepted as list item
            return self.value
        elif item_rule.inner_spec:
            return [merged(item_rule.inner_spec, item) for item in self.value]
        else:
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
        return isinstance(self.spec, compat.func_types)

    def process(self):
        if self.value is None:
            return self.spec()
        else:
            return self.value


class PassThroughMerger(ValueMerger):
    """ Lets any value pass.
    """
    def check(self):
        return True

    def process(self):
        return self.value


VALUE_MERGERS = ExplicitDefaultMerger, AnyMerger, DictMerger, ListMerger, FuncMerger, TypeMerger, PassThroughMerger


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
    :func:`~monk.validation.validate`.

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

    for key in set(list(spec.keys()) + list(data.keys())):
        if key in spec:
            value = merge_value(spec[key], data.get(key), mergers=mergers)
        else:
            # never mind if there are nested structures: anyway we cannot check
            # them as they aren't in the spec
            value = data[key]

        result[key] = value

    return result


def unfold_list_of_dicts(value, default_key):
    """
    Converts given value to a list of dictionaries as follows:

    * ``[{...}]`` → ``[{...}]``
    * ``{...}``   → ``[{...}]``
    * ``'xyz'``   → ``[{default_key: 'xyz'}]``

    """
    if value is None:
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, unicode):
        return [{default_key: value}]
    if isinstance(value, list):
        if not all(isinstance(x, dict) for x in value):
            def _fix(x):
                return {default_key: x} if isinstance(x, unicode) else x
            return map(_fix, value)
    return value


def unfold_to_list(value):
    """
    Converts given value to a list  as follows:

    * ``[x]`` → ``[x]``
    * ``x``  → ``[x]``

    """
    if value and not isinstance(value, list):
        return [value]
    else:
        return value
