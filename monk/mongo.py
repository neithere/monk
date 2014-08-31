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
~~~~~~~~~~~~~~~~~~~
MongoDB integration
~~~~~~~~~~~~~~~~~~~

This module combines Monk's modeling and validation capabilities with MongoDB.

Declaring indexes
-----------------

Let's declare a model with indexes::

    from monk.mongo import Document

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

from bson import DBRef
from monk import modeling


class MongoResultSet(object):
    """ A wrapper for pymongo cursor that wraps each item using given function
    or class.

    .. warning::

       This class does not introduce caching.
       Iterating over results exhausts the cursor.

    """
    def __init__(self, cursor, wrapper):
        self._cursor = cursor
        self._wrap = wrapper

    def __iter__(self):
        return (self._wrap(x) for x in self._cursor)

    def __getitem__(self, index):
        return self._wrap(self._cursor[index])

    def __getattr__(self, attr):
        return getattr(self._cursor, attr)

    def ids(self):
        """ Returns a generator with identifiers of objects in set.
        These expressions are equivalent::

            ids = (item.id for item in result_set)

            ids = result_set.ids()

        .. warning::

           This method **exhausts** the cursor, so an attempt to iterate over
           results after calling this method will *fail*. The results are *not*
           cached.

        """
        return (item.id for item in self)

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
        if self.collection and self.id:
            return hash(self.collection) | hash(self.id)
        raise TypeError('Document is unhashable: collection or id is not set')

    def __eq__(self, other):
        # both must inherit to this class
        if not isinstance(other, MongoBoundDictMixin):
            return False
        # both must have collections defined
        if not self.collection or not other.collection:
            return False
        # both must have ids
        if not self.id or not other.id:
            return False

        # collections must be equal
        if self.collection != other.collection:
            return False
        # ids must be equal
        if self.id != other.id:
            return False

        return True

    def __ne__(self, other):
        # this is required to override the call to dict.__eq__()
        return not self.__eq__(other)

    @classmethod
    def _ensure_indexes(cls, db):
        for field, kwargs in cls.indexes.items():
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

    @property
    def id(self):
        """ Returns object id or ``None``.
        """
        return self.get('_id')

    def get_id(self):
        """ Returns object id or ``None``.
        """
        import warnings
        warnings.warn('{0}.get_id() is deprecated, '
                      'use {0}.id instead'.format(type(self).__name__),
                      DeprecationWarning)
        return self.get('_id')

    def get_ref(self):
        """ Returns a `DBRef` for this object or ``None``.
        """
        _id = self.id
        if _id is None:
            return None
        else:
            return DBRef(self.collection, _id)

    def remove(self, db):
        """
        Removes the object from given database. Usage::

            item = Item.get_one(db)
            item.remove(db)

        Collection name is taken from :attr:`MongoBoundDictMixin.collection`.
        """
        assert self.collection
        assert self.id

        db[self.collection].remove(self.id)


def _db_to_dict_pairs(spec, data, db):
    for key, value in data.items():
        if isinstance(value, dict):
            yield key, dict(_db_to_dict_pairs(spec.get(key, {}), value, db))
        elif isinstance(value, DBRef):
            obj = db.dereference(value)
            cls = spec.get(key, dict)
            yield key, cls(obj, _id=obj['_id']) if obj else None
        else:
            yield key, value


def dict_from_db(spec, data, db):
    return dict(_db_to_dict_pairs(spec, data, db))


def _dict_to_db_pairs(spec, data):
    for key, value in data.items():
        if key == '_id' and value is None:
            # let the database assign an identifier
            continue
        if isinstance(value, dict):
            if '_id' in value:
                collection = spec[key].collection
                yield key, DBRef(collection, value['_id'])
            else:
                yield key, dict(_dict_to_db_pairs(spec.get(key, {}), value))
        else:
            yield key, value


def dict_to_db(data, spec={}):
    return dict(_dict_to_db_pairs(spec, data))


class Document(
        modeling.TypedDictReprMixin,
        modeling.DotExpandedDictMixin,
        modeling.StructuredDictMixin,
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
        self._insert_defaults()
        self._make_dot_expanded()

    def save(self, db):
        self.validate()
        return super(Document, self).save(db)
