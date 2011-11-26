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

from monk.validation import (
    walk_dict, validate_structure_spec, validate_structure,
    StructureSpecificationError
)
from monk import models


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
        self.assertEqual(sorted(walk_dict(data)), sorted(paths))

    def test_correct_types(self):
        """ `None` stands for "any value". """
        validate_structure_spec({'foo': None})
        validate_structure_spec({'foo': bool})
        validate_structure_spec({'foo': dict})
        validate_structure_spec({'foo': float})
        validate_structure_spec({'foo': int})
        validate_structure_spec({'foo': list})
        validate_structure_spec({'foo': unicode})
        validate_structure_spec({'foo': datetime.datetime})
        validate_structure_spec({'foo': pymongo.binary.Binary})
        validate_structure_spec({'foo': pymongo.code.Code})
        validate_structure_spec({'foo': pymongo.objectid.ObjectId})
        validate_structure_spec({'foo': pymongo.dbref.DBRef})

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

    def test_bad_types(self):
        # instances are not accepted; only types
        with self.assertRaisesRegexp(StructureSpecificationError, 'type'):
            validate_structure_spec({'foo': u'hello'})

        with self.assertRaisesRegexp(StructureSpecificationError, 'type'):
            validate_structure_spec({'foo': 123})

    def test_malformed_lists(self):
        single_elem_err_msg = 'list must contain exactly 1 item'

        with self.assertRaisesRegexp(StructureSpecificationError, single_elem_err_msg):
            validate_structure_spec({'foo': []})

        with self.assertRaisesRegexp(StructureSpecificationError, single_elem_err_msg):
            validate_structure_spec({'foo': [unicode, unicode]})

        with self.assertRaisesRegexp(StructureSpecificationError, single_elem_err_msg):
            validate_structure_spec({'foo': {'bar': [unicode, unicode]}})

        with self.assertRaisesRegexp(StructureSpecificationError, single_elem_err_msg):
            validate_structure_spec({'foo': {'bar': [{'baz': [unicode, unicode]}]}})


class DocumentStructureValidationTestCase(unittest2.TestCase):

    def test_empty(self):
        validate_structure({'a': unicode}, {'a': None})
        validate_structure({'a': list}, {'a': None})
        validate_structure({'a': dict}, {'a': None})

        # None is allowed to represent empty value, but bool(value)==False
        # is not (unless bool is the correct type for this value)
        validate_structure({'a': bool}, {'a': None})
        validate_structure({'a': bool}, {'a': False})
        with self.assertRaises(TypeError):
            validate_structure({'a': unicode}, {'a': False})
        with self.assertRaises(TypeError):
            validate_structure({'a': unicode}, {'a': 0})
        with self.assertRaises(TypeError):
            validate_structure({'a': bool}, {'a': u''})

    def test_missing(self):
        validate_structure({'a': unicode}, {}, skip_missing=True)
        with self.assertRaises(KeyError):
            validate_structure({'a': unicode}, {})
        with self.assertRaises(KeyError):
            validate_structure({'a': unicode, 'b': int}, {'b': 1})

    def test_unknown_keys(self):
        validate_structure({}, {'x': 123}, skip_unknown=True)
        with self.assertRaises(KeyError):
            validate_structure({}, {'x': 123})
        with self.assertRaises(KeyError):
            validate_structure({'a': unicode}, {'a': u'A', 'x': 123})
        with self.assertRaisesRegexp(TypeError, "a: b: expected int, got str 'bad'"):
            validate_structure({'a': [{'b': [int]}]}, {'a': [{'b': ['bad']}]})

    def test_bool(self):
        validate_structure({'a': bool}, {'a': None})
        validate_structure({'a': bool}, {'a': True})
        validate_structure({'a': bool}, {'a': False})

    def test_dict(self):
        validate_structure({'a': dict}, {'a': None})
        validate_structure({'a': dict}, {'a': {}})
        validate_structure({'a': dict}, {'a': {'b': 'c'}})

    def test_float(self):
        validate_structure({'a': float}, {'a': None})
        validate_structure({'a': float}, {'a': .5})

    def test_int(self):
        validate_structure({'a': int}, {'a': None})
        validate_structure({'a': int}, {'a': 123})

    def test_list(self):
        validate_structure({'a': list}, {'a': None})
        validate_structure({'a': list}, {'a': []})
        validate_structure({'a': list}, {'a': ['b', 123]})

    def test_unicode(self):
        validate_structure({'a': unicode}, {'a': None})
        validate_structure({'a': unicode}, {'a': u'hello'})
        with self.assertRaises(TypeError):
            validate_structure({'a': unicode}, {'a': 123})

    def test_datetime(self):
        validate_structure({'a': datetime.datetime}, {'a': None})
        validate_structure({'a': datetime.datetime},
                                {'a': datetime.datetime.utcnow()})

    def test_objectid(self):
        validate_structure({'a': pymongo.objectid.ObjectId}, {'a': None})
        validate_structure({'a': pymongo.objectid.ObjectId},
                                {'a': pymongo.objectid.ObjectId()})

    def test_dbref(self):
        validate_structure({'a': pymongo.dbref.DBRef}, {'a': None})
        validate_structure({'a': pymongo.dbref.DBRef},
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
        validate_structure(spec, data)



class DocumentDefaultsTestCase(unittest2.TestCase):
    class Entry(models.Document):
        structure = {
            'title': unicode,
            'author': {
                'first_name': unicode,
                'last_name': unicode,
            },
            'comments': [
                {
                    'text': unicode,
                    'is_spam': bool,
                },
            ]
        }
        defaults = {
            'comments.is_spam': False,
        }
    data = {
        'title': u'Hello',
        'author': {
            'first_name': u'John',
            'last_name': u'Doe',
        },
        'comments': [
            # XXX when do we add the default value is_spam=False?
            # anything that is inside a list (0..n) cannot be included in skel.
            # (just check or also append defaults) on (add / save / validate)?
            {'text': u'Oh hi'},
            {'text': u'Hi there', 'is_spam': True},
        ]
    }
    def test_basic_document(self):
        entry = self.Entry(self.data)
        self.assertEquals(entry['title'], self.data['title'])
        with self.assertRaises(KeyError):
            entry['nonexistent_key']

    @unittest2.expectedFailure
    def test_dot_expanded(self):
        entry = self.Entry(self.data)
        self.assertEquals(entry.title, entry['title'])
        with self.assertRaises(AttributeError):
            entry.nonexistent_key
        self.assertEquals(entry.author.first_name,
                          entry['author']['first_name'])
