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
~~~~~~~~~~~~~
Compatibility
~~~~~~~~~~~~~

This module is intended to hide away implementation details of various Python
versions.
"""
import sys
import types


func_types = (
    types.FunctionType,
    types.MethodType,
    # CPython: datetime.datetime.[utc]now()
    types.BuiltinFunctionType,
)


if sys.version_info < (3,0):
    text_types = unicode, str
    text_type = unicode
    binary_type = str
else:
    text_types = str,
    text_type = str
    binary_type = bytes


def safe_str(value):
    """ Returns:

    * a `str` instance (bytes) in Python 2.x, or
    * a `str` instance (Unicode) in Python 3.x.

    """
    if sys.version_info < (3,0) and isinstance(value, unicode):
        return value.encode('utf-8')
    else:
        return str(value)


def safe_unicode(value):
    """ Returns:

    * a `unicode` instance in Python 2.x, or
    * a `str` instance in Python 3.x.

    """
    if sys.version_info < (3,0):
        if isinstance(value, str):
            return value.decode('utf-8')
        else:
            return unicode(value)
    else:
        return str(value)
