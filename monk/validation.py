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
Validation
~~~~~~~~~~
"""
from . import errors
from . import translate

__all__ = [
    # functions
    'validate'
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

    :class:`TypeError`
        if the value (or a nested value) does not belong to the designated type.

    """
    validator = translate(spec)
    validator(value)
