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
Models
======
"""
from functools import partial

from pymongo import dbref

from monk import validation


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
    """ A dictionary with structure specification and validation.
    """
    structure = {}
    defaults = {}
    #required = []
    #validators = {}
    with_skeleton = True

#    def __init__(self, *args, **kwargs):
#        super(StructuredDict, self).__init__(*args, **kwargs)

    def validate(self):
        validation.validate_structure(self.structure, self)


class Document(TypedDictReprMixin, MongoBoundDictMixin, DotExpandedDictMixin,
               StructuredDict):
    """ A structured dictionary that is bound to MongoDB and supports dot
    notation for access to items.
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