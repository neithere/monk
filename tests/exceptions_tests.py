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
Exception Formatting Tests
~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
from monk.errors import (
    ValidationError,
    MissingKeys, InvalidKeys,
    AllFailed, AtLeastOneFailed,
)


def test_validation_error():
    e = ValidationError('ima a-thinking ye is wrong')
    assert str(e) == 'ima a-thinking ye is wrong'

def test_missing_key():
    e = MissingKeys('foo')
    assert str(e) == "must have keys: 'foo'"

    e = MissingKeys('foo', 'bar')
    assert str(e) == "must have keys: 'foo', 'bar'"


def test_invalid_key():
    e = InvalidKeys('foo')
    assert str(e) == "must not have keys like 'foo'"

    e = InvalidKeys('foo', 'bar')
    assert str(e) == "must not have keys like 'foo', 'bar'"


def test_all_failed():
    errors = ValidationError('w00t'), ValidationError('haX0r')
    e = AllFailed(*errors)
    assert str(e) == "w00t or haX0r"


def test_at_least_one_failed():
    errors = ValidationError('w00t'), ValidationError('haX0r')
    e = AtLeastOneFailed(*errors)
    assert str(e) == "w00t and haX0r"
