# -*- coding: utf-8 -*-
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
Validation
==========

.. attribute:: VALUE_VALIDATORS

    Default sequence of validators:

    * :class:`DictValidator`
    * :class:`ListValidator`
    * :class:`TypeValidator`

"""
# TODO yield/return subdocuments (spec and value) for external processing so
#      that we don't pass validators/skip_missing/skip_unknown recursively to
#      each validator.

from . import compat
from .manipulation import merged
from .schema import canonize


__all__ = [
    # errors
    'ValidationError', 'StructureSpecificationError', 'MissingKey',
    'UnknownKey',
    # validators
    'ValueValidator', 'DictValidator', 'ListValidator', 'TypeValidator',
    # functions
    'validate_structure_spec', 'validate_structure', 'validate_value',
]


class ValidationError(Exception):
    "Raised when a document or its part cannot pass validation."


class StructureSpecificationError(ValidationError):
    "Raised when malformed document structure is detected."


class MissingKey(ValidationError):
    """ Raised when a key is defined in the structure spec but is missing from
    a data dictionary.
    """


class UnknownKey(ValidationError):
    """ Raised when a key in data dictionary is missing from the corresponding
    structure spec.
    """


class ValueValidator(object):
    """ Base class for value validators.
    """
    def __init__(self, rule, value, skip_missing=False, skip_unknown=False,
                 value_preprocessor=None):
        self.rule = rule
        self.value = value
        self.skip_missing = skip_missing
        self.skip_unknown = skip_unknown
        self.value_preprocessor = value_preprocessor


    def check(self):
        """ Returns ``True`` if this validator can handle given spec/value
        pair, otherwise returns ``False``.

        Subclasses must overload this method.
        """
        raise NotImplementedError

    def validate(self):
        """ Returns ``None`` if `self.value` is valid for `self.spec` or raises
        a :class:`ValidationError`.

        Subclasses must overload this method.
        """
        raise NotImplementedError


class DictValidator(ValueValidator):
    """ Nested dictionary. May contain complex structures which are validated
    recursively.

    The specification can be any dictionary, whether empty or not. It will be
    treated as a separate document.
    """
    def check(self):
        return self.rule.datatype == dict

    def validate(self):
        if not isinstance(self.value, dict):
            raise TypeError('expected {spec.__name__}, got '
                            '{valtype.__name__} {value!r}'.format(
                            spec=dict, valtype=type(self.value),
                            value=self.value))

        if not self.rule.inner_spec:
            # spec is {} which means "a dict of anything"
            return

        # compare the two structures; nested dictionaries are included in the
        # comparison but nested lists are opaque and will be dealt with later on.
        spec_keys = set(self.rule.inner_spec.keys() if self.rule.inner_spec else [])
        data_keys = set(self.value.keys() if self.value else [])
        unknown = data_keys - spec_keys

        if unknown and not self.rule.skip_unknown:
            raise UnknownKey('Unknown keys: {0}'.format(
                ', '.join(compat.safe_str(x) for x in unknown)))

        # check types and deal with nested lists
        for key in spec_keys | data_keys:
            rule = canonize(self.rule.inner_spec.get(key))
            if key in data_keys:
                value = self.value.get(key)
                try:
                    validate_structure(rule, value)
                except (MissingKey, UnknownKey, TypeError) as e:
                    raise type(e)('{k}: {e}'.format(k=key, e=e))
            else:
                if rule.skip_missing:
                    continue
                raise MissingKey('{0}'.format(key))


        # validate value as a separate document



class ListValidator(ValueValidator):
    """ Nested list. May contain complex structures which are validated
    recursively.

    The specification can be either an empty list::

        >>> ListValidator([], [123]).validate()

    ...or a list with exactly one item::

        >>> ListValidator([int], [123, 456]).validate()
        >>> ListValidator([{'foo': int], [{'foo': 123}]).validate()

    """
    def check(self):
        return self.rule.datatype == list

    def validate(self):
        if not isinstance(self.value, list):
            raise TypeError('expected {spec.__name__}, got '
                            '{valtype.__name__} {value!r}'.format(
                            spec=list, valtype=type(self.value),
                            value=self.value))

        if 1 < len(self.rule.inner_spec):
            raise StructureSpecificationError(
                'Expected an empty list or a list containing exactly 1 item; '
                'got {cnt}: {spec}'.format(cnt=len(self.rule.inner_spec), spec=self.rule.inner_spec))

        if not self.rule.inner_spec:
            # spec is [] which means "a list of anything"
            return

        # FIXME this belongs to the internals of canonize()
        #       and the "first item as spec for inner collection" thing
        #       should go to a special Rule attribute
        item_spec = canonize(self.rule.inner_spec[0])

        for item in self.value:
            if item_spec == dict or isinstance(item, dict):

                # value is a dict; expected something else
                if isinstance(item, dict) and not item_spec.datatype == dict:
                    raise TypeError('expected {spec}, got a dictionary'.format(
                        spec=item_spec))

                # validate each value in the list as a separate document
                validate_structure(item_spec, item)
            else:
                validate_value(item_spec, item, [TypeValidator])


class TypeValidator(ValueValidator):
    """ Simple type check.
    """
    def check(self):
        return isinstance(self.rule.datatype, type)

    def validate(self):
        if not isinstance(self.value, self.rule.datatype):
            raise TypeError('expected {typespec.__name__}, got '
                            '{valtype.__name__} {value!r}'.format(
                            typespec=self.rule.datatype, valtype=type(self.value),
                            value=self.value))


VALUE_VALIDATORS = (
    DictValidator, ListValidator, TypeValidator,
)


def validate(rule, value, validators=VALUE_VALIDATORS,
             skip_missing=False, skip_unknown=False,
             value_preprocessor=None):
    """ Checks if given `value` is valid for given `spec`, using given sequence
    of `validators`.

    The validators are expected to be subclasses of :class:`ValueValidator`.
    They are polled one by one; the first one that agrees to process given
    value is used to validate the value.
    """
    if value is None:
        # empty value, ok unless required
        return

    rule_kwargs = dict(skip_missing=skip_missing, skip_unknown=skip_unknown)
    rule = canonize(rule, rule_kwargs)    # → Rule instance

    if not rule:
        # no rule defined at all
        return

    if rule.datatype is None:
        # any value is acceptable
        return

    if rule.datatype == dict:
        validators = [DictValidator]
    elif rule.datatype == list:
        validators = [ListValidator]
    else:
        assert not rule.inner_spec

    for validator_class in validators:
        validator = validator_class(rule, value, skip_missing, skip_unknown,
                   value_preprocessor=value_preprocessor)
        if validator.check():
            return validator.validate()
    else:
        pass  # for test coverage


validate_value = validate_structure = validate


def validate_structure_spec(spec, validators=VALUE_VALIDATORS):
    # this is a pretty dumb function that simply populates the data when normal
    # manipulation function fails to do that because of ambiguity.
    # The dictionaries are created even within lists; missing keys are created
    # with None values.
    # This enables validate_structure() to peek into nested levels (by default
    # it bails out when a key is missing).
    def dictmerger(typespec, value):
        if value == [] and typespec:
            for elem in typespec:
                if isinstance(elem, type):
                    # [int] -> [None]
                    value.append(None)
                elif isinstance(elem, dict):
                    # [{'a': int}] -> [{'a': None}]
                    value.append(merged(elem, {}))
        return value
    validate_structure(spec, merged(spec, {}), skip_missing=True, skip_unknown=True,
                       validators=validators, value_preprocessor=dictmerger)
