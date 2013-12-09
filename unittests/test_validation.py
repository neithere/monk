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

import bson
import pytest

from monk.compat import text_type, safe_unicode
from monk.errors import MissingKey, MissingValue, UnknownKey, ValidationError
from monk.schema import Rule, optional, any_value, any_or_none
from monk.validation import validate


class TestOverall:

    def test_empty(self):

        # MISSING VALUE

        validate({'a': optional(text_type)}, {'a': text_type('')})
        with pytest.raises(MissingValue):
            validate({'a': text_type}, {'a': None})

        validate({'a': optional(dict)}, {'a': {}})
        with pytest.raises(MissingValue):
            validate({'a': dict}, {'a': None})

        validate({'a': optional(list)}, {'a': []})
        with pytest.raises(MissingValue):
            validate({'a': list}, {'a': None})

        validate({'a': bool}, {'a': True})
        validate({'a': bool}, {'a': False})
        validate({'a': optional(bool)}, {'a': None})
        with pytest.raises(MissingValue):
            validate({'a': bool}, {'a': None})

        # TYPE ERROR

        with pytest.raises(TypeError):
            validate({'a': text_type}, {'a': False})
        with pytest.raises(TypeError):
            validate({'a': text_type}, {'a': 0})
        with pytest.raises(TypeError):
            validate({'a': bool}, {'a': ''})

    def test_missing(self):

        # MISSING KEY

        validate({Rule(text_type, optional=True): text_type}, {})

        with pytest.raises(MissingKey):
            validate({'a': Rule(text_type, optional=True)}, {})
        with pytest.raises(MissingKey):
            validate({'a': text_type}, {})
        with pytest.raises(MissingKey):
            validate({'a': text_type, 'b': int}, {'b': 1})

    def test_unknown_keys(self):
        # verbose notation
        validate(Rule(dict, dict_allow_unknown_keys=True), {'x': 123})

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


class TestDataTypes:

    def test_bool(self):
        validate({'a': bool}, {'a': True})
        validate({'a': bool}, {'a': False})

    def test_bool_instance(self):
        validate({'a': True}, {'a': True})
        validate({'a': True}, {'a': False})

    def test_dict(self):
        validate({'a': dict}, {'a': {}})
        validate({'a': dict}, {'a': {'b': 'c'}})

    def test_dict_instance(self):
        validate({'a': {}}, {'a': {}})
        validate({'a': {}}, {'a': {'b': 123}})

    def test_float(self):
        validate({'a': float}, {'a': .5})

    def test_float_instance(self):
        validate({'a': .2}, {'a': .5})

    def test_int(self):
        validate({'a': int}, {'a': 123})

    def test_int_instance(self):
        validate({'a': 1}, {'a': 123})

    def test_list(self):
        validate({'a': list}, {'a': []})
        validate({'a': list}, {'a': ['b', 123]})

    def test_list_instance(self):
        validate({'a': []}, {'a': []})
        validate({'a': []}, {'a': ['b', 123]})

        with pytest.raises(MissingValue) as excinfo:
            validate({'a': [int]}, {'a': []})
        assert "MissingValue: a: expected at least one item, got empty list" in excinfo.exconly()

        validate({'a': [int]}, {'a': [123]})
        validate({'a': [int]}, {'a': [123, 456]})
        with pytest.raises(TypeError):
            validate({'a': [int]}, {'a': ['b', 123]})
        with pytest.raises(TypeError):
            validate({'a': [text_type]}, {'a': [{'b': 'c'}]})

    def test_unicode(self):
        validate({'a': text_type}, {'a': text_type('hello')})
        with pytest.raises(TypeError):
            validate({'a': text_type}, {'a': 123})

    def test_unicode_instance(self):
        validate({'a': text_type('foo')}, {'a': text_type('hello')})
        with pytest.raises(TypeError):
            validate({'a': text_type('foo')}, {'a': 123})

    def test_datetime(self):
        validate({'a': datetime.datetime},
                 {'a': datetime.datetime.utcnow()})
        with pytest.raises(TypeError):
            validate({'a': datetime.datetime}, {'a': 123})

    def test_datetime_instance(self):
        validate({'a': datetime.datetime(1900, 1, 1)},
                 {'a': datetime.datetime.utcnow()})
        with pytest.raises(TypeError):
            validate({'a': datetime.datetime}, {'a': 123})

    def test_objectid(self):
        validate({'a': bson.ObjectId}, {'a': bson.ObjectId()})

    def test_dbref(self):
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


