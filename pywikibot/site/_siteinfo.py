"""Objects representing site info data contents."""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import copy
import datetime
import re
from collections.abc import Container
from contextlib import suppress
from typing import Any, Optional, Union

import pywikibot
from pywikibot.exceptions import APIError
from pywikibot.tools.collections import EMPTY_DEFAULT


class Siteinfo(Container):

    """
    A 'dictionary' like container for siteinfo.

    This class queries the server to get the requested siteinfo property.
    Optionally it can cache this directly in the instance so that later
    requests don't need to query the server.

    All values of the siteinfo property 'general' are directly available.
    """

    WARNING_REGEX = re.compile(r'Unrecognized values? for parameter '
                               r'["\']siprop["\']: (.+?)\.?$')

    # Until we get formatversion=2, we have to convert empty-string properties
    # into booleans so they are easier to use.
    BOOLEAN_PROPS = {
        'general': [
            'imagewhitelistenabled',
            'langconversion',
            'titleconversion',
            'rtl',
            'readonly',
            'writeapi',
            'variantarticlepath',
            'misermode',
            'uploadsenabled',
        ],
        'namespaces': [  # for each namespace
            'subpages',
            'content',
            'nonincludable',
        ],
        'magicwords': [  # for each magicword
            'case-sensitive',
        ],
    }

    def __init__(self, site) -> None:
        """Initialise it with an empty cache."""
        self._site = site
        self._cache = {}

    def clear(self) -> None:
        """Remove all items from Siteinfo.

        .. versionadded: 7.1
        """
        self._cache.clear()

    @staticmethod
    def _get_default(key: str):
        """
        Return the default value for different properties.

        If the property is 'restrictions' it returns a dictionary with:
         - 'cascadinglevels': 'sysop'
         - 'semiprotectedlevels': 'autoconfirmed'
         - 'levels': '' (everybody), 'autoconfirmed', 'sysop'
         - 'types': 'create', 'edit', 'move', 'upload'
        Otherwise it returns :py:obj:`tools.EMPTY_DEFAULT`.

        :param key: The property name
        :return: The default value
        :rtype: dict or :py:obj:`tools.EmptyDefault`
        """
        if key == 'restrictions':
            # implemented in b73b5883d486db0e9278ef16733551f28d9e096d
            return {
                'cascadinglevels': ['sysop'],
                'semiprotectedlevels': ['autoconfirmed'],
                'levels': ['', 'autoconfirmed', 'sysop'],
                'types': ['create', 'edit', 'move', 'upload']
            }

        if key == 'fileextensions':
            # the default file extensions in MediaWiki
            return [{'ext': ext} for ext in ['png', 'gif', 'jpg', 'jpeg']]

        return EMPTY_DEFAULT

    @staticmethod
    def _post_process(prop, data) -> None:
        """Do some default handling of data. Directly modifies data."""
        # Be careful with version tests inside this here as it might need to
        # query this method to actually get the version number

        # Convert boolean props from empty strings to actual boolean values
        if prop in Siteinfo.BOOLEAN_PROPS:
            # siprop=namespaces and
            # magicwords has properties per item in result
            if prop in ('namespaces', 'magicwords'):
                for index, value in enumerate(data):
                    # namespaces uses a dict, while magicwords uses a list
                    key = index if type(data) is list else value
                    for p in Siteinfo.BOOLEAN_PROPS[prop]:
                        data[key][p] = p in data[key]
            else:
                for p in Siteinfo.BOOLEAN_PROPS[prop]:
                    data[p] = p in data

    def _get_siteinfo(self, prop, expiry) -> dict:
        """
        Retrieve a siteinfo property.

        All properties which the site doesn't
        support contain the default value. Because pre-1.12 no data was
        returned when a property doesn't exists, it queries each property
        independetly if a property is invalid.

        .. seealso:: :api:Siteinfo

        :param prop: The property names of the siteinfo.
        :type prop: str or iterable
        :param expiry: The expiry date of the cached request.
        :type expiry: int (days), :py:obj:`datetime.timedelta`, False (config)
        :return: A dictionary with the properties of the site. Each entry in
            the dictionary is a tuple of the value and a boolean to save if it
            is the default value.
        """
        def warn_handler(mod, message) -> bool:
            """Return True if the warning is handled."""
            matched = Siteinfo.WARNING_REGEX.match(message)
            if mod == 'siteinfo' and matched:
                invalid_properties.extend(
                    prop.strip() for prop in matched.group(1).split(','))
                return True
            return False

        props = [prop] if isinstance(prop, str) else prop
        if not props:
            raise ValueError('At least one property name must be provided.')

        invalid_properties = []
        request = self._site._request(
            expiry=pywikibot.config.API_config_expiry
            if expiry is False else expiry,
            parameters={
                'action': 'query', 'meta': 'siteinfo', 'siprop': props,
            }
        )
        # With 1.25wmf5 it'll require continue or rawcontinue. As we don't
        # continue anyway we just always use continue.
        request['continue'] = True
        # warnings are handled later
        request._warning_handler = warn_handler
        try:
            data = request.submit()
        except APIError as e:
            if e.code == 'siunknown_siprop':
                if len(props) == 1:
                    pywikibot.log(
                        "Unable to get siprop '{}'".format(props[0]))
                    return {props[0]: (Siteinfo._get_default(props[0]), False)}
                pywikibot.log('Unable to get siteinfo, because at least '
                              "one property is unknown: '{}'".format(
                                  "', '".join(props)))
                results = {}
                for prop in props:
                    results.update(self._get_siteinfo(prop, expiry))
                return results
            raise
        else:
            result = {}
            if invalid_properties:
                for prop in invalid_properties:
                    result[prop] = (Siteinfo._get_default(prop), False)
                pywikibot.log("Unable to get siprop(s) '{}'".format(
                    "', '".join(invalid_properties)))
            if 'query' in data:
                # If the request is a CachedRequest, use the _cachetime attr.
                cache_time = getattr(
                    request, '_cachetime', None) or datetime.datetime.utcnow()
                for prop in props:
                    if prop in data['query']:
                        self._post_process(prop, data['query'][prop])
                        result[prop] = (data['query'][prop], cache_time)
            return result

    @staticmethod
    def _is_expired(cache_date, expire):
        """Return true if the cache date is expired."""
        if isinstance(expire, bool):
            return expire

        if not cache_date:  # default values are always expired
            return True

        # cached date + expiry are in the past if it's expired
        return cache_date + expire < datetime.datetime.utcnow()

    def _get_general(self, key: str, expiry):
        """
        Return a siteinfo property which is loaded by default.

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
            props += ['general']
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
        expiry: Union[datetime.datetime, float, bool] = False
    ) -> Any:
        """
        Return a siteinfo property.

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
        else:
            return True

    def __contains__(self, key: str) -> bool:
        """Return whether the value is in Siteinfo container.

        .. versionchanged:: 7.1
           Previous implementation only checked for cached keys.
        """
        try:
            self[key]
        except KeyError:
            return False
        else:
            return True

    def is_recognised(self, key: str) -> Optional[bool]:
        """Return if 'key' is a valid property name. 'None' if not cached."""
        time = self.get_requested_time(key)
        return None if time is None else bool(time)

    def get_requested_time(self, key: str):
        """
        Return when 'key' was successfully requested from the server.

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
