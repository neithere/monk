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
~~~~~~~~~~~~~~~~~
Data manipulation
~~~~~~~~~~~~~~~~~
"""
from .compat import text_type
from . import translate


__all__ = [
    # functions
    'merge_defaults',
    # helpers
    'normalize_to_list', 'normalize_list_of_dicts',
]


def merge_defaults(spec, value):
    """
    Returns a copy of `value` recursively updated to match the `spec`:

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

    Examples::

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

    validator = translate(spec)

    return validator.get_default_for(value)


class UNDEFINED:
    pass


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
