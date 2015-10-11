# coding: utf-8
#
#    Monk is an unobtrusive data modeling, manipulation and validation library.
#    Copyright © 2011—2015  Andrey Mikhaylenko
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
    'Exists',
    'IsA',
    'HasAttr',
    'Equals',
    'Contains',
    'InRange',
    'Length',
    'ListOf',
    'ListOfAll',
    'ListOfAny',
    'DictOf',

    # functions
    'translate',

    # special objects
    'MISSING',
]


import copy

from . import compat
from .errors import (
    CombinedValidationError, AtLeastOneFailed, AllFailed, ValidationError,
    NoDefaultValue, InvalidKeys, MissingKeys, StructureSpecificationError,
    DictValueError,
)


#: The value is valid if any of its items passes validation.
ITEM_STRATEGY_ANY = 'any'
#: The value is valid if all of its items pass validation.
ITEM_STRATEGY_ALL = 'all'


class MISSING:
    """
    Stub for Exists validator to pass if the value is missing
    (e.g. for dictionary keys).
    """
    pass


def _reluctantly_translate(spec):
    # `translate()` can do it itself but some validators have the `implies`
    # attribute which can trigger instantiation of a BaseValidator subclass
    # before the translation function is ready.
    #
    # We don't want to defer its usage as far as we can because it is best
    # to fully build the validator in order to fail early.
    #
    # So this function is just a small barrier that prevents NameError
    # in some cases.

    if isinstance(spec, BaseValidator):
        return spec
    else:
        return translate(spec)


class BaseValidator(object):
    error_class = ValidationError
    _default = NotImplemented
    negated = False

    def _combine(self, other, combinator):
        # XXX should we flatten same-logic one-item combs?
        if isinstance(other, type) and issubclass(other, BaseValidator):
            # e.g. Exists instead of Exists()
            raise TypeError('got {cls} class instead of its instance'
                            .format(cls=other.__name__))


        return combinator([self, _reluctantly_translate(other)])

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

    def __invert__(self):
        clone = copy.deepcopy(self)
        clone.negated = not self.negated
        return clone

    def __call__(self, value):
        try:
            self._check(value)
        except ValidationError:
            if self.negated:
                return
            else:
                raise
        else:
            if self.negated:
                self._raise_error(value)

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

    def _check(self, value):
        raise NotImplementedError

    def _raise_error(self, value):
        raise self.error_class(repr(self))


class BaseCombinator(BaseValidator):
    error_class = CombinedValidationError
    break_on_first_fail = False
    _repr_tmpl = '{not_}({items})'
    _repr_items_sep = '; '

    def __init__(self, specs, default=None, first_is_default=False):
        assert specs
        self._specs = [_reluctantly_translate(s) for s in specs]
        self._default = default
        self._first_is_default = first_is_default

    def _check(self, value):
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
            raise self.error_class(*errors)


    def __repr__(self):
        return self._repr_tmpl.format(
            cls=self.__class__.__name__,
            items=self._repr_items_sep.join(map(str, self._specs)),
            not_='not ' if self.negated else '')


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
    _repr_items_sep = ' and '

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
    _repr_items_sep = ' or '

    def can_tolerate(self, errors):
        if len(errors) < len(self._specs):
            return True


class BaseRequirement(BaseValidator):
    # a hint for combinators, see their code
    is_recursive = False
    implies = NotImplemented

    def __call__(self, value):
        if self.implies is not NotImplemented:
            self.implies(value)
        super(BaseRequirement, self).__call__(value)

    def _represent(self):
        return self.__dict__

    def __repr__(self):
        return '{negated}{cls}({rep})'.format(
            cls=self.__class__.__name__,
            rep=self._represent(),
            negated='~' if self.negated else '')


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
            self._raise_error(value)

    def __repr__(self):
        s = 'must be {pattern_}'.format(pattern_=self.expected_type.__name__)
        if self.negated:
            s = 'not ({s})'.format(s=s)
        return s


class Equals(BaseRequirement):
    """
    Requires that the value equals given expected value.
    """
    def __init__(self, expected_value):
        self._expected_value = expected_value

    def _check(self, value):
        if self._expected_value != value:
            self._raise_error(value)

    def __repr__(self):
        s = 'must equal {pattern_!r}'.format(pattern_=self._expected_value)
        if self.negated:
            s = 'not ({s})'.format(s=s)
        return s

    @property
    def _default(self):
        return self._expected_value


class Contains(BaseRequirement):
    """
    Requires that the value contains given expected value.
    """
    def __init__(self, expected_value):
        self._expected_value = expected_value

    def _check(self, value):
        if self._expected_value not in value:
            self._raise_error(value)

    def __repr__(self):
        s = 'must contain {pattern_!r}'.format(pattern_=self._expected_value)
        if self.negated:
            s = 'not ({s})'.format(s=s)
        return s

    @property
    def _default(self):
        return self._expected_value


class Exists(BaseRequirement):
    """
    Requires that the value exists.  Obviously this only makes sense in
    special cases like dictionary keys; otherwise there's simply nothing to
    validate.  Note that this is *not* a check against `None` or `False`.
    """
    def __init__(self, default=None):
        self._default = default

    def _check(self, value):
        if value is MISSING:
            self._raise_error(value)

    def __repr__(self):
        if self.negated:
            return 'must not exist'
        else:
            return 'must exist'


