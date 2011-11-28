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
Data manipulation
=================
"""
from monk.helpers import walk_dict


def merged(spec, data):
    """ Returns a dictionary based on `spec` + `data`.

    Does not validate values. If `data` overrides a default value, it is
    trusted. The result can be validated later with
    :func:`~monk.validation.validate_structure`.

    :param spec:
        `dict`. A document structure specification.
    :param data:
        `dict`. Overrides some or all default values from the spec.
    """
    result = {}
    for key in set(spec.keys() + data.keys()):
        value = None
        if key in spec:
            if key in data:
                value = data[key]
            else:
                value = spec[key]
            # TODO: special handling of dict and list instances
            # ...
        else:
            # never mind if there are nested structures: anyway we cannot check
            # them as they aren't in the spec
            value = data[key]
        result[key] = value
    return result
