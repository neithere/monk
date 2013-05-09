# coding: utf-8
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
Exceptions
~~~~~~~~~~
"""
class ValidationError(Exception):
    "Raised when a document or its part cannot pass validation."


class StructureSpecificationError(ValidationError):
    "Raised when malformed document structure is detected."


class MissingValue(ValidationError):
    """ Raised when the value is `None` and the rule neither allows this
    (i.e. a `datatype` is defined) nor provides a `default` value.
    """


class MissingKey(ValidationError):
    """ Raised when a dictionary key is defined in :attr:`Rule.inner_spec`
    but is missing from the value.
    """


class UnknownKey(ValidationError):
    """ Raised whan the value dictionary contains a key which is not
    in the dictionary's :attr:`Rule.inner_spec`.
    """
