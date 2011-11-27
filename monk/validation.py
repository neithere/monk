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
"""
from collections import deque


class StructureSpecificationError(Exception):
    "Raised when malformed document structure is detected."
    pass


class MissingKey(KeyError):
    """ Raised when a key is defined in the structure spec but is missing from
    a data dictionary.
    """


class UnknownKey(KeyError):
    """ Raised when a key in data dictionary is missing from the corresponding
    structure spec.
    """


def walk_dict(data):
    """ Generates pairs ``(keys, value)`` for each item in given dictionary,
    including nested dictionaries. Each pair contains:

    `keys`
        a tuple of 1..n keys, e.g. ``('foo',)`` for a key on root level or
        ``('foo', 'bar')`` for a key in a nested dictionary.
    `value`
        the value of given key or ``None`` if it is a nested dictionary and
        therefore can be further unwrapped.
    """
    assert hasattr(data, '__getitem__')
    for key, value in data.iteritems():
        if isinstance(value, dict):
            yield (key,), None
            for keys, value in walk_dict(value):
                path = (key,) + keys
                yield path, value
        else:
            yield (key,), value


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
                stack.append((keys+subkeys, subvalue))
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


def check_type(typespec, value, keys_tuple):
    if typespec is None:
        return
    if not isinstance(typespec, type):
        key = '.'.join(keys_tuple)
        raise StructureSpecificationError(
            '{path}: expected dict, list, type or None (got {value!r})'
                .format(path=key, value=value))
    if not isinstance(value, typespec):
        key = '.'.join(keys_tuple)
        raise TypeError('{key}: expected {typespec.__name__}, got '
                        '{valtype.__name__} {value!r}'.format(key=key,
                        typespec=typespec, valtype=type(value), value=value))


def validate_structure(spec, data, skip_missing=False, skip_unknown=False):
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
    # flatten the structures so that nested dictionaries are moved to the root
    # level and {'a': {'b': 1}} becomes {('a','b'): 1}
    flat_spec = dict(walk_dict(spec))
    flat_data = dict(walk_dict(data))

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
    for keys, value in flat_data.iteritems():
        typespec = flat_spec.get(keys)
        if value is None:
            # empty value, ok unless required
            continue
        elif typespec is None:
            # any value is acceptable
            continue
        elif isinstance(typespec, list) and value:
            # nested list
            item_spec = typespec[0]
            for item in value:
                if item_spec == dict or isinstance(item, dict):
                    # validate each value in the list as a separate document
                    # and fix error message to include outer key
                    try:
                        validate_structure(item_spec, item,
                                           skip_missing=skip_missing,
                                           skip_unknown=skip_unknown)
                    except (MissingKey, UnknownKey, TypeError) as e:
                        raise type(e)('{k}: {e}'.format(k='.'.join(keys), e=e))
                else:
                    check_type(item_spec, item, keys)
        else:
            check_type(typespec, value, keys)