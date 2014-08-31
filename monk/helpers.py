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
~~~~~~~
Helpers
~~~~~~~
"""
from .validators import translate


__all__ = [
    # functions
    'validate',
    'walk_dict',
]


def validate(spec, value):
    """
    Validates given value against given specification.
    Raises an exception if the value is invalid.
    Always returns ``None``.

    In fact, it's just a very thin wrapper around the validators.
    These three expressions are equal::

        IsA(str)('foo')
        translate(str)('foo')
        validate(str, 'foo')

    :spec:
        a validator instance or any value digestible by :func:`translate`.
    :value:
        any value including complex structures.

    Can raise:

    :class:`MissingValue`
        if a dictionary key is in the spec but not in the value.
        This applies to root and nested dictionaries.

    :class:`MissingKey`
        if a dictionary key is in the spec but not in the value.
        This applies to root and nested dictionaries.

    :class:`InvalidKey`
        if a dictionary key is the value but not not in the spec.

    :class:`StructureSpecificationError`
        if errors were found in spec.

    """
    validator = translate(spec)
    validator(value)


def walk_dict(data):
    """ Generates pairs ``(keys, value)`` for each item in given dictionary,
    including nested dictionaries. Each pair contains:

    `keys`
        a tuple of 1..n keys, e.g. ``('foo',)`` for a key on root level or
        ``('foo', 'bar')`` for a key in a nested dictionary.
    `value`
        the value of given key or ``None`` if it is a nested dictionary and
        therefore can be further unwrapped.
    """
    assert hasattr(data, '__getitem__')
    for key, value in data.items():
        if isinstance(value, dict):
            yield (key,), None
            for keys, value in walk_dict(value):
                path = (key,) + keys
                yield path, value
        else:
            yield (key,), value