class TestRuleSettings:

    def test_any_required(self):
        "A value of any type"

        # value is present
        validate(Rule(datatype=None), 1)

        # value is missing
        with pytest.raises(MissingValue) as excinfo:
            validate(Rule(datatype=None), None)
        assert "MissingValue: expected a value, got None" in excinfo.exconly()

    def test_any_optional(self):
        "A value of any type or no value"

        # value is present
        validate(Rule(datatype=None, optional=True), 1)

        # value is missing
        validate(Rule(datatype=None, optional=True), None)

    def test_typed_required(self):
        "A value of given type"

        # value is present and matches datatype
        validate(Rule(int), 1)

        # value is present but does not match datatype
        with pytest.raises(TypeError) as excinfo:
            validate(Rule(int), 'bogus')
        assert "TypeError: expected int, got str 'bogus'" in excinfo.exconly()

        # value is missing
        with pytest.raises(MissingValue) as excinfo:
            validate(Rule(int), None)
        assert "MissingValue: expected int, got None" in excinfo.exconly()

    def test_typed_optional(self):
        "A value of given type or no value"

        # value is present and matches datatype
        validate(Rule(int, optional=True), 1)

        # value is present but does not match datatype
        with pytest.raises(TypeError) as excinfo:
            validate(Rule(int), 'bogus')
        assert "TypeError: expected int, got str 'bogus'" in excinfo.exconly()

        # value is missing
        validate(Rule(int, optional=True), None)

    def test_typed_required_dict(self):
        "A value of given type (dict)"

        # value is present
        validate(Rule(datatype=dict), {})

        # value is missing
        with pytest.raises(MissingValue) as excinfo:
            validate(Rule(datatype=dict), None)
        assert "MissingValue: expected dict, got None" in excinfo.exconly()

    def test_typed_optional_dict(self):
        "A value of given type (dict) or no value"

        # value is present
        validate(Rule(datatype=dict, optional=True), {})

        # value is missing
        validate(Rule(datatype=dict, optional=True), None)

    def test_typed_required_list(self):
        "A value of given type (list)"

        # value is present
        validate(Rule(datatype=list), [])

        with pytest.raises(TypeError) as excinfo:
            validate(Rule(datatype=list), 'bogus')
        assert "TypeError: expected list, got str 'bogus'" in excinfo.exconly()

        # value is missing
        with pytest.raises(MissingValue) as excinfo:
            validate(Rule(datatype=list), None)
        assert "MissingValue: expected list, got None" in excinfo.exconly()

    def test_typed_optional_list(self):
        "A value of given type (list) or no value"

        # value is present
        validate(Rule(datatype=list, optional=True), [])

        # value is missing
        validate(Rule(datatype=list, optional=True), None)


