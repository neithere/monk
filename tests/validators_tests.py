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
from pytest import raises_regexp

from monk.errors import ValidationError, MissingKey, InvalidKey
from monk.schema import Rule
from monk.validation import validate
from monk import validators

from monk.combinators import All, Any
from monk.reqs import IsA, Equals, Length, ListOf, DictOf, NotExists, MISSING


class TestLegacyValidators:

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


def test_isa():
    v = IsA(str)

    assert repr(v) == 'IsA(str)'

    v('foo')

    with raises_regexp(ValidationError, '^must be str'):
        v(123)


def test_equals():
    v = Equals('foo')

    assert repr(v) == "Equals('foo')"

    v('foo')

    with raises_regexp(ValidationError, "^!= 'foo'"):
        v('bar')


def test_length():
    len_2_to_4 = Length(min=2, max=4)
    len_min_2 = Length(min=2)
    len_max_4 = Length(max=4)

    assert repr(len_2_to_4) == 'Length(2..4)'
    assert repr(len_min_2) == 'Length(2..)'
    assert repr(len_max_4) == 'Length(..4)'

    # below limit
    with raises_regexp(ValidationError, '^length must be ≥ 2'):
        len_min_2('a')
    with raises_regexp(ValidationError, '^length must be ≥ 2'):
        len_2_to_4('a')
    len_max_4('a')

    # at lower limit
    len_2_to_4('aa')
    len_min_2('aa')
    len_max_4('aa')

    # between limits
    len_2_to_4('aaa')
    len_min_2('aaa')
    len_max_4('aaa')

    # at higher limit
    len_2_to_4('aaaa')
    len_min_2('aaaa')
    len_max_4('aaaa')

    # above limit
    len_min_2('aaaaa')
    with raises_regexp(ValidationError, '^length must be ≤ 4'):
        len_2_to_4('aaaaa')
    with raises_regexp(ValidationError, '^length must be ≤ 4'):
        len_max_4('aaaaa')


def test_listof():
    v = ListOf(IsA(str))

    assert repr(v) == 'ListOf(IsA(str))'

    with raises_regexp(ValidationError, '^must be list'):
        v('foo')

    v([])

    v(['foo'])

    v(['foo', 'bar'])

    with raises_regexp(ValidationError, '^#2: must be str'):
        v(['foo', 'bar', 123])


def test_dictof():
    # key may be missing
    dict_of_str_to_int_optional_keys = DictOf([
        (IsA(str) | NotExists(), IsA(int)),
    ])
    dict_of_str_to_int_optional_keys({})
    dict_of_str_to_int_optional_keys({'foo': 123})
    with raises_regexp(InvalidKey, '123'):
        dict_of_str_to_int_optional_keys({123: 456})

    # key must be present, exact literals not specified
    dict_of_str_to_int = DictOf([
        (IsA(str), IsA(int)),
    ])
    with raises_regexp(MissingKey, 'IsA\(str\)'):
        dict_of_str_to_int({})
    dict_of_str_to_int({'foo': 123})
    dict_of_str_to_int({'foo': 123, 'bar': 456})

    with raises_regexp(InvalidKey, '123'):
        dict_of_str_to_int({'foo': 123, 'bar': 456, 123: 'quux'})
    with raises_regexp(ValidationError, "'quux': must be int"):
        dict_of_str_to_int({'foo': 123, 'bar': 456, 'quux': 4.2})


def test_notexists():
    v = NotExists()

    assert repr(v) == 'NotExists()'

    v(MISSING)    # because the validator is for a special case — this one

    with raises_regexp(ValidationError, 'must not exist'):
        v(None)

    with raises_regexp(ValidationError, 'must not exist'):
        v('foo')


def test_combinator_any():
    v = Any([ IsA(str), IsA(int) ])

    assert repr(v) == 'Any[IsA(str), IsA(int)]'

    v('foo')
    v(123)
    with raises_regexp(ValidationError, '^4.2 \(ValidationError: must be str;'
                                              ' ValidationError: must be int\)'):
        v(4.2)


def test_combinator_all():
    v = All([ Length(min=2), Length(max=3) ])

    assert repr(v) == 'All[Length(2..), Length(..3)]'

    with raises_regexp(ValidationError, 'length must be ≥ 2'):
        v('f')
    v('fo')
    v('foo')
    with raises_regexp(ValidationError, 'length must be ≤ 3'):
        v('fooo')


def test_magic_and_or():
    v = IsA(str) | IsA(int)
    assert isinstance(v, Any)
    assert repr(v) == 'Any[IsA(str), IsA(int)]'

    v = IsA(str) & IsA(int)    # silly but who cares
    assert isinstance(v, All)
    assert repr(v) == 'All[IsA(str), IsA(int)]'

    v = IsA(str) & IsA(int) | IsA(float)
    assert repr(v) == 'Any[All[IsA(str), IsA(int)], IsA(float)]'

    v = IsA(str) | IsA(int) & IsA(float)
    assert repr(v) == 'Any[IsA(str), All[IsA(int), IsA(float)]]'


def test_combinator_edge_cases():
    with raises_regexp(TypeError, 'got NotExists class instead of its instance'):
        IsA(str) | NotExists

    with raises_regexp(TypeError, 'expected a BaseValidator subclass instance,'
                                  " got 'Albatross!'"):
        IsA(str) | "Albatross!"
