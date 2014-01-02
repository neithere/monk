# -*- coding: utf-8 -*-
#
#    Monk is an unobtrusive data modeling, manipulation and validation library.
#    Copyright © 2011—2013  Andrey Mikhaylenko
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
~~~~~~~~~~~~~~
"""
import mock
import pytest

from monk.compat import text_type
from monk import manipulation, modeling


def test_make_dot_expanded():

    data = modeling.DotExpandedDict()
    assert id(data) == id(modeling.make_dot_expanded(data))

    data = {'foo': {'bar': 123}}
    result = modeling.make_dot_expanded(data)
    assert isinstance(result, modeling.DotExpandedDict)
    assert isinstance(result['foo'], modeling.DotExpandedDict)
    assert result.foo.bar == 123

    data = {'foo': [{'bar': 123, 'baz': {'quux': 456}}, {'zzz': 'yyy'}]}
    result = modeling.make_dot_expanded(data)
    assert isinstance(result, modeling.DotExpandedDict)
    assert isinstance(result['foo'][0], modeling.DotExpandedDict)
    assert isinstance(result['foo'][1], modeling.DotExpandedDict)
    assert result.foo[0].bar == 123
    assert result.foo[0].baz.quux == 456

    assert modeling.make_dot_expanded(123) == 123
    assert modeling.make_dot_expanded('foo') == 'foo'


def test_dot_expanded_dict():
    obj = modeling.DotExpandedDict(foo=dict(bar=123))
    assert obj.foo.bar == 123

    obj.foo.bar = text_type('Whoa')
    assert obj.foo.bar == text_type('Whoa')
    assert obj.foo.bar == obj['foo']['bar']

    obj = modeling.DotExpandedDict(comments=[{'text': 'hi'}])
    assert obj.comments[0].text == obj['comments'][0]['text']

def test_dot_expanded_dict_mixin():
    class Entry(modeling.DotExpandedDictMixin, dict):
        pass

    entry = Entry(foo=123)

    # getattr -> getitem
    assert entry['foo'] == 123
    assert entry['foo'] == entry.foo
    with pytest.raises(AttributeError):
        entry.nonexistent_key

    # setattr -> setitem
    entry.foo = 'bar'
    assert entry.foo == 'bar'
    assert entry.foo == entry['foo']

    # setattr -> setitem  won't work if key did not exist
    #   (reason: ambiguity of intent)
    entry.title = text_type('zzz')
    assert 'title' not in entry
    assert hasattr(entry, 'title')


def test_typed_dict_repr_mixin():
    class Entry(modeling.TypedDictReprMixin, dict):
        pass

    obj = Entry(foo=123)
    assert repr(obj) == "<Entry {'foo': 123}>"


def test_structured_dict_mixin():
    class Entry(modeling.StructuredDictMixin, dict):
        structure = {'foo': int, 'bar': {'quux': 123}}

    obj = Entry()
    expected = manipulation.merged(obj.structure, obj)
    obj._insert_defaults()
    assert obj == expected

    data = {'foo': 5, 'bar': {'quux': 9}}
    obj = Entry(data)
    sentinel = mock.MagicMock()
    @mock.patch('monk.validation.validate_structure', sentinel)
    def x():
        obj.validate()
    assert sentinel.called_once_with(obj.structure, data)
