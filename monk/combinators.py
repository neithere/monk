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
    'BaseValidator',
    'BaseCombinator',
    'All',
    'Any',
]


from .errors import (
    CombinedValidationError, AtLeastOneFailed, AllFailed, ValidationError
)


class BaseValidator:
    def _combine(self, other, combinator):
        # XXX should we flatten same-logic one-item combs?
        if not isinstance(other, BaseValidator):
            if isinstance(other, type) and issubclass(other, BaseValidator):
                # e.g. NotExists instead of NotExists()
                raise TypeError('got {} class instead of its instance'
                                .format(other.__name__))
            raise TypeError('expected a {} subclass instance, got {!r}'
                            .format(BaseValidator.__name__, other))
        return combinator([self, other])

    def __and__(self, other):
        return self._combine(other, All)

    def __or__(self, other):
        return self._combine(other, Any)


class BaseCombinator(BaseValidator):
    error_class = CombinedValidationError
    break_on_first_fail = False

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
                if self.break_on_first_fail:
                    # don't even wrap the error
                    raise
                errors.append(e)
        if not self.can_tolerate(errors):
            raise self.error_class('{!r} ({})'.format(
                value, '; '.join(('{}: {}'.format(e.__class__.__name__, e) for e in errors))))


    def __repr__(self):
        return '{}[{}]'.format(
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
    """
    Requires that the value passes all nested validators.
    """
    error_class = AtLeastOneFailed
    break_on_first_fail = True

    def can_tolerate(self, errors):
        # TODO: fail early, work as `or` does
        # (this also enables basic if-then in the schema)
        if not errors:
            return True


class Any(BaseCombinator):
    """
    Requires that the value passes at least one of nested validators.
    """
    error_class = AllFailed

    def can_tolerate(self, errors):
        if len(errors) < len(self._specs):
            return True
