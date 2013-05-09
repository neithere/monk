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
Schema Definition
~~~~~~~~~~~~~~~~~
"""
from . import compat


__all__ = [
    'Rule', 'canonize',
    # shortcuts:
    'any_value', 'optional'
]


#-------------------------------------------
# Classes
#

class Rule:
    """
    Extended specification of a field.  Allows marking it as optional.

    :param datatype:
        one of:

        * a type/class (stands for "an instance of this type/class")
        * `None` (stands for "any value of any kind or no value at all")

    :param default:
        an instance of `datatype` to be used in the absence of a value.

    :param inner_spec:
        a spec for nested data (can be another :class:`Rule` instance
        or something that :func:`canonize` can convert to one).

    :param optional:
        ``bool``; if ``True``, :class:`MissingValue` is never raised.
        Default is ``False``.

    :param skip_unknown_keys:
        ``bool``; if ``True``, :class:`UnknownKey` is never raised.
        Default is ``False``.

    .. note:: Missing Key vs. Unknown Key

       :MissingKey:
            Applies: to a dictionary key.

            Trigger: a key is missing from the dictionary.

            Suppress: turn the `optional` setting on.
            This allows the key to be completely missing from an outer dictionary.

       :UnknownKey:
            Applies: to a dictionary key.

            Trigger: the dictionary contains a key which is not in
            the dictionary's `inner_spec`.

            Suppress: turn the `skip_unknown_keys` setting on
            (of course on dictionary level).

    """
    def __init__(self, datatype, inner_spec=None, optional=False, skip_unknown_keys=False, default=None):
        if isinstance(datatype, type(self)):
            raise ValueError('Cannot use a Rule instance as datatype')
        self.datatype = datatype
        self.inner_spec = inner_spec
        self.optional = optional
        self.skip_unknown_keys = skip_unknown_keys
        if default is not None and not isinstance(default, self.datatype):
            raise ValueError('Default value must match datatype {0} (got {1})'.format(
                self.datatype, default))
        self.default = default

        # sanity checks
        if self.inner_spec:
            assert isinstance(self.inner_spec, self.datatype)

    def __repr__(self):
        return '<Rule {datatype} {policy}{default}{inner_spec}>'.format(
            datatype=('any' if self.datatype is None else
                str(self.datatype).replace('<','').replace('>','')),
            policy=('optional' if self.skip_missing else 'required'),
            default=(' default={0}'.format(self.default)
                     if self.default is not None else ''),
            inner_spec=(' inner_spec={0}'.format(self.inner_spec)
                     if self.inner_spec is not None else ''))

    def __eq__(self, other):
        if (isinstance(other, type(self)) and self.__dict__ == other.__dict__):
            return True


#-------------------------------------------
# Functions
#

def canonize(spec, rule_kwargs={}):
    """
    Returns the canonic representation of given natural spec.

    :param spec: :term:`natural spec` (a `dict`)

    :return: :term:`detailed spec` (`dict` with :class:`Rule` instances as values)
    """
    value = spec

    if isinstance(value, Rule):
        rule = value
    elif value is None:
        rule = Rule(None, **rule_kwargs)
    elif isinstance(value, type):
        rule = Rule(value, **rule_kwargs)
    elif type(value) in compat.func_types:
        real_value = value()
        kwargs = dict(rule_kwargs, default=real_value)
        rule = Rule(type(real_value), **kwargs)
    elif type(value) in (dict, list):
        kwargs = dict(rule_kwargs, inner_spec=value)
        rule = Rule(type(value), **kwargs)
    else:
        kwargs = dict(rule_kwargs, default=value)
        rule = Rule(type(value), **kwargs)

    return rule


#-------------------------------------------
# Shortcuts
#

def optional(spec):
    """
    Returns a canonized `spec` marked as optional.
    ::

        >>> optional(str) == Rule(datatype=str, optional=True)
        True

    """
    if isinstance(spec, Rule):
        spec.optional = True
        return spec
    else:
        return canonize(spec, rule_kwargs={'optional': True})


any_value = Rule(None)
"A shortcut for ``Rule(None)``"


any_or_none = Rule(None, optional=True)
"A shortcut for ``Rule(None, optional=True)"
