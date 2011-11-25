# -*- coding: utf-8 -*-
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
    def test_walk(self):
        spec = {
            'a': {
                'b': [
                    { 'c': int },
                ],
                'd': str
            },
            'e': list
        }
        paths = [
            (('a', 'b', 'c'), int),
            (('a', 'd',), str),
            (('e',), list)
        ]
        all_paths = [
            (('a',), None),
            (('a', 'b'), None),
            (('a', 'b', 'c'), int),
            (('a', 'd',), str),
            (('e',), list)
        ]
        self.assertEqual(set(monk.walk_structure_spec(spec)), set(paths))


        print list(monk.walk_structure_spec(spec, all_keys=True))


        self.assertEqual(set(monk.walk_structure_spec(spec, all_keys=True)),
                         set(all_paths))

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
