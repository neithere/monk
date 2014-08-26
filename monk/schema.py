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
Schema Definition
~~~~~~~~~~~~~~~~~
"""
from . import compat, errors, validators


__all__ = [
    'Rule', 'OneOf', 'canonize',
    # shortcuts:
    'any_value', 'any_or_none', 'optional', 'in_range', 'one_of'
]


#-------------------------------------------
# Classes
#


class BaseSchemaNode:
    # if NotImplemented is encountered, data type should not be checked
    datatype = NotImplemented
    optional = False


class Rule(BaseSchemaNode):
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
        ``bool``; if ``True``, :class:`~monk.validation.MissingValue`
        is never raised.  Default is ``False``.

    :param validators:
        a list of callables.

    .. note:: Missing Value vs. Missing Key vs. Unknown Key

       :MissingValue:
            Applies: to any value on any level.

            Trigger: the value is `None` and the rule neither allows this
            (i.e. a `datatype` is defined) nor provides a `default` value.

            Suppress: turn the `optional` setting on.
            This allows the value to be `None` even if a `datatype` is defined.

       :MissingKey:
            Applies: to a dictionary key.

            Trigger: a key is missing from the dictionary.

            Suppress: turn the `optional` setting on.
            This allows the key to be completely missing from an outer dictionary.

       :UnknownKey:
            Applies: to a dictionary key.

            Trigger: the dictionary contains a key which is not in
            the dictionary's `inner_spec`.

    """
    def __init__(self, datatype, inner_spec=None, optional=False,
                 default=None, validators=None):
        if isinstance(datatype, type(self)):
            raise ValueError('Cannot use a Rule instance as datatype')
        self.datatype = datatype
        self.inner_spec = inner_spec
        self.optional = optional
        self.default = default
        self.validators = validators or []

        # sanity checks

        if default is not None and self.datatype and not isinstance(default, self.datatype):
            raise TypeError('Default value must match datatype {0} (got {1})'.format(
                self.datatype.__name__, default))

#        if self.inner_spec and not isinstance(self.inner_spec, self.datatype):
#            raise TypeError('Inner spec must match datatype {0} (got {1})'.format(
#                self.datatype.__name__, inner_spec))

    def __hash__(self):
        # TODO think this over and check Python docs
        #return hash(((k,v) for k,v in self.__dict__.items()))
        return hash('rule_'+str(self.datatype))

    def __repr__(self):
        flags = []
        flags.append('any' if self.datatype is None else self.datatype.__name__)
        flags.append('optional' if self.optional else 'required')
        if self.default is not None:
            flags.append('default={0}'.format(self.default))
        if self.inner_spec is not None:
            flags.append('inner_spec={0}'.format(self.inner_spec))

        return '<Rule {flags}>'.format(flags=' '.join(flags))

    def __eq__(self, other):
        if (isinstance(other, type(self)) and self.__dict__ == other.__dict__):
            return True


