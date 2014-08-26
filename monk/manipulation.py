# -*- coding: utf-8 -*-
#
#    Monk is an unobtrusive data modeling, manipulation and validation library.
#    Copyright © 2011—2014  Andrey Mikhaylenko
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
from monk.compat import text_type
from monk.schema import Rule, OneOf, canonize


__all__ = [
    # functions
    'merge_defaults', 'merged',
    # helpers
    'unfold_list_of_dicts', 'unfold_to_list',
    # constants
    'TYPE_MERGERS',
    # merger functions
    'merge_any', 'merge_dict', 'merge_list',
]


# NOTE: updated at the end of file
TYPE_MERGERS = {}
""" The default set of type-specific value mergers:

* ``dict`` -- :func:`merge_dict`
* ``list`` -- :func:`merge_list`

"""


def merge_any(spec, value, mergers, fallback):
    """ Always returns the value as is.
    """
    return value


def merge_dict(spec, value, mergers, fallback):
    """ Returns a dictionary based on `value` with each value recursively
    merged with `spec`.
    """
    assert spec.datatype is dict

    if spec.optional and value is None:
        return None

    if spec.inner_spec is None:
        if value is None:
            return {}
        else:
            return value

    if value is not None and not isinstance(value, dict):
        # bogus value; will not pass validation but should be preserved
        return value

    data = value or {}
    result = {}

    for key in set(list(spec.inner_spec.keys()) + list(data.keys())):
        if isinstance(key, Rule):
            continue

        if key in spec.inner_spec:
            value = merge_defaults(spec.inner_spec[key], data.get(key),
                                   mergers, fallback)
        else:
            # never mind if there are nested structures: anyway we cannot check
            # them as they aren't in the spec
            value = data[key]

        result[key] = value

    return result


def merge_list(spec, value, mergers, fallback):
    """ Returns a list based on `value`:

    * missing required value is converted to an empty list;
    * missing required items are never created;
    * nested items are merged recursively.

    """
    assert spec.datatype is list

    if spec.optional and value is None:
        return None

    if not value:
        return []

    if value is not None and not isinstance(value, list):
        # bogus value; will not pass validation but should be preserved
        return value

    item_spec = canonize(spec.inner_spec or None)

    if isinstance(item_spec, OneOf):
        # FIXME we've been expecting a rule (Rule instance) but got an instance
        # of another class.  OneOf should inherit Rule or they should have
        # a common base class.
        if item_spec.first_is_default:
            return merge_defaults(item_spec.choices[0], value, mergers, fallback)
        else:
            return value

    if item_spec.datatype is None:
        # any value is accepted as list item
        return value

    if item_spec.inner_spec:
        return [merge_defaults(item_spec.inner_spec, item, mergers, fallback)
                for item in value]

    return value


def merge_defaults(spec, value, mergers=TYPE_MERGERS, fallback=merge_any):
    """ Returns a copy of `value` recursively updated to match the `spec`:

    * New values are added whenever possible (including nested ones).
    * Existing values are never changed or removed.

      * Exception: container values (lists, dictionaries) may be populated;
        see respective merger functions for details.

    The result may not pass validation against the `spec`
    in the following cases:

    a) a required value is missing and the spec does not provide defaults;
    b) an existing value is invalid.

    The business logic is as follows:

    * if `value` is empty, use default value from `spec`;
    * if `value` is present or `spec` has no default value:

      * if `spec` datatype is present as a key in `mergers`,
        use the respective merger function to obtain the value;
      * if no merger is assigned to the datatype, use `fallback` function.

    See documentation on concrete merger functions for further details.

    :spec:
        A "natural" or "verbose" spec.

    :value:
        The value to merge into the `spec`.

    :mergers:
        An dictionary of merger functions assigned to specific types
        of values (sort of `{int: integer_merger_func}`).

        A merger function should accept the same arguments as this function,
        only with `spec` always being a :class:`~monk.schema.Rule` instance.

        Default: :attr:`TYPE_MERGERS`.

    :fallback:
        A merger function to use when no datatype-specific merger is found.

        Default: :func:`merge_any`

    Examples (with standard mergers)::

        >>> merge_defaults('foo', None)
        'foo'
        >>> merge_defaults('foo', 'bar')
        'bar'
        >>> merge_defaults({'a': 'foo'}, {})
        {'a': 'foo'}
        >>> merge_defaults({'a': [{'b': 123}]},
        ...                {'a': [{'b': None},
        ...                       {'x': 0}]})
        {'a': [{'b': 123}, {'b': 123, 'x': 0}]}

    """
    rule = canonize(spec)

    if isinstance(rule, OneOf):
        # FIXME we've been expecting a rule (Rule instance) but got an instance
        # of another class.  OneOf should inherit Rule or they should have
        # a common base class.
        if rule.first_is_default:
            return merge_defaults(rule.choices[0], value, mergers, fallback)

        return value

    if value is None and rule.default is not None:
        return rule.default

    merger = mergers.get(rule.datatype, fallback)

    return merger(rule, value, mergers=mergers, fallback=fallback)


def merged(spec, data, mergers=TYPE_MERGERS):
    """
    .. deprecated:: 0.10.0

       Use :func:`merge_defaults` instead.
    """
    import warnings
    warnings.warn('merged() is deprecated, use merge_defaults() instead',
                  DeprecationWarning)

    return merge_defaults(spec, data, mergers=mergers)


class UNDEFINED:
    pass


def normalize_list_of_dicts(value, default_key, default_value=UNDEFINED):
    """
    Converts given value to a list of dictionaries as follows:

    * ``[{...}]`` → ``[{...}]``
    * ``{...}``   → ``[{...}]``
    * ``'xyz'``   → ``[{default_key: 'xyz'}]``
    * ``None``    → ``[{default_key: default_value}]``  (if specified)
    * ``None``    → ``[]``

    :param default_value:
        only Unicode, i.e. `str` in Python 3.x and **only** `unicode` in Python 2.x

    """
    if value is None:
        if default_value is UNDEFINED:
            return []
        value = default_value

    if isinstance(value, dict):
        return [value]

    if isinstance(value, text_type):
        return [{default_key: value}]

    if isinstance(value, list):
        if not all(isinstance(x, dict) for x in value):
            def _fix(x):
                return {default_key: x} if isinstance(x, text_type) else x
            return list(map(_fix, value))

    return value


def normalize_to_list(value):
    """
    Converts given value to a list  as follows:

    * ``[x]`` → ``[x]``
    * ``x``  → ``[x]``

    """
    if value and not isinstance(value, list):
        return [value]
    else:
        return value


def unfold_list_of_dicts(value, default_key):
    """
    .. deprecated:: 0.10.0

       Use :func:`normalize_list_of_dicts` instead.
    """
    return normalize_list_of_dicts(value, default_key)


def unfold_to_list(value):
    """
    .. deprecated:: 0.10.0

       Use :func:`normalize_to_list` instead.
    """
    return normalize_to_list(value)

TYPE_MERGERS.update({
    dict: merge_dict,
    list: merge_list,
})
