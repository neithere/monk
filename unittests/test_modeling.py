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
~~~~~~~~~~~~~~
"""
from monk import modeling


def test_make_dot_expanded():

    data = modeling.DotExpandedDict()
    assert id(data) == id(make_dot_expanded(data))

    data = {'foo': {'bar': 123}}
    result = make_dot_expanded(data)
    assert isinstance(result, DotExpandedDict)
    assert isinstance(result['foo'], DotExpandedDict)
    assert result.foo.bar == 123

    data = {'foo': [{'bar': 123, 'baz': {'quux': 456}}]
    result = make_dot_expanded(data)
    assert isinstance(result, DotExpandedDict)
    assert isinstance(result['foo'][0], DotExpandedDict)
    assert isinstance(result['foo'][1], DotExpandedDict)
    assert result.foo[0].bar == 123
    assert result.foo[0].baz.quux == 456

    assert make_dot_expanded(123) == 123
    assert make_dot_expanded('foo') == 'foo'


def test_dot_expanded_dict():
    obj = modeling.DotExpandedDict(foo=dict(bar=123))
    assert obj.foo.bar == 123


def test_dot_expanded_dict_mixin():
    class Entry(modeling.DotExpandedDictMixin, dict):
        pass

    obj = Entry(foo=dict(bar=123), baz='quux', comments=[{'text': 'hi'}])
    assert obj.foo.bar == 123

    # getattr -> getitem
    assert entry['baz'] == 'quux'
    assert entry['baz'] == entry.title
    with pytest.raises(AttributeError):
        entry.nonexistent_key
    assert entry['foo']['bar'] == entry.foo.bar

    # setattr -> setitem
    entry.title = u'zzz'
    assert entry.title == u'zzz'
    assert entry.title == entry['title']

    entry.foo.bar = u'Whoa'
    assert entry.foo.bar == u'Whoa'
    assert entry.foo.bar == entry['foo']['bar']

    assert entry.comments[0].text == entry['comments'][0]['text']


def test_typed_dict_repr_mixin():
    class Entry(modeling.TypedDictReprMixin, dict):
        pass

    obj = Entry(foo=123)
    assert repr(obj) == "<Entry {'foo': 123}>"


def test_structured_dict_mixin():
    class Entry(modeling.StructuredDictMixin, dict):
        structure = {'foo': int, 'bar': {'quux': 123}}

    obj = Entry()
    assert obj._insert_defaults() == manipulation.merged(obj.structure, obj)

    data = {'foo': 5, 'bar': {'quux': 9}}
    obj = Entry(data)
    sentinel = mock.MagicMock()
    @mock.patch('monk.validation.validate_structure', sentinel)
    def x():
        obj.validate()
    assert sentinel.called_once_with(obj.structure, data)
