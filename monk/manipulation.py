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
def merged(spec, data, value_processor=lambda x:x):
    """ Returns a dictionary based on `spec` + `data`.

    Does not validate values. If `data` overrides a default value, it is
    trusted. The result can be validated later with
    :func:`~monk.validation.validate_structure`.

    Note that a key/value pair is added from `spec` either if `data` does not
    define this key at all, or if the value is ``None``. This behaviour may not
    be suitable for all cases and therefore may change in the future.

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
                if data[key] is None:
                    value = spec[key]
                else:
                    value = data[key]
            else:
                value = spec[key]

            # special handling of dict and list instances
            if (spec[key] == dict or isinstance(spec[key], dict)) and isinstance(value, dict):
                # nested dictionary
                value = merged(spec.get(key, {}), value)
            if (spec[key] == list or isinstance(spec[key], list)) and isinstance(value, list):
                # nested list
                item_spec = spec[key][0] if spec[key] else None
                if isinstance(item_spec, type):
                    value = []
                elif isinstance(item_spec, dict):
                    # list of dictionaries
                    # FIXME `value` was prematurely merged, refactor this
                    value = data.get(key, [])
                    value = [merged(item_spec, item) for item in value]
                elif item_spec == None:
                    # any value is accepted as list item
                    pass
                else:
                    # probably default list item like [1]
                    pass
            else:
                # some value from spec that can be checked for type
                pass
        else:
            # never mind if there are nested structures: anyway we cannot check
            # them as they aren't in the spec
            value = data[key]

        if isinstance(value, type):
            # there's no default value for this key, just a restriction on type
            value = None

        # call additional value processor, if any
        #
        # TODO: move most of logic above to such pluggable processors
        #       because similar logic is also used in validation
        value = value_processor(value)

        result[key] = value

    return result
