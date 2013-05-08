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
    # functions
    'validate'
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



def validate_dict(rule, value):
    """ Nested dictionary. May contain complex structures which are validated
    recursively.

    The specification can be any dictionary, whether empty or not. It will be
    treated as a separate document.
    """
    if not isinstance(value, dict):
        raise TypeError('expected {spec.__name__}, got '
                        '{valtype.__name__} {value!r}'.format(
                        spec=dict, valtype=type(value),
                        value=value))

    if not rule.inner_spec:
        # spec is {} which means "a dict of anything"
        return

    # compare the two structures; nested dictionaries are included in the
    # comparison but nested lists are opaque and will be dealt with later on.
    spec_keys = set(rule.inner_spec.keys() if rule.inner_spec else [])
    data_keys = set(value.keys() if value else [])
    unknown = data_keys - spec_keys

    if unknown and not rule.skip_unknown:
        raise UnknownKey('Unknown keys: {0}'.format(
            ', '.join(compat.safe_str(x) for x in unknown)))

    # check types and deal with nested lists
    for key in spec_keys | data_keys:
        subrule = canonize(rule.inner_spec.get(key))
        if key in data_keys:
            value_ = value.get(key)
            try:
                validate(subrule, value_)
            except (MissingKey, UnknownKey, TypeError) as e:
                raise type(e)('{k}: {e}'.format(k=key, e=e))
        else:
            if subrule.skip_missing:
                continue
            raise MissingKey('{0}'.format(key))


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

    # FIXME this belongs to the internals of canonize()
    #       and the "first item as spec for inner collection" thing
    #       should go to a special Rule attribute
    if 1 < len(rule.inner_spec):
        raise StructureSpecificationError(
            'Expected an empty list or a list containing exactly 1 item; '
            'got {cnt}: {spec}'.format(cnt=len(rule.inner_spec), spec=rule.inner_spec))
    item_spec = canonize(rule.inner_spec[0])

    for item in value:
        if item_spec == dict or isinstance(item, dict):

            # value is a dict; expected something else
            if isinstance(item, dict) and not item_spec.datatype == dict:
                raise TypeError('expected {spec}, got a dictionary'.format(
                    spec=item_spec))

            # validate each value in the list as a separate document
            validate(item_spec, item)
        else:
            validate_type(item_spec, item)


def validate_type(rule, value):
    """ Simple type check.
    """
    if not isinstance(value, rule.datatype):
        raise TypeError('expected {typespec.__name__}, got '
                        '{valtype.__name__} {value!r}'.format(
                        typespec=rule.datatype, valtype=type(value),
                        value=value))



def validate(rule, value):
    """ Checks if given `value` is valid for given `spec`, using given sequence
    of `validators`.

    The validators are expected to be subclasses of :class:`ValueValidator`.
    They are polled one by one; the first one that agrees to process given
    value is used to validate the value.
    """
    if value is None:
        # empty value, ok unless required
        return

    rule = canonize(rule)

    if not rule:
        # no rule defined at all
        return

    if rule.datatype is None:
        # any value is acceptable
        return

    if rule.datatype == dict:
        return validate_dict(rule, value)

    if rule.datatype == list:
        return validate_list(rule, value)

    assert not rule.inner_spec
    if isinstance(rule.datatype, type):
        validate_type(rule, value)

    return None


validate_value = validate_structure = validate


def validate_structure_spec(spec):
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
                       value_preprocessor=dictmerger)
