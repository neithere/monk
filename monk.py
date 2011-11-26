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
Monk
====

A simple schema validation layer for pymongo_. Inspired by MongoKit and Doqu.

.. _pymongo: http://api.mongodb.org/python/current/

"""
from collections import deque
from functools import partial

from pymongo import dbref


class DotExpandedDictMixin(object):
    def __getattr__(self, attr):
        if not attr.startswith('_') and attr in self:
            return self[attr]
        raise AttributeError('Attribute or key {0.__class__.__name__}.{1} '
                             'does not exist'.format(self, attr))


class TypedDictReprMixin(object):
    def __repr__(self):
        return '<{0.__class__.__name__} {1}>'.format(self, unicode(self))

    def __unicode__(self):
        return unicode(dict(self))


class MongoResultSet(object):
    def __init__(self, cursor, wrapper):
        self._cursor = cursor
        self._wrap = wrapper

    def __iter__(self):
        return (self._wrap(x) for x in self._cursor)

    def __getattr__(self, attr):
        return getattr(self._cursor, attr)


class MongoBoundDictMixin(object):
    collection = None
    indexes = []

    def __hash__(self):
        "Collection name and id together make the hash."
        return hash(self.collection) | hash(self.get('_id'))

    @classmethod
    def _ensure_indexes(cls, db):
        for definition in cls.indexes:
            fields = definition['fields']
            for field in fields:
                kwargs = dict(definition)
                kwargs.pop('fields')
                db[cls.collection].ensure_index(field, **kwargs)

    @classmethod
    def wrap_incoming(cls, data, db):
        return cls(dict_from_db(data, db))

    @classmethod
    def find(cls, db, *args, **kwargs):
        cls._ensure_indexes(db)
        docs = db[cls.collection].find(*args, **kwargs)
        return MongoResultSet(docs, partial(cls.wrap_incoming, db=db))

    @classmethod
    def get_one(cls, db, *args, **kwargs):
        cls._ensure_indexes(db)
        data = db[cls.collection].find_one(*args, **kwargs)
        if data:
            return cls.wrap_incoming(data, db)

    def save(self, db):
        assert self.collection
        #self.populate_defaults()
        self.validate()
        outgoing = dict(dict_to_db(self, self.structure))
        db[self.collection].save(outgoing)


class StructuredDict(dict):
    """ Словарь с валидацией структуры.
    """
    structure = {}
    defaults = {}
    #required = []
    #validators = {}
    with_skeleton = True

#    def __init__(self, *args, **kwargs):
#        super(StructuredDict, self).__init__(*args, **kwargs)

    def validate(self):
        # TODO
        pass


class Document(TypedDictReprMixin, MongoBoundDictMixin, DotExpandedDictMixin,
               StructuredDict):
    """ Структурированный словарь с привязкой с MongoDB и getattr->getitem.
    """


def dict_from_db(data, db):
    def generate():
        for key, value in data.iteritems():
            if isinstance(value, dbref.DBRef):
                yield key, dict(
                    db.dereference(value),
                    _id = value['_id']
                )
            else:
                yield key, value
    return dict(generate())


def dict_to_db(data, structure={}):
    def generate():
        for key, value in data.iteritems():
            if hasattr(value, '_id'):
                collection = structure[key].collection
                yield key, dbref.DBRef(collection, value['_id'])
            else:
                yield key, value
    return dict(generate())



class StructureSpecificationError(Exception):
    pass


def get_item(dictionary, keys, transparent_lists=False):
    """ Usage::

        >>> data = {'foo': {'bar': {'baz': 123}}}

        # drill down the dictionary
        >>> get_item(data, ('foo','bar','baz'))
        123
        >>> get_item(data, ('quux',))
        Traceback (most recent call last):
          ...
        KeyError: 'quux'

        # same as:
        >>> data['foo']['bar']['baz']
        123

    """
    value = dictionary
    for key in keys:
        value = value[key]
    return value


def walk_dict(data):
    """ Usage::

        >>> data = {
        ...     'foo': {
        ...         'bar': 123,
        ...         'baz': {
        ...             {'quux': 456},
        ...         }
        ...     },
        ...     'yada': u'yadda'
        ... }
        ...
        >>> for keys, value in walk_dict(data):
        ...     print keys, value
        ...
        ('foo',)
        ('foo', 'bar') 123
        ('foo', 'baz')
        ('foo', 'baz', 'quux') 456
        ('yada',) yadda

    """
    for key, value in data.iteritems():
        if isinstance(value, dict):
            yield (key,), None
            for keys, value in walk_dict(value):
                path = (key,) + keys
                yield path, value
        else:
            yield (key,), value


def validate_structure_spec(spec):
    """ Checks whether given document structure specification dictionary if
    defined correctly.
    Raises `StructureSpecificationError` if the specification is malformed.
    """
    stack = deque(walk_dict(spec))
    while stack:
        keys, value = stack.pop()
        if isinstance(value, list):
            # accepted: list of values of given type
            # e.g.: [unicode] -> [u'foo', u'bar']
            if len(value) == 1:
                stack.append((keys, value[0]))
            else:
                raise StructureSpecificationError(
                    '{path}: list must contain exactly 1 item (got {count})'
                         .format(path='.'.join(keys), count=len(value)))
        elif isinstance(value, dict):
            # accepted: nested dictionary (a spec on its own)
            # e.g.: {...} -> {...}
            for subkeys, subvalue in walk_dict(value):
                stack.append((keys+subkeys, subvalue))
        elif value is None:
            # accepted: any value
            # e.g.: None -> 123
            pass
        elif isinstance(value, type):
            # accepted: given type
            # e.g.: unicode -> u'foo'   or   dict -> {'a': 123}   or whatever.
            pass
        else:
            raise StructureSpecificationError(
                '{path}: expected dict, list, type or None (got {value!r})'
                    .format(path='.'.join(keys), value=value))


def check_type(typespec, value, keys_tuple):
    if typespec is None:
        return
    if not isinstance(typespec, type):
        key = '.'.join(keys_tuple)
        raise StructureSpecificationError(
            '{path}: expected dict, list, type or None (got {value!r})'
                .format(path=key, value=value))
    if not isinstance(value, typespec):
        key = '.'.join(keys_tuple)
        raise TypeError('{key}: expected {typespec.__name__}, got '
                        '{valtype.__name__} {value!r}'.format(key=key,
                        typespec=typespec, valtype=type(value), value=value))


def validate_structure(spec, data, skip_missing=False, skip_unknown=False):
    """ Validates given document against given structure specification.
    """
    # flatten the structures so that nested dictionaries are moved to the root
    # level and {'a': {'b': 1}} becomes {('a','b'): 1}
    flat_spec = dict(walk_dict(spec))
    flat_data = dict(walk_dict(data))

    # compare the two structures; nested dictionaries are included in the
    # comparison but nested lists are opaque and will be dealt with later on.
    spec_keys = set(spec.iterkeys())
    data_keys = set(data.iterkeys())
    missing = spec_keys - data_keys
    unknown = data_keys - spec_keys

    if missing and not skip_missing:
        raise KeyError('Missing keys: {0}'.format(', '.join(missing)))

    if unknown and not skip_unknown:
        raise KeyError('Unknown keys: {0}'.format(', '.join(unknown)))

    # check types and deal with nested lists
    for keys, value in flat_data.iteritems():
        typespec = flat_spec.get(keys)
        if value is None:
            # empty value, ok unless required
            continue
        elif typespec is None:
            # any value is acceptable
            continue
        elif isinstance(typespec, list) and value:
            # nested list
            item_spec = typespec[0]
            for item in value:
                if item_spec == dict or isinstance(item, dict):
                    # validate each value in the list as a separate document
                    # and fix error message to include outer key
                    try:
                        validate_structure(item_spec, item,
                                           skip_missing=skip_missing,
                                           skip_unknown=skip_unknown)
                    except (KeyError, TypeError) as e:
                        raise type(e)('{k}: {e}'.format(k='.'.join(keys), e=e))
                else:
                    check_type(item_spec, item, keys)
        else:
            check_type(typespec, value, keys)