class OneOf(BaseSchemaNode):
    """
    A special kind of schema node along with :class:`Rule`.  Represents a set
    of alternative rules which can be applied at given place.  A typical use
    case is when significant variations are accepted for a document field but
    it is hard or impossible to describe them with validators.

    Example::

        {
            'foo': OneOf([
                int,
                float,
                Rule(str, validators=[can_be_coerced_to_int]),
            ]),
        }

    """
    def __init__(self, choices, first_is_default=False):
        assert choices
        self.choices = choices
        self.first_is_default = first_is_default

    def __repr__(self):
        flags = []
        if self.first_is_default:
            flags.append('first-is-default')
        return '<OneOf {choices!r} {flags}>'.format(
            choices=self.choices, flags=' '.join(flags))

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
    elif isinstance(value, OneOf):
        rule = value
    elif value is None:
        rule = Rule(None, **rule_kwargs)
    elif isinstance(value, type):
        rule = Rule(value, **rule_kwargs)
    elif type(value) in compat.func_types:
        real_value = value()
        kwargs = dict(rule_kwargs, default=real_value)
        rule = Rule(datatype=type(real_value), **kwargs)
    elif isinstance(value, list):
        if value == []:
            # no inner spec, just an empty list as the default value
            kwargs = dict(rule_kwargs, default=value)
            rule = Rule(datatype=list, **kwargs)
        elif len(value) == 1:
            # the only item as spec for each item of the collection
            kwargs = dict(rule_kwargs, inner_spec=value[0])
            rule = Rule(datatype=list, **kwargs)
        else:
            raise errors.StructureSpecificationError(
                'Expected a list containing exactly 1 item; '
                'got {cnt}: {spec}'.format(cnt=len(value), spec=value))
    elif isinstance(value, dict):
        kwargs = dict(rule_kwargs, inner_spec=value)
        rule = Rule(datatype=dict, **kwargs)
    else:
        kwargs = dict(rule_kwargs, default=value)
        rule = Rule(datatype=type(value), **kwargs)

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
    if isinstance(spec, BaseSchemaNode):
        spec.optional = True
        return spec
    else:
        return canonize(spec, rule_kwargs={'optional': True})


any_value = Rule(None)
"A shortcut for ``Rule(None)``"


any_or_none = Rule(None, optional=True)
"A shortcut for ``Rule(None, optional=True)``"


def one_of(choices, first_is_default=False, as_rules=False):
    """
    A shortcut for either a :class:`OneOf` instance or a rule with
    :func:`~monk.validators.validate_choice` validator.

    Alternative rules::

        # given the two rules (in pythonic notation):

        rules = ['foo', 123]

        # these expressions are equal:

        one_of(rules, as_rules=True)
        OneOf(rules)

        # first_is_default propagates, so these are equal again:

        one_of(rules, first_is_default=True, as_rules=True)
        OneOf(rules, first_is_default=True)

    A rule with a choice validator::

        # given the two literals:

        choices = ['foo', 'bar']

        # these expressions are equal:

        one_of(choices)

        Rule(str, validators=[monk.validators.validate_choice(choices)])

        # default value can be taken from the first choice:

        one_of(choices, first_is_default=True)

        Rule(str, default=choices[0],
             validators=[monk.validators.choice(choices)])

    :param choices:
        a list of choices (literals by default; see `as_rules`).
    :param as_rules:
        `bool`, default is `True`.  If `False`, the `choices` are interpreted
        as rules instead of literals and the result would be a :class:`OneOf`
        instance instead of .  In this case a list of `['foo', 'bar']`
        is considered a "pythonic" schema which should be canonized, so `'foo'`
        becomes a :class:`Rule` with datatype being `str` and default value
        being `'foo'`.  However, that specific schema is invalid (the list
        must contain only one item), so an error would be raised.
    :param first_is_default:
        use the first choice to define the default value
        (for :func:`monk.manipulation.merge_defaults`).

    """
    assert choices

    if as_rules:
        return OneOf(choices, first_is_default=first_is_default)

    if first_is_default:
        default_choice = choices[0]
    else:
        default_choice = None

    return Rule(datatype=type(choices[0]),
                default=default_choice,
                validators=[validators.validate_choice(choices)])


def in_range(start, stop, first_is_default=False):
    """
    A shortcut for a rule with :func:`~monk.validators.validate_range` validator.
    ::

        # these expressions are equal:

        in_range(0, 200)

        Rule(int, validators=[monk.validators.validate_range(0, 200)])

        # default value can be taken from the first choice:

        in_range(0, 200, first_is_default=True)

        Rule(int, default=0,
             validators=[monk.validators.validate_range(0, 200)])

    """
    if first_is_default:
        default_value = start
    else:
        default_value = None

    return Rule(datatype=int,
                default=default_value,
                validators=[validators.validate_range(start, stop)])
