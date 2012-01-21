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
# TODO yield/return subdocuments (spec and value) for external processing so
#      that we don't pass validators/skip_missing/skip_unknown recursively to
#      each validator.

import types

from manipulation import merged


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
    def __init__(self, spec, value, skip_missing=False, skip_unknown=False,
                 value_preprocessor=None):
        self.spec = spec
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
                           skip_unknown=self.skip_unknown,
                           value_preprocessor=self.value_preprocessor)



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
        return isinstance(self.spec, list)

    def validate(self):
        if not isinstance(self.value, list):
            raise TypeError('expected {spec.__name__}, got '
                            '{valtype.__name__} {value!r}'.format(
                            spec=list, valtype=type(self.value),
                            value=self.value))

        if 1 < len(self.spec):
            raise StructureSpecificationError(
                'Expected an empty list or a list containing exactly 1 item; '
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
                                   skip_unknown=self.skip_unknown,
                                   value_preprocessor=self.value_preprocessor)
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
        print 'value is None'
        return

    if spec is None:
        # any value is acceptable
        return

    for validator_class in validators:
        validator = validator_class(spec, value, skip_missing, skip_unknown,
                   value_preprocessor=value_preprocessor)
        if validator.check():
            return validator.validate()
    else:
        pass  # for test coverage


def validate_structure(spec, data, skip_missing=False, skip_unknown=False,
                       validators=VALUE_VALIDATORS, value_preprocessor=None):
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
        if value_preprocessor:
            value = value_preprocessor(typespec, value)
        print key, typespec, value
        try:
            validate_value(typespec, value, validators,
                           skip_missing, skip_unknown,
                           value_preprocessor=value_preprocessor)
        except (MissingKey, UnknownKey, TypeError) as e:
            raise type(e)('{k}: {e}'.format(k=key, e=e))


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
