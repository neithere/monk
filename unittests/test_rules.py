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
Schema Rules Tests
~~~~~~~~~~~~~~~~~~
"""
import datetime
import pytest

from monk.schema import Rule, canonize


class TestRule:
    def test_rule_as_datatype(self):
        rule = Rule(None)
        with pytest.raises(ValueError) as excinfo:
            Rule(rule)
        assert 'Cannot use a Rule instance as datatype' in excinfo.exconly()


class TestCanonization:

    def test_none(self):
        assert canonize(None) == Rule(None)

    def test_bool(self):
        assert canonize(bool) == Rule(bool)
        assert canonize(True)  == Rule(bool, default=True)
        assert canonize(False)  == Rule(bool, default=False)

    def test_datetime(self):
        assert canonize(datetime.datetime) == Rule(datetime.datetime)

        dt = datetime.datetime.now()
        assert canonize(dt) == Rule(datetime.datetime, default=dt)

    def test_dict(self):
        assert canonize(dict) == Rule(dict)
        assert canonize({'foo': 123}) == Rule(dict, inner_spec={'foo': 123})

    def test_float(self):
        assert canonize(float) == Rule(float)
        assert canonize(.5) == Rule(float, default=.5)

    def test_int(self):
        assert canonize(int) == Rule(int)
        assert canonize(5) == Rule(int, default=5)

    def test_list(self):
        assert canonize(list) == Rule(list)
        assert canonize([1,2]) == Rule(list, inner_spec=[1,2])

    def test_string(self):
        assert canonize(str) == Rule(str)
        assert canonize('foo') == Rule(str, default='foo')

    def test_rule(self):
        rule = Rule(str, default='abc', skip_missing=True)
        assert rule == canonize(rule)
