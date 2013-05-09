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
Validation tests
================
"""
import datetime
import sys

import bson
import pytest

from monk.compat import text_type, safe_unicode
from monk.schema import Rule, canonize, optional, any_value, any_or_none
from monk.validation import (
    validate, StructureSpecificationError,
    MissingKey, UnknownKey
)


# FIXME decide if this is still needed
validate_spec = NotImplemented


class TestStructureSpec:

    @pytest.mark.xfail
    def test_correct_types(self):
        '`None` stands for "any value".'
        validate_spec({'foo': None})
        validate_spec({'foo': bool})
        validate_spec({'foo': dict})
        validate_spec({'foo': float})
        validate_spec({'foo': int})
        validate_spec({'foo': list})
        validate_spec({'foo': text_type})
        validate_spec({'foo': datetime.datetime})
        validate_spec({'foo': bson.Binary})
        validate_spec({'foo': bson.Code})
        validate_spec({'foo': bson.ObjectId})
        validate_spec({'foo': bson.DBRef})

    @pytest.mark.xfail
    def test_correct_structures(self):
        # foo is of given type
        validate_spec({'foo': int})
        # foo and bar are of given types
        validate_spec({'foo': int, 'bar': text_type})
        # foo is a list of values of given type
        validate_spec({'foo': [int]})
        # foo.bar is of given type
        validate_spec({'foo': {'bar': int}})
        # foo.bar is a list of values of given type
        validate_spec({'foo': {'bar': [int]}})
        # foo.bar is a list of mappings where each "baz" is of given type
        validate_spec({'foo': {'bar': [{'baz': [text_type]}]}})

    @pytest.mark.xfail
    def test_malformed_lists(self):
        single_elem_err_msg = 'empty list or a list containing exactly 1 item'

        with pytest.raises(StructureSpecificationError) as excinfo:
            validate_spec({'foo': [text_type, text_type]})
        assert single_elem_err_msg in excinfo.exconly()

        with pytest.raises(StructureSpecificationError) as excinfo:
            validate_spec({'foo': {'bar': [text_type, text_type]}})
        assert single_elem_err_msg in excinfo.exconly()

        with pytest.raises(StructureSpecificationError) as excinfo:
            validate_spec({'foo': {'bar': [{'baz': [text_type, text_type]}]}})
        assert single_elem_err_msg in excinfo.exconly()


class TestDocumentStructureValidation:

    def test_correct_structures(self):
        '''
        # foo is of given type
        validate({'foo': int}, {}, optional=True)
        # foo and bar are of given types
        validate({'foo': int, 'bar': unicode}, {}, optional=True)
        # foo is a list of values of given type
        validate({'foo': [int]}, {}, optional=True)
        # foo.bar is of given type
        validate({'foo': {'bar': int}}, {}, optional=True)
        # foo.bar is a list of values of given type
        validate({'foo': {'bar': [int]}}, {}, optional=True)
        # foo.bar is a list of mappings where each "baz" is of given type
        validate({'foo': {'bar': [{'baz': [unicode]}]}}, {}, optional=True)
        '''

    def test_malformed_lists(self):
        pass

    #---

    def test_bad_types(self):
        with pytest.raises(TypeError) as excinfo:
            validate({'a': int}, {'a': 'bad'})
        assert "a: expected int, got str 'bad'" in excinfo.exconly()

        with pytest.raises(TypeError) as excinfo:
            validate({'a': [int]}, {'a': 'bad'})
        assert "a: expected list, got str 'bad'" in excinfo.exconly()

        with pytest.raises(TypeError) as excinfo:
            validate({'a': [int]}, {'a': ['bad']})
        assert "a: expected int, got str 'bad'" in excinfo.exconly()

        with pytest.raises(TypeError) as excinfo:
            validate({'a': {'b': int}}, {'a': 'bad'})
        assert "a: expected dict, got str 'bad'" in excinfo.exconly()

        with pytest.raises(TypeError) as excinfo:
            validate({'a': {'b': int}}, {'a': {'b': 'bad'}})
        assert "a: b: expected int, got str 'bad'" in excinfo.exconly()

        with pytest.raises(TypeError) as excinfo:
            validate({'a': [{'b': [int]}]}, {'a': [{'b': ['bad']}]})
        assert "a: b: expected int, got str 'bad'" in excinfo.exconly()

    def test_empty(self):
        validate({'a': text_type}, {'a': None})
        validate({'a': list}, {'a': None})
        validate({'a': dict}, {'a': None})

        # None is allowed to represent empty value, but bool(value)==False
        # is not (unless bool is the correct type for this value)
        validate({'a': bool}, {'a': None})
        validate({'a': bool}, {'a': False})
        with pytest.raises(TypeError):
            validate({'a': text_type}, {'a': False})
        with pytest.raises(TypeError):
            validate({'a': text_type}, {'a': 0})
        with pytest.raises(TypeError):
            validate({'a': bool}, {'a': ''})

    def test_missing(self):
        validate({'a': Rule(text_type, optional=True)}, {})
        with pytest.raises(MissingKey):
            validate({'a': text_type}, {})
        with pytest.raises(MissingKey):
            validate({'a': text_type, 'b': int}, {'b': 1})

    def test_unknown_keys(self):
        # verbose notation
        validate(Rule(dict, skip_unknown_keys=True), {'x': 123})

        # special behaviour: missing/empty inner_spec means "a dict of anything"
        validate(Rule(dict), {'x': 123})

        # inner_spec not empty, value matches it
        validate({'x': None}, {'x': 123})

        with pytest.raises(UnknownKey):
            validate({'x': None}, {'y': 123})

        with pytest.raises(UnknownKey):
            validate({'x': None}, {'x': 123, 'y': 456})

    def test_unknown_keys_encoding(self):
        with pytest.raises(UnknownKey):
            validate({'a': text_type}, {'привет': 1})
        with pytest.raises(UnknownKey):
            validate({'a': text_type}, {safe_unicode('привет'): 1})

    def test_bool(self):
        validate({'a': bool}, {'a': None})
        validate({'a': bool}, {'a': True})
        validate({'a': bool}, {'a': False})

    def test_bool_instance(self):
        validate({'a': True}, {'a': None})
        validate({'a': True}, {'a': True})
        validate({'a': True}, {'a': False})

    def test_dict(self):
        validate({'a': dict}, {'a': None})
        validate({'a': dict}, {'a': {}})
        validate({'a': dict}, {'a': {'b': 'c'}})

    def test_dict_instance(self):
        validate({'a': {}}, {'a': None})
        validate({'a': {}}, {'a': {}})
        validate({'a': {}}, {'a': {'b': 123}})

    def test_float(self):
        validate({'a': float}, {'a': None})
        validate({'a': float}, {'a': .5})

    def test_float_instance(self):
        validate({'a': .2}, {'a': None})
        validate({'a': .2}, {'a': .5})

    def test_int(self):
        validate({'a': int}, {'a': None})
        validate({'a': int}, {'a': 123})

    def test_int_instance(self):
        validate({'a': 1}, {'a': None})
        validate({'a': 1}, {'a': 123})

    def test_list(self):
        validate({'a': list}, {'a': None})
        validate({'a': list}, {'a': []})
        validate({'a': list}, {'a': ['b', 123]})

    def test_list_instance(self):
        validate({'a': []}, {'a': None})
        validate({'a': []}, {'a': []})
        validate({'a': []}, {'a': ['b', 123]})

        validate({'a': [int]}, {'a': None})
        validate({'a': [int]}, {'a': []})
        validate({'a': [int]}, {'a': [123]})
        validate({'a': [int]}, {'a': [123, 456]})
        with pytest.raises(TypeError):
            validate({'a': [int]}, {'a': ['b', 123]})
        with pytest.raises(TypeError):
            validate({'a': [text_type]}, {'a': [{'b': 'c'}]})

    def test_unicode(self):
        validate({'a': text_type}, {'a': None})
        validate({'a': text_type}, {'a': text_type('hello')})
        with pytest.raises(TypeError):
            validate({'a': text_type}, {'a': 123})

    def test_unicode_instance(self):
        validate({'a': text_type('foo')}, {'a': None})
        validate({'a': text_type('foo')}, {'a': text_type('hello')})
        with pytest.raises(TypeError):
            validate({'a': text_type('foo')}, {'a': 123})

    def test_datetime(self):
        validate({'a': datetime.datetime}, {'a': None})
        validate({'a': datetime.datetime},
                           {'a': datetime.datetime.utcnow()})
        with pytest.raises(TypeError):
            validate({'a': datetime.datetime}, {'a': 123})

    def test_datetime_instance(self):
        validate({'a': datetime.datetime(1900, 1, 1)}, {'a': None})
        validate({'a': datetime.datetime(1900, 1, 1)},
                           {'a': datetime.datetime.utcnow()})
        with pytest.raises(TypeError):
            validate({'a': datetime.datetime}, {'a': 123})

    def test_objectid(self):
        validate({'a': bson.ObjectId}, {'a': None})
        validate({'a': bson.ObjectId}, {'a': bson.ObjectId()})

    def test_dbref(self):
        validate({'a': bson.DBRef}, {'a': None})
        validate({'a': bson.DBRef},
                           {'a': bson.DBRef('a', 'b')})

    def test_callable(self):
        def func():
            return 1

        class Obj:
            @staticmethod
            def smeth():
                return 1

            @classmethod
            def cmeth(cls):
                return 1

            def ometh(self):
                return 1

        validate({'a': func}, {'a': 2})
        validate({'a': Obj.smeth}, {'a': 2})
        validate({'a': Obj.cmeth}, {'a': 2})
        validate({'a': Obj().ometh}, {'a': 2})

        with pytest.raises(TypeError):
            validate({'a': func}, {'a': 'foo'})
        with pytest.raises(TypeError):
            validate({'a': Obj.smeth}, {'a': 'foo'})
        with pytest.raises(TypeError):
            validate({'a': Obj.cmeth}, {'a': 'foo'})
        with pytest.raises(TypeError):
            validate({'a': Obj().ometh}, {'a': 'foo'})

    def test_valid_document(self):
        "a complex document"
        spec = {
            'text': text_type,
            'tags': [text_type],
            'views': int,
            'comments': [
                {
                    'time': datetime.datetime,
                    'text': text_type,
                },
            ]
        }
        data = {
            'text': text_type('Hello world!'),
            'tags': [text_type('hello'), text_type('world')],
            'views': 2,
            'comments': [
                {
                    'time': datetime.datetime(2000,1,1),
                    'text': text_type('Is there anybody out there?')
                },
                {
                    'time': datetime.datetime.utcnow(),
                    'text': text_type('Yes, I am, why?')
                },
            ],
        }
        validate(spec, data)


class TestValidationRules:
    def test_simple(self):
        # simple rule behaves as the spec within it
        spec = {
            'a': Rule(int),
        }
        validate(spec, {'a': 1})
        with pytest.raises(MissingKey):
            validate(spec, {})
        with pytest.raises(TypeError):
            validate(spec, {'a': 'bogus'})

    def test_optional(self):
        assert optional(int) == Rule(int, optional=True)

        # the rule modifies behaviour of nested validator
        spec = {
            'a': optional(int),
        }
        validate(spec, {})

    def test_optional_nested(self):
        spec = {
            'a': {'b': optional(int)},
        }

        validate(spec, {'a': None})

        with pytest.raises(MissingKey) as excinfo:
            validate(spec, {})
        prefix = '' if sys.version_info < (3,0) else 'monk.validation.'
        assert excinfo.exconly() == prefix + 'MissingKey: a'

        validate(spec, {'a': {}})

    def test_optional_nested_required(self):
        "optional dict contains a dict with required values"
        spec = {
            'a': optional({
                'b': int}),
        }
        verbose_spec = Rule(dict, inner_spec={
            'a': Rule(dict, optional=True, inner_spec={
                'b': int})})

        assert canonize(spec) == verbose_spec

        # None is OK (optional)
        validate(spec, {'a': None})

        # empty dict is OK (optional)
        validate(spec, {})

        # empty subdict fails because only its parent is optional
        with pytest.raises(MissingKey) as excinfo:
            validate(spec, {'a': {}})
        prefix = '' if sys.version_info < (3,0) else 'monk.validation.'
        assert excinfo.exconly() == prefix + 'MissingKey: a: b'


class TestRuleShortcuts:

    def test_any_value(self):
        assert any_value == Rule(None)

    def test_any_or_none(self):
        assert any_or_none == Rule(None, optional=True)
        assert any_or_none == optional(any_value)

    def test_optional(self):
        assert optional(str) == Rule(str, optional=True)
        assert optional(Rule(str)) == Rule(str, optional=True)
