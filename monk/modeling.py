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

Declaring indexes
-----------------

Let's declare a model with indexes::

    class Item(Document):
        structure = dict(text=unicode, slug=unicode)
        indexes = dict(text=None, slug=dict(unique=True))

Now create a model instance::

    item = Item(text=u'foo', slug=u'bar')

Save it and make sure the indexes are created::

    item.save(db)

The last line is roughly equivalent to::

    collection = db[item.collection]
    collection.ensure_index('text')
    collection.ensure_index('slug', unique=True)
    collection.save(dict(item))  # also validation, transformation, etc.

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
    """ Makes the dictionary dot-expandable by exposing dictionary members
    via ``__getattr__`` and ``__setattr__`` in addition to ``__getitem__`` and
    ``__setitem__``. For example, this is the default API::

        data = {'foo': {'bar': 0 } }
        print data['foo']['bar']
        data['foo']['bar'] = 123

    This mixin adds the following API::

        print data.foo.bar
        data.foo.bar = 123

    Nested dictionaries are converted to dot-expanded ones on adding.
    """
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
    """ Makes ``repr(self)`` depend on ``unicode(self)``.
    """
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

#    def count(self):
#        return self._cursor.count()


class MongoBoundDictMixin(object):
    """ Adds MongoDB-specific features to the dictionary.

    .. attribute:: collection

        Collection name.

    .. attribute:: indexes

        (TODO)

    """
    collection = None
    indexes = {}

    def __hash__(self):
        """ Collection name and id together make the hash; document class
        doesn't matter.

        Raises `TypeError` if collection or id is not set.
        """
        if self.collection and self.get_id():
            return hash(self.collection) | hash(self.get_id())
        raise TypeError('Document is unhashable: collection or id is not set')

    def __eq__(self, other):
        # both must inherit to this class
        if not isinstance(other, MongoBoundDictMixin):
            return False
        # both must have collections defined
        if not self.collection or not other.collection:
            return False
        # both must have ids
        if not self.get_id() or not other.get_id():
            return False

        # collections must be equal
        if self.collection != other.collection:
            return False
        # ids must be equal
        if self.get_id() != other.get_id():
            return False

        return True

    def __ne__(self, other):
        # this is required to override the call to dict.__eq__()
        return not self.__eq__(other)

    @classmethod
    def _ensure_indexes(cls, db):
        for field, kwargs in cls.indexes.iteritems():
            kwargs = kwargs or {}
            db[cls.collection].ensure_index(field, **kwargs)

    @classmethod
    def wrap_incoming(cls, data, db):
        # XXX self.structure belongs to StructuredDictMixin !!
        return cls(dict_from_db(cls.structure, data, db))

    @classmethod
    def find(cls, db, *args, **kwargs):
        """
        Returns a :class:`MongoResultSet` object.

        Example::

            items = Item.find(db, {'title': u'Hello'})

        .. note::

           The arguments are those of pymongo collection's `find` method.
           A frequent error is to pass query key/value pairs as keyword
           arguments. This is **wrong**. In most cases you will want to pass
           a dictionary ("query spec") as the first positional argument.

        """
        cls._ensure_indexes(db)
        docs = db[cls.collection].find(*args, **kwargs)
        return MongoResultSet(docs, partial(cls.wrap_incoming, db=db))

    @classmethod
    def get_one(cls, db, *args, **kwargs):
        """
        Returns an object that corresponds to given query or ``None``.

        Example::

            item = Item.get_one(db, {'title': u'Hello'})

        """
        data = db[cls.collection].find_one(*args, **kwargs)
        if data:
            return cls.wrap_incoming(data, db)
        else:
            return None

    def save(self, db):
        """
        Saves the object to given database. Usage::

            item = Item(title=u'Hello')
            item.save(db)

        Collection name is taken from :attr:`MongoBoundDictMixin.collection`.
        """
        assert self.collection

        self._ensure_indexes(db)

        # XXX self.structure belongs to StructuredDictMixin !!
        outgoing = dict(dict_to_db(self, self.structure))

        object_id = db[self.collection].save(outgoing)

        if self.get('_id') is None:
            self['_id'] = object_id
        else:
            pass

        return object_id

    def get_id(self):
        """ Returns object id or ``None``.
        """
        return self.get('_id')

    def get_ref(self):
        """ Returns a `DBRef` for this object or ``None``.
        """
        _id = self.get_id()
        if _id is None:
            return None
        else:
            return dbref.DBRef(self.collection, _id)

    def remove(self, db):
        """
        Removes the object from given database. Usage::

            item = Item.get_one(db)
            item.remove(db)

        Collection name is taken from :attr:`MongoBoundDictMixin.collection`.
        """
        assert self.collection
        assert self.get_id()

        db[self.collection].remove(self.get_id())


class StructuredDictMixin(object):
    """ A dictionary with structure specification and validation.

    .. attribute:: structure

        The document structure specification. For details see
        :func:`monk.validation.validate_structure_spec` and
        :func:`monk.validation.validate_structure`.

    """
    structure = {}
    #defaults = {}
    #required = []
    #validators = {}
    #with_skeleton = True

    def _insert_defaults(self):
        """ Inserts default values from :attr:`StructuredDictMixin.structure`
        to `self` by merging the two structures
        (see :func:`monk.manipulation.merged`).
        """
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

    Inherits features from:

    * `dict` (builtin),
    * :class:`~TypedDictReprMixin`,
    * :class:`~DotExpandedDictMixin`,
    * :class:`~StructuredDictMixin` and
    * :class:`~MongoBoundDictMixin`.

    """
    def __init__(self, *args, **kwargs):
        super(Document, self).__init__(*args, **kwargs)
# TODO
#        self._validate_structure_spec()
        self._insert_defaults()
        self._make_dot_expanded()

    def save(self, db):
        self.validate()
        return super(Document, self).save(db)


def _db_to_dict_pairs(spec, data, db):
    for key, value in data.iteritems():
        if isinstance(value, dict):
            yield key, dict(_db_to_dict_pairs(spec.get(key, {}), value, db))
        elif isinstance(value, dbref.DBRef):
            obj = db.dereference(value)
            cls = spec.get(key, dict)
            yield key, cls(obj, _id=obj['_id']) if obj else None
        else:
            yield key, value


def dict_from_db(spec, data, db):
    return dict(_db_to_dict_pairs(spec, data, db))


def _dict_to_db_pairs(spec, data):
    for key, value in data.iteritems():
        if key == '_id' and value is None:
            # let the database assign an identifier
            continue
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
