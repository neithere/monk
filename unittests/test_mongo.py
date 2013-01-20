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
MongoDB integration tests
~~~~~~~~~~~~~~~~~~~~~~~~~
"""
import datetime
import pymongo
import pytest

from bson import DBRef, ObjectId
from monk import mongo


class TestDocumentModel:
    class Entry(mongo.Document):
        structure = {
            'title': unicode,
            'author': {
                'first_name': unicode,
                'last_name': unicode,
            },
            'comments': [
                {
                    'text': unicode,
                    'is_spam': False,
                },
            ]
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
        ],
        'views_cnt': 0,
    }
    def test_basic_document(self):
        entry = self.Entry(self.data)
        assert entry['title'] == self.data['title']
        with pytest.raises(KeyError):
            entry['nonexistent_key']

    def test_dot_expanded(self):
        entry = self.Entry(self.data)

        # getattr -> getitem
        assert entry['title'] == self.data['title']
        assert entry['title'] == entry.title
        with pytest.raises(AttributeError):
            entry.nonexistent_key
        assert entry['author']['first_name'] == entry.author.first_name

        # setattr -> setitem
        entry.title = u'Bye!'
        assert entry.title == u'Bye!'
        assert entry.title == entry['title']

        entry.author.first_name = u'Joan'
        assert entry.author.first_name == u'Joan'
        assert entry.author.first_name == entry['author']['first_name']

        assert entry.comments[0].text == entry['comments'][0]['text']

    def test_defaults(self):
        entry = self.Entry(self.data)
        assert entry.views_cnt == 0

    def test_defaults_dict_in_list(self):
        entry = self.Entry(self.data)
        assert entry.comments[0].is_spam == False

    def test_callable_defaults_builtin_func(self):
        class Event(mongo.Document):
            structure = {
                'time': datetime.datetime.utcnow,
            }

        event = Event(time=datetime.datetime.utcnow())
        event.validate()
        assert isinstance(event.time, datetime.datetime)

        event = Event()
        event.validate()
        assert isinstance(event.time, datetime.datetime)

        with pytest.raises(TypeError):
            event = Event(time=datetime.date.today())
            event.validate()

    def test_callable_defaults_custom_func(self):
        class Event(mongo.Document):
            structure = {
                'text': lambda: u'hello'
            }

        event = Event(text=u'albatross')
        event.validate()
        assert isinstance(event.text, unicode)
        assert event.text == u'albatross'

        event = Event()
        event.validate()
        assert isinstance(event.text, unicode)
        assert event.text == u'hello'

        with pytest.raises(TypeError):
            event = Event(text=123)
            event.validate()


    def test_callable_defaults_custom_func_nested(self):
        # Issue #1  https://bitbucket.org/neithere/monk/issue/1/callable-defaults-in-nested-structures
        class Event(mongo.Document):
            structure = {
                'content': {
                    'text': lambda: u'hello'
                }
            }

        event = Event(content=dict(text=u'albatross'))
        event.validate()
        assert isinstance(event.content.text, unicode)
        assert event.content.text == u'albatross'

        event = Event()
        event.validate()
        assert isinstance(event.content.text, unicode)
        assert event.content.text == u'hello'

        with pytest.raises(TypeError):
            event = Event(content=dict(text=123))
            event.validate()


class TestMongo:

    DATABASE = 'test_monk'

    class Entry(mongo.Document):
        collection = 'entries'
        structure = {
            '_id': ObjectId,
            'title': unicode,
        }

    def setup_method(self, method):
        self.db = pymongo.Connection()[self.DATABASE]
        self.collection = self.db[self.Entry.collection]
        self.collection.drop()

    def test_query(self):
        self.collection.insert({'title': u'Hello world!'})
        entries = self.Entry.find(self.db, {'title': u'Hello world!'})
        assert entries.count() == 1
        entry = entries[0]
        assert entry.title == u'Hello world!'

    def test_insert(self):
        entry = self.Entry(title=u'Hello')
        entry.save(self.db)
        assert self.collection.find().count() == 1
        assert self.collection.find({'title': u'Hello'}).count() == 1

    def test_remove(self):
        self.collection.insert({'title': u'Hello'})

        entries = self.Entry.find(self.db)
        assert entries.count() == 1

        entry = entries[0]
        entry.remove(self.db)

        entries = self.Entry.find(self.db)
        assert entries.count() == 0

    def test_id(self):
        entry = self.Entry(title=u'Hello')
        assert entry['_id'] is None
        assert entry.get_id() is None

        # save the first time
        obj_id = entry.save(self.db)
        assert obj_id == entry['_id']
        assert self.Entry.find(self.db).count() == 1
        assert [entry] == list(self.Entry.find(self.db, _id=obj_id))

        # update
        entry.title = u'Bye'
        same_id = entry.save(self.db)
        assert obj_id == same_id
        assert obj_id == entry['_id']
        assert obj_id == entry.get_id()
        assert self.Entry.find(self.db).count() == 1

    def test_get_ref(self):
        entry = self.Entry(title=u'Hello')
        assert entry.get_ref() is None
        entry.save(self.db)
        assert entry.get_ref() == DBRef(self.Entry.collection, entry.get_id())

    def test_result_set_ids(self):
        self.collection.insert({'title': u'Foo'})
        self.collection.insert({'title': u'Bar'})
        results = self.Entry.find(self.db)
        ids_manual = [x.get_id() for x in results]
        # new object because caching is not supported
        ids = self.Entry.find(self.db).ids()
        assert ids_manual == list(ids)

    def test_equality(self):
        """Documents are equal if all these conditions are met:

        * both inherit to the same class;
        * both are stored in the same collection;
        * both have assigned ids and ids are equal.
        """
        a = self.Entry(title=u'Hello')
        b = self.Entry(title=u'Hello')
        assert a != b
        a.save(self.db)
        assert a != b
        c = self.Entry.get_one(self.db)
        assert a == c
        b.save(self.db)
        assert a != b
        d = dict(title=u'Hello')
        assert a != d

        class E(mongo.Document):
            structure = self.Entry.structure
        e = E(title=u'Hello')
        assert a != e

        class F(mongo.Document):
            collection = 'comments'
            structure = self.Entry.structure
        e = F(title=u'Hello')
        e.save(self.db)
        assert a != e

    def test_index_id(self):
        "Index for _id is created on first save to a collection"
        assert self.collection.index_information() == {}
        self.Entry(title=u'entry').save(self.db)
        assert '_id_' in self.collection.index_information()

    def test_index_custom(self):
        "Index for _id is created on first save to a collection"
        assert self.collection.index_information() == {}
        class IndexedEntry(self.Entry):
            indexes = {'title': None}
        IndexedEntry(title=u'Hello').save(self.db)
        assert 'title_1' in self.collection.index_information()
