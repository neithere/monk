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

from monk import manipulation
from monk import validation


def make_dot_expanded(data):
    if isinstance(data, DotExpandedDictMixin):
        return data
    elif isinstance(data, dict):
        pairs = []
        for key, value in data.iteritems():
            pairs.append((key, make_dot_expanded(value)))
        return DotExpandedDict(pairs)
    elif isinstance(data, list):
        return [make_dot_expanded(x) for x in data]
    return data


class DotExpandedDictMixin(object):
    def _make_dot_expanded(self):
        for key, value in self.iteritems():
            self[key] = make_dot_expanded(value)

    def __getattr__(self, attr):
        if not attr.startswith('_') and attr in self:
            return self[attr]
        raise AttributeError('Attribute or key {0.__class__.__name__}.{1} '
                             'does not exist'.format(self, attr))

    def __setattr__(self, attr, value):
        if not attr.startswith('_') and attr in self:
            self[attr] = value

    def __setitem__(self, key, value):
        if isinstance(value, dict) and \
           not isinstance(value, DotExpandedDict):
            value = make_dot_expanded(value)
        super(DotExpandedDictMixin, self).__setitem__(key, value)



class DotExpandedDict(DotExpandedDictMixin, dict):
    def __init__(self, *args, **kwargs):
        super(DotExpandedDict, self).__init__(*args, **kwargs)
        self._make_dot_expanded()


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

    def __getitem__(self, index):
        return self._wrap(self._cursor[index])

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
        # XXX self.structure belongs to StructuredDictMixin !!
        return cls(dict_from_db(cls.structure, data, db))

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
        # XXX self.structure belongs to StructuredDictMixin !!
        outgoing = dict(dict_to_db(self, self.structure))
        db[self.collection].save(outgoing)


class StructuredDictMixin(object):
    """ A dictionary with structure specification and validation.
    """
    structure = {}
    #defaults = {}
    #required = []
    #validators = {}
    #with_skeleton = True

    def _insert_defaults(self):
        with_defaults = manipulation.merged(self.structure, self)
        for key, value in with_defaults.iteritems():
            self[key] = value

    def _validate_structure_spec(self):
        validation.validate_structure_spec(self.structure)

    def validate(self):
        validation.validate_structure(self.structure, self)


class Document(
        TypedDictReprMixin,
        DotExpandedDictMixin,
        StructuredDictMixin,
        MongoBoundDictMixin,
        dict
    ):
    """ A structured dictionary that is bound to MongoDB and supports dot
    notation for access to items.
    """
    def __init__(self, *args, **kwargs):
        super(Document, self).__init__(*args, **kwargs)
# TODO
#        self._validate_structure_spec()
        self._insert_defaults()
        self._make_dot_expanded()

    def save(self, db):
        self.validate()
        super(Document, self).save(db)


def _db_to_dict_pairs(spec, data, db):
    for key, value in data.iteritems():
        if isinstance(value, dict):
            yield key, dict(_db_to_dict_pairs(spec.get(key, {}), value, db))
        elif isinstance(value, dbref.DBRef):
            yield key, dict(
                db.dereference(value),
                _id = value['_id']
            )
        else:
            yield key, value


def dict_from_db(spec, data, db):
    return dict(_db_to_dict_pairs(spec, data, db))


def _dict_to_db_pairs(spec, data):
    for key, value in data.iteritems():
        if isinstance(value, dict):
            if '_id' in value:
                collection = spec[key].collection
                yield key, dbref.DBRef(collection, value['_id'])
            else:
                yield key, dict(_dict_to_db_pairs(spec.get(key, {}), value))
        else:
            yield key, value


def dict_to_db(data, spec={}):
    return dict(_dict_to_db_pairs(spec, data))
