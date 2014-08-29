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
~~~~~~~~~~~~~~~~~~~~~~~~~~
Tests for Merging Defaults
~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import mock
import pytest

from monk.compat import text_type as t
from monk.combinators import Any
from monk.reqs import (
    Anything, IsA, DictOf, ListOf, Equals, NotExists,
    translate
)
from monk.schema import optional
import monk.manipulation as m


class TestValidators:
    """
    Validator-specific mergers
    """
    def test_merge_anything(self):
        # "any value is OK"
        assert Anything().get_default_for(None) == None
        assert Anything().get_default_for(1234) == 1234
        assert Anything().get_default_for('hi') == 'hi'
        assert Anything().get_default_for({1: 2}) == {1: 2}

    def test_merge_isa__dict(self):
        # TODO use a single test for all types used with IsA

        # optional missing dictionary
        assert (IsA(dict) | Equals(None)).get_default_for(None) == None

        # XXX CHANGED
        ## required missing dictionary → empty dictionary
        #assert IsA(dict).get_default_for(None) == {}
        assert IsA(dict).get_default_for(None) == None

        # required empty dictionary
        assert IsA(dict).get_default_for({}) == {}

        # required non-empty dictionary
        assert IsA(dict).get_default_for({'x': 1}) == {'x': 1}

    def test_merge_dictof(self):

        ## present non-empty inner spec (optional)
        spec = DictOf([
            (Equals('a'), IsA(int, default=1)),
        ]) | Equals(None)

        # optional missing dictionary with required key
        assert spec.get_default_for(None) == None

        # optional empty dictionary with required key
        assert spec.get_default_for({}) == {'a': 1}

        ## present non-empty inner spec (optional)
        spec = DictOf([
            (Equals('a'), IsA(int, default=1) | Equals(None)),
        ])

        # optional missing dictionary with optional key
        # XXX CHANGED
        #assert spec.get_default_for(None) == None
        assert spec.get_default_for(None) == {'a': None}

        # optional empty dictionary with optional key
        # XXX CHANGED
        # (if the value can be either int or None, why choose one?
        # here we set None not because of Equals(None) but because
        # we *mean* None — no value could be chosen.
        #assert spec.get_default_for({}) == {'a': 1}
        assert spec.get_default_for({}) == {'a': None}

        ## present non-empty inner spec (required)
        spec = DictOf([
            (Equals('a'), IsA(int, default=1)),
        ])

        # required missing dictionary → inner spec
        assert spec.get_default_for({}) == {'a': 1}

        # required empty dictionary → inner spec
        assert spec.get_default_for({}) == {'a': 1}

        # XXX CHANGED
        ## required non-empty dictionary → inner spec
        #fallback = lambda s, v, **kw: v
        #assert m.merge_defaults(rule, {'a': 2}, {}, fallback) == {'a': 2}
        #assert m.merge_defaults(rule, {'b': 3}, {}, fallback) == {'a': 1, 'b': 3}

        # bogus value; will not pass validation but should be preserved
        assert spec.get_default_for(123) == 123

    def test_merge_list(self):

        ## present but empty inner spec (optional)
        rule = ListOf([]) | Equals(None)

        # optional missing list
        assert rule.get_default_for(None) == None

        ## present but empty inner spec (required)
        rule = ListOf([])

        # required missing list → empty list
        assert rule.get_default_for(None) == []

        ## present non-empty inner spec (optional)
        rule = ListOf(IsA(int, default=123)) | Equals(None)

        # optional missing list with required item(s)
        assert rule.get_default_for(None) == None

        # optional empty list with required item(s)
        assert rule.get_default_for([]) == []

        ## present non-empty inner spec (optional)
        elem_spec = IsA(int, default=123) | Equals(None)
        rule = ListOf(elem_spec) | Equals(None)

        # optional missing list with optional item(s)
        assert rule.get_default_for(None) == None

        # optional empty list with optional item
        assert rule.get_default_for([]) == []

        ## present non-empty inner spec (required)
        rule = ListOf(IsA(int, default=123))

        # required missing list → inner spec
        assert rule.get_default_for(None) == []

        # required empty list → inner spec
        assert rule.get_default_for([]) == []

        # required non-empty list → inner spec
#        fallback = lambda s, v, **kw: v
        assert rule.get_default_for([None]) == [None]
        assert rule.get_default_for([456]) == [456]

        ## present inner spec with empty item spec
        rule = ListOf(Anything())
        assert rule.get_default_for([456]) == [456]

        ## present inner spec with item spec that has an inner spec
        #rule = Rule(datatype=list, inner_spec=[123])
        rule = ListOf(ListOf(IsA(int, default=123)))

        # XXX CHANGED    WTF was it before!?
        ##assert rule.get_default_for([None]) == [123]
        #assert rule.get_default_for([[]]) == [[123]]

        # bogus value; will not pass validation but should be preserved
        assert rule.get_default_for(123) == 123

    def test_merge_list_with_oneof(self):
        "Non-rule node in list's inner spec"

        # TODO: refactor and reformulate.
        #       This test was written for older implementation of Monk.

        int_spec = IsA(int, default=123)
        str_spec = IsA(str, default='foo')

        # no defaults

        #rule = Rule(datatype=list, inner_spec=OneOf([123, 456]))
        item_spec = Any([int_spec, str_spec])
        rule = ListOf(item_spec)
        assert rule.get_default_for([]) == []
        assert rule.get_default_for([789]) == [789]

        # with defaults
        # (same results because defaults have no effect on lists)

        #rule = Rule(datatype=list,
        #            inner_spec=OneOf([123, 456], first_is_default=True))

        item_spec = Any([int_spec, str_spec], first_is_default=True)
        rule = ListOf(item_spec)
        assert rule.get_default_for([]) == []
        assert rule.get_default_for([789]) == [789]


class TestNaturalNotation:
    """
    Tests for :func:`merge_defaults` with "natural" notation
    and more or less complex (and random) cases.

    These were written much earlier than :class:`TestMergingDefaults`
    and may be outdated in terms of organization.
    """
    def test_merge(self):
        spec = translate({'a': 1})

        assert spec.get_default_for({'b': 2}) == {'a': 1, 'b': 2}

    def test_none_in_dict(self):
        spec = translate({'a': None})
        assert spec.get_default_for({}) == {'a': None}
        assert spec.get_default_for({'a': None}) == {'a': None}
        assert spec.get_default_for({'a': 1234}) == {'a': 1234}

    def test_type_in_dict(self):
        spec = translate({'a': t})

        assert spec.get_default_for({}) == {'a': None}
        assert spec.get_default_for({'a': None}) == {'a': None}
        assert spec.get_default_for({'a': t('a')}) == {'a': t('a')}

    def test_type_in_dict_in_dict(self):
        spec = translate({'a': {'b': int}})

        # key is absent; should be inserted
        assert spec.get_default_for({}) == {'a': {'b': None}}
        # same with nested key
        assert spec.get_default_for({'a': {}}) == {'a': {'b': None}}

        # key is present but value is None; should be overridden with defaults
        #
        #   XXX do we really need to override *present* values in data
        #       even if they are None?
        #
        assert spec.get_default_for({'a': None}) == {'a': {'b': None}}
        assert spec.get_default_for({'a': {'b': None}}) == {'a': {'b': None}}

        # key is present, value is not None; leave as is
        # (even if it won't pass validation)
        assert spec.get_default_for({'a': {'b': 1234}}) == {'a': {'b': 1234}}
        assert spec.get_default_for({'a': t('bogus string')}) == {'a': t('bogus string')}

    def test_type_in_list_in_dict(self):
        spec = translate({'a': [int]})

        assert spec.get_default_for({'a': []}) == {'a': []}
        assert spec.get_default_for({'a': [123]}) == {'a': [123]}
        assert spec.get_default_for({'a': [123, 456]}) == {'a': [123, 456]}

    def test_rule_in_list(self):
        spec = translate({'a': [IsA(int)]})

        assert spec.get_default_for({'a': []}) == {'a': []}
        assert spec.get_default_for({'a': None}) == {'a': []}
        assert spec.get_default_for({}) == {'a': []}

    def test_instance_in_dict(self):
        spec = translate({'a': 1})

        assert spec.get_default_for({}) == {'a': 1}

    def test_instance_in_dict(self):
        spec = translate({'a': {'b': 1}})

        assert spec.get_default_for({}) == {'a': {'b': 1}}

    def test_instance_in_list_in_dict(self):
        spec = translate({})

        assert spec.get_default_for({'a': [1]}) == {'a': [1]}

        spec = translate({'a': [0]})

        assert spec.get_default_for({'a': [0]}) == {'a': [0]}
        assert spec.get_default_for({'a': [0, 1]}) == {'a': [0, 1]}

    def test_instance_in_list_of_dicts_in_dict(self):
        spec = translate({'a': [{'b': 1}]})

        assert spec.get_default_for({}) == {'a': []}
        assert spec.get_default_for({'a': []}) == {'a': []}
        assert spec.get_default_for({'a': [{}]}) == {'a': [{'b': 1}]}
        assert spec.get_default_for({'a': [{'b': 0}]}) == {'a': [{'b': 0}]}

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
        spec = translate({})
        data = {'a': [{'b': {'c': 123}}]}
        assert spec.get_default_for(data) == data

    def test_unexpected_dict_in_dict(self):
        """ Non-dictionary in spec, dict in data.
        Data is preserved though won't validate.
        """
        spec = translate({'a': t})
        data = {'a': {'b': 123}}
        assert spec.get_default_for(data) == data

    def test_unexpected_list_in_dict(self):
        """ Non-list in spec, list in data.
        Data is preserved though won't validate.
        """
        spec = translate({'a': t})
        data = {'a': [123]}
        assert spec.get_default_for(data) == data

    def test_callable_in_dict(self):
        """ Callable defaults.
        """
        spec = translate({'text': lambda: t('hello')})
        data = {}
        expected = {'text': t('hello')}
        assert m.merge_defaults(spec, data) == expected

    def test_callable_nested_in_dict(self):
        """ Nested callable defaults.
        """
        spec = translate({'content': {'text': lambda: t('hello')}})
        data = {}
        expected = {'content': {'text': t('hello')}}
        assert m.merge_defaults(spec, data) == expected

    def test_validator_in_dict(self):
        spec = translate({'foo': IsA(str, default='bar')})
        data = {}
        expected = {'foo': 'bar'}
        assert m.merge_defaults(spec, data) == expected

    def test_required_inside_optional_dict_in_dict(self):
        spec = translate({
            'foo': optional({
                'a': 1,
                'b': optional(2),
            }),
        })

        data = {}
        expected = {'foo': None}
        assert m.merge_defaults(spec, data) == expected

        data = {'foo': None}
        expected = {'foo': None}
        assert m.merge_defaults(spec, data) == expected

        data = {'foo': {}}
        # XXX CHANGED:
        #expected = {'foo': {'a': 1, 'b': 2}}
        expected = {'foo': {'a': 1, 'b': None}}
        assert m.merge_defaults(spec, data) == expected

        data = {'foo': {'a': 3}}
        # XXX CHANGED:
        #expected = {'foo': {'a': 3, 'b': 2}}
        expected = {'foo': {'a': 3, 'b': None}}
        assert m.merge_defaults(spec, data) == expected

        data = {'foo': {'b': 3}}
        expected = {'foo': {'a': 1, 'b': 3}}
        assert m.merge_defaults(spec, data) == expected


