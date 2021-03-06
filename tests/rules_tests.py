# -*- coding: utf-8 -*-
#
#    Monk is an unobtrusive data modeling, manipulation and validation library.
#    Copyright © 2011—2015  Andrey Mikhaylenko
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
import sys

from monk import compat, errors
from monk import (
    Any, Anything, IsA, Equals, Exists, DictOf, translate,
    one_of, optional, opt_key
)


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
        schema(123)
        schema('foo')
        with pytest.raises(errors.ValidationError) as excinfo:
            schema({})
        assert "AllFailed: must be int or must be str" in excinfo.exconly()

    def test_nested(self):
        schema = Any([
            {'foo': int},
            {'bar': str},
        ])
        schema({'foo': 123})
        schema({'bar': 'hi'})
        with pytest.raises(errors.ValidationError) as excinfo:
            schema({'foo': 'hi'})
        assert (
            "AllFailed: 'foo' value must be int or must not have keys like 'foo'"
        ) in excinfo.exconly()
        with pytest.raises(errors.ValidationError) as excinfo:
            schema({'bar': 123})
        assert (
            "AllFailed: must not have keys like 'bar' or 'bar' value must be str"
        ) in excinfo.exconly()


class TestShortcuts:

    def test_one_of(self):
        # literals (behaviour implicitly turned on)

        assert one_of(['foo', 'bar']) == Equals('foo') | Equals('bar')

        v = one_of(['foo', 'bar'])
        v('foo')
        with pytest.raises(errors.ValidationError) as excinfo:
            v('quux')
        assert "AllFailed: must equal 'foo' or must equal 'bar'" in excinfo.exconly()

        # non-literals → rules (behaviour explicitly turned on)

        shortcut_rule = one_of(['foo', 'bar'], as_rules=True)
        verbose_rule = Any(['foo', 'bar'])
        assert shortcut_rule == verbose_rule

        v = one_of(['foo', 123], as_rules=True)
        v('hello')
        v(456)
        with pytest.raises(errors.ValidationError) as excinfo:
            v(5.5)
        assert "AllFailed: must be str or must be int" in excinfo.exconly()

    def test_optional(self):
        assert optional(str) == IsA(str) | ~Exists()
        assert optional(IsA(str)) == IsA(str) | ~Exists()
        assert optional('foo') == IsA(str, default='foo') | ~Exists()

    @pytest.mark.skipif(sys.version_info >= (3,0), reason='Python 2.x only')
    def test_opt_key__py2_unicode(self):
        raw = {
            opt_key(unicode('foo')): int,
        }
        assert translate(raw) == DictOf([
            (Equals(unicode('foo')) | ~Exists(), IsA(int)),
        ])

    def test_opt_key__str(self):
        # this also means Unicode for Py3 but it's OK
        raw = {
            opt_key('foo'): int,
        }
        assert translate(raw) == DictOf([
            (Equals('foo') | ~Exists(), IsA(int)),
        ])
