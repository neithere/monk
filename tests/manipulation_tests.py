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
Data manipulation tests
=======================
"""
import mock
import pytest

from monk.compat import text_type as t
from monk.schema import Rule, OneOf, optional
import monk.manipulation as m


class TestMergingDefaults:
    "Basic behaviour of merge_defaults()"

    def test_defaults_from_rule(self):
        "Default value from rule"
        rule = Rule(int, default=1)
        assert m.merge_defaults(rule, None) == 1
        assert m.merge_defaults(rule, 2) == 2

    def test_type_merger(self):
        "No default value → datatype-specific merger"
        type_merger = mock.Mock()
        fallback = mock.Mock()

        m.merge_defaults(
            Rule(int), 1, {int: type_merger}, fallback)

        type_merger.assert_called_once_with(
            Rule(int), 1, mergers={int: type_merger}, fallback=fallback)
        fallback.assert_not_called()

    def test_fallback(self):
        "No datatype-specific merger → fallback merger"
        type_merger = mock.Mock()
        fallback = mock.Mock()

        m.merge_defaults(
            Rule(int), 1, {str: type_merger}, fallback)

        type_merger.assert_not_called()
        fallback.assert_called_once_with(
            Rule(int), 1, mergers={str: type_merger}, fallback=fallback)

    def test_deprecation(self):
        "Deprecated function wraps the new one"
        with mock.patch('monk.manipulation.merge_defaults') as new_func:
            with mock.patch('warnings.warn') as warn:
                new_func.return_value = 'returned'
                m.merged('spec', 'value', 'mergers') == 'returned'
                new_func.assert_called_once_with('spec', 'value', mergers='mergers')
                warn.assert_called_once_with(
                    'merged() is deprecated, use merge_defaults() instead',
                    DeprecationWarning)

    def test_rule_as_key(self):
        spec_a = {Rule(str): int}
        spec_b = {Rule(str, optional=True): int}

        assert m.merged(spec_a, {}) == {}
        assert m.merged(spec_b, {}) == {}

    def test_merge_oneof(self):
        str_rule = Rule(datatype=str, default='hello')
        int_rule = Rule(datatype=int, default=123)

        schema = OneOf([str_rule, int_rule])
        assert m.merge_defaults(schema, None) == None

        schema = OneOf([str_rule, int_rule], first_is_default=True)
        assert m.merge_defaults(schema, None) == 'hello'

        schema = OneOf([int_rule, str_rule], first_is_default=True)
        assert m.merge_defaults(schema, None) == 123


class TestMergingDefaultsTypeSpecific:
    "Type-specific mergers"

    def test_default_type_mergers(self):

        assert m.TYPE_MERGERS == {
            dict: m.merge_dict,
            list: m.merge_list,
        }

    def test_merge_any(self):

        # datatype None stands for "any value is OK"
        rule = Rule(datatype=None)

        assert m.merge_any(rule, None, {}, None) == None
        assert m.merge_any(rule, 1234, {}, None) == 1234
        assert m.merge_any(rule, 'hi', {}, None) == 'hi'
        assert m.merge_any(rule, {1:2}, {}, None) == {1:2}

    def test_merge_dict(self):

        with pytest.raises(AssertionError):
            # function should check for rule datatype
            m.merge_dict(Rule(datatype=int), None, {}, None)

    def test_merge_dict_type(self):

        rule = Rule(datatype=dict, optional=True)

        # optional missing dictionary
        assert m.merge_dict(rule, None, {}, None) == None

        rule = Rule(datatype=dict)

        # required missing dictionary → empty dictionary
        assert m.merge_dict(rule, None, {}, None) == {}

        # required empty dictionary
        assert m.merge_dict(rule, {}, {}, None) == {}

        # required non-empty dictionary
        assert m.merge_dict(rule, {'x': 1}, {}, None) == {'x': 1}

    def test_merge_dict_innerspec(self):

        ## present but empty inner spec (optional)
        rule = Rule(datatype=dict, inner_spec={}, optional=True)

        # optional missing dictionary
        assert m.merge_dict(rule, None, {}, None) == None

        ## present but empty inner spec (required)
        rule = Rule(datatype=dict, inner_spec={})

        # required missing dictionary → empty dictionary
        assert m.merge_dict(rule, None, {}, None) == {}

        ## present non-empty inner spec (optional)
        rule = Rule(datatype=dict, inner_spec={'a': 1}, optional=True)

        # optional missing dictionary with required key
        assert m.merge_dict(rule, None, {}, None) == None

        # optional empty dictionary with required key
        assert m.merge_dict(rule, {}, {}, None) == {'a': 1}

        ## present non-empty inner spec (optional)
        rule = Rule(datatype=dict, inner_spec={'a': optional(1)},
                    optional=True)

        # optional missing dictionary with optional key
        assert m.merge_dict(rule, None, {}, None) == None

        # optional empty dictionary with optional key
        assert m.merge_dict(rule, {}, {}, None) == {'a': 1}

        ## present non-empty inner spec (required)
        rule = Rule(datatype=dict, inner_spec={'a': 1})

        # required missing dictionary → inner spec
        assert m.merge_dict(rule, None, {}, None) == {'a': 1}

        # required empty dictionary → inner spec
        assert m.merge_dict(rule, {}, {}, None) == {'a': 1}

        # required non-empty dictionary → inner spec
        fallback = lambda s, v, **kw: v
        assert m.merge_dict(rule, {'a': 2}, {}, fallback) == {'a': 2}
        assert m.merge_dict(rule, {'b': 3}, {}, fallback) == {'a': 1, 'b': 3}

        # bogus value; will not pass validation but should be preserved
        assert m.merge_dict(rule, 123, {}, None) == 123

    def test_merge_list(self):

        ## present but empty inner spec (optional)
        rule = Rule(datatype=list, inner_spec=[], optional=True)

        # optional missing list
        assert m.merge_list(rule, None, {}, None) == None

        ## present but empty inner spec (required)
        rule = Rule(datatype=list, inner_spec=[])

        # required missing list → empty list
        assert m.merge_list(rule, None, {}, None) == []

        ## present non-empty inner spec (optional)
        rule = Rule(datatype=list, inner_spec=123, optional=True)

        # optional missing list with required item(s)
        assert m.merge_list(rule, None, {}, None) == None

        # optional empty list with required item(s)
        assert m.merge_list(rule, [], {}, None) == []

        ## present non-empty inner spec (optional)
        rule = Rule(datatype=list, inner_spec=[optional(1)],
                    optional=True)

        # optional missing list with optional item(s)
        assert m.merge_list(rule, None, {}, None) == None

        # optional empty list with optional item
        assert m.merge_list(rule, [], {}, None) == []

        ## present non-empty inner spec (required)
        rule = Rule(datatype=list, inner_spec=123)

        # required missing list → inner spec
        assert m.merge_list(rule, None, {}, None) == []

        # required empty list → inner spec
        assert m.merge_list(rule, [], {}, None) == []

        # required non-empty list → inner spec
        fallback = lambda s, v, **kw: v
        assert m.merge_list(rule, [None], {}, fallback) == [None]
        assert m.merge_list(rule, [456], {}, fallback) == [456]

        ## present inner spec with empty item spec
        rule = Rule(datatype=list, inner_spec=None)

        assert m.merge_list(rule, [456], {}, fallback) == [456]

        ## present inner spec with item spec that has an inner spec
        rule = Rule(datatype=list, inner_spec=[123])

        assert m.merge_list(rule, [None], {}, fallback) == [123]

        # bogus value; will not pass validation but should be preserved
        assert m.merge_list(rule, 123, {}, None) == 123

    def test_merge_list_with_oneof(self):
        "Non-rule node in list's inner spec"

        # no defaults
        rule = Rule(datatype=list, inner_spec=OneOf([123, 456]))
        assert m.merge_defaults(rule, []) == []
        assert m.merge_defaults(rule, [789]) == [789]

        # with defaults
        # (same results because defaults have no effect on lists)
        rule = Rule(datatype=list,
                    inner_spec=OneOf([123, 456], first_is_default=True))
        assert m.merge_defaults(rule, []) == []
        assert m.merge_defaults(rule, [789]) == [789]


class TestMergingDefaultsNaturalNotation:
    """
    Tests for :func:`merge_defaults` with "natural" notation
    and more or less complex (and random) cases.

    These were written much earlier than :class:`TestMergingDefaults`
    and may be outdated in terms of organization.
    """

    def test_merge(self):
        assert {'a': 1, 'b': 2} == m.merge_defaults({'a': 1}, {'b': 2})

    def test_none(self):
        assert {'a': None} == m.merge_defaults({'a': None}, {})
        assert {'a': None} == m.merge_defaults({'a': None}, {'a': None})
        assert {'a': 1234} == m.merge_defaults({'a': None}, {'a': 1234})

    def test_type(self):
        assert {'a': None} == m.merge_defaults({'a': t}, {})
        assert {'a': None} == m.merge_defaults({'a': t}, {'a': None})
        assert {'a': t('a')} == m.merge_defaults({'a': t}, {'a': t('a')})

    def test_type_in_dict(self):
        spec = {'a': {'b': int}}

        # key is absent; should be inserted
        assert {'a': {'b': None}} == m.merge_defaults(spec, {})
        # same with nested key
        assert {'a': {'b': None}} == m.merge_defaults(spec, {'a': {}})

        # key is present but value is None; should be overridden with defaults
        #
        #   XXX do we really need to override *present* values in data
        #       even if they are None?
        #
        assert {'a': {'b': None}} == m.merge_defaults(spec, {'a': None})
        assert {'a': {'b': None}} == m.merge_defaults(spec, {'a': {'b': None}})

        # key is present, value is not None; leave as is
        # (even if it won't pass validation)
        assert {'a': {'b': 1234}} == m.merge_defaults(spec, {'a': {'b': 1234}})
        assert {'a': t('bogus string')} == m.merge_defaults(spec, {'a': t('bogus string')})

    def test_type_in_list(self):
        assert {'a': []} == m.merge_defaults({'a': [int]}, {'a': []})
        assert {'a': [123]} == m.merge_defaults({'a': [int]}, {'a': [123]})
        assert {'a': [123, 456]} == m.merge_defaults({'a': [int]}, {'a': [123, 456]})

    def test_rule_in_list(self):
        assert {'a': []} == m.merge_defaults({'a': [Rule(datatype=int)]}, {'a': []})
        assert {'a': []} == m.merge_defaults({'a': [Rule(datatype=int)]}, {'a': None})
        assert {'a': []} == m.merge_defaults({'a': [Rule(datatype=int)]}, {})

    def test_instance(self):
        assert {'a': 1} == m.merge_defaults({'a': 1}, {})

    def test_instance_in_dict(self):
        assert {'a': {'b': 1}} == m.merge_defaults({'a': {'b': 1}}, {})

    def test_instance_in_list(self):
        assert {'a': [1]} == m.merge_defaults({}, {'a': [1]})
        assert {'a': [1]} == m.merge_defaults({'a': []}, {'a': [1]})
        assert {'a': [0]} == m.merge_defaults({'a': [0]}, {'a': [0]})
        assert {'a': [0, 1]} == m.merge_defaults({'a': [0]}, {'a': [0, 1]})

    def test_instance_in_list_of_dicts(self):
        spec = {'a': [{'b': 1}]}
        assert {'a': []} == m.merge_defaults(spec, {})
        assert {'a': []} == m.merge_defaults(spec, {'a': []})
        assert {'a': [{'b': 1}]} == m.merge_defaults(spec, {'a': [{}]})
        assert {'a': [{'b': 0}]} == m.merge_defaults(spec, {'a': [{'b': 0}]})

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
        assert m.merge_defaults(spec, data) == expected

    def test_custom_structures(self):
        "custom keys should not be lost even if they are not in spec"
        data = {'a': [{'b': {'c': 123}}]}
        assert data == m.merge_defaults({}, data)

    def test_unexpected_dict(self):
        """ Non-dictionary in spec, dict in data.
        Data is preserved though won't validate.
        """
        assert {'a': {'b': 123}} == m.merge_defaults({'a': t}, {'a': {'b': 123}})

    def test_unexpected_list(self):
        """ Non-list in spec, list in data.
        Data is preserved though won't validate.
        """
        assert {'a': [123]} == m.merge_defaults({'a': t}, {'a': [123]})

    def test_callable(self):
        """ Callable defaults.
        """
        spec = {'text': lambda: t('hello')}
        data = {}
        expected = {'text': t('hello')}
        assert m.merge_defaults(spec, data) == expected

    def test_callable_nested(self):
        """ Nested callable defaults.
        """
        spec = {'content': {'text': lambda: t('hello')}}
        data = {}
        expected = {'content': {'text': t('hello')}}
        assert m.merge_defaults(spec, data) == expected

    def test_rule_merger(self):
        spec = {'foo': Rule(str, default='bar')}
        data = {}
        expected = {'foo': 'bar'}
        assert m.merge_defaults(spec, data) == expected

    def test_required_inside_optional_dict(self):
        spec = {'foo': optional({'a': 1, 'b': optional(2)})}

        data = {}
        expected = {'foo': None}
        assert m.merge_defaults(spec, data) == expected

        data = {'foo': None}
        expected = {'foo': None}
        assert m.merge_defaults(spec, data) == expected

        data = {'foo': {}}
        expected = {'foo': {'a': 1, 'b': 2}}
        assert m.merge_defaults(spec, data) == expected

        data = {'foo': {'a': 3}}
        expected = {'foo': {'a': 3, 'b': 2}}
        assert m.merge_defaults(spec, data) == expected

        data = {'foo': {'b': 3}}
        expected = {'foo': {'a': 1, 'b': 3}}
        assert m.merge_defaults(spec, data) == expected


class TestMolding:
    def test_normalize_to_list(self):
        assert [1] == m.normalize_to_list(1)
        assert [1] == m.normalize_to_list([1])

    def test_normalize_list_of_dicts(self):
        assert [{'x': 'a'}] == m.normalize_list_of_dicts([{'x': 'a'}], default_key='x')
        assert [{'x': 'a'}] == m.normalize_list_of_dicts( {'x': 'a'}, default_key='x')
        assert [{'x': 'a'}] == m.normalize_list_of_dicts(     t('a'), default_key='x')
        assert [{'x': 'a'}, {'x': 'b'}] == \
            m.normalize_list_of_dicts([{'x': 'a'}, t('b')], default_key='x')
        assert [] == m.normalize_list_of_dicts(None, default_key='x')
        assert [{'x': t('y')}] == m.normalize_list_of_dicts(None, default_key='x',
                                                            default_value=t('y'))

        # edge cases (may need revision)
        assert [{'x': 1}] == m.normalize_list_of_dicts({'x': 1}, default_key='y')
        assert [] == m.normalize_list_of_dicts(None, default_key='y')
        assert 123 == m.normalize_list_of_dicts(123, default_key='x')

