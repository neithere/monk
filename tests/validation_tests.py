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
Validation tests
================
"""
import datetime

import bson
from pytest import raises, raises_regexp

from monk.compat import text_type, safe_unicode
from monk import (
    Anything, IsA, Equals, Exists, ListOf, InRange,
    MISSING,
    translate,
    validate,
    optional,
    MissingKey, InvalidKey, ValidationError, AllFailed,
)


class TestOverall:

    def test_empty(self):

        # (pre-v0.13 "missing value", now None != MISSING)

        validate({'a': optional(text_type)}, {'a': text_type('')})
        with raises(ValidationError):
            validate({'a': text_type}, {'a': None})

        validate({'a': optional(dict)}, {'a': {}})
        with raises(ValidationError):
            validate({'a': dict}, {'a': None})

        validate({'a': optional(list)}, {'a': []})
        with raises(ValidationError):
            validate({'a': list}, {'a': None})

        validate({'a': bool}, {'a': True})
        validate({'a': bool}, {'a': False})
        with raises(ValidationError):
            validate({'a': optional(bool)}, {'a': None})
        with raises(ValidationError):
            validate({'a': bool}, {'a': None})

        # (pre-v0.13 TypeError, now everything has ValidationError as base)

        with raises(ValidationError):
            validate({'a': text_type}, {'a': False})
        with raises(ValidationError):
            validate({'a': text_type}, {'a': 0})
        with raises(ValidationError):
            validate({'a': bool}, {'a': ''})

    def test_missing(self):

        # MISSING KEY

        dict_with_opt_key = translate({IsA(text_type) | ~Exists(): text_type})
        dict_with_opt_key({})

        dict_with_req_key_opt_value = translate({'a': IsA(text_type) | Equals(None)})
        with raises(MissingKey):
            dict_with_req_key_opt_value({})

        dict_with_req_key_req_value = translate({'a': IsA(text_type)})
        with raises(MissingKey):
            dict_with_req_key_req_value({})

        dict_with_req_keys_req_values = translate({'a': text_type, 'b': int})
        with raises(MissingKey):
            dict_with_req_keys_req_values({'b': 1})

    def test_unknown_keys(self):
        # special behaviour: missing/empty inner_spec means "a dict of anything"
        validate(dict, {'x': 123})

        # inner_spec not empty, value matches it
        validate({'x': None}, {'x': 123})

        with raises(InvalidKey):
            validate({'x': None}, {'y': 123})

        with raises(InvalidKey):
            validate({'x': None}, {'x': 123, 'y': 456})

    def test_unknown_keys_encoding(self):
        with raises(InvalidKey):
            validate({'a': text_type}, {'привет': 1})
        with raises(InvalidKey):
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

        with raises_regexp(ValidationError, "'a': missing element: must be int"):
            validate({'a': [int]}, {'a': []})

        validate({'a': [int]}, {'a': [123]})
        validate({'a': [int]}, {'a': [123, 456]})
        with raises(ValidationError):
            validate({'a': [int]}, {'a': ['b', 123]})
        with raises(ValidationError):
            validate({'a': [text_type]}, {'a': [{'b': 'c'}]})

    def test_unicode(self):
        validate({'a': text_type}, {'a': text_type('hello')})
        with raises(ValidationError):
            validate({'a': text_type}, {'a': 123})

    def test_unicode_instance(self):
        validate({'a': text_type('foo')}, {'a': text_type('hello')})
        with raises(ValidationError):
            validate({'a': text_type('foo')}, {'a': 123})

    def test_datetime(self):
        validate({'a': datetime.datetime},
                 {'a': datetime.datetime.utcnow()})
        with raises(ValidationError):
            validate({'a': datetime.datetime}, {'a': 123})

    def test_datetime_instance(self):
        validate({'a': datetime.datetime(1900, 1, 1)},
                 {'a': datetime.datetime.utcnow()})
        with raises(ValidationError):
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

        with raises(ValidationError):
            validate({'a': func}, {'a': 'foo'})
        with raises(ValidationError):
            validate({'a': Obj.smeth}, {'a': 'foo'})
        with raises(ValidationError):
            validate({'a': Obj.cmeth}, {'a': 'foo'})
        with raises(ValidationError):
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

        spec = Anything()

        # value is present
        spec(1)

        # XXX CHANGED:
        #
        ## value is missing
        #with pytest.raises(MissingValue) as excinfo:
        #    validate(Rule(datatype=None), None)
        #assert "MissingValue: expected a value, got None" in excinfo.exconly()
        #
        spec(None)
        spec(MISSING)

    def test_any_optional(self):
        "A value of any type or no value"

        spec = Anything() | ~Exists()

        # value is present
        spec(1)

        # value is missing
        spec(None)
        spec(MISSING)

    def test_typed_required(self):
        "A value of given type"

        spec = IsA(int)

        # value is present and matches datatype
        spec(1)

        # value is present but does not match datatype
        with raises_regexp(ValidationError, 'must be int'):
            spec('bogus')

        # value is missing
        with raises_regexp(ValidationError, 'must be int'):
            spec(None)

    def test_typed_optional(self):
        "A value of given type or no value"

        spec = IsA(int) | Equals(None)

        # value is present and matches datatype
        spec(1)

        # value is present but does not match datatype
        with raises_regexp(AllFailed, "'bogus' \(must be int; != None\)"):
            spec('bogus')


        # value is missing
        spec(None)

    def test_typed_required_dict(self):
        "A value of given type (dict)"

        spec = IsA(dict)

        # value is present
        spec({})

        # value is missing
        with raises_regexp(ValidationError, 'must be dict'):
            spec(None)

    def test_typed_optional_dict(self):
        "A value of given type (dict) or no value"

        spec = IsA(dict) | Equals(None)

        # value is present
        spec({})

        # value is missing
        spec(None)

    def test_typed_required_list(self):
        "A value of given type (list)"

        spec = IsA(list)

        # value is present

        spec([])

        with raises_regexp(ValidationError, 'must be list'):
            spec('bogus')

        # value is missing
        with raises_regexp(ValidationError, 'must be list'):
            spec(None)

    def test_typed_optional_list(self):
        "A value of given type (list) or no value"

        spec = IsA(list) | Equals(None)

        # value is present
        spec([])

        # value is missing
        spec(None)


class TestNested:

    def test_int_in_dict(self):
        "A required int nested in a required dict"

        spec = translate({'foo': int})

        # key is missing

        with raises_regexp(MissingKey, "Equals\('foo'\)"):
            spec({})

        # key is present, value is missing

        with raises_regexp(ValidationError, "'foo': must be int"):
            spec({'foo': None})

        # key is present, value is present

        spec({'foo': 1})

    def test_dict_in_dict(self):
        "A required dict nested in another required dict"

        spec = translate({'foo': dict})

        # key is missing

        with raises_regexp(MissingKey, "Equals\('foo'\)"):
            spec({})

        # key is present, value is missing

        with raises_regexp(ValidationError, "'foo': must be dict"):
            spec({'foo': None})

        # value is present

        validate(spec, {'foo': {}})

    def test_int_in_dict_in_dict(self):
        "A required int nested in a required dict nested in another required dict"

        spec = translate({'foo': {'bar': int}})

        # inner key is missing

        with raises_regexp(MissingKey, "'foo': Equals\('bar'\)"):
            spec({'foo': {}})

        # inner key is present, inner value is missing

        with raises_regexp(ValidationError, "'foo': 'bar': must be int"):
            spec({'foo': {'bar': None}})

        # inner value is present

        spec({'foo': {'bar': 123}})

    def test_int_in_optional_dict(self):
        "A required int nested in an optional dict"

        spec = translate({'foo': int}) | Equals(None)

        # outer optional value is missing

        spec(None)

        # outer optional value is present, inner key is missing

        with raises_regexp(AllFailed, "{} \(MissingKey: Equals\('foo'\); != None\)"):
            spec({})

        # inner key is present, inner value is missing

        with raises_regexp(AllFailed, "{'foo': None} \('foo': must be int; != None\)"):
            spec({'foo': None})

        # inner value is present

        spec({'foo': 123})

    def test_int_in_list(self):
        spec = ListOf(int)

        # outer value is missing

        with raises_regexp(ValidationError, 'must be list'):
            spec(None)

        # outer value is present, inner value is missing

        with raises_regexp(ValidationError, 'missing element: must be int'):
            spec([])

        # outer value is present, inner optional value is missing

        relaxed_spec = ListOf(int) | None
        relaxed_spec([])

        # inner value is present but is None

        with raises_regexp(ValidationError, '#0: must be int'):
            spec([None])

        # inner value is present

        spec([123])

        # multiple inner values are present

        spec([123, 456])

        # one of the inner values is of a wrong type

        with raises_regexp(ValidationError, '#1: must be int'):
            spec([123, 'bogus'])

    def test_freeform_dict_in_list(self):
        spec = ListOf(dict)

        # inner value is present

        spec([{}])
        spec([{'foo': 123}])

        # multiple inner values are present

        spec([{'foo': 123}, {'bar': 456}])

        # one of the inner values is of a wrong type

        with raises_regexp(ValidationError, '#1: must be dict'):
            spec([{}, 'bogus'])

    def test_schemed_dict_in_list(self):
        spec = ListOf({'foo': int})

        # dict in list: missing key

        with raises(ValidationError):
            spec([{}])

        with raises_regexp(ValidationError, "#1: Equals\('foo'\)"):
            spec([{'foo': 123}, {}])

        # dict in list: missing value

        with raises_regexp(ValidationError, "#0: 'foo': must be int"):
            spec([{'foo': None}])

        with raises_regexp(ValidationError, "#1: 'foo': must be int"):
            spec([{'foo': 123}, {'foo': None}])

        # multiple innermost values are present

        spec([{'foo': 123}])
        spec([{'foo': 123}, {'foo': 456}])

        # one of the innermost values is of a wrong type

        with raises_regexp(ValidationError, "#2: 'foo': must be int"):
            spec([{'foo': 123}, {'foo': 456}, {'foo': 'bogus'}])

    def test_int_in_list_in_dict_in_list_in_dict(self):
        spec = translate({'foo': [{'bar': [int]}]})

        with raises_regexp(ValidationError, "'foo': must be list"):
            spec({'foo': None})

        with raises_regexp(ValidationError, "'foo': #0: 'bar': must be list"):
            spec({'foo': [{'bar': None}]})

        with raises_regexp(ValidationError, "'foo': missing element: must be dict"):
            spec({'foo': []})

        with raises_regexp(ValidationError,
                           "'foo': #0: 'bar': missing element: must be int"):
            spec({'foo': [{'bar': []}]})

        spec({'foo': [{'bar': [1]}]})
        spec({'foo': [{'bar': [1, 2]}]})

        with raises_regexp(ValidationError, "'foo': #0: 'bar': #1: must be int"):
            spec({'foo': [{'bar': [1, 'bogus']}]})


class TestRulesAsDictKeys:

    def test_datatype_to_datatype(self):
        spec = translate({str: int})

        assert spec == translate({IsA(str): int})

        spec({'a': 1})

    def test_multi_datatypes_to_datatype(self):
        schema = {
            str: int,
            int: int,
        }
        with raises(MissingKey):
            validate(schema, {'a': 1})
        with raises(MissingKey):
            validate(schema, {123: 1})
        validate(schema, {'a': 1, 'b': 2, 123: 4, 456: 5})

    def test_type_error(self):
        #with raises(TypeError):
        with raises(InvalidKey):
            validate({str: int}, {'a': 1, NotImplemented: 5})

    def test_invalid_key(self):
        with raises(InvalidKey):
            validate({str: int}, {'a': 1, 1: 2})
        with raises(InvalidKey):
            # special handling of rule.default in dict keys
            validate({'a': int}, {'a': 1, 'b': 5})

    def test_missing_key(self):
        with raises(MissingKey):
            validate({str: int}, {})

    def test_any_value_as_key(self):
        validate({None: 1}, {2: 3})

    def test_custom_validators_in_dict_keys(self):
        day_note_schema = translate({
            InRange(2000, 2020): {
                InRange(1, 12): {
                    InRange(1, 31): str,
                },
            },
        })
        good_note = {2013: {12: {9:  'it is a good day today'}}}
        bad_note1 = {1999: {12: {9:  'wrong year: below min'}}}
        bad_note2 = {2013: {13: {9:  'wrong month: above max'}}}
        bad_note3 = {2013: {12: {40: 'wrong day of month: above max'}}}

        day_note_schema(good_note)

        with raises_regexp(InvalidKey, '^1999$'):
            day_note_schema(bad_note1)

        with raises_regexp(InvalidKey, '^2013: 13$'):
            day_note_schema(bad_note2)

        with raises_regexp(InvalidKey, '^2013: 12: 40$'):
            day_note_schema(bad_note3)

    def test_nonsense(self):
        with raises(InvalidKey):
            validate({int: str}, {int: 'foo'})


class TestOneOf:
    # regressions for edge cases where the kludge named "OneOf" would break
    def test_validate_optional_one_of_in_a_list(self):
        # unset "optional" should work exactly as in a Rule
        schema = translate([IsA(str) | IsA(int)])
        with raises(ValidationError):
            schema([])

        schema = translate([optional(IsA(str) | IsA(int))])

        schema([])
        schema([123])
        schema([123, 'sss'])
        with raises(ValidationError):
            schema([123, 'sss', 999.999])


class TestListEdgeCases:
    def test_list_type(self):

        v = translate(list)

        with raises_regexp(ValidationError, 'must be list'):
            v(None)
        v([])
        v(['hi'])
        v([1234])

    def test_list_obj_empty(self):

        v = translate([])

        with raises_regexp(ValidationError, 'must be list'):
            v(None)
        v([])
        v([None])
        v(['hi'])
        v([1234])

    def test_list_with_req_elem(self):

        v = translate([str])

        with raises_regexp(ValidationError, 'must be list'):
            v(None)
        with raises_regexp(ValidationError, 'missing element: must be str'):
            v([])
        with raises_regexp(ValidationError, '#0: must be str'):
            v([None])
        v(['hi'])
        with raises_regexp(ValidationError, '#0: must be str'):
            v([1234])

    def test_list_with_opt_elem(self):

        v = translate([optional(str)])

        with raises_regexp(ValidationError, 'must be list'):
            v(None)
        v([])
        with raises_regexp(ValidationError, 'must be str; ~Exists()'):
            v([None])
        v(['hi'])
        with raises_regexp(ValidationError, 'must be str'):
            v([1234])
