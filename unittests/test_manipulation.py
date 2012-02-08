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
    def test_merge(self):
        assert {'a': 1, 'b': 2} == merged({'a': 1}, {'b': 2})

    def test_none(self):
        assert {'a': None} == merged({'a': None}, {})
        assert {'a': None} == merged({'a': None}, {'a': None})
        assert {'a': 1234} == merged({'a': None}, {'a': 1234})

    def test_type(self):
        assert {'a': None} == merged({'a': unicode}, {})
        assert {'a': None} == merged({'a': unicode}, {'a': None})
        assert {'a': u'a'} == merged({'a': unicode}, {'a': u'a'})

    def test_type_in_dict(self):
        spec = {'a': {'b': int}}

        # key is absent; should be inserted
        assert {'a': {'b': None}} == merged(spec, {})
        # same with nested key
        assert {'a': {'b': None}} == merged(spec, {'a': {}})

        # key is present but value is None; should be overridden with defaults
        #
        #   XXX do we really need to override *present* values in data
        #       even if they are None?
        #
        assert {'a': {'b': None}} == merged(spec, {'a': None})
        assert {'a': {'b': None}} == merged(spec, {'a': {'b': None}})

        # key is present, value is not None; leave as is
        # (even if it won't pass validation)
        assert {'a': {'b': 1234}} == merged(spec, {'a': {'b': 1234}})
        assert {'a': u'bogus string'} == merged(spec, {'a': u'bogus string'})

    def test_type_in_list(self):
        assert {'a': []} == merged({'a': [int]}, {'a': []})
        assert {'a': [123]} == merged({'a': [int]}, {'a': [123]})
        assert {'a': [123, 456]} == merged({'a': [int]}, {'a': [123, 456]})

    def test_instance(self):
        assert {'a': 1} == merged({'a': 1}, {})

    def test_instance_in_dict(self):
        assert {'a': {'b': 1}} == merged({'a': {'b': 1}}, {})

    def test_instance_in_list(self):
        assert {'a': [1]} == merged({}, {'a': [1]})
        assert {'a': [1]} == merged({'a': []}, {'a': [1]})
        assert {'a': [0]} == merged({'a': [0]}, {'a': [0]})
        assert {'a': [0, 1]} == merged({'a': [0]}, {'a': [0, 1]})

    def test_instance_in_list_of_dicts(self):
        spec = {'a': [{'b': 1}]}
        assert {'a': []} == merged(spec, {})
        assert {'a': []} == merged(spec, {'a': []})
        assert {'a': [{'b': 1}]} == merged(spec, {'a': [{}]})
        assert {'a': [{'b': 0}]} == merged(spec, {'a': [{'b': 0}]})

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
                {'c': 1},
                {'b': 2, 'c': {'d': 1}}
            ]
        }
        expected = {
            'a': [
                {'b': 1},
                {'b': 1, 'c': 1},
                {'b': 2, 'c': {'d': 1}}
            ]
        }
        assert merged(spec, data) == expected

    def test_custom_structures(self):
        "custom keys should not be lost even if they are not in spec"
        data = {'a': [{'b': {'c': 123}}]}
        assert data == merged({}, data)

    def test_unexpected_dict(self):
        """ Non-dictionary in spec, dict in data.
        Data is preserved though won't validate.
        """
        assert {'a': {'b': 123}} == merged({'a': unicode}, {'a': {'b': 123}})

    def test_unexpected_list(self):
        """ Non-list in spec, list in data.
        Data is preserved though won't validate.
        """
        assert {'a': [123]} == merged({'a': unicode}, {'a': [123]})

    def test_callable(self):
        """ Callable defaults.
        """
        spec = {'text': lambda: u'hello'}
        data = {}
        expected = {'text': u'hello'}
        assert merged(spec, data) == expected

    def test_callable_nested(self):
        """ Nested callable defaults.
        """
        spec = {'content': {'text': lambda: u'hello'}}
        data = {}
        expected = {'content': {'text': u'hello'}}
        assert merged(spec, data) == expected
