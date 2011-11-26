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
Unit Tests
==========
"""
import datetime
import pymongo
import pymongo.binary
import pymongo.code
import pymongo.dbref
import pymongo.objectid
import unittest2

import monk


class StructureSpecTestCase(unittest2.TestCase):

    def test_walk_dict(self):
        data = {
            'a': {
                'b': {
                    'c': 'C',
                },
                'd': [
                    { 'e': 123 },
                ],
            },
            'f': ['F'],
            'g': dict,
            'h': list,
            'i': None,
        }
        paths = [
            # value is a dictionary, not yielded, queued for unwrapping
            (('a',), None),
            # nested dict unwrapped; value is a dict; queued for unwrapping
            (('a', 'b',), None),
            # nested dict unwrapped; value is a string; yielded as is
            (('a', 'b', 'c'), 'C'),
            # nested dict unwrapped; next value is a list which in opaque for
            # this function, so yielded as is, even if there are dicts inside
            (('a', 'd'), [{'e': 123}]),
            # value is a list again; yielded as is
            (('f',), ['F']),
            # a couple of type definitions
            (('g',), dict),
            (('h',), list),
            (('i',), None),
        ]
        self.assertEqual(sorted(monk.walk_dict(data)), sorted(paths))

    def test_correct_types(self):
        """ `None` stands for "any value". """
        monk.validate_structure_spec({'foo': None})
        monk.validate_structure_spec({'foo': bool})
        monk.validate_structure_spec({'foo': dict})
        monk.validate_structure_spec({'foo': float})
        monk.validate_structure_spec({'foo': int})
        monk.validate_structure_spec({'foo': list})
        monk.validate_structure_spec({'foo': unicode})
        monk.validate_structure_spec({'foo': datetime.datetime})
        monk.validate_structure_spec({'foo': pymongo.binary.Binary})
        monk.validate_structure_spec({'foo': pymongo.code.Code})
        monk.validate_structure_spec({'foo': pymongo.objectid.ObjectId})
        monk.validate_structure_spec({'foo': pymongo.dbref.DBRef})

    def test_correct_structures(self):
        # foo is of given type
        monk.validate_structure_spec({'foo': int})
        # foo and bar are of given types
        monk.validate_structure_spec({'foo': int, 'bar': unicode})
        # foo is a list of values of given type
        monk.validate_structure_spec({'foo': [int]})
        # foo.bar is of given type
        monk.validate_structure_spec({'foo': {'bar': int}})
        # foo.bar is a list of values of given type
        monk.validate_structure_spec({'foo': {'bar': [int]}})
        # foo.bar is a list of mappings where each "baz" is of given type
        monk.validate_structure_spec({'foo': {'bar': [{'baz': [unicode]}]}})

    def test_bad_types(self):
        # instances are not accepted; only types
        with self.assertRaisesRegexp(monk.StructureSpecificationError, 'type'):
            monk.validate_structure_spec({'foo': u'hello'})

        with self.assertRaisesRegexp(monk.StructureSpecificationError, 'type'):
            monk.validate_structure_spec({'foo': 123})

    def test_malformed_lists(self):
        single_elem_err_msg = 'list must contain exactly 1 item'

        with self.assertRaisesRegexp(monk.StructureSpecificationError, single_elem_err_msg):
            monk.validate_structure_spec({'foo': []})

        with self.assertRaisesRegexp(monk.StructureSpecificationError, single_elem_err_msg):
            monk.validate_structure_spec({'foo': [unicode, unicode]})

        with self.assertRaisesRegexp(monk.StructureSpecificationError, single_elem_err_msg):
            monk.validate_structure_spec({'foo': {'bar': [unicode, unicode]}})

        with self.assertRaisesRegexp(monk.StructureSpecificationError, single_elem_err_msg):
            monk.validate_structure_spec({'foo': {'bar': [{'baz': [unicode, unicode]}]}})


class DocumentStructureValidationTestCase(unittest2.TestCase):

    def test_empty(self):
        monk.validate_structure({'a': unicode}, {'a': None})
        monk.validate_structure({'a': list}, {'a': None})
        monk.validate_structure({'a': dict}, {'a': None})

        # None is allowed to represent empty value, but bool(value)==False
        # is not (unless bool is the correct type for this value)
        monk.validate_structure({'a': bool}, {'a': None})
        monk.validate_structure({'a': bool}, {'a': False})
        with self.assertRaises(TypeError):
            monk.validate_structure({'a': unicode}, {'a': False})
        with self.assertRaises(TypeError):
            monk.validate_structure({'a': unicode}, {'a': 0})
        with self.assertRaises(TypeError):
            monk.validate_structure({'a': bool}, {'a': u''})

    def test_missing(self):
        monk.validate_structure({'a': unicode}, {}, skip_missing=True)
        with self.assertRaises(KeyError):
            monk.validate_structure({'a': unicode}, {})
        with self.assertRaises(KeyError):
            monk.validate_structure({'a': unicode, 'b': int}, {'b': 1})

    def test_unknown_keys(self):
        monk.validate_structure({}, {'x': 123}, skip_unknown=True)
        with self.assertRaises(KeyError):
            monk.validate_structure({}, {'x': 123})
        with self.assertRaises(KeyError):
            monk.validate_structure({'a': unicode}, {'a': u'A', 'x': 123})
        with self.assertRaisesRegexp(TypeError, "a: b: expected int, got str 'bad'"):
            monk.validate_structure({'a': [{'b': [int]}]}, {'a': [{'b': ['bad']}]})

    def test_bool(self):
        monk.validate_structure({'a': bool}, {'a': None})
        monk.validate_structure({'a': bool}, {'a': True})
        monk.validate_structure({'a': bool}, {'a': False})

    def test_dict(self):
        monk.validate_structure({'a': dict}, {'a': None})
        monk.validate_structure({'a': dict}, {'a': {}})
        monk.validate_structure({'a': dict}, {'a': {'b': 'c'}})

    def test_float(self):
        monk.validate_structure({'a': float}, {'a': None})
        monk.validate_structure({'a': float}, {'a': .5})

    def test_int(self):
        monk.validate_structure({'a': int}, {'a': None})
        monk.validate_structure({'a': int}, {'a': 123})

    def test_list(self):
        monk.validate_structure({'a': list}, {'a': None})
        monk.validate_structure({'a': list}, {'a': []})
        monk.validate_structure({'a': list}, {'a': ['b', 123]})

    def test_unicode(self):
        monk.validate_structure({'a': unicode}, {'a': None})
        monk.validate_structure({'a': unicode}, {'a': u'hello'})
        with self.assertRaises(TypeError):
            monk.validate_structure({'a': unicode}, {'a': 123})

    def test_datetime(self):
        monk.validate_structure({'a': datetime.datetime}, {'a': None})
        monk.validate_structure({'a': datetime.datetime},
                                {'a': datetime.datetime.utcnow()})

    def test_objectid(self):
        monk.validate_structure({'a': pymongo.objectid.ObjectId}, {'a': None})
        monk.validate_structure({'a': pymongo.objectid.ObjectId},
                                {'a': pymongo.objectid.ObjectId()})

    def test_dbref(self):
        monk.validate_structure({'a': pymongo.dbref.DBRef}, {'a': None})
        monk.validate_structure({'a': pymongo.dbref.DBRef},
                                {'a': pymongo.dbref.DBRef('a', 'b')})

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
        monk.validate_structure(spec, data)
