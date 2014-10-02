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
~~~~~~~~~
Shortcuts
~~~~~~~~~
"""
from .compat import text_types
from . import Any, Equals, NotExists, InRange, translate


__all__ = ['nullable', 'optional', 'opt_key', 'one_of']


def nullable(spec):
    """
    Returns a validator which allows the value to be `None`.
    ::

        >>> nullable(str) == IsA(str) | Equals(None)
        True

    """
    return translate(spec) | Equals(None)


def optional(spec):
    """
    Returns a validator which allows the value to be missing.

    ::

        >>> optional(str) == IsA(str) | NotExists()
        True
        >>> optional('foo') == IsA(str, default='foo') | NotExists()
        True

    Note that you should normally :func:`opt_key` to mark dictionary keys
    as optional.
    """
    return translate(spec) | NotExists()


def opt_key(spec):
    """
    Returns a validator which allows the value to be missing.
    Similar to :func:`optional` but wraps a string in
    :class:`~monk.validators.Equals` instead of :class:`~monk.validators.IsA`.
    Intended for dictionary keys.

    ::

        >>> opt_key(str) == IsA(str) | NotExists()
        True
        >>> opt_key('foo') == Equals('foo') | NotExists()
        True

    """
    if isinstance(spec, text_types):
        spec = Equals(spec)
    return optional(spec)


def one_of(choices, first_is_default=False, as_rules=False):
    """
    A wrapper for :class:`Any`.

    :param as_rules:
        `bool`.  If `False` (by default), each element of `choices`
        is wrapped in the :class:`Equals` validator so they are interpreted
        as literals.

    .. deprecated:: 0.13

       Use :class:`Any` instead.

    """
    assert choices

    if as_rules:
        None    # for coverage
    else:
        choices = [Equals(x) for x in choices]

    return Any(choices, first_is_default=first_is_default)


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

    .. deprecated:: 0.13

       Use :class:`InRange` instead.

    """
    if first_is_default:
        default_value = start
    else:
        default_value = None

    return InRange(start, stop, default=default_value)
