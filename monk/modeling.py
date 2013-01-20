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
Modeling
~~~~~~~~

DB-agnostic helpers to build powerful ODMs.

"""
from __future__ import unicode_literals
from functools import partial

from monk import manipulation
from monk import validation


__all__ = ['DotExpandedDictMixin', 'DotExpandedDict', 'make_dot_expanded',
           'TypedDictReprMixin',
           'StructuredDictMixin',
           'Document']


def make_dot_expanded(data):
    if isinstance(data, DotExpandedDictMixin):
        return data
    elif isinstance(data, dict):
        pairs = []
        for key, value in data.iteritems():
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
        for key, value in self.iteritems():
            self[key] = make_dot_expanded(value)

    def __getattr__(self, attr):
        if not attr.startswith('_') and attr in self:
            return self[attr]
        raise AttributeError('Attribute or key {0.__class__.__name__}.{1} '
                             'does not exist'.format(self, attr))

    def __setattr__(self, attr, value):
        if not attr.startswith('_') and attr in self:
            self[attr] = value

    def __setitem__(self, key, value):
        if isinstance(value, dict) and \
           not isinstance(value, DotExpandedDict):
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
        return '<{0.__class__.__name__} {1}>'.format(self, unicode(self))

    def __unicode__(self):
        return unicode(dict(self))


class StructuredDictMixin(object):
    """ A dictionary with structure specification and validation.

    .. attribute:: structure

        The document structure specification. For details see
        :func:`monk.validation.validate_structure_spec` and
        :func:`monk.validation.validate_structure`.

    """
    structure = {}
    #defaults = {}
    #required = []
    #validators = {}
    #with_skeleton = True

    def _insert_defaults(self):
        """ Inserts default values from :attr:`StructuredDictMixin.structure`
        to `self` by merging the two structures
        (see :func:`monk.manipulation.merged`).
        """
        with_defaults = manipulation.merged(self.structure, self)

        for key, value in with_defaults.iteritems():
            self[key] = value

    def _validate_structure_spec(self):
        validation.validate_structure_spec(self.structure)

    def validate(self):
        validation.validate_structure(self.structure, self)


def Document(*args, **kwargs):
    import warnings
    warnings.warn('monk.modeling.Document is deprecated, use '
                  'monk.mongo.Document instead', DeprecationWarning)
    import monk.mongo
    return monk.mongo.Document(*args, **kwargs)
