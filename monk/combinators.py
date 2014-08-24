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
Value Specification Combinators
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
__all__ = [
    'BaseCombinator',
    'All',
    'Any',
]


from .errors import (
    CombinedValidationError, AtLeastOneFailed, AllFailed, ValidationError
)
from .bases import BaseValidator


class BaseCombinator(BaseValidator):
    error_class = CombinedValidationError

    def __init__(self, specs, default=None):
        assert specs
        self._specs = specs
        self._default = default

    def __call__(self, value):
        errors = []
        for spec in self._specs:
            # TODO: group errors by exception type
            # TODO: try recursive validators after all flat ones are OK
            #       (may be not a good idea because the order may matter)
            #if spec.is_recursive and errors:
            #    # Don't collect nested errors if we already have one here.
            #    # Another optimized strategy would be to fail early instead of
            #    # trying to collect all exceptions for the node.
            #    continue
            try:
                spec(value)
            except ValidationError as e:
                errors.append(e)
        if not self.can_tolerate(errors):
            raise self.error_class('{!r} ({})'.format(
                value, '; '.join(('{}: {}'.format(e.__class__.__name__, e) for e in errors))))


    def __repr__(self):
        return '<{} [{}]>'.format(
            self.__class__.__name__,
            ', '.join(map(str, self._specs)))

    @property
    def default(self):
        # TODO: default value gathering strategy:
        # 1. explicitly defined; if none--
        # 2. poll the specs; if gathered exactly one unique value -- use it
        return self._default

    def can_tolerate(self, errors):
        raise NotImplementedError


class All(BaseCombinator):
    error_class = AtLeastOneFailed

    def can_tolerate(self, errors):
        if not errors:
            return True


class Any(BaseCombinator):
    error_class = AllFailed

    def can_tolerate(self, errors):
        if len(errors) < len(self._specs):
            return True
