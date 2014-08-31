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
~~~~~~~~~~
Validators
~~~~~~~~~~
"""
__all__ = [
    'BaseValidator',

    # combinators
    'BaseCombinator',
    'All',
    'Any',

    # requirements
    'BaseRequirement',
    'Anything',
    'IsA',
    'Equals',
    'InRange',
    'Length',
    'ListOf',
    'DictOf',
    'NotExists',

    # functions
    'translate',

    # special objects
    'MISSING',
]


from . import compat
from .errors import (
    CombinedValidationError, AtLeastOneFailed, AllFailed, ValidationError,
    NoDefaultValue, InvalidKey, MissingKey, StructureSpecificationError
)


class BaseValidator(object):
    _default = NotImplemented

    def _combine(self, other, combinator):
        # XXX should we flatten same-logic one-item combs?
        if isinstance(other, type) and issubclass(other, BaseValidator):
            # e.g. NotExists instead of NotExists()
            raise TypeError('got {cls} class instead of its instance'
                            .format(cls=other.__name__))

        return combinator([self, translate(other)])

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
            def fmt_err(e):
                # only display error class if it's not obvious
                if type(e) is ValidationError:
                    tmpl = '{err}'
                else:
                    tmpl = '{cls}: {err}'
                return tmpl.format(cls=e.__class__.__name__, err=e)

            errors_str = '; '.join((fmt_err(e) for e in errors))
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


class MISSING:
    """
    Stub for NotExists validator to pass if the value is missing
    (e.g. for dictionary keys).
    """
    pass


class BaseRequirement(BaseValidator):
    # a hint for combinators, see their code
    is_recursive = False
    implies = NotImplemented

    def __call__(self, value):
        if self.implies is not NotImplemented:
            self.implies(value)
        self._check(value)

    def _represent(self):
        return self.__dict__

    def __repr__(self):
        return '{cls}({rep})'.format(cls=self.__class__.__name__,
                                     rep=self._represent())



class Anything(BaseRequirement):
    """
    Any values passes validation.
    """
    def _check(self, value):
        pass

    def _represent(self):
        return ''


class IsA(BaseRequirement):
    """
    Requires that the value is an instance of given type.
    """
    def __init__(self, expected_type, default=None):
        self.expected_type = expected_type
        self._default = default

    def _check(self, value):
        if not isinstance(value, self.expected_type):
            raise ValidationError('must be {type}'
                                  .format(type=self.expected_type.__name__))

    def _represent(self):
        if self._default:
            return '{name} {default!r}'.format(
                name=self.expected_type.__name__,
                default=self._default)
        else:
            return self.expected_type.__name__


class Equals(BaseRequirement):
    """
    Requires that the value equals given expected value.
    """
    def __init__(self, expected_value):
        self._expected_value = expected_value

    def _check(self, value):
        if self._expected_value != value:
            raise ValidationError('!= {expected!r}'
                                  .format(expected=self._expected_value))

    def _represent(self):
        return repr(self._expected_value)

    @property
    def _default(self):
        return self._expected_value


class NotExists(BaseRequirement):
    """
    Requires that the value does not exist.  Obviously this only makes sense in
    special cases like dictionary keys; otherwise there's simply nothing to
    validate.  Note that this is *not* a check against `None` or `False`.
    """
    def __init__(self, default=None):
        self._default = default

    def _check(self, value):
        if value is not MISSING:
            raise ValidationError('must not exist')

    def _represent(self):
        return ''



class ListOf(BaseRequirement):
    """
    Requires that the value is a `list` which items match given validator.
    Usage::

        >>> v = ListOf(IsA(int) | IsA(str))
        >>> v([123, 'hello'])
        >>> v([123, 'hello', 5.5])
        Traceback (most recent call last):
        ...
        ValidationError: #2: 5.5 (ValidationError: must be int;
                                  ValidationError: must be str)

    """
    is_recursive = True
    implies = IsA(list)

    def __init__(self, validator, default=None):
        self._nested_validator = translate(validator)
        self._default = default

    def _check(self, value):
        if not value:
            try:
                self._nested_validator(MISSING)
            except ValidationError as e:
                raise ValidationError('missing element: {error}'
                                      .format(error=e))
        for i, nested_value in enumerate(value):
            try:
                self._nested_validator(nested_value)
            except ValidationError as e:
                raise ValidationError('#{elem}: {error}'
                                      .format(elem=i, error=e))

    def _represent(self):
        return repr(self._nested_validator)

    def _merge(self, value):
        """ Returns a list based on `value`:

        * missing required value is converted to an empty list;
        * missing required items are never created;
        * nested items are merged recursively.

        """
        if not value:
            return []

        if value is not None and not isinstance(value, list):
            # bogus value; will not pass validation but should be preserved
            return value

        item_spec = self._nested_validator
        return [x if x is None else item_spec.get_default_for(x) for x in value]



#@requirement(implies=[IsA(dict)], is_recursive=True, vars=['key', 'req'])
#def dict_contains(ctx, value):
#    nested_value = value[ctx['key']]
#    ctx['req'](nested_value)




class DictOf(BaseRequirement):
    """
    Requires that the value is a `dict` which items match given patterns.
    Usage::

        >>> v = DictOf([
        ...     # key "name" must exist; its value must be a `str`
        ...     (Equals('name'), IsA(str)),
        ...     # key "age" may not exist; its value must be an `int`
        ...     (Equals('age') | NotExists(), IsA(int)),
        ...     # there may be other `str` keys with `str` or `int` values
        ...     (IsA(str), IsA(str) | IsA(int)),
        ... ])
        >>> v({'name': 'John'})
        >>> v({'name': 'John', 'age': 25})
        >>> v({'name': 'John', 'age': 25.5})
        Traceback (most recent call last):
        ...
        monk.errors.ValidationError: 'age': must be int
        >>> v({'name': 'John', 'age': 25, 'note': 'custom field'})
        >>> v({'name': 'John', 'age': 25, 'note': 5.5})
        Traceback (most recent call last):
        ...
        AllFailed: 'note': 5.5 (ValidationError: must be str;
                                ValidationError: must be int)

    Note that this validator supports :class:`NotExists` to mark keys that can
    be missing.
    """
    implies = IsA(dict)

    def __init__(self, pairs):
        self._pairs = pairs

    def _represent(self):
        return repr(self._pairs)

    def _check(self, value):
        value = value or {}
        validated_data_keys = []
        missing_key_specs = []
        for k_validator, v_validator in self._pairs:
            # NOTE kspec.datatype can be None => any key of any datatype
            # NOTE kspec.default  can be None => any key of given datatype

            # gather data keys that match given kspec;
            # then validate them against vspec
            matched = False
            for k,v in value.items():
                if k in validated_data_keys:
                    continue

                # check if this key is described by current rule;
                # if it isn't, just skip it (and try another rule on it later on)
                try:
                    k_validator(k)
                except (TypeError, ValidationError):
                    continue

                # this key *is* described by current rule;
                # validate the value (it *must* validate)
                try:
                    v_validator(v)
                except (ValidationError, TypeError) as e:
                    raise type(e)('{k!r}: {e}'.format(k=k, e=e))

                validated_data_keys.append(k)
                matched = True

#            if not matched and not k_validator.optional:
            if not matched:
                try:
                    k_validator(MISSING)
                except ValidationError:
                    missing_key_specs.append(k_validator)

        # TODO document that unknown keys are checked before missing ones

        # check if there are data keys that did not match any key spec;
        # if yes, raise InvalidKey for them
        if len(validated_data_keys) < len(value):
            raise InvalidKey(', '.join(repr(x) for x in set(value) - set(validated_data_keys)))

        if missing_key_specs:
            # NOTE: this prints rules, not keys as strings
            raise MissingKey('{0}'.format(
                ', '.join(compat.safe_str(rule) for rule in missing_key_specs)))


    def _merge(self, value):
        """
        Returns a dictionary based on `value` with each value recursively
        merged with `spec`.
        """

        if value is not None and not isinstance(value, dict):
            # bogus value; will not pass validation but should be preserved
            return value

        if not self._pairs:
            return {}

        collected = {}
#        collected.update(value)
        for k_validator, v_validator in self._pairs:
            k_default = k_validator.get_default_for(None)
            if k_default is None:
                continue

            # even None is ok
            if value:
                v_for_this_k = value.get(k_default)
            else:
                v_for_this_k = None
            v_default = v_validator.get_default_for(v_for_this_k)
            collected.update({k_default: v_default})

        if value:
            for k, v in value.items():
                if k not in collected:
                    collected[k] = v

        return collected


class InRange(BaseRequirement):
    """
    Requires that the numeric value is in given boundaries.
    """
    def __init__(self, min=None, max=None, default=NotImplemented):
        self._min = min
        self._max = max
        self._default = default

    def _check(self, value):
        if value is MISSING:
            raise InvalidKey(value)
        if self._min is not None and self._min > value:
            raise ValidationError('must be ≥ {expected}'
                                  .format(expected=self._min))
        if self._max is not None and self._max < value:
            raise ValidationError('must be ≤ {expected}'
                                  .format(expected=self._max))

    def _represent(self):
        def _fmt(x):
            return '' if x is None else x
        return '{min}..{max}'.format(min=_fmt(self._min),
                                     max=_fmt(self._max))


class Length(InRange):
    """
    Requires that the value length is in given boundaries.
    """
    def _check(self, value):
        try:
            super(Length, self)._check(len(value))
        except ValidationError as e:
            raise ValidationError('length ' + str(e))


def translate(value):
    """
    Translates given schema from "pythonic" syntax to a validator.

    Usage::

        >>> translate(str)
        IsA(str)
        >>> translate('hello')
        IsA(str, default='hello')

    """
    if isinstance(value, BaseValidator):
        return value

    if value is None:
        return Anything()

    if isinstance(value, type):
        return IsA(value)

    if type(value) in compat.func_types:
        real_value = value()
        return IsA(type(real_value), default=real_value)

    if isinstance(value, list):
        if value == []:
            # no inner spec, just an empty list as the default value
            return IsA(list)
        elif len(value) == 1:
            # the only item as spec for each item of the collection
            return ListOf(translate(value[0]))
        else:
            raise StructureSpecificationError(
                'Expected a list containing exactly 1 item; '
                'got {cnt}: {spec}'.format(cnt=len(value), spec=value))

    if isinstance(value, dict):
        if not value:
            return IsA(dict)
        items = []
        for k, v in value.items():
            if isinstance(k, BaseValidator):
                k_validator = k
            else:
                k_validator = translate(k)
                default = k_validator.get_default_for(None)
                if default is not None:
                    k_validator = Equals(default)
            v_validator = translate(v)
            items.append((k_validator, v_validator))
        return DictOf(items)

    return IsA(type(value), default=value)