class BaseListOf(BaseRequirement):
    """
    The base class for validating lists.  Supports different error toleration
    strategies which can be selected by subclasses.  In many aspects this is
    similar to :class:`BaseCombinator`.
    """
    implies = IsA(list)
    item_strategy = NotImplemented
    error_class = CombinedValidationError
    is_recursive = True

    def __init__(self, validator, default=None):
        self._nested_validator = translate(validator)
        self._default = default

    def _check(self, value):
        if not value:
            try:
                self._nested_validator(MISSING)
            except ValidationError as e:
                raise ValidationError('lacks item: {error}'
                                      .format(error=e))

        errors = []
        for i, nested_value in enumerate(value):
            try:
                self._nested_validator(nested_value)
            except ValidationError as e:
                annotated_error = ValidationError(
                    'item #{elem}: {error}'.format(elem=i, error=e))
                if self.item_strategy == ITEM_STRATEGY_ALL:
                    raise annotated_error
                errors.append(annotated_error)

        if self.can_tolerate(errors, value):
            return

        raise self.error_class(*errors)

    def can_tolerate(self, errors, value):
        if self.item_strategy == ITEM_STRATEGY_ALL:
            if errors:
                return False
            else:
                return True
        elif self.item_strategy == ITEM_STRATEGY_ANY:
            if len(errors) < len(value):
                return True
            else:
                return False
        else:
            raise ValueError('unknown strategy')

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


class ListOfAll(BaseListOf):
    """
    Requires that the value is a `list` which items match given validator.
    Usage::

        >>> v = ListOfAll(IsA(int) | IsA(str))

        >>> v([123, 'hello'])

        >>> v([123, 'hello', 5.5])
        Traceback (most recent call last):
        ...
        ValidationError: item #2: must be int or must be str

    """
    error_class = AtLeastOneFailed
    item_strategy = ITEM_STRATEGY_ALL


class ListOfAny(BaseListOf):
    """
    Same as :class:`ListOfAll` but tolerates invalid items as long as there
    is at least one valid among them.
    """
    error_class = AllFailed
    item_strategy = ITEM_STRATEGY_ANY


ListOf = ListOfAll


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
        ...     (Equals('age') | ~Exists(), IsA(int)),
        ...     # there may be other `str` keys with `str` or `int` values
        ...     (IsA(str), IsA(str) | IsA(int)),
        ... ])

        >>> v({'name': 'John'})

        >>> v({'name': 'John', 'age': 25})

        >>> v({'name': 'John', 'age': 25.5})
        Traceback (most recent call last):
        ...
        DictValueError: 'age' value must be int

        >>> v({'name': 'John', 'age': 25, 'note': 'custom field'})

        >>> v({'name': 'John', 'age': 25, 'note': 5.5})
        Traceback (most recent call last):
        ...
        DictValueError: 'note' value must be str or must be int

    Note that this validator supports :class:`Exists` to mark keys that can
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

                # check if this key is described by current key validator;
                # if it isn't, just skip it (and try another validator
                # on it later on)
                try:
                    k_validator(k)
                except (TypeError, ValidationError):
                    continue

                # this key *is* described by current value validator;
                # validate the value (it *must* validate)
                try:
                    v_validator(v)
                except (ValidationError, TypeError) as e:
                    if isinstance(e, DictValueError):
                        msg = 'in {k!r} ({e})'
                    else:
                        msg = '{k!r} value {e}'
                    raise DictValueError(msg.format(k=k, e=e))

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
            invalid_keys = set(value) - set(validated_data_keys)
            raise InvalidKeys(*invalid_keys)

        if missing_key_specs:
            # XXX this prints validators, not keys as strings;
            #     one exception is the Equals validator from which we get
            #     the expected value via internal API.  And that's gross.
            reprs = (spec._expected_value if isinstance(spec, Equals) else spec
                     for spec in missing_key_specs)
            raise MissingKeys(*reprs)


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
    implies = IsA(int) | IsA(float)

    def __init__(self, min=None, max=None, default=NotImplemented):
        self._min = min
        self._max = max
        if default is not NotImplemented:
            self._default = default

    def _check(self, value):
        if self._min is not None and self._min > value:
            self._raise_error(value)
        if self._max is not None and self._max < value:
            self._raise_error(value)

    def __repr__(self):
        if self.negated:
            must = 'must not'
        else:
            must = 'must'
        def _fmt(x):
            return '' if x is None else x
        return '{must} belong to {min_}..{max_}'.format(
            must=must, min_=_fmt(self._min), max_=_fmt(self._max))



class HasAttr(BaseRequirement):
    """
    Requires that the value has given attribute.
    """
    def __init__(self, attr_name):
        self._attr_name = attr_name

    def _check(self, value):
        if not hasattr(value, self._attr_name):
            self._raise_error(value)

    def __repr__(self):
        if self.negated:
            must = 'must not'
        else:
            must = 'must'
        return '{must} have attribute {name!r}'.format(
            must=must, name=self._attr_name)



class Length(InRange):
    """
    Requires that the value length is in given boundaries.
    """
    implies = HasAttr('__len__')

    def _check(self, value):
        try:
            super(Length, self)._check(len(value))
        except ValidationError as e:
            self._raise_error(value)

    def __repr__(self):
        if self.negated:
            must = 'must not'
        else:
            must = 'must'
        def _fmt(x):
            return '' if x is None else x
        return '{must} have length of {min_}..{max_}'.format(
            must=must, min_=_fmt(self._min), max_=_fmt(self._max))


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
