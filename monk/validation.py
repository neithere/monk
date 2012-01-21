# -*- coding: utf-8 -*-
#
#    Monk is a lightweight schema/query framework for document databases.
#    Copyright © 2011  Andrey Mikhaylenko
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
    * :class:`FuncValidator`
    * :class:`InstanceValidator`

"""
from collections import deque
import types

from monk.helpers import walk_dict


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


def validate_structure_spec(spec):
    """ Checks whether given document structure specification dictionary if
    defined correctly.

    Raises :class:`StructureSpecificationError` if the specification is
    malformed.
    """
    stack = deque(walk_dict(spec))
    while stack:
        keys, value = stack.pop()
        if isinstance(value, list):
            # accepted: list of values of given type
            # e.g.: [unicode] -> [u'foo', u'bar']
            if len(value) == 1:
                stack.append((keys, value[0]))
            else:
                raise StructureSpecificationError(
                    '{path}: list must contain exactly 1 item (got {count})'
                         .format(path='.'.join(keys), count=len(value)))
        elif isinstance(value, dict):
            # accepted: nested dictionary (a spec on its own)
            # e.g.: {...} -> {...}
            for subkeys, subvalue in walk_dict(value):
                stack.append((keys + subkeys, subvalue))
        elif value is None:
            # accepted: any value
            # e.g.: None -> 123
            pass
        elif isinstance(value, type):
            # accepted: given type
            # e.g.: unicode -> u'foo'   or   dict -> {'a': 123}   or whatever.
            pass
        else:
            raise StructureSpecificationError(
                '{path}: expected dict, list, type or None (got {value!r})'
                    .format(path='.'.join(keys), value=value))


class ValueValidator(object):
    """ Base class for value validators.
    """
    def __init__(self, spec, value, skip_missing=False, skip_unknown=False):
        self.spec = spec
        self.value = value
        self.skip_missing = skip_missing
        self.skip_unknown = skip_unknown

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
    """
    def check(self):
        return isinstance(self.spec, dict)

    def validate(self):
        if not isinstance(self.value, dict):
            raise TypeError('expected {spec.__name__}, got '
                            '{valtype.__name__} {value!r}'.format(
                            spec=dict, valtype=type(self.value),
                            value=self.value))

        if not self.spec:
            # spec is {} which means "a dict of anything"
            return

        # validate value as a separate document
        validate_structure(self.spec, self.value,
                           skip_missing=self.skip_missing,
                           skip_unknown=self.skip_unknown)



class ListValidator(ValueValidator):
    """ Nested list. May contain complex structures which are validated
    recursively.
    """
    def check(self):
        return isinstance(self.spec, list)

    def validate(self):
        if not isinstance(self.value, list):
            raise TypeError('expected {spec.__name__}, got '
                            '{valtype.__name__} {value!r}'.format(
                            spec=list, valtype=type(self.value),
                            value=self.value))

        if 1 < len(self.spec):
            raise StructureSpecificationError(
                'List specification must contain exactly one item; '
                'got {cnt}: {spec}'.format(cnt=len(self.spec), spec=self.spec))

        if not self.spec:
            # spec is [] which means "a list of anything"
            return

        item_spec = self.spec[0]

        for item in self.value:
            if item_spec == dict or isinstance(item, dict):
                # validate each value in the list as a separate document
                validate_structure(item_spec, item,
                                   skip_missing=self.skip_missing,
                                   skip_unknown=self.skip_unknown)
            else:
                validate_value(item_spec, item, [TypeValidator])


class TypeValidator(ValueValidator):
    """ Simple type check.
    """
    def check(self):
        return isinstance(self.spec, type)

    def validate(self):
        if not isinstance(self.value, self.spec):
            raise TypeError('expected {typespec.__name__}, got '
                            '{valtype.__name__} {value!r}'.format(
                            typespec=self.spec, valtype=type(self.value),
                            value=self.value))