class TestMisc:
    """
    Some cases not covered elsewhere.
    """
    def test_defaults_from_rule(self):
        "Default value from rule"
        assert IsA(int, default=1).get_default_for(None) == 1
        assert IsA(int, default=1).get_default_for(2) == 2

    def test_rule_as_key(self):
        spec_a = DictOf([ (IsA(str), IsA(int)) ])
        spec_b = DictOf([ (IsA(str) | NotExists(), IsA(int)) ])

        assert spec_a.get_default_for({}) == {}
        assert spec_b.get_default_for({}) == {}

    def test_merge_oneof(self):
        str_rule = IsA(str, default='hello')
        int_rule = IsA(int, default=123)

        schema = Any([str_rule, int_rule])
        assert schema.get_default_for(None) == None

        schema = Any([str_rule, int_rule], default=456)
        assert schema.get_default_for(None) == 456

        schema = Any([str_rule, int_rule], first_is_default=True)
        assert schema.get_default_for(None) == 'hello'

        schema = Any([int_rule, str_rule], first_is_default=True)
        assert schema.get_default_for(None) == 123

    def test_merge_dictof_dictof_isa(self):
        raw_spec = {
            'content': {
                'text': t('hello'),
            },
        }

        spec = translate(raw_spec)

        # make sure translation went as expected
        assert spec == DictOf([
            (Equals('content'), DictOf([
                (Equals('text'), IsA(t, default=t('hello'))),
            ])),
        ])

        # make sure merging works as expected for nested dict
        assert raw_spec == spec.get_default_for({'content': {}})

        # make sure merging works as expected for nested *and* root dicts
        assert raw_spec == spec.get_default_for({})
