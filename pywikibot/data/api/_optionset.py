"""Object representing boolean API option."""
#
# (C) Pywikibot team, 2015-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from collections.abc import MutableMapping

import pywikibot
from pywikibot.tools import deprecate_arg


__all__ = ['OptionSet']


class OptionSet(MutableMapping):

    """A class to store a set of options which can be either enabled or not.

    If it is instantiated with the associated site, module and parameter
    it will only allow valid names as options. If instantiated 'lazy
    loaded' it won't checks if the names are valid until the site has
    been set (which isn't required, but recommended). The site can only
    be set once if it's not None and after setting it, any site (even
    None) will fail.
    """

    @deprecate_arg('dict', 'data')  # since 9.0
    def __init__(self,
                 site: pywikibot.site.APISite | None = None,
                 module: str | None = None,
                 param: str | None = None,
                 data: dict | None = None) -> None:
        """Initializer.

        If a site is given, the module and param must be given too.

        .. versionchanged:: 9.0
           *dict* parameter was renamed to *data*.

        :param site: The associated site
        :param module: The module name which is used by paraminfo. (Ignored
            when site is None)
        :param param: The parameter name inside the module. That parameter must
            have a 'type' entry. (Ignored when site is None)
        :param data: The initializing data dict which is used for
            :meth:`from_dict`
        """
        self._site_set = False
        self._enabled = set()
        self._disabled = set()
        self._set_site(site, module, param)
        if data:
            self.from_dict(data)

    def _set_site(self, site, module: str, param: str, *,
                  clear_invalid: bool = False) -> None:
        """Set the site and valid names.

        As soon as the site has been not None, any subsequent calls will
        fail, unless there had been invalid names and a KeyError was
        thrown.

        :param site: The associated site
        :type site: pywikibot.site.APISite
        :param module: The module name which is used by paraminfo.
        :param param: The parameter name inside the module. That
            parameter must have a 'type' entry.
        :param clear_invalid: Instead of throwing a KeyError, invalid
            names are silently removed from the options (disabled by
            default).
        """
        if self._site_set:
            raise TypeError('The site cannot be set multiple times.')
        # If the entries written to this are valid, it will never be
        # overwritten
        self._valid_enable = set()
        self._valid_disable = set()
        if site is None:
            return
        for type_value in site._paraminfo.parameter(module, param)['type']:
            if type_value[0] == '!':
                self._valid_disable.add(type_value[1:])
            else:
                self._valid_enable.add(type_value)
        if clear_invalid:
            self._enabled &= self._valid_enable
            self._disabled &= self._valid_disable
        else:
            invalid_names = ((self._enabled - self._valid_enable)
                             | (self._disabled - self._valid_disable))
            if invalid_names:
                raise KeyError('OptionSet already contains invalid name(s) '
                               '"{}"'.format('", "'.join(invalid_names)))
        self._site_set = True

    def from_dict(self, dictionary) -> None:
        """Load options from the dict.

        The options are not cleared before. If changes have been made
        previously, but only the dict values should be applied it needs
        to be cleared first.

        :param dictionary: a dictionary containing for each entry either
            the value False, True or None. The names must be valid
            depending on whether they enable or disable the option. All
            names with the value None can be in either of the list.
        :type dictionary: dict (keys are strings, values are bool/None)
        """
        enabled = set()
        disabled = set()
        removed = set()
        for name, value in dictionary.items():
            if value is True:
                enabled.add(name)
            elif value is False:
                disabled.add(name)
            elif value is None:
                removed.add(name)
            else:
                raise ValueError(f'Dict contains invalid value "{value}"')
        invalid_names = (
            (enabled - self._valid_enable) | (disabled - self._valid_disable)
            | (removed - self._valid_enable - self._valid_disable)
        )
        if invalid_names and self._site_set:
            raise ValueError('Dict contains invalid name(s) "{}"'.format(
                '", "'.join(invalid_names)))
        self._enabled = enabled | (self._enabled - disabled - removed)
        self._disabled = disabled | (self._disabled - enabled - removed)

    def __setitem__(self, name, value) -> None:
        """Set option to enabled, disabled or neither."""
        if value is True:
            if self._site_set and name not in self._valid_enable:
                raise KeyError(f'Invalid name "{name}"')
            self._enabled.add(name)
            self._disabled.discard(name)
        elif value is False:
            if self._site_set and name not in self._valid_disable:
                raise KeyError(f'Invalid name "{name}"')
            self._disabled.add(name)
            self._enabled.discard(name)
        elif value is None:
            if self._site_set and (name not in self._valid_enable
                                   or name not in self._valid_disable):
                raise KeyError(f'Invalid name "{name}"')
            self._enabled.discard(name)
            self._disabled.discard(name)
        else:
            raise ValueError(f'Invalid value "{value}"')

    def __getitem__(self, name) -> bool | None:
        """Return whether the option is enabled.

        :return: If the name has been set it returns whether it is
            enabled. Otherwise it returns None. If the site has been set
            it raises a KeyError if the name is invalid. Otherwise it
            might return a value even though the name might be invalid.
        """
        if name in self._enabled:
            return True
        if name in self._disabled:
            return False
        if (self._site_set or name in self._valid_enable
                or name in self._valid_disable):
            return None
        raise KeyError(f'Invalid name "{name}"')

    def __delitem__(self, name) -> None:
        """Remove the item by setting it to None."""
        self[name] = None

    def __iter__(self):
        """Iterate over each enabled and disabled option."""
        yield from self._enabled
        yield from self._disabled

    def api_iter(self):
        """Iterate over each option as they appear in the URL."""
        yield from self._enabled
        for disabled in self._disabled:
            yield f'!{disabled}'

    def __len__(self) -> int:
        """Return the number of enabled and disabled options."""
        return len(self._enabled) + len(self._disabled)