class InstanceValidator(ValueValidator):
    """ Type check against an instance: both instances must be of the same
    type. Example::

        >>> InstanceValidator(1, 2).validate()
        >>> InstanceValidator(1, 'a').validate()
        TypeError: ...

    """
    def check(self):
        # NOTE: greedy!
        return not isinstance(self.spec, type)

    def validate(self):
        spec = type(self.spec)
        validate_value(spec, self.value, [TypeValidator])


class FuncValidator(ValueValidator):
    """ Default value is obtained from a function with no arguments;
    then check type against what the callable returns. (It is expected
    that the callable does not have side effects.)
    Example::

        >>> FuncValidator(lambda: int, 2).validate()
        >>> FuncValidator(lambda: int, 'a').validate()
        TypeError: ...

    Instances are also supported::

        >>> FuncValidator(lambda: 1, 2).validate()
        >>> FuncValidator(lambda: 1, 'a').validate()
        TypeError: ...

    """
    def check(self):
        func_types = types.FunctionType, types.BuiltinFunctionType
        return isinstance(self.spec, func_types)

    def validate(self):
        spec = self.spec()
        validate_value(spec, self.value, [TypeValidator, InstanceValidator])


VALUE_VALIDATORS = (
    DictValidator, ListValidator, TypeValidator, FuncValidator,
    InstanceValidator
)


def validate_value(spec, value, validators,
                   skip_missing=False, skip_unknown=False):
    """ Checks if given `value` is valid for given `spec`, using given sequence
    of `validators`.

    The validators are expected to be subclasses of :class:`ValueValidator`.
    They are polled one by one; the first one that agrees to process given
    value is used to validate the value.
    """
    if value is None:
        # empty value, ok unless required
        return

    if spec is None:
        # any value is acceptable
        return

    for validator_class in validators:
        validator = validator_class(spec, value, skip_missing, skip_unknown)
        if validator.check():
            return validator.validate()
    else:
        pass  # for test coverage


def validate_structure(spec, data, skip_missing=False, skip_unknown=False,
                       validators=VALUE_VALIDATORS):
    """ Validates given document against given structure specification.
    Always returns ``None``.

    :param spec:
        `dict`; document structure specification.
    :param data:
        `dict`; document to be validated against the spec.
    :param skip_missing:
        ``bool``; if ``True``, :class:`MissingKey` is never raised.
        Default is ``False``.
    :param skip_unknown:
        ``bool``; if ``True``, :class:`UnknownKey` is never raised.
        Default is ``False``.
    :param validators:
        `sequence`. An ordered series of :class:`ValueValidator` subclasses.
        Default is :attr:`VALUE_VALIDATORS`. The validators are passed to
        :func:`validate_value`.

    Can raise:

    :class:`MissingKey`
        if a key is in `spec` but not in `data`.
    :class:`UnknownKey`
        if a key is in `data` but not in `spec`.
    :class:`StructureSpecificationError`
        if errors were found in `spec`.
    :class:`TypeError`
        if a value in `data` does not belong to the designated type.

    """
    # compare the two structures; nested dictionaries are included in the
    # comparison but nested lists are opaque and will be dealt with later on.
    spec_keys = set(spec.iterkeys())
    data_keys = set(data.iterkeys())
    missing = spec_keys - data_keys
    unknown = data_keys - spec_keys

    if missing and not skip_missing:
        raise MissingKey('Missing keys: {0}'.format(', '.join(missing)))

    if unknown and not skip_unknown:
        raise UnknownKey('Unknown keys: {0}'.format(', '.join(unknown)))

    # check types and deal with nested lists
    for key in spec_keys | data_keys:
        typespec = spec.get(key)
        value = data.get(key)
        try:
            validate_value(typespec, value, validators,
                           skip_missing, skip_unknown)
        except (MissingKey, UnknownKey, TypeError) as e:
            raise type(e)('{k}: {e}'.format(k=key, e=e))
