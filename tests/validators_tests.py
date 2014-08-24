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
Validators tests
================
"""
import pytest

from monk.errors import ValidationError
from monk.schema import Rule
from monk.validation import validate
from monk import validators


class TestValidators:

    def test_choice(self):

        choices = 'a', 'b'
        spec = Rule(str, validators=[validators.validate_choice(choices)])

        validate(spec, 'a')
        validate(spec, 'b')

        with pytest.raises(ValidationError) as excinfo:
            validate(spec, 'c')
        assert "expected one of ('a', 'b'), got 'c'" in excinfo.exconly()

    def test_range(self):

        spec = Rule(int, validators=[validators.validate_range(2, 5)])

        validate(spec, 2)
        validate(spec, 4)

        with pytest.raises(ValidationError) as excinfo:
            validate(spec, 6)
        assert 'expected value in range 2..5, got 6' in excinfo.exconly()

    def test_length(self):

        spec = Rule(str, validators=[validators.validate_length(3)])

        validate(spec, 'foo')

        with pytest.raises(ValidationError) as excinfo:
            validate(spec, 'foobar')
        assert "expected value of length 3, got 'foobar'" in excinfo.exconly()