class TestNested:

    def test_int_in_dict(self):
        "A required int nested in a required dict"

        spec = Rule(datatype=dict, inner_spec={'foo': int})

        # key is missing

        with pytest.raises(MissingKey) as excinfo:
            validate(spec, {})
        assert 'MissingKey: "foo"' in excinfo.exconly()

        # key is present, value is missing

        with pytest.raises(MissingValue) as excinfo:
            validate(spec, {'foo': None})
        assert 'MissingValue: foo: expected int, got None' in excinfo.exconly()

        # key is present, value is present

        validate(spec, {'foo': 1})

    def test_dict_in_dict(self):
        "A required dict nested in another required dict"

        spec = Rule(datatype=dict, inner_spec={'foo': dict})

        # key is missing

        with pytest.raises(MissingKey) as excinfo:
            validate(spec, {})
        assert 'MissingKey: "foo"' in excinfo.exconly()

        # key is present, value is missing

        with pytest.raises(MissingValue) as excinfo:
            validate(spec, {'foo': None})
        assert 'MissingValue: foo: expected dict, got None' in excinfo.exconly()

        # value is present

        validate(spec, {'foo': {}})

    def test_int_in_dict_in_dict(self):
        "A required int nested in a required dict nested in another required dict"

        spec = Rule(datatype=dict, inner_spec={
            'foo': Rule(datatype=dict, inner_spec={
                'bar': int})})

        # inner key is missing

        with pytest.raises(MissingKey) as excinfo:
            validate(spec, {'foo': {}})
        assert 'MissingKey: foo: "bar"' in excinfo.exconly()

        # inner key is present, inner value is missing

        with pytest.raises(MissingValue) as excinfo:
            validate(spec, {'foo': {'bar': None}})
        assert 'MissingValue: foo: bar: expected int, got None' in excinfo.exconly()

        # inner value is present

        validate(spec, {'foo': {'bar': 123}})

    def test_int_in_optional_dict(self):
        "A required int nested in an optional dict"

        spec = Rule(datatype=dict, optional=True, inner_spec={'foo': int})

        # outer optional value is missing

        validate(spec, None)

        # outer optional value is present, inner key is missing

        with pytest.raises(MissingKey) as excinfo:
            validate(spec, {})
        assert 'MissingKey: "foo"' in excinfo.exconly()

        # inner key is present, inner value is missing

        with pytest.raises(MissingValue) as excinfo:
            validate(spec, {'foo': None})
        assert 'MissingValue: foo: expected int, got None' in excinfo.exconly()

        # inner value is present

        validate(spec, {'foo': 123})

    def test_int_in_list(self):
        spec = Rule(datatype=list, inner_spec=int)

        # outer value is missing

        with pytest.raises(MissingValue) as excinfo:
            validate(spec, None)
        assert "MissingValue: expected list, got None" in excinfo.exconly()

        # outer value is present, inner value is missing

        with pytest.raises(MissingValue) as excinfo:
            validate(spec, [])
        assert "MissingValue: expected at least one item, got empty list" in excinfo.exconly()

        # outer value is present, inner optional value is missing

        relaxed_spec = Rule(datatype=list, inner_spec=Rule(int, optional=True))
        validate(relaxed_spec, [])

        # inner value is present but is None

        with pytest.raises(MissingValue) as excinfo:
            validate(spec, [None])
        assert "MissingValue: #0: expected int, got None" in excinfo.exconly()

        # inner value is present

        validate(spec, [123])

        # multiple inner values are present

        validate(spec, [123, 456])

        # one of the inner values is of a wrong type

        with pytest.raises(TypeError) as excinfo:
            validate(spec, [123, 'bogus'])
        assert "TypeError: #1: expected int, got str 'bogus'" in excinfo.exconly()

    def test_freeform_dict_in_list(self):
        spec = Rule(datatype=list, inner_spec=dict)

        # inner value is present

        validate(spec, [{}])
        validate(spec, [{'foo': 123}])

        # multiple inner values are present

        validate(spec, [{'foo': 123}, {'bar': 456}])

        # one of the inner values is of a wrong type

        with pytest.raises(TypeError) as excinfo:
            validate(spec, [{}, 'bogus'])
        assert "TypeError: #1: expected dict, got str 'bogus'" in excinfo.exconly()

    def test_schemed_dict_in_list(self):
        spec = Rule(datatype=list, inner_spec={'foo': int})

        # dict in list: missing key

        with pytest.raises(MissingKey) as excinfo:
            validate(spec, [{}])

        with pytest.raises(MissingKey) as excinfo:
            validate(spec, [{'foo': 123}, {}])
        assert 'MissingKey: #1: "foo"' in excinfo.exconly()

        # dict in list: missing value

        with pytest.raises(MissingValue) as excinfo:
            validate(spec, [{'foo': None}])
        assert 'MissingValue: #0: foo: expected int, got None' in excinfo.exconly()

        with pytest.raises(MissingValue) as excinfo:
            validate(spec, [{'foo': 123}, {'foo': None}])
        assert 'MissingValue: #1: foo: expected int, got None' in excinfo.exconly()

        # multiple innermost values are present

        validate(spec, [{'foo': 123}])
        validate(spec, [{'foo': 123}, {'foo': 456}])

        # one of the innermost values is of a wrong type

        with pytest.raises(TypeError) as excinfo:
            validate(spec, [{'foo': 123}, {'foo': 456}, {'foo': 'bogus'}])
        assert 'TypeError: #2: foo: expected int, got str \'bogus\'' in excinfo.exconly()

    def test_int_in_list_in_dict_in_list_in_dict(self):
        spec = Rule(datatype=dict, inner_spec={'foo': [{'bar': [int]}]})

        with pytest.raises(MissingValue) as excinfo:
            validate(spec, {'foo': None})
        assert "MissingValue: foo: expected list, got None" in excinfo.exconly()

        with pytest.raises(MissingValue) as excinfo:
            validate(spec, {'foo': [{'bar': None}]})
        assert "MissingValue: foo: #0: bar: expected list, got None" in excinfo.exconly()

        with pytest.raises(MissingValue) as excinfo:
            validate(spec, {'foo': []})
        assert "MissingValue: foo: expected at least one item, got empty list" in excinfo.exconly()

        with pytest.raises(MissingValue) as excinfo:
            validate(spec, {'foo': [{'bar': []}]})
        assert "MissingValue: foo: #0: bar: expected at least one item, got empty list" in excinfo.exconly()

        validate(spec, {'foo': [{'bar': [1]}]})
        validate(spec, {'foo': [{'bar': [1, 2]}]})

        with pytest.raises(TypeError) as excinfo:
            validate(spec, {'foo': [{'bar': [1, 'bogus']}]})
        assert "TypeError: foo: #0: bar: #1: expected int, got str 'bogus'" in excinfo.exconly()


