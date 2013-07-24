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
~~~~~~~~~~~~~~~~~
"""
from monk.schema import canonize


__all__ = [
    # merger functions
    'merge_any_value', 'merge_dict_value', 'merge_list_value',
    # functions
    'merge_value', 'merged',
    # helpers
    'unfold_list_of_dicts', 'unfold_to_list'
]


def merge_any_value(spec, value):
    """ The "any value" merger.

    Example::

        >>> merge_any_value(None, None)
        None
        >>> merge_any_value(None, 123)
        123

    """
    # there's no default value for this key, just a restriction on type
    return value


def merge_dict_value(spec, value):
    """ Nested dictionary.
    Example::

        >>> merge_dict_value({'a': 123}, {})
        {'a': 123}
        >>> merge_dict_value({'a': 123}, {'a': 456})
        {'a': 456}

    """
    if value is not None and not isinstance(value, dict):
        # bogus value; will not pass validation but should be preserved
        return value
    return merged(spec.inner_spec or {}, value or {})


def merge_list_value(spec, value):
    """ Nested list.
    """
    item_spec = spec.inner_spec or None
    item_rule = canonize(item_spec)

    if not value:
        return []

    if item_rule.datatype is None:
        # any value is accepted as list item
        return value
    elif item_rule.inner_spec:
        return [merged(item_rule.inner_spec, item) for item in value]
    else:
        return value


DATATYPE_MERGERS = {
    dict: merge_dict_value,
    list: merge_list_value,
}
"The default set of type-specific value mergers"


def merge_value(spec, value, datatype_mergers,
                fallback_merger=merge_any_value):
    """ Returns a merged value based on given spec and data, using given
    set of mergers.

    If `value` is empty and `spec` has a default value, the default is used.

    If spec datatype is present as a key in `datatype_mergers`,
    the respective merger function is used to obtain the value.
    If no merger is assigned to the datatype, `fallback_merger` is used.

    :datatype_mergers:
        A list of merger functions assigned to specific types of values.

        A merger function should accept two arguments: `spec`
        (a :class:`~monk.schema.Rule` instance) and `value`.

    Example::

        >>> merge_value({'a': 123}, {}, [merge_dict_value])
        {'a': 123}
        >>> merge_value({'a': 123}, {'a': 456}, [merge_dict_value])
        {'a': 456}

    """
    rule = canonize(spec)

    if value is None and rule.default is not None:
        return rule.default

    merger = datatype_mergers.get(rule.datatype, fallback_merger)

    return merger(rule, value)


def merged(spec, data, datatype_mergers=DATATYPE_MERGERS):
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
            value = merge_value(spec[key], data.get(key),
                                datatype_mergers=datatype_mergers)
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
