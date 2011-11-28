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
Modeling tests
==============
"""
import pymongo
import pytest

from monk import modeling


class TestDocumentModel:
    class Entry(modeling.Document):
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
        ]
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
        assert entry.comments[0].is_spam == False


    '''
    TEST_DATABASE_NAME = 'test_monk'


    class BaseTestCase(unittest2.TestCase):
        FIXTURES = {}

        def setUp(self):
            self.db = pymongo.Connection()[TEST_DATABASE_NAME]
            self.load_fixtures()

        def load_fixtures(self):
            for cname, documents in self.FIXTURES.iteritems():
                collection = self.db[cname]
                collection.drop()
                for document in documents:
                    collection.insert(document)
    '''
