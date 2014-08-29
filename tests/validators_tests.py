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

from monk.errors import (
    ValidationError, MissingKey, InvalidKey,
    StructureSpecificationError
)
from monk import (
    All, Any, Anything, IsA, Equals, InRange, Length, ListOf, DictOf,
    NotExists, MISSING, translate
)


def test_anything():
    v = Anything()

    assert repr(v) == 'Anything()'

    v('foo')
    v(123)
    v(MISSING)
    v([5])


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


def test_inrange():
    range_2_to_4 = InRange(min=2, max=4)
    range_min_2 = InRange(min=2)
    range_max_4 = InRange(max=4)

    assert repr(range_2_to_4) == 'InRange(2..4)'
    assert repr(range_min_2) == 'InRange(2..)'
    assert repr(range_max_4) == 'InRange(..4)'

    # below limit
    with raises_regexp(ValidationError, '^must be ≥ 2'):
        range_min_2(1)
    with raises_regexp(ValidationError, '^must be ≥ 2'):
        range_2_to_4(1)
    range_max_4(1)

    # at lower limit
    range_2_to_4(2)
    range_min_2(2)
    range_max_4(2)

    # between limits
    range_2_to_4(3)
    range_min_2(3)
    range_max_4(3)

    # at higher limit
    range_2_to_4(4)
    range_min_2(4)
    range_max_4(4)

    # above limit
    range_min_2(5)
    with raises_regexp(ValidationError, '^must be ≤ 4'):
        range_2_to_4(5)
    with raises_regexp(ValidationError, '^must be ≤ 4'):
        range_max_4(5)


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
    with raises_regexp(ValidationError, '^4.5 \(must be str; must be int\)'):
        v(4.5)


def test_combinator_all():
    v = All([ Length(min=2), Length(max=3) ])

    assert repr(v) == 'All[Length(2..), Length(..3)]'

    with raises_regexp(ValidationError, 'length must be ≥ 2'):
        v('f')
    v('fo')
    v('foo')
    with raises_regexp(ValidationError, 'length must be ≤ 3'):
        v('fooo')


def test_magic_eq():
    assert IsA(str) == IsA(str)
    assert IsA(str) != IsA(str, default='foo')
    assert IsA(str) != IsA(int)
    assert IsA(str) != Equals(int)

    # nested
    v1 = ListOf([DictOf([ (Equals('foo'), IsA(str)) ])])
    v2 = ListOf([DictOf([ (Equals('foo'), IsA(str)) ])])
    v3 = ListOf([DictOf([ (Equals('bar'), IsA(str)) ])])
    v4 = ListOf([DictOf([ (Equals('foo'), IsA(int)) ])])
    v5 = ListOf([DictOf([ (Equals('foo'), IsA(str, default='x')) ])])
    assert v1 == v1
    assert v1 == v2
    assert v1 != v3
    assert v1 != v4
    assert v1 != v5


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


def test_magic_hash():
    assert hash(IsA(str)) == hash(IsA(str))
    assert hash(IsA(str)) != hash(IsA(str, default='foo'))
    assert hash(IsA(str)) != hash(IsA(int))
    assert hash(IsA(str)) != hash(IsA(str) | IsA(int))


def test_combinator_edge_cases():
    with raises_regexp(TypeError, 'got NotExists class instead of its instance'):
        IsA(str) | NotExists

    # translate() is applied to the right argument
    assert IsA(str) | 'Albatross!' == IsA(str) | IsA(str, default='Albatross!')
    assert IsA(str) | None == IsA(str) | Anything()
    assert Length(min=3) & [] == Length(min=3) & IsA(list)


def test_translate_validator():
    assert translate(IsA(int)) == IsA(int)
    assert translate(IsA(str, default='hello')) == IsA(str, default='hello')


def test_translate_none():
    assert translate(None) == Anything()


def test_translate_type():
    assert translate(int) == IsA(int)
    assert translate(str) == IsA(str)


def test_translate_func():
    # FIXME things like datetime.now() imply transient defaults
    def func():
        return 'hello'
    assert translate(func) == IsA(str, default='hello')


def test_translate_list():
    assert translate(list) == IsA(list)
    assert translate([]) == IsA(list)
    assert translate([int]) == ListOf(IsA(int)) & Length(min=1)
    assert translate([1]) == ListOf(IsA(int, default=1)) & Length(min=1)
    with raises_regexp(StructureSpecificationError,
                       'Expected a list containing exactly 1 item; '
                       'got 3: \[1, 2, 3\]'):
        translate([1, 2, 3])


def test_translate_dict():
    assert translate(dict) == IsA(dict)
    assert translate({}) == IsA(dict)

    # literal as a key
    assert translate({'foo': 123}) == DictOf([
        (Equals('foo'), IsA(int, default=123)),
    ])
    assert translate({123: str}) == DictOf([
        (Equals(123), IsA(str)),
    ])

    # validator as a key
    assert translate({Equals('foo') | Equals('bar'): str}) == DictOf([
        (Equals('foo') | Equals('bar'), IsA(str)),
    ])

    # type as a key
    assert translate({str: int}) == DictOf([
        (IsA(str), IsA(int)),
    ])

    # function as a key
    func = lambda: 'foo'
    assert translate({func: int}) == DictOf([
        (Equals('foo'), IsA(int)),
    ])


def test_translate_fallback():
    assert translate('hello') == IsA(str, default='hello')
