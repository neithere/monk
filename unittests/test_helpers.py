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
Helpers tests
=============
"""
from monk.validation import walk_dict


class TestDataWalking:

    def test_walk_dict(self):
        data = {
            'a': {
                'b': {
                    'c': 'C',
                },
                'd': [
                    { 'e': 123 },
                ],
            },
            'f': ['F'],
            'g': dict,
            'h': list,
            'i': None,
        }
        paths = [
            # value is a dictionary, not yielded, queued for unwrapping
            (('a',), None),
            # nested dict unwrapped; value is a dict; queued for unwrapping
            (('a', 'b',), None),
            # nested dict unwrapped; value is a string; yielded as is
            (('a', 'b', 'c'), 'C'),
            # nested dict unwrapped; next value is a list which in opaque for
            # this function, so yielded as is, even if there are dicts inside
            (('a', 'd'), [{'e': 123}]),
            # value is a list again; yielded as is
            (('f',), ['F']),
            # a couple of type definitions
            (('g',), dict),
            (('h',), list),
            (('i',), None),
        ]
        assert sorted(walk_dict(data)) == sorted(paths)
