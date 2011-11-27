# -*- coding: utf-8 -*-
#
#    Monk is a lightweight schema/query framework for document databases.
#    Copyright © 2011  Andrey Mikhaylenko
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
Data manipulation tests
=======================
"""
import pytest

from monk.manipulation import merged


class TestDocumentDefaults:
    @pytest.mark.xfail()
    def test_none(self):
        assert {'a': None} == merged({'a': None}, {})
        assert {'a': None} == merged({'a': None}, {'a': None})
        assert {'a': 1234} == merged({'a': None}, {'a': 1234})

    @pytest.mark.xfail()
    def test_type(self):
        assert {'a': None} == merged({'a': unicode}, {})
        assert {'a': None} == merged({'a': unicode}, {'a': None})
        assert {'a': u'a'} == merged({'a': 1}, {'a': u'a'})

    @pytest.mark.xfail()
    def test_type_in_dict(self):
        spec = {'a': {'b': int}}
        # value is absent
        assert {'a': {'b': None}} == merged(spec, {})
        assert {'a': {'b': None}} == merged(spec, {'a': None})
        assert {'a': {'b': None}} == merged(spec, {'a': {}})
        assert {'a': {'b': None}} == merged(spec, {'a': {'b': None}})
        # value is present
        assert {'a': {'b': 1234}} == merged(spec, {'a': {'b': 1234}})

    @pytest.mark.xfail()
    def test_type_in_list(self):
        assert {'a': [int]} == merged({}, {'a': []})
        assert {'a': [int]} == merged({'a': []}, {'a': []})

    @pytest.mark.xfail()
    def test_instance(self):
        assert {'a': 1} == merged({'a': 1}, {})

    @pytest.mark.xfail()
    def test_instance_in_dict(self):
        assert {'a': {'b': 1}} == merged({'a': {'b': 1}}, {})

    @pytest.mark.xfail()
    def test_instance_in_list(self):
        assert {'a': [1]} == merged({}, {'a': [1]})
        assert {'a': [1]} == merged({'a': []}, {'a': [1]})
        assert {'a': [0]} == merged({'a': [0]}, {'a': [0]})

    @pytest.mark.xfail()
    def test_instance_in_list_of_dicts(self):
        assert {'a': {'b': 1}} == merged({'a': [{'b': 1}]}, {})
        assert {'a': {'b': 1}} == merged({'a': [{'b': 1}]}, {'a': []})
        assert {'a': {'b': 1}} == merged({'a': [{'b': 1}]}, {'a': [{}]})
        assert {'a': {'b': 0}} == merged({'a': [{'b': 1}]}, {'a': [{'b': 0}]})

    @pytest.mark.xfail()
    def test_complex_list_of_dicts(self):
        "some items are populated, some aren't"
        spec = {
            'a': [
                {'b': 1}
            ]
        }
        data = {
            'a': [
                { },
                {'b': 2}
            ]
        }
        expected = {
            'a': [
                {'b': 1},
                {'b': 2}
            ]
        }
        assert merged(spec, data) == expected