class TestRuleShortcuts:

    def test_any_value(self):
        assert any_value == Rule(None)

    def test_any_or_none(self):
        assert any_or_none == Rule(None, optional=True)
        assert any_or_none == optional(any_value)

    def test_optional(self):
        assert optional(str) == Rule(str, optional=True)
        assert optional(Rule(str)) == Rule(str, optional=True)


class TestCustomValidators:

    def test_single(self):
        def validate_foo(value):
            if value != 'foo':
                raise ValidationError('value must be "foo"')

        spec = Rule(str, validators=[validate_foo])

        validate(spec, 'foo')

        with pytest.raises(ValidationError) as excinfo:
            validate(spec, 'bar')
        assert 'value must be "foo"' in excinfo.exconly()

    def test_multiple(self):

        def validate_gt_2(value):
            if value <= 2:
                raise ValidationError('value must be greater than 2')

        def validate_lt_5(value):
            if 5 <= value:
                raise ValidationError('value must be lesser than 5')

        spec = Rule(int, validators=[validate_gt_2, validate_lt_5])

        # first validator fails
        with pytest.raises(ValidationError) as excinfo:
            validate(spec, 1)
        assert 'value must be greater than 2' in excinfo.exconly()

        # both validators ok
        validate(spec, 3)

        # second validator fails
        with pytest.raises(ValidationError) as excinfo:
            validate(spec, 6)
        assert 'value must be lesser than 5' in excinfo.exconly()


class TestRulesAsDictKeys:

    def test_datatype_to_datatype(self):
        validate({str: int}, {'a': 1})
        validate({Rule(str): int}, {'a': 1})

    def test_multi_datatypes_to_datatype(self):
        schema = {
            str: int,
            int: int,
        }
        with pytest.raises(MissingKey):
            validate(schema, {'a': 1})
        with pytest.raises(MissingKey):
            validate(schema, {123: 1})
        validate(schema, {'a': 1, 'b': 2, 123: 4, 456: 5})

    def test_type_error(self):
        #with pytest.raises(TypeError):
        with pytest.raises(UnknownKey):
            validate({str: int}, {'a': 1, NotImplemented: 5})

    def test_unknown_key(self):
        with pytest.raises(UnknownKey):
            validate({str: int}, {'a': 1, 1: 2})
        with pytest.raises(UnknownKey):
            # special handling of rule.default in dict keys
            validate({'a': int}, {'a': 1, 'b': 5})

    def test_missing_key(self):
        with pytest.raises(MissingKey):
            validate({str: int}, {})
