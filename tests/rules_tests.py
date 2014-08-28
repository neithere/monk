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
Schema Rules Tests
~~~~~~~~~~~~~~~~~~
"""
import datetime
import pytest

from monk import errors
#from monk.schema import Rule, OneOf, canonize, one_of, any_value, any_or_none
from monk.schema import one_of
from monk.reqs import Anything, IsA, Equals, ListOf, DictOf, translate
from monk.combinators import Any
from monk.validation import validate


class TestRule:

    def test_rule_as_datatype(self):
        rule = Rule(None)
        with pytest.raises(ValueError) as excinfo:
            Rule(rule)
        assert 'Cannot use a Rule instance as datatype' in excinfo.exconly()

    def test_rule_repr(self):
        assert repr(Rule(None)) == '<Rule any required>'
        assert repr(Rule(None, optional=True)) == '<Rule any optional>'
        assert repr(Rule(str)) == '<Rule str required>'
        assert repr(Rule(str, default='foo')) == '<Rule str required default=foo>'

    def test_sanity_default(self):
        Rule(str)
        Rule(str, default='foo')
        with pytest.raises(TypeError) as excinfo:
            Rule(str, default=123)
        assert excinfo.exconly() == 'TypeError: Default value must match datatype str (got 123)'

    @pytest.mark.xfail
    def test_sanity_inner_spec(self):
        #
        # this won't work because only dict wants a dict as its inner_spec;
        # a list doesn't need this duplication.
        #
        Rule(dict)
        Rule(dict, inner_spec={})
        with pytest.raises(TypeError) as excinfo:
            Rule(dict, inner_spec=123)
        assert excinfo.exconly() == 'TypeError: Inner spec must match datatype dict (got 123)'


class TestTranslation:
    # FIXME this is largerly duplicated in validators_tests

    def test_none(self):
        assert translate(None) == Anything()

    def test_bool(self):
        assert translate(bool) == IsA(bool)
        assert translate(True)  == IsA(bool, default=True)
        assert translate(False)  == IsA(bool, default=False)

    def test_datetime(self):
        assert translate(datetime.datetime) == IsA(datetime.datetime)

        dt = datetime.datetime.now()
        assert translate(dt) == IsA(datetime.datetime, default=dt)

    def test_dict(self):
        assert translate(dict) == IsA(dict)
        assert translate({'foo': 123}) == DictOf([
            (Equals('foo'), IsA(int, default=123)),
        ])

    def test_float(self):
        assert translate(float) == IsA(float)
        assert translate(.5) == IsA(float, default=.5)

    def test_int(self):
        assert translate(int) == IsA(int)
        assert translate(5) == IsA(int, default=5)

    def test_list(self):
        assert translate(list) == IsA(list)

        assert translate([]) == IsA(list)

        with pytest.raises(errors.StructureSpecificationError) as excinfo:
            translate([1,2])
        assert ("StructureSpecificationError: Expected a list "
                "containing exactly 1 item; got 2: [1, 2]") in excinfo.exconly()

    def test_string(self):
        assert translate(str) == IsA(str)
        assert translate('foo') == IsA(str, default='foo')

    def test_rule(self):
        rule = IsA(str, default='abc') | IsA(int)
        assert rule == translate(rule)


class TestAlternativeRules:

    def test_flat(self):
        schema = Any([int, str])
        validate(schema, 123)
        validate(schema, 'foo')
        with pytest.raises(errors.ValidationError) as excinfo:
            validate(schema, {})
        assert (
            'ValidationError: failed 2 alternative rules:'
            ' 1) TypeError: expected int, got dict {};'
            ' 2) TypeError: expected str, got dict {}'
        ) in excinfo.exconly()

    def test_nested(self):
        schema = OneOf([
            {'foo': int},
            {'bar': str},
        ])
        validate(schema, {'foo': 123})
        validate(schema, {'bar': 'hi'})
        with pytest.raises(errors.ValidationError) as excinfo:
            validate(schema, {'foo': 'hi'})
        assert (
            'ValidationError: failed 2 alternative rules:'
            ' 1) TypeError: foo: expected int, got str \'hi\';'
            " 2) InvalidKey: 'foo'"
        ) in excinfo.exconly()
        with pytest.raises(errors.ValidationError) as excinfo:
            validate(schema, {'bar': 123})
        assert (
            'ValidationError: failed 2 alternative rules:'
            " 1) InvalidKey: 'bar';"
            ' 2) TypeError: bar: expected str, got int 123'
        ) in excinfo.exconly()


class TestShortcuts:

    def test_one_of(self):
        # literals (behaviour implicitly turned on)

        assert one_of(['foo', 'bar']) == Equals('foo') | Equals('bar')

        v = one_of(['foo', 'bar'])
        v('foo')
        with pytest.raises(errors.ValidationError) as excinfo:
            v('quux')
        assert ("AllFailed: 'quux' (ValidationError: != 'foo';"
                                  " ValidationError: != 'bar')"
        ) in excinfo.exconly()

        # non-literals → rules (behaviour explicitly turned on)

        shortcut_rule = one_of(['foo', 'bar'], as_rules=True)
        verbose_rule = Any(['foo', 'bar'])
        assert shortcut_rule == verbose_rule

        v = one_of(['foo', 123], as_rules=True)
        v('hello')
        v(456)
        with pytest.raises(errors.ValidationError) as excinfo:
            v(5.5)
        assert (
            'AllFailed: 5.5 (ValidationError: must be str;'
                           ' ValidationError: must be int)'
        ) in excinfo.exconly()
