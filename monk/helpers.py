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
Helpers
=======
"""


def walk_dict(data):
    """ Generates pairs ``(keys, value)`` for each item in given dictionary,
    including nested dictionaries. Each pair contains:

    `keys`
        a tuple of 1..n keys, e.g. ``('foo',)`` for a key on root level or
        ``('foo', 'bar')`` for a key in a nested dictionary.
    `value`
        the value of given key or ``None`` if it is a nested dictionary and
        therefore can be further unwrapped.
    """
    assert hasattr(data, '__getitem__')
    for key, value in data.iteritems():
        if isinstance(value, dict):
            yield (key,), None
            for keys, value in walk_dict(value):
                path = (key,) + keys
                yield path, value
        else:
            yield (key,), value
