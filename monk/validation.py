# -*- coding: utf-8 -*-
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
Validation
~~~~~~~~~~
"""
from . import compat
from .schema import OneOf, canonize
from . import errors

__all__ = [
    # functions
    'validate'
]



def validate_dict(rule, value):
    """ Nested dictionary. May contain complex structures which are validated
    recursively.

    The specification can be any dictionary, whether empty or not. It will be
    treated as a separate document.
    """
    validate_type(rule, value)

    if not rule.inner_spec:
        # spec is {} which means "a dict of anything"
        return

    spec = tuple((canonize(k), canonize(v)) for k,v in rule.inner_spec.items())

    #missing = spec_keys - data_keys


    value = value or {}
    validated_data_keys = []
    missing_key_specs = []
    for kspec, vspec in spec:
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
                validate(kspec, k)
            except (TypeError, errors.ValidationError):
                continue
            else:
                # key validation is more strict: if default value is present,
                # the key *must* be equal to it
                if kspec.default is not None and k != kspec.default:
                    continue

            # this key *is* described by current rule;
            # validate the value (it *must* validate)
            try:
                validate(vspec, v)
            except (errors.ValidationError, TypeError) as e:
                raise type(e)('{k}: {e}'.format(k=k, e=e))

            validated_data_keys.append(k)
            matched = True

        if not matched and not kspec.optional:
            missing_key_specs.append(kspec)

    # TODO document that unknown keys are checked before missing ones

    # check if there are data keys that did not match any key spec;
    # if yes, raise InvalidKey for them
    if len(validated_data_keys) < len(value):
        raise errors.InvalidKey(', '.join(repr(x) for x in set(value) - set(validated_data_keys)))

    if missing_key_specs:
        # NOTE: this prints rules, not keys as strings
        raise errors.MissingKey('"{0}"'.format(
            '", "'.join(rule.default if rule.default else compat.safe_str(rule)
                        for rule in missing_key_specs)))


def validate_list(rule, value):
    """ Nested list. May contain complex structures which are validated
    recursively.

    The specification can be either an empty list::

        >>> validate_list(Rule(list, inner_spec=[]), [123])

    ...or a list with exactly one item::

        >>> validate_list(Rule(list, inner_spec=[int]), [123, 456])
        >>> validate_list(Rule(list, inner_spec=[{'foo': int]), [{'foo': 123}])

    """
    if not isinstance(value, list):
        raise TypeError('expected {spec.__name__}, got '
                        '{valtype.__name__} {value!r}'.format(
                        spec=list, valtype=type(value),
                        value=value))

    if not rule.inner_spec:
        # spec is [] which means "a list of anything"
        return

    item_spec = canonize(rule.inner_spec)
    assert item_spec

    # XXX custom validation stuff can be inserted here, e.g. min/max items

    if not value and not item_spec.optional:
        raise errors.MissingValue('expected at least one item, got empty list')

    for i, item in enumerate(value):
        try:
            validate(item_spec, item)
        except (errors.ValidationError, TypeError) as e:
            raise type(e)('#{i}: {e}'.format(i=i, e=e))


def validate_type(rule, value):
    """ Simple type check.
    """
    if not isinstance(value, rule.datatype):
        raise TypeError('expected {typespec.__name__}, got '
                        '{valtype.__name__} {value!r}'.format(
                        typespec=rule.datatype, valtype=type(value),
                        value=value))



def validate(rule, value):
    """
    Validates given value against given specification.
    Raises an exception if the value is invalid.
    Always returns ``None``.

    :rule:
        a :class:`~monk.schema.Rule` instance or any other value digestible
        by :func:`canonize`.
    :value:
        any value including complex structures.

    Can raise:

    :class:`MissingValue`
        if a dictionary key is in the spec but not in the value.
        This applies to root and nested dictionaries.

    :class:`MissingKey`
        if a dictionary key is in the spec but not in the value.
        This applies to root and nested dictionaries.

    :class:`InvalidKey`
        if a dictionary key is the value but not not in the spec.

    :class:`StructureSpecificationError`
        if errors were found in spec.

    :class:`TypeError`
        if the value (or a nested value) does not belong to the designated type.

    """
    rule = canonize(rule)

    if value is None:
        # empty value, ok unless required
        if rule.optional:
            return

        if rule.datatype is NotImplemented:
            pass
        elif rule.datatype is None:
            raise errors.MissingValue('expected a value, got None')
        else:
            raise errors.MissingValue('expected {0}, got None'.format(rule.datatype.__name__))

    if isinstance(rule, OneOf):
        # FIXME we've been expecting a rule (Rule instance) but got an instance
        # of another class.  OneOf should inherit Rule or they should have
        # a common base class.

        # validating against the alternative rules, one by one
        failures = []
        for subrule in rule.choices:
            try:
                validate(subrule, value)
            except Exception as e:
                failures.append(e)
                continue
            else:
                # we have a winner! that's enough to pass the test
                return
        raise errors.ValidationError('failed {0} alternative rules: {1}'.format(
            len(rule.choices),
            '; '.join(
                ('{0}) {1}: {2}'.format(i+1, e.__class__.__name__, e)
                    for i, e in enumerate(failures)))))

    if rule.datatype is NotImplemented:
        pass
    elif rule.datatype is None:
        # any value is acceptable
        pass
    elif rule.datatype == dict:
        validate_dict(rule, value)
    elif rule.datatype == list:
        validate_list(rule, value)
    else:
        assert not rule.inner_spec
        if isinstance(rule.datatype, type):
            validate_type(rule, value)

    if rule.validators is NotImplemented:
        pass
    else:
        for validator in rule.validators:
            validator(value)
