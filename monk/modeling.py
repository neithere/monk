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
~~~~~~~~
Modeling
~~~~~~~~

DB-agnostic helpers to build powerful ODMs.

"""
from __future__ import unicode_literals

from .compat import text_type
from . import validate, merge_defaults


__all__ = ['DotExpandedDictMixin', 'DotExpandedDict', 'make_dot_expanded',
           'TypedDictReprMixin',
           'StructuredDictMixin']


def make_dot_expanded(data):
    if isinstance(data, DotExpandedDictMixin):
        return data
    elif isinstance(data, dict):
        pairs = []
        for key, value in data.items():
            pairs.append((key, make_dot_expanded(value)))
        return DotExpandedDict(pairs)
    elif isinstance(data, list):
        return [make_dot_expanded(x) for x in data]
    return data


class DotExpandedDictMixin(object):
    """ Makes the dictionary dot-expandable by exposing dictionary members
    via ``__getattr__`` and ``__setattr__`` in addition to ``__getitem__`` and
    ``__setitem__``. For example, this is the default API::

        data = {'foo': {'bar': 0 } }
        print data['foo']['bar']
        data['foo']['bar'] = 123

    This mixin adds the following API::

        print data.foo.bar
        data.foo.bar = 123

    Nested dictionaries are converted to dot-expanded ones on adding.
    """
    def _make_dot_expanded(self):
        for key, value in self.items():
            self[key] = make_dot_expanded(value)

    def __getattr__(self, attr):
        if not attr.startswith('_') and attr in self:
            return self[attr]
        raise AttributeError('Attribute or key {0.__class__.__name__}.{1} '
                             'does not exist'.format(self, attr))

    def __setattr__(self, attr, value):
        if not attr.startswith('_') and attr in self:
            self[attr] = value
        else:
            # Ambigous intent: cannot tell whether user wants to create
            # a dictionary key or actually set an object attribute.
            # Assuming the last option.
            super(DotExpandedDictMixin, self).__setattr__(attr, value)

    def __setitem__(self, key, value):
        if isinstance(value, dict) and not isinstance(value, DotExpandedDict):
            value = make_dot_expanded(value)
        super(DotExpandedDictMixin, self).__setitem__(key, value)


class DotExpandedDict(DotExpandedDictMixin, dict):
    def __init__(self, *args, **kwargs):
        super(DotExpandedDict, self).__init__(*args, **kwargs)
        self._make_dot_expanded()


class TypedDictReprMixin(object):
    """ Makes ``repr(self)`` depend on ``unicode(self)``.
    """
    def __repr__(self):
        return '<{0.__class__.__name__} {1}>'.format(self, text_type(self))

    def __unicode__(self):
        return text_type(dict(self))

    def __str__(self):
        return text_type(dict(self))


class StructuredDictMixin(object):
    """ A dictionary with structure specification and validation.

    .. attribute:: structure

        The document structure specification. For details see
        :func:`monk.shortcuts.validate`.

    """
    structure = {}
    #defaults = {}
    #required = []
    #validators = {}
    #with_skeleton = True

    def _insert_defaults(self):
        """ Inserts default values from :attr:`StructuredDictMixin.structure`
        to `self` by merging the two structures
        (see :func:`monk.manipulation.merge_defaults`).
        """
        merged = merge_defaults(self.structure, self)
        self.update(merged)

    def validate(self):
        validate(self.structure, self)
