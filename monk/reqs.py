# coding: utf-8
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
Value Specification Classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
__all__ = [
    'BaseRequirement',
    'IsA',
    'Equals',
    'CanBeNone',
    'Required',
    'Optional',
    'DictContains',
    'ListContains',
]

from functools import partial

from .errors import ValidationError, MissingKey, MissingValue
from .bases import BaseValidator


class BaseRequirement(BaseValidator):
    # a hint for combinators, see their code
    is_recursive = False
    implies = ()

    def __call__(self, value):
        for implied in self.implies:
            implied(value)
        self.check(value)

    def _represent(self):
        return self.__dict__

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self._represent())


class IsA(BaseRequirement):
    def __init__(self, expected_type):
        self.expected_type = expected_type

    def check(self, value):
        if not isinstance(value, self.expected_type):
            raise ValidationError('must be {}'.format(self.expected_type.__name__))

    def _represent(self):
        return self.expected_type.__name__


class Equals(BaseRequirement):
    def __init__(self, expected_value):
        self.expected_value = expected_value

    def check(self, value):
        if self.expected_value != value:
            raise ValidationError('!= {}' .format(self.expected_value))

    def _represent(self):
        return repr(self.expected_value)


class CanBeNone(BaseRequirement):
    def __init__(self, is_allowed):
        self.is_allowed = is_allowed

    def check(self, value):
        if value is None and not self.is_allowed:
            raise MissingValue('must be defined')

    def _represent(self):
        return self.is_allowed

Required = partial(CanBeNone(False))
Optional = partial(CanBeNone(True))


class ListContains(BaseRequirement):
    is_recursive = True
    implies = [IsA(list), CanBeNone(False)]

    def __init__(self, req):
        self.nested_req = req

    def check(self, value):
        for i, nested_value in enumerate(value):
            try:
                self.nested_req(nested_value)
            except ValidationError as e:
                raise ValidationError('#{}: {}'.format(i, e))

    def _represent(self):
        return repr(self.nested_req)


class DictContains(BaseRequirement):
    is_recursive = True
    implies = [IsA(dict), CanBeNone(False)]

    def __init__(self, key, req):
        self.key = key
        self.nested_req = req

    def check(self, value):
        if self.key not in value:
            raise MissingKey(repr(self.key))
        nested_value = value[self.key]
        try:
            self.nested_req(nested_value)
        except ValidationError as e:
            raise ValidationError('{!r}: {}'.format(self.key, e))


#@requirement(implies=[IsA(dict)], is_recursive=True, vars=['key', 'req'])
#def dict_contains(ctx, value):
#    nested_value = value[ctx['key']]
#    ctx['req'](nested_value)
