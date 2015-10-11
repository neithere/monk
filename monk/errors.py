# coding: utf-8
#
#    Monk is an unobtrusive data modeling, manipulation and validation library.
#    Copyright © 2011—2015  Andrey Mikhaylenko
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
~~~~~~~~~~
Exceptions
~~~~~~~~~~
"""
class ValidationError(Exception):
    """
    Raised when a document or its part cannot pass validation.
    """


class StructureSpecificationError(ValidationError):
    """
    Raised when malformed document structure is detected.
    """


class DictValueError(ValidationError):
    """
    Raised when dictionary value fails validation.  Used to detect nested
    errors in order to format the human-readable messages unambiguously.
    """


class MissingKeys(ValidationError):
    """
    Raised when a required dictionary key is missing from the value dict.
    """
    def __str__(self):
        keys_str = ', '.join(map(repr, self.args))
        return 'must have keys: {keys}'.format(keys=keys_str)


class InvalidKeys(ValidationError):
    """
    Raised whan the value dictionary contains an unexpected key.
    """
    def __str__(self):
        keys_str = ', '.join(map(repr, self.args))
        return 'must not have keys like {keys}'.format(keys=keys_str)


class CombinedValidationError(ValidationError):
    """
    Raised when a combination of specs has failed validation.
    """
    _error_string_separator = '; '

    def _format_nested_error(self, e):
        # only display error class if it's not obvious
        if isinstance(e, str):
            tmpl = '{err}'
        elif isinstance(e, ValidationError):
            tmpl = '{err}'
        else:
            tmpl = '{cls}: {err}'
        return tmpl.format(cls=e.__class__.__name__, err=e)

    def __str__(self):
        err_strings = map(self._format_nested_error, self.args)
        return self._error_string_separator.join(err_strings)


class AllFailed(CombinedValidationError):
    """
    Raised when at least one validator was expected to pass but none did.
    """
    _error_string_separator = ' or '


class AtLeastOneFailed(CombinedValidationError):
    """
    Raised when all validators were expected to pas but at least one didn't.
    """
    _error_string_separator = ' and '


class NoDefaultValue(Exception):
    """
    Raised when the validator could not produce a default value.
    """
