"""Objects representing site info data contents."""
#
# (C) Pywikibot team, 2008-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import copy
import datetime
import re
from collections.abc import Container
from contextlib import suppress
from typing import TYPE_CHECKING, Any, Literal, cast

import pywikibot
from pywikibot.backports import Dict, List
from pywikibot.exceptions import APIError
from pywikibot.tools.collections import EMPTY_DEFAULT


if TYPE_CHECKING:
    from pywikibot.site import APISite


class Siteinfo(Container):

    """A dictionary-like container for siteinfo.

    This class queries the server to get the requested siteinfo
    property. Results can be cached in the instance to avoid repeated
    queries.

    All values of the 'general' property  are directly available.

    .. versionchanged:: 10.5
       formatversion 2 is used for API calls.

    .. admonition:: Compatibility note
       :class: note

       For formatversion 2, some siteinfo data structures differ from
       version 1. Fallback '*' keys are added in the data structure for
       'namespaces', 'languages', 'namespacealiases' and 'skins'
       properties for backwards compatibility. These fallbacks may be
       removed in future versions of Pywikibot.

       The 'thumblimits', 'imagelimits' and 'magiclinks' entries of the
       'general' property are normalized to lists for easier use and to
       match the format used in formatversion 1. For example:

       :code:`'thumblimits': [120, 150, 180, 200, 220, 250, 300, 400]`

    .. deprecated:: 10.5
       Accessing the fallback '*' keys in 'languages', 'namespaces',
       'namespacealiases', and 'skins' properties are deprecated and
       will be removed in a future release of Pywikibot.

    .. seealso:: :api:`siteinfo`
    """

    WARNING_REGEX = re.compile(r'Unrecognized values? for parameter '
                               r'["\']siprop["\']: (.+?)\.?')

    def __init__(self, site: APISite) -> None:
        """Initialize Siteinfo for a given site with an empty cache."""
        self._site = site
        self._cache: dict[str,
                          tuple[Any, datetime.datetime | Literal[False]]] = {}

    def clear(self) -> None:
        """Clear all cached siteinfo properties.

        .. versionadded:: 7.1
        """
        self._cache.clear()

    @staticmethod
    def _post_process(prop: str,
                      data: dict[str, Any] | list[dict[str, Any]]) -> None:
        """Convert empty-string boolean properties to actual booleans.

        Modifies *data* in place.

        .. versionchanged:: 10.5
           Modify *data* for formatversion 1 compatibility and easier
           to use lists.

        :param prop: The siteinfo property name (e.g., 'general',
            'namespaces', 'magicwords')
        :param data: The raw data returned from the server

        :meta public:
        """
        # Be careful with version tests inside this here as it might need to
        # query this method to actually get the version number

        if prop == 'general':
            data = cast(Dict[str, Any], data)
            for key in 'thumblimits', 'imagelimits':
                data[key] = list(data[key].values())
            data['magiclinks'] = [k for k, v in data['magiclinks'].items()
                                  if v]
        elif prop == 'namespaces':
            data = cast(Dict[str, Any], data)
            for ns_info in data.values():
                ns_info['*'] = ns_info['name']
        elif prop in ('languages', 'namespacealiases'):
            data = cast(List[Dict[str, Any]], data)
            for ns_info in data:
                key = 'name' if 'name' in ns_info else 'alias'
                ns_info['*'] = ns_info[key]
        elif prop == 'skins':
            data = cast(List[Dict[str, Any]], data)
            for ns_info in data:
                ns_info['*'] = ns_info['name']
                for key in 'default', 'unusable':
                    ns_info.setdefault(key, False)

    def _get_siteinfo(self, prop, expiry) -> dict:
        """Retrieve one or more siteinfo properties from the server.

        .. seealso:: :api:Siteinfo

        :param prop: The property names of the siteinfo.
        :type prop: str or iterable
        :param expiry: The expiry date of the cached request.
        :type expiry: int (days), :py:obj:`datetime.timedelta`, False (config)
        :return: A dictionary with the properties of the site. Each entry in
            the dictionary is a tuple of the value and a boolean to save if it
            is the default value.
        """
        invalid_properties: list[str] = []

        def warn_handler(mod, message) -> bool:
            """Return True if the warning is handled."""
            matched = Siteinfo.WARNING_REGEX.fullmatch(message)
            if mod == 'siteinfo' and matched:
                invalid_properties.extend(
                    prop.strip() for prop in matched[1].split(','))
                return True
            return False

        # Convert to list for consistent iteration
        props = [prop] if isinstance(prop, str) else list(prop)
        if not props:
            raise ValueError('At least one property name must be provided.')

        request = self._site._request(
            expiry=pywikibot.config.API_config_expiry
            if expiry is False else expiry,
            parameters={
                'action': 'query',
                'meta': 'siteinfo',
                'siprop': props,
                'formatversion': 2,
            }
        )

        # warnings are handled later
        request._warning_handler = warn_handler

        try:
            data = request.submit()
        except APIError as e:
            if e.code == 'siunknown_siprop':
                if len(props) == 1:
                    pywikibot.log(f"Unable to get siprop '{props[0]}'")
                    return {props[0]: (EMPTY_DEFAULT, False)}

                pywikibot.log('Unable to get siteinfo, because at least '
                              "one property is unknown: '{}'"
                              .format("', '".join(props)))
                results = {}
                for p in props:
                    results.update(self._get_siteinfo(p, expiry))
                return results
            raise

        result: dict[str, tuple[Any, datetime.datetime | Literal[False]]] = {}
        if invalid_properties:
            for invalid_prop in invalid_properties:
                result[invalid_prop] = (EMPTY_DEFAULT, False)
            pywikibot.log("Unable to get siprop(s) '{}'"
                          .format("', '".join(invalid_properties)))

        # Process valid properties
        if 'query' in data:
            # If the request is a CachedRequest, use the _cachetime attr.
            cache_time = getattr(
                request, '_cachetime', None) or pywikibot.Timestamp.nowutc()
            for prop in props:
                if prop in data['query']:
                    self._post_process(prop, data['query'][prop])
                    result[prop] = (data['query'][prop], cache_time)
        return result

    @staticmethod
    def _is_expired(cache_date: datetime.datetime | Literal[False] | None,
                    expire: datetime.timedelta | Literal[False]) -> bool:
        """Return true if the cache date is expired.

        :param cache_date: The timestamp when the value was cached, or
            False if default, None if never.
        :param expire: Expiry period as timedelta, or False to never
            expire.
        :return: True if expired, False otherwise.
        """
        if isinstance(expire, bool):
            return expire

        if not cache_date:  # default values are always expired
            return True

        # cached date + expiry are in the past if it's expired
        return cache_date + expire < pywikibot.Timestamp.nowutc()

    def _get_general(self, key: str, expiry):
        """Return a siteinfo property which is loaded by default.

        The property 'general' will be queried if it wasn't yet or it's forced.
        Additionally all uncached default properties are queried. This way
        multiple default properties are queried with one request. It'll cache
        always all results.

        :param key: The key to search for.
        :param expiry: If the cache is older than the expiry it ignores the
            cache and queries the server to get the newest value.
        :type expiry: int (days), :py:obj:`datetime.timedelta`, False (never)
        :return: If that property was retrieved via this method. Returns None
            if the key was not in the retrieved values.
        :rtype: various (the value), bool (if the default value is used)
        """
        if 'general' not in self._cache:
            pywikibot.debug('general siteinfo not loaded yet.')
            force = True
            props = ['namespaces', 'namespacealiases']
        else:
            force = Siteinfo._is_expired(self._cache['general'][1], expiry)
            props = []
        if force:
            props = [prop for prop in props if prop not in self._cache]
            if props:
                pywikibot.debug(
                    "Load siteinfo properties '{}' along with 'general'"
                    .format("', '".join(props)))
            props.append('general')
            default_info = self._get_siteinfo(props, expiry)
            for prop in props:
                self._cache[prop] = default_info[prop]
            if key in default_info:
                return default_info[key]

        if key in self._cache['general'][0]:
            return self._cache['general'][0][key], self._cache['general']

        return None

    def __getitem__(self, key: str):
        """Return a siteinfo property, caching and not forcing it."""
        return self.get(key, False)  # caches and doesn't force it

    def get(
        self,
        key: str,
        get_default: bool = True,
        cache: bool = True,
        expiry: datetime.datetime | float | bool = False
    ) -> Any:
        """Return a siteinfo property.

        It will never throw an APIError if it only stated, that the siteinfo
        property doesn't exist. Instead it will use the default value.

        .. seealso:: :py:obj:`_get_siteinfo`

        :param key: The name of the siteinfo property.
        :param get_default: Whether to throw an KeyError if the key is invalid.
        :param cache: Caches the result internally so that future accesses via
            this method won't query the server.
        :param expiry: If the cache is older than the expiry it ignores the
            cache and queries the server to get the newest value.
        :return: The gathered property
        :raises KeyError: If the key is not a valid siteinfo property and the
            get_default option is set to False.
        """
        # If expiry is True, convert it to 0 to be coherent with
        # _get_siteinfo() and _get_general() docstring.
        if expiry is True:
            expiry = 0
        # If expiry is a float or int convert to timedelta
        # Note: bool is an instance of int
        if isinstance(expiry, float) or type(expiry) is int:
            expiry = datetime.timedelta(expiry)

        # expire = 0 (or timedelta(0)) are always expired and their bool is
        # False, so skip them EXCEPT if it's literally False, then they expire
        # never.
        if expiry and expiry is not True or expiry is False:
            try:
                cached = self._get_cached(key)
            except KeyError:
                pass
            else:  # cached value available
                # is a default value, but isn't accepted
                if not cached[1] and not get_default:
                    raise KeyError(key)
                if not Siteinfo._is_expired(cached[1], expiry):
                    return copy.deepcopy(cached[0])

        preloaded = self._get_general(key, expiry)
        if not preloaded:
            preloaded = self._get_siteinfo(key, expiry)[key]
        else:
            cache = False

        if not preloaded[1] and not get_default:
            raise KeyError(key)

        if cache:
            self._cache[key] = preloaded

        return copy.deepcopy(preloaded[0])

    def _get_cached(self, key: str):
        """Return the cached value or a KeyError exception if not cached."""
        if 'general' in self._cache:
            if key in self._cache['general'][0]:
                return (self._cache['general'][0][key],
                        self._cache['general'][1])
            return self._cache[key]
        raise KeyError(key)

    def is_cached(self, key: str) -> bool:
        """Return whether the value is cached.

        .. versionadded:: 7.1
        """
        try:
            self._get_cached(key)
        except KeyError:
            return False

        return True

    def __contains__(self, key: object) -> bool:
        """Check whether the given key is present in the Siteinfo container.

        This method implements the Container protocol and allows usage
        like `key in container`.Only string keys are valid. Non-string
        keys always return False.

        .. versionchanged:: 7.1
           Previous implementation only checked for cached keys.

        :param key: The key to check for presence. Should be a string.
        :return: True if the key exists in the container, False otherwise.

        :meta public:
        """
        if isinstance(key, str):
            with suppress(KeyError):
                self[key]
                return True

        return False

    def is_recognised(self, key: str) -> bool | None:
        """Return if 'key' is a valid property name.

        'None' if not cached.
        """
        time = self.get_requested_time(key)
        return None if time is None else bool(time)

    def get_requested_time(self, key: str):
        """Return when 'key' was successfully requested from the server.

        If the property is actually in the siprop 'general' it returns the
        last request from the 'general' siprop.

        :param key: The siprop value or a property of 'general'.
        :return: The last time the siprop of 'key' was requested.
        :rtype: None (never), False (default),
            :py:obj:`datetime.datetime` (cached)
        """
        with suppress(KeyError):
            return self._get_cached(key)[1]

        return None
