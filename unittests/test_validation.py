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
Validation tests
================
"""
import datetime
import bson
import pytest

from monk.validation import (
    validate_structure_spec, validate_structure, StructureSpecificationError,
    MissingKey, UnknownKey, Rule, optional
)


class TestStructureSpec:

    def test_correct_types(self):
        '`None` stands for "any value".'
        validate_structure_spec({'foo': None})
        validate_structure_spec({'foo': bool})
        validate_structure_spec({'foo': dict})
        validate_structure_spec({'foo': float})
        validate_structure_spec({'foo': int})
        validate_structure_spec({'foo': list})
        validate_structure_spec({'foo': unicode})
        validate_structure_spec({'foo': datetime.datetime})
        validate_structure_spec({'foo': bson.Binary})
        validate_structure_spec({'foo': bson.Code})
        validate_structure_spec({'foo': bson.ObjectId})
        validate_structure_spec({'foo': bson.DBRef})

    def test_correct_structures(self):
        # foo is of given type
        validate_structure_spec({'foo': int})
        # foo and bar are of given types
        validate_structure_spec({'foo': int, 'bar': unicode})
        # foo is a list of values of given type
        validate_structure_spec({'foo': [int]})
        # foo.bar is of given type
        validate_structure_spec({'foo': {'bar': int}})
        # foo.bar is a list of values of given type
        validate_structure_spec({'foo': {'bar': [int]}})
        # foo.bar is a list of mappings where each "baz" is of given type
        validate_structure_spec({'foo': {'bar': [{'baz': [unicode]}]}})

    def test_malformed_lists(self):
        single_elem_err_msg = 'empty list or a list containing exactly 1 item'

        with pytest.raises(StructureSpecificationError) as excinfo:
            validate_structure_spec({'foo': [unicode, unicode]})
        assert single_elem_err_msg in excinfo.exconly()

        with pytest.raises(StructureSpecificationError) as excinfo:
            validate_structure_spec({'foo': {'bar': [unicode, unicode]}})
        assert single_elem_err_msg in excinfo.exconly()

        with pytest.raises(StructureSpecificationError) as excinfo:
            validate_structure_spec({'foo': {'bar': [{'baz': [unicode, unicode]}]}})
        assert single_elem_err_msg in excinfo.exconly()


class TestDocumentStructureValidation:

    def test_correct_structures(self):
        '''
        # foo is of given type
        validate_structure({'foo': int}, {}, skip_missing=True)
        # foo and bar are of given types
        validate_structure({'foo': int, 'bar': unicode}, {}, skip_missing=True)
        # foo is a list of values of given type
        validate_structure({'foo': [int]}, {}, skip_missing=True)
        # foo.bar is of given type
        validate_structure({'foo': {'bar': int}}, {}, skip_missing=True)
        # foo.bar is a list of values of given type
        validate_structure({'foo': {'bar': [int]}}, {}, skip_missing=True)
        # foo.bar is a list of mappings where each "baz" is of given type
        validate_structure({'foo': {'bar': [{'baz': [unicode]}]}}, {}, skip_missing=True)
        '''

    def test_malformed_lists(self):
        pass

    #---

    def test_bad_types(self):
        with pytest.raises(TypeError) as excinfo:
            validate_structure({'a': int}, {'a': 'bad'})
        assert "a: expected int, got str 'bad'" in excinfo.exconly()

        with pytest.raises(TypeError) as excinfo:
            validate_structure({'a': [int]}, {'a': 'bad'})
        assert "a: expected list, got str 'bad'" in excinfo.exconly()

        with pytest.raises(TypeError) as excinfo:
            validate_structure({'a': [int]}, {'a': ['bad']})
        assert "a: expected int, got str 'bad'" in excinfo.exconly()

        with pytest.raises(TypeError) as excinfo:
            validate_structure({'a': {'b': int}}, {'a': 'bad'})
        assert "a: expected dict, got str 'bad'" in excinfo.exconly()

        with pytest.raises(TypeError) as excinfo:
            validate_structure({'a': {'b': int}}, {'a': {'b': 'bad'}})
        assert "a: b: expected int, got str 'bad'" in excinfo.exconly()

        with pytest.raises(TypeError) as excinfo:
            validate_structure({'a': [{'b': [int]}]}, {'a': [{'b': ['bad']}]})
        assert "a: b: expected int, got str 'bad'" in excinfo.exconly()

    def test_empty(self):
        validate_structure({'a': unicode}, {'a': None})
        validate_structure({'a': list}, {'a': None})
        validate_structure({'a': dict}, {'a': None})

        # None is allowed to represent empty value, but bool(value)==False
        # is not (unless bool is the correct type for this value)
        validate_structure({'a': bool}, {'a': None})
        validate_structure({'a': bool}, {'a': False})
        with pytest.raises(TypeError):
            validate_structure({'a': unicode}, {'a': False})
        with pytest.raises(TypeError):
            validate_structure({'a': unicode}, {'a': 0})
        with pytest.raises(TypeError):
            validate_structure({'a': bool}, {'a': u''})

    def test_missing(self):
        validate_structure({'a': unicode}, {}, skip_missing=True)
        with pytest.raises(MissingKey):
            validate_structure({'a': unicode}, {})
        with pytest.raises(MissingKey):
            validate_structure({'a': unicode, 'b': int}, {'b': 1})

    def test_unknown_keys(self):
        validate_structure({}, {'x': 123}, skip_unknown=True)
        with pytest.raises(UnknownKey):
            validate_structure({}, {'x': 123})
        with pytest.raises(UnknownKey):
            validate_structure({'a': unicode}, {'a': u'A', 'x': 123})

    def test_unknown_keys_encoding(self):
        with pytest.raises(UnknownKey):
            validate_structure({'a': unicode}, {'привет': 1})
        with pytest.raises(UnknownKey):
            validate_structure({'a': unicode}, {u'привет': 1})

    def test_bool(self):
        validate_structure({'a': bool}, {'a': None})
        validate_structure({'a': bool}, {'a': True})
        validate_structure({'a': bool}, {'a': False})

    def test_bool_instance(self):
        validate_structure({'a': True}, {'a': None})
        validate_structure({'a': True}, {'a': True})
        validate_structure({'a': True}, {'a': False})

    def test_dict(self):
        validate_structure({'a': dict}, {'a': None})
        validate_structure({'a': dict}, {'a': {}})
        validate_structure({'a': dict}, {'a': {'b': 'c'}})

    def test_dict_instance(self):
        validate_structure({'a': {}}, {'a': None})
        validate_structure({'a': {}}, {'a': {}})
        validate_structure({'a': {}}, {'a': {'b': 123}})

    def test_float(self):
        validate_structure({'a': float}, {'a': None})
        validate_structure({'a': float}, {'a': .5})

    def test_float_instance(self):
        validate_structure({'a': .2}, {'a': None})
        validate_structure({'a': .2}, {'a': .5})

    def test_int(self):
        validate_structure({'a': int}, {'a': None})
        validate_structure({'a': int}, {'a': 123})

    def test_int_instance(self):
        validate_structure({'a': 1}, {'a': None})
        validate_structure({'a': 1}, {'a': 123})

    def test_list(self):
        validate_structure({'a': list}, {'a': None})
        validate_structure({'a': list}, {'a': []})
        validate_structure({'a': list}, {'a': ['b', 123]})

    def test_list_instance(self):
        validate_structure({'a': []}, {'a': None})
        validate_structure({'a': []}, {'a': []})
        validate_structure({'a': []}, {'a': ['b', 123]})

        validate_structure({'a': [int]}, {'a': None})
        validate_structure({'a': [int]}, {'a': []})
        validate_structure({'a': [int]}, {'a': [123]})
        validate_structure({'a': [int]}, {'a': [123, 456]})
        with pytest.raises(TypeError):
            validate_structure({'a': [int]}, {'a': ['b', 123]})
        with pytest.raises(TypeError):
            validate_structure({'a': [unicode]}, {'a': [{'b': 'c'}]})

    def test_unicode(self):
        validate_structure({'a': unicode}, {'a': None})
        validate_structure({'a': unicode}, {'a': u'hello'})
        with pytest.raises(TypeError):
            validate_structure({'a': unicode}, {'a': 123})

    def test_unicode_instance(self):
        validate_structure({'a': u'foo'}, {'a': None})
        validate_structure({'a': u'foo'}, {'a': u'hello'})
        with pytest.raises(TypeError):
            validate_structure({'a': u'foo'}, {'a': 123})

    def test_datetime(self):
        validate_structure({'a': datetime.datetime}, {'a': None})
        validate_structure({'a': datetime.datetime},
                           {'a': datetime.datetime.utcnow()})
        with pytest.raises(TypeError):
            validate_structure({'a': datetime.datetime}, {'a': 123})

    def test_datetime_instance(self):
        validate_structure({'a': datetime.datetime(1900, 1, 1)}, {'a': None})
        validate_structure({'a': datetime.datetime(1900, 1, 1)},
                           {'a': datetime.datetime.utcnow()})
        with pytest.raises(TypeError):
            validate_structure({'a': datetime.datetime}, {'a': 123})

    def test_objectid(self):
        validate_structure({'a': bson.ObjectId}, {'a': None})
        validate_structure({'a': bson.ObjectId}, {'a': bson.ObjectId()})

    def test_dbref(self):
        validate_structure({'a': bson.DBRef}, {'a': None})
        validate_structure({'a': bson.DBRef},
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

        validate_structure({'a': func}, {'a': 2})
        validate_structure({'a': Obj.smeth}, {'a': 2})
        validate_structure({'a': Obj.cmeth}, {'a': 2})
        validate_structure({'a': Obj().ometh}, {'a': 2})

        with pytest.raises(TypeError):
            validate_structure({'a': func}, {'a': 'foo'})
        with pytest.raises(TypeError):
            validate_structure({'a': Obj.smeth}, {'a': 'foo'})
        with pytest.raises(TypeError):
            validate_structure({'a': Obj.cmeth}, {'a': 'foo'})
        with pytest.raises(TypeError):
            validate_structure({'a': Obj().ometh}, {'a': 'foo'})

    def test_valid_document(self):
        "a complex document"
        spec = {
            'text': unicode,
            'tags': [unicode],
            'views': int,
            'comments': [
                {
                    'time': datetime.datetime,
                    'text': unicode,
                },
            ]
        }
        data = {
            'text': u'Hello world!',
            'tags': [u'hello', u'world'],
            'views': 2,
            'comments': [
                {
                    'time': datetime.datetime(2000,1,1),
                    'text': u'Is there anybody out there?'
                },
                {
                    'time': datetime.datetime.utcnow(),
                    'text': u'Yes, I am, why?'
                },
            ],
        }
        validate_structure(spec, data)


class TestValidationRules:
    def test_simple(self):
        # simple rule behaves as the spec within it
        spec = {
            'a': Rule(int),
        }
        validate_structure(spec, {'a': 1})
        with pytest.raises(MissingKey):
            validate_structure(spec, {})
        with pytest.raises(TypeError):
            validate_structure(spec, {'a': 'bogus'})

    def test_skip_missing(self):
        # the rule modifies behaviour of nested validator
        spec = {
            'a': optional(int),
        }
        validate_structure(spec, {})

    def test_skip_missing_nested(self):
        spec = {
            'a': {'b': optional(int)},
        }

        validate_structure(spec, {'a': None})

        with pytest.raises(MissingKey) as excinfo:
            validate_structure(spec, {})
        assert excinfo.exconly() == 'MissingKey: a'

        validate_structure(spec, {'a': {}})

    def test_skip_missing_nested_required(self):
        "optional dict contains a dict with required values"
        spec = {
            'a': optional({'b': int}),
        }

        # None is OK (optional)
        validate_structure(spec, {'a': None})

        # empty dict is OK (optional)
        validate_structure(spec, {})

        # empty subdict fails because only its parent is optional
        with pytest.raises(MissingKey) as excinfo:
            validate_structure(spec, {'a': {}})
        assert excinfo.exconly() == 'MissingKey: a: b'
