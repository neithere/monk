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
    CombinedValidationError, AtLeastOneFailed, AllFailed, ValidationError,
    NoDefaultValue
)


class BaseValidator(object):
    _default = NotImplemented

    def _combine(self, other, combinator):
        # XXX should we flatten same-logic one-item combs?
        if not isinstance(other, BaseValidator):
            if isinstance(other, type) and issubclass(other, BaseValidator):
                # e.g. NotExists instead of NotExists()
                raise TypeError('got {cls} class instead of its instance'
                                .format(cls=other.__name__))
            raise TypeError('expected a {cls} subclass instance, got {other!r}'
                            .format(cls=BaseValidator.__name__, other=other))
        return combinator([self, other])

    def _merge(self, value):
        if value is not None:
            raise NoDefaultValue('value is not None')

        if self._default is NotImplemented:
            raise NoDefaultValue('self._default is not implemented')

        return self._default

    def __and__(self, other):
        return self._combine(other, All)

    def __or__(self, other):
        return self._combine(other, Any)

    def __eq__(self, other):
        return isinstance(other, type(self)) and self.__dict__ == other.__dict__

    def __hash__(self):
        # TODO think this over and check Python docs
        #return hash(((k,v) for k,v in self.__dict__.items()))
        return hash('validator_'+str(self.__dict__))

    def get_default_for(self, value, silent=True):
        try:
            return self._merge(value)
        except NoDefaultValue:
            if silent:
                return value
            else:
                raise


class BaseCombinator(BaseValidator):
    error_class = CombinedValidationError
    break_on_first_fail = False

    def __init__(self, specs, default=None, first_is_default=False):
        assert specs

        # FIXME resolve circular import
        from .reqs import translate

        self._specs = [translate(s) for s in specs]
        self._default = default
        self._first_is_default = first_is_default

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
            errors_str = '; '.join((
                '{cls}: {error}'.format(cls=e.__class__.__name__, error=e)
                for e in errors))
            raise self.error_class(
                '{value!r} ({errors})'.format(value=value, errors=errors_str))


    def __repr__(self):
        return '{cls}[{validators}]'.format(
            cls=self.__class__.__name__,
            validators=', '.join(map(str, self._specs)))


    def can_tolerate(self, errors):
        raise NotImplementedError

    def _merge(self, value):
        if self._default:
            return self._default
        defaults = []
        for choice in self._specs:
            try:
                default = choice.get_default_for(value, silent=False)
            except NoDefaultValue:
                pass
            else:
                defaults.append(default)
        if not defaults:
            return value
        if len(defaults) == 1:
            return defaults[0]
        else:
            if self._first_is_default:
                return defaults[0]
            else:
                return value


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
