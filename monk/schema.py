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


__all__ = ['Rule', 'canonize', 'optional']


class Rule:
    "Extended specification of a field.  Allows marking it as optional."
    def __init__(self, datatype, inner_spec=None, skip_missing=False, skip_unknown=False, default=None):
        self.datatype = datatype
        self.inner_spec = inner_spec
        self.skip_missing = skip_missing
        self.skip_unknown = skip_unknown
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


optional = lambda x: Rule(x, skip_missing=True)


def canonize(spec, rule_kwargs={}):
    """
    Returns the canonic representation of given natural spec.

    :param spec: :term:`natural spec` (a `dict`)

    :return: :term:`detailed spec` (`dict` with :class:`Rule` instances as values)
    """
    print('----- canonize(', spec, ')')
#    canonic = {}
#    for key, value in spec.items():
#        print(key, ':', value)
    value = spec

    if isinstance(value, Rule):
        print('  value is a Rule')
        rule = value
    elif value is None:
        print('  value is None')
        rule = Rule(None, **rule_kwargs)
    elif isinstance(value, type):
        print('  value is instance of type')
        rule = Rule(value, **rule_kwargs)
    elif type(value) in compat.func_types:
        print('  ', value, compat.func_types)
        print('  ', value, 'is callable')
        real_value = value()
        print('  real value: ', real_value, 'type', type(real_value))
        kwargs = dict(rule_kwargs, default=real_value)
        rule = Rule(type(real_value), **kwargs)
    elif type(value) in (dict, list):
        print('  inner spec:', value)
        kwargs = dict(rule_kwargs, inner_spec=value)
        print(value, kwargs)
        rule = Rule(type(value), **kwargs)
    else:
        print('  value is a type instance')
        kwargs = dict(rule_kwargs, default=value)
        rule = Rule(type(value), **kwargs)

    print('  ->', rule)
    print()
    #canonic[key] = rule
    #return canonic
    return rule


#def validates(spec):
#    canonic_spec = canonize(spec)

