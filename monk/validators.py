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
Validators
~~~~~~~~~~
"""
from monk.errors import ValidationError


def validate_choice(choices):
    def _validate_choice(value):
        if value not in choices:
            raise ValidationError('expected one of {0}, got {1!r}'.format(choices, value))
    return _validate_choice


def validate_range(start, stop):
    def _validate_range(value):
        if not start <= value <= stop:
            raise ValidationError('expected value in range {0}..{1}, got {2!r}'.format(start, stop, value))
    return _validate_range


def validate_length(expected):
    def _validate_length(value):
        if len(value) != expected:
            raise ValidationError('expected value of length {0}, got {1!r}'.format(expected, value))
    return _validate_length

