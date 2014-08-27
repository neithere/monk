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
Value Specification Classes
~~~~~~~~~~~~~~~~~~~~~~~~~~~
"""
__all__ = [
    'BaseRequirement',
    'IsA',
    'Equals',
    'Length',
    'ListOf',
    'DictOf',
    'NotExists',
]

from functools import partial

from . import compat
from .errors import ValidationError, InvalidKey, MissingKey, MissingValue
from .combinators import BaseValidator


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
    default = NotImplemented

    def __call__(self, value):
        if self.implies is not NotImplemented:
            self.implies(value)
        self._check(value)

    def _represent(self):
        return self.__dict__

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, self._represent())


class IsA(BaseRequirement):
    """
    Requires that the value is an instance of given type.
    """
    def __init__(self, expected_type, default=None):
        self.expected_type = expected_type
        self.default = default

    def _check(self, value):
        if not isinstance(value, self.expected_type):
            raise ValidationError('must be {}'.format(self.expected_type.__name__))

    def _represent(self):
        return self.expected_type.__name__


class Equals(BaseRequirement):
    """
    Requires that the value equals given expected value.
    """
    def __init__(self, expected_value, default=None):
        self.expected_value = expected_value
        self.default = default

    def _check(self, value):
        if self.expected_value != value:
            raise ValidationError('!= {!r}' .format(self.expected_value))

    def _represent(self):
        return repr(self.expected_value)


class NotExists(BaseRequirement):
    """
    Requires that the value does not exist.  Obviously this only makes sense in
    special cases like dictionary keys; otherwise there's simply nothing to
    validate.  Note that this is *not* a check against `None` or `False`.
    """
    def __init__(self, default=None):
        self.default = default

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
        self.nested_validator = validator
        self.default = default

    def _check(self, value):
        for i, nested_value in enumerate(value):
            try:
                self.nested_validator(nested_value)
            except ValidationError as e:
                raise ValidationError('#{}: {}'.format(i, e))

    def _represent(self):
        return repr(self.nested_validator)




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


class Length(BaseRequirement):
    """
    Requires that the value length is in given boundaries.
    """
    def __init__(self, min=None, max=None):
        self._min = min
        self._max = max

    def _check(self, value):
        if self._min is not None and self._min > len(value):
            raise ValidationError('length must be ≥ {}'.format(self._min))
        if self._max is not None and self._max < len(value):
            raise ValidationError('length must be ≤ {}'.format(self._max))

    def _represent(self):
        def _fmt(x):
            return '' if x is None else x
        return '{}..{}'.format(_fmt(self._min), _fmt(self._max))
