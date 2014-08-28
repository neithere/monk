# coding: utf-8
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
~~~~~~~~~~~~~~~~~~~~~~
Tests for Data Molding
~~~~~~~~~~~~~~~~~~~~~~
"""
from monk.compat import text_type as t
from monk import manipulation


def test_normalize_to_list():
    f = manipulation.normalize_to_list

    assert [1] == f(1)
    assert [1] == f([1])


def test_normalize_list_of_dicts():
    f = manipulation.normalize_list_of_dicts

    assert [{'x': 'a'}] == f([{'x': 'a'}], default_key='x')
    assert [{'x': 'a'}] == f( {'x': 'a'},  default_key='x')
    assert [{'x': 'a'}] == f(     t('a'),  default_key='x')
    assert [{'x': 'a'}, {'x': 'b'}] == f([{'x': 'a'}, t('b')], default_key='x')
    assert [] == f(None, default_key='x')
    assert [{'x': t('y')}] == f(None, default_key='x', default_value=t('y'))

    # edge cases (may need revision)
    assert [{'x': 1}] == f({'x': 1}, default_key='y')
    assert [] == f(None, default_key='y')
    assert 123 == f(123, default_key='x')
