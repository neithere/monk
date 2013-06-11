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
~~~~~~~~~~
"""
from . import compat
from .schema import canonize
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

    spec_keys = set(rule.inner_spec.keys() if rule.inner_spec else [])
    data_keys = set(value.keys() if value else [])
    unknown = data_keys - spec_keys
    #missing = spec_keys - data_keys

    if unknown and not rule.dict_allow_unknown_keys:
        raise errors.UnknownKey('"{0}"'.format(
            '", "'.join(compat.safe_str(x) for x in unknown)))

    for key in spec_keys | data_keys:
        subrule = canonize(rule.inner_spec.get(key))
        if key in data_keys:
            value_ = value.get(key)
            try:
                validate(subrule, value_)
            except (errors.ValidationError, TypeError) as e:
                raise type(e)('{k}: {e}'.format(k=key, e=e))
        else:
            if subrule.optional:
                continue
            raise errors.MissingKey('{0}'.format(key))


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

    :class:`UnknownKey`
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

        if rule.datatype is None:
            raise errors.MissingValue('expected a value, got None')
        else:
            raise errors.MissingValue('expected {0}, got None'.format(rule.datatype.__name__))

    if rule.datatype is None:
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

    for validator in rule.validators:
        validator(value)
