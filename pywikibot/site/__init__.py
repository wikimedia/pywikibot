# -*- coding: utf-8 -*-
"""
Objects representing MediaWiki sites (wikis).

This module also includes functions to load families, which are
groups of wikis on the same topic in different languages.
"""
#
# (C) Pywikibot team, 2008-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import copy
import datetime
import functools
import heapq
import itertools
import json
import mimetypes
import os
import re
from textwrap import fill
import threading
import time
import uuid

try:
    from collections.abc import Iterable, Container, Mapping
except ImportError:  # Python 2.7
    from collections import Iterable, Container, Mapping
from collections import defaultdict, namedtuple
from enum import IntEnum
from warnings import warn

import pywikibot
import pywikibot.family

from pywikibot.comms.http import get_authentication
from pywikibot.data import api
from pywikibot.echo import Notification
from pywikibot.exceptions import (
    ArticleExistsConflict,
    CaptchaError,
    CascadeLockedPage,
    CircularRedirect,
    EditConflict,
    EntityTypeUnknownException,
    Error,
    FamilyMaintenanceWarning,
    InconsistentTitleReceived,
    InterwikiRedirectPage,
    IsNotRedirectPage,
    LockedNoPage,
    LockedPage,
    NoCreateError,
    NoPage,
    NoUsername,
    NoWikibaseEntity,
    PageCreatedConflict,
    PageDeletedConflict,
    PageRelatedError,
    PageSaveRelatedError,
    SiteDefinitionError,
    SpamblacklistError,
    TitleblacklistError,
    UnknownExtension,
    UnknownSite,
    UserBlocked,
    UserRightsError,
)
from pywikibot.throttle import Throttle
from pywikibot.tools import (
    compute_file_hash,
    itergroup, UnicodeMixin, ComparableMixin, SelfCallMixin, SelfCallString,
    deprecated, deprecate_arg, deprecated_args, remove_last_args,
    redirect_func, issue_deprecation_warning,
    manage_wrapping, MediaWikiVersion, first_upper, normalize_username,
    merge_unique_dicts,
    PY2,
    filter_unique,
    UnicodeType
)
from pywikibot.tools import is_IP

if not PY2:
    from itertools import zip_longest
    from urllib.parse import urlencode, urlparse
else:
    from future_builtins import zip
    from itertools import izip_longest as zip_longest
    from urllib import urlencode
    from urlparse import urlparse


_logger = 'wiki.site'


class PageInUse(pywikibot.Error):

    """Page cannot be reserved for writing due to existing lock."""


class LoginStatus(IntEnum):

    """
    Enum for Login statuses.

    >>> LoginStatus.NOT_ATTEMPTED
    LoginStatus(-3)
    >>> LoginStatus.IN_PROGRESS.value
    -2
    >>> LoginStatus.NOT_LOGGED_IN.name
    NOT_LOGGED_IN
    >>> int(LoginStatus.AS_USER)
    0
    >>> LoginStatus(-3).name
    'NOT_ATTEMPTED'
    >>> LoginStatus(0).name
    'AS_USER'
    """

    NOT_ATTEMPTED = -3
    IN_PROGRESS = -2
    NOT_LOGGED_IN = -1
    AS_USER = 0

    def __repr__(self):
        """Return internal representation."""
        return 'LoginStatus({})'.format(self)


Family = redirect_func(pywikibot.family.Family.load,
                       target_module='pywikibot.family.Family',
                       old_name='Family',
                       since='20141001')


class Namespace(Iterable, ComparableMixin, UnicodeMixin):

    """
    Namespace site data object.

    This is backwards compatible with the structure of entries
    in site._namespaces which were a list of::

        [customised namespace,
         canonical namespace name?,
         namespace alias*]

    If the canonical_name is not provided for a namespace between -2
    and 15, the MediaWiki built-in names are used.
    Image and File are aliases of each other by default.

    If only one of canonical_name and custom_name are available, both
    properties will have the same value.
    """

    MEDIA = -2
    SPECIAL = -1
    MAIN = 0
    TALK = 1
    USER = 2
    USER_TALK = 3
    PROJECT = 4
    PROJECT_TALK = 5
    FILE = 6
    FILE_TALK = 7
    MEDIAWIKI = 8
    MEDIAWIKI_TALK = 9
    TEMPLATE = 10
    TEMPLATE_TALK = 11
    HELP = 12
    HELP_TALK = 13
    CATEGORY = 14
    CATEGORY_TALK = 15

    # These are the MediaWiki built-in names for MW 1.14+.
    # Namespace prefixes are always case-insensitive, but the
    # canonical forms are capitalized.
    canonical_namespaces = {
        -2: 'Media',
        -1: 'Special',
        0: '',
        1: 'Talk',
        2: 'User',
        3: 'User talk',
        4: 'Project',
        5: 'Project talk',
        6: 'File',
        7: 'File talk',
        8: 'MediaWiki',
        9: 'MediaWiki talk',
        10: 'Template',
        11: 'Template talk',
        12: 'Help',
        13: 'Help talk',
        14: 'Category',
        15: 'Category talk',
    }

    @deprecated_args(use_image_name=None)
    def __init__(self, id, canonical_name=None, custom_name=None,
                 aliases=None, **kwargs):
        """Initializer.

        @param custom_name: Name defined in server LocalSettings.php
        @type custom_name: str
        @param canonical_name: Canonical name
        @type canonical_name: str
        @param aliases: Aliases
        @type aliases: list of unicode
        """
        self.id = id
        canonical_name = canonical_name or self.canonical_namespaces.get(id)

        assert custom_name is not None or canonical_name is not None, \
            'Namespace needs to have at least one name'

        self.custom_name = custom_name \
            if custom_name is not None else canonical_name
        self.canonical_name = canonical_name \
            if canonical_name is not None else custom_name

        if aliases:
            self.aliases = aliases
        elif id in (6, 7):
            alias = 'Image'
            if id == 7:
                alias += ' talk'
            self.aliases = [alias]
        else:
            self.aliases = []

        for key, value in kwargs.items():
            setattr(self, key, value)

    def _distinct(self):
        if self.custom_name == self.canonical_name:
            return [self.canonical_name] + self.aliases
        else:
            return [self.custom_name, self.canonical_name] + self.aliases

    def _contains_lowercase_name(self, name):
        """Determine a lowercase normalised name is a name of this namespace.

        @rtype: bool
        """
        return name in (x.lower() for x in self._distinct())

    def __contains__(self, item):
        """Determine if item is a name of this namespace.

        The comparison is case insensitive, and item may have a single
        colon on one or both sides of the name.

        @param item: name to check
        @type item: basestring
        @rtype: bool
        """
        if item == '' and self.id == 0:
            return True

        name = Namespace.normalize_name(item)
        if not name:
            return False

        return self._contains_lowercase_name(name.lower())

    def __len__(self):
        """Obtain length of the iterable."""
        if self.custom_name == self.canonical_name:
            return len(self.aliases) + 1
        else:
            return len(self.aliases) + 2

    def __iter__(self):
        """Return an iterator."""
        return iter(self._distinct())

    def __getitem__(self, index):
        """Obtain an item from the iterable."""
        if self.custom_name != self.canonical_name:
            if index == 0:
                return self.custom_name
            else:
                index -= 1

        if index == 0:
            return self.canonical_name
        else:
            return self.aliases[index - 1]

    @staticmethod
    def _colons(id, name):
        """Return the name with required colons, depending on the ID."""
        if id == 0:
            return ':'

        if id in (6, 14):
            return ':' + name + ':'

        return name + ':'

    def __str__(self):
        """Return the canonical string representation."""
        return self.canonical_prefix()

    def __unicode__(self):
        """Return the custom string representation."""
        return self.custom_prefix()

    def canonical_prefix(self):
        """Return the canonical name with required colons."""
        return Namespace._colons(self.id, self.canonical_name)

    def custom_prefix(self):
        """Return the custom name with required colons."""
        return Namespace._colons(self.id, self.custom_name)

    def __int__(self):
        """Return the namespace id."""
        return self.id

    def __index__(self):
        """Return the namespace id."""
        return self.id

    def __hash__(self):
        """Return the namespace id."""
        return self.id

    def __eq__(self, other):
        """Compare whether two namespace objects are equal."""
        if isinstance(other, int):
            return self.id == other

        if isinstance(other, Namespace):
            return self.id == other.id

        if isinstance(other, UnicodeType):
            return other in self

        return False

    def __ne__(self, other):
        """Compare whether two namespace objects are not equal."""
        return not self.__eq__(other)

    def __mod__(self, other):
        """Apply modulo on the namespace id."""
        return self.id.__mod__(other)

    def __sub__(self, other):
        """Apply subtraction on the namespace id."""
        return self.id - other

    def __add__(self, other):
        """Apply addition on the namespace id."""
        return self.id + other

    def _cmpkey(self):
        """Return the ID as a comparison key."""
        return self.id

    def __repr__(self):
        """Return a reconstructable representation."""
        standard_attr = ['id', 'custom_name', 'canonical_name', 'aliases']
        extra = [(key, self.__dict__[key])
                 for key in sorted(self.__dict__)
                 if key not in standard_attr]

        if extra:
            kwargs = ', ' + ', '.join(
                key + '=' + repr(value) for key, value in extra)
        else:
            kwargs = ''

        return '%s(id=%d, custom_name=%r, canonical_name=%r, aliases=%r%s)' \
               % (self.__class__.__name__, self.id, self.custom_name,
                  self.canonical_name, self.aliases, kwargs)

    @staticmethod
    def default_case(id, default_case=None):
        """Return the default fixed case value for the namespace ID."""
        # https://www.mediawiki.org/wiki/Manual:$wgCapitalLinkOverrides#Warning
        if id > 0 and id % 2 == 1:  # the talk ns has the non-talk ns case
            id -= 1
        if id in (-1, 2, 8):
            return 'first-letter'
        else:
            return default_case

    @classmethod
    @deprecated_args(use_image_name=None)
    def builtin_namespaces(cls, use_image_name=None, case='first-letter'):
        """Return a dict of the builtin namespaces."""
        if use_image_name is not None:
            issue_deprecation_warning(
                'positional argument of "use_image_name"', None, 3,
                DeprecationWarning, since='20181015')

        return {i: cls(i, case=cls.default_case(i, case))
                for i in range(-2, 16)}

    @staticmethod
    def normalize_name(name):
        """
        Remove an optional colon before and after name.

        TODO: reject illegal characters.
        """
        if name == '':
            return ''

        parts = name.split(':', 4)
        count = len(parts)
        if count > 3 or (count == 3 and parts[2]):
            return False

        # Discard leading colon
        if count >= 2 and not parts[0] and parts[1]:
            return parts[1].strip()

        if parts[0]:
            return parts[0].strip()

        return False

    @classmethod
    @deprecated('NamespacesDict.lookup_name', since='20150703')
    def lookup_name(cls, name, namespaces=None):
        """
        Find the Namespace for a name.

        @param name: Name of the namespace.
        @type name: basestring
        @param namespaces: namespaces to search
                           default: builtins only
        @type namespaces: dict of Namespace
        @rtype: Namespace or None
        """
        if not namespaces:
            namespaces = cls.builtin_namespaces()

        return NamespacesDict._lookup_name(name, namespaces)

    @staticmethod
    @deprecated('NamespacesDict.resolve', since='20150703')
    def resolve(identifiers, namespaces=None):
        """
        Resolve namespace identifiers to obtain Namespace objects.

        Identifiers may be any value for which int() produces a valid
        namespace id, except bool, or any string which Namespace.lookup_name
        successfully finds. A numerical string is resolved as an integer.

        @param identifiers: namespace identifiers
        @type identifiers: iterable of basestring or Namespace key,
            or a single instance of those types
        @param namespaces: namespaces to search (default: builtins only)
        @type namespaces: dict of Namespace
        @return: list of Namespace objects in the same order as the
            identifiers
        @rtype: list
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if not namespaces:
            namespaces = Namespace.builtin_namespaces()

        return NamespacesDict._resolve(identifiers, namespaces)


class NamespacesDict(Mapping, SelfCallMixin):

    """
    An immutable dictionary containing the Namespace instances.

    It adds a deprecation message when called as the 'namespaces' property of
    APISite was callable.
    """

    _own_desc = 'the namespaces property'

    def __init__(self, namespaces):
        """Create new dict using the given namespaces."""
        super(NamespacesDict, self).__init__()
        self._namespaces = namespaces
        self._namespace_names = {}
        for namespace in self._namespaces.values():
            for name in namespace:
                self._namespace_names[name.lower()] = namespace

    def __iter__(self):
        """Iterate over all namespaces."""
        return iter(self._namespaces)

    def __getitem__(self, key):
        """
        Get the namespace with the given key.

        @param key: namespace key
        @type key: Namespace, int or str
        @rtype: Namespace
        """
        if isinstance(key, (Namespace, int)):
            return self._namespaces[key]
        else:
            namespace = self.lookup_name(key)
            if namespace:
                return namespace

        return super(NamespacesDict, self).__getitem__(key)

    def __getattr__(self, attr):
        """
        Get the namespace with the given key.

        @param attr: namespace key
        @type attr: Namespace, int or str
        @rtype: Namespace
        """
        # lookup_name access _namespaces
        if attr.isupper():
            if attr == 'MAIN':
                return self[0]

            namespace = self.lookup_name(attr)
            if namespace:
                return namespace

        return self.__getattribute__(attr)

    def __len__(self):
        """Get the number of namespaces."""
        return len(self._namespaces)

    def lookup_name(self, name):
        """
        Find the Namespace for a name also checking aliases.

        @param name: Name of the namespace.
        @type name: basestring
        @rtype: Namespace or None
        """
        name = Namespace.normalize_name(name)
        if name is False:
            return None
        return self.lookup_normalized_name(name.lower())

    def lookup_normalized_name(self, name):
        """
        Find the Namespace for a name also checking aliases.

        The name has to be normalized and must be lower case.

        @param name: Name of the namespace.
        @type name: basestring
        @rtype: Namespace or None
        """
        return self._namespace_names.get(name)

    # Temporary until Namespace.lookup_name can be removed
    @staticmethod
    def _lookup_name(name, namespaces):
        name = Namespace.normalize_name(name)
        if name is False:
            return None
        name = name.lower()

        for namespace in namespaces.values():
            if namespace._contains_lowercase_name(name):
                return namespace

        return None

    def resolve(self, identifiers):
        """
        Resolve namespace identifiers to obtain Namespace objects.

        Identifiers may be any value for which int() produces a valid
        namespace id, except bool, or any string which Namespace.lookup_name
        successfully finds. A numerical string is resolved as an integer.

        @param identifiers: namespace identifiers
        @type identifiers: iterable of basestring or Namespace key,
            or a single instance of those types
        @return: list of Namespace objects in the same order as the
            identifiers
        @rtype: list
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        return self._resolve(identifiers, self._namespaces)

    # Temporary until Namespace.resolve can be removed
    @staticmethod
    def _resolve(identifiers, namespaces):
        if isinstance(identifiers, (UnicodeType, Namespace)):
            identifiers = [identifiers]
        else:
            # convert non-iterators to single item list
            try:
                iter(identifiers)
            except TypeError:
                identifiers = [identifiers]

        # lookup namespace names, and assume anything else is a key.
        # int(None) raises TypeError; however, bool needs special handling.
        result = [NotImplemented if isinstance(ns, bool) else
                  NamespacesDict._lookup_name(ns, namespaces)
                  if isinstance(ns, UnicodeType)
                  and not ns.lstrip('-').isdigit() else
                  namespaces[int(ns)] if int(ns) in namespaces
                  else None
                  for ns in identifiers]

        if NotImplemented in result:
            raise TypeError('identifiers contains inappropriate types: %r'
                            % identifiers)

        # Namespace.lookup_name returns None if the name is not recognised
        if None in result:
            raise KeyError(
                'Namespace identifier(s) not recognised: %s'
                % ','.join(str(identifier) for identifier, ns in zip(
                    identifiers, result) if ns is None))

        return result


class _IWEntry(object):

    """An entry of the _InterwikiMap with a lazy loading site."""

    def __init__(self, local, url):
        self._site = None
        self.local = local
        self.url = url

    @property
    def site(self):
        if self._site is None:
            try:
                self._site = pywikibot.Site(url=self.url)
            except Exception as e:
                self._site = e
        return self._site


class _InterwikiMap(object):

    """A representation of the interwiki map of a site."""

    def __init__(self, site):
        """
        Create an empty uninitialized interwiki map for the given site.

        @param site: Given site for which interwiki map is to be created
        @type site: pywikibot.site.APISite
        """
        super(_InterwikiMap, self).__init__()
        self._site = site
        self._map = None

    def reset(self):
        """Remove all mappings to force building a new mapping."""
        self._map = None

    @property
    def _iw_sites(self):
        """Fill the interwikimap cache with the basic entries."""
        # _iw_sites is a local cache to return a APISite instance depending
        # on the interwiki prefix of that site
        if self._map is None:
            self._map = {iw['prefix']: _IWEntry('local' in iw, iw['url'])
                         for iw in self._site.siteinfo['interwikimap']}
        return self._map

    def __getitem__(self, prefix):
        """
        Return the site, locality and url for the requested prefix.

        @param prefix: Interwiki prefix
        @type prefix: Dictionary key
        @rtype: _IWEntry
        @raises KeyError: Prefix is not a key
        @raises TypeError: Site for the prefix is of wrong type
        """
        if prefix not in self._iw_sites:
            raise KeyError("'{0}' is not an interwiki prefix.".format(prefix))
        if isinstance(self._iw_sites[prefix].site, BaseSite):
            return self._iw_sites[prefix]
        elif isinstance(self._iw_sites[prefix].site, Exception):
            raise self._iw_sites[prefix].site
        else:
            raise TypeError('_iw_sites[%s] is wrong type: %s'
                            % (prefix, type(self._iw_sites[prefix].site)))

    def get_by_url(self, url):
        """
        Return a set of prefixes applying to the URL.

        @param url: URL for the interwiki
        @type url: str
        @rtype: set
        """
        return {prefix for prefix, iw_entry in self._iw_sites
                if iw_entry.url == url}


class BaseSite(ComparableMixin):

    """Site methods that are independent of the communication interface."""

    @remove_last_args(['sysop'])
    def __init__(self, code, fam=None, user=None):
        """
        Initializer.

        @param code: the site's language code
        @type code: str
        @param fam: wiki family name (optional)
        @type fam: str or pywikibot.family.Family
        @param user: bot user name (optional)
        @type user: str
        """
        if code.lower() != code:
            # Note the Site function in __init__ also emits a UserWarning
            # for this condition, showing the callers file and line no.
            pywikibot.log('BaseSite: code "%s" converted to lowercase' % code)
            code = code.lower()
        if not all(x in pywikibot.family.CODE_CHARACTERS for x in str(code)):
            pywikibot.log('BaseSite: code "%s" contains invalid characters'
                          % code)
        self.__code = code
        if isinstance(fam, UnicodeType) or fam is None:
            self.__family = pywikibot.family.Family.load(fam)
        else:
            self.__family = fam

        self.obsolete = False
        # if we got an outdated language code, use the new one instead.
        if self.__code in self.__family.obsolete:
            if self.__family.obsolete[self.__code] is not None:
                self.__code = self.__family.obsolete[self.__code]
                # Note the Site function in __init__ emits a UserWarning
                # for this condition, showing the callers file and line no.
                pywikibot.log('Site {} instantiated using aliases code of {}'
                              .format(self, code))
            else:
                # no such language anymore
                self.obsolete = True
                pywikibot.log('Site %s instantiated and marked "obsolete" '
                              'to prevent access' % self)
        elif self.__code not in self.languages():
            if self.__family.name in list(self.__family.langs.keys()) and \
               len(self.__family.langs) == 1:
                self.__code = self.__family.name
                if self.__family == pywikibot.config.family \
                        and code == pywikibot.config.mylang:
                    pywikibot.config.mylang = self.__code
                    warn('Global configuration variable "mylang" changed to '
                         '"%s" while instantiating site %s'
                         % (self.__code, self), UserWarning)
            else:
                raise UnknownSite("Language '%s' does not exist in family %s"
                                  % (self.__code, self.__family.name))

        self._username = normalize_username(user)

        self.use_hard_category_redirects = (
            self.code in self.family.use_hard_category_redirects)

        # following are for use with lock_page and unlock_page methods
        self._pagemutex = threading.Condition()
        self._locked_pages = set()

    @property
    @deprecated(
        "APISite.siteinfo['case'] or Namespace.case == 'case-sensitive'",
        since='20170504')
    def nocapitalize(self):
        """
        Return whether this site's default title case is case-sensitive.

        DEPRECATED.
        """
        return self.siteinfo['case'] == 'case-sensitive'

    @property
    def throttle(self):
        """Return this Site's throttle. Initialize a new one if needed."""
        if not hasattr(self, '_throttle'):
            self._throttle = Throttle(self, multiplydelay=True)
        return self._throttle

    @property
    def family(self):
        """The Family object for this Site's wiki family."""
        return self.__family

    @property
    def code(self):
        """
        The identifying code for this Site equal to the wiki prefix.

        By convention, this is usually an ISO language code, but it does
        not have to be.
        """
        return self.__code

    @property
    def lang(self):
        """The ISO language code for this Site.

        Presumed to be equal to the site code, but this can be overridden.
        """
        return self.__code

    @property
    def doc_subpage(self):
        """
        Return the documentation subpage for this Site.

        @rtype: tuple
        """
        if not hasattr(self, '_doc_subpage'):
            try:
                doc, codes = self.family.doc_subpages.get('_default', ((), []))
                if self.code not in codes:
                    try:
                        doc = self.family.doc_subpages[self.code]
                    # Language not defined in doc_subpages in x_family.py file
                    # It will use default for the family.
                    # should it just raise an Exception and fail?
                    # this will help to check the dictionary ...
                    except KeyError:
                        warn('Site {0} has no language defined in '
                             'doc_subpages dict in {1}_family.py file'
                             .format(self, self.family.name),
                             FamilyMaintenanceWarning, 2)
            # doc_subpages not defined in x_family.py file
            except AttributeError:
                doc = ()  # default
                warn('Site {0} has no doc_subpages dict in {1}_family.py file'
                     .format(self, self.family.name),
                     FamilyMaintenanceWarning, 2)
            self._doc_subpage = doc

        return self._doc_subpage

    def _cmpkey(self):
        """Perform equality and inequality tests on Site objects."""
        return (self.family.name, self.code)

    def __getstate__(self):
        """Remove Lock based classes before pickling."""
        new = self.__dict__.copy()
        del new['_pagemutex']
        if '_throttle' in new:
            del new['_throttle']
        # site cache contains exception information, which can't be pickled
        if '_iw_sites' in new:
            del new['_iw_sites']
        return new

    def __setstate__(self, attrs):
        """Restore things removed in __getstate__."""
        self.__dict__.update(attrs)
        self._pagemutex = threading.Condition()

    def user(self):
        """Return the currently-logged in bot username, or None."""
        if self.logged_in():
            return self.username()
        else:
            return None

    @remove_last_args(['sysop'])
    def username(self):
        """Return the username used for the site."""
        return self._username

    def __getattr__(self, attr):
        """Delegate undefined methods calls to the Family object."""
        if hasattr(self.__class__, attr):
            return getattr(self.__class__, attr)
        try:
            method = getattr(self.family, attr)
            if not callable(method):
                raise AttributeError
            f = functools.partial(method, self.code)
            if hasattr(method, '__doc__'):
                f.__doc__ = method.__doc__
            return f
        except AttributeError:
            raise AttributeError("%s instance has no attribute '%s'"
                                 % (self.__class__.__name__, attr))

    def __str__(self):
        """Return string representing this Site's name and code."""
        return self.family.name + ':' + self.code

    @property
    def sitename(self):
        """String representing this Site's name and code."""
        return SelfCallString(self.__str__())

    def __repr__(self):
        """Return internal representation."""
        return '{0}("{1}", "{2}")'.format(
            self.__class__.__name__, self.code, self.family)

    def __hash__(self):
        """Return hashable key."""
        return hash(repr(self))

    def languages(self):
        """Return list of all valid language codes for this site's Family."""
        return list(self.family.langs.keys())

    def validLanguageLinks(self):
        """Return list of language codes to be used in interwiki links."""
        return [lang for lang in self.languages()
                if self.namespaces.lookup_normalized_name(lang) is None]

    def _interwiki_urls(self, only_article_suffixes=False):
        base_path = self.path()
        if not only_article_suffixes:
            yield base_path
        yield base_path + '/'
        yield base_path + '?title='
        yield self.article_path

    def interwiki(self, prefix):
        """
        Return the site for a corresponding interwiki prefix.

        @raises pywikibot.exceptions.SiteDefinitionError: if the url given in
            the interwiki table doesn't match any of the existing families.
        @raises KeyError: if the prefix is not an interwiki prefix.
        """
        return self._interwikimap[prefix].site

    def interwiki_prefix(self, site):
        """
        Return the interwiki prefixes going to that site.

        The interwiki prefixes are ordered first by length (shortest first)
        and then alphabetically. L{interwiki(prefix)} is not guaranteed to
        equal C{site} (i.e. the parameter passed to this function).

        @param site: The targeted site, which might be it's own.
        @type site: L{BaseSite}
        @return: The interwiki prefixes
        @rtype: list (guaranteed to be not empty)
        @raises KeyError: if there is no interwiki prefix for that site.
        """
        assert site is not None, 'Site must not be None'
        prefixes = set()
        for url in site._interwiki_urls():
            prefixes.update(self._interwikimap.get_by_url(url))
        if not prefixes:
            raise KeyError(
                "There is no interwiki prefix to '{0}'".format(site))
        return sorted(prefixes, key=lambda p: (len(p), p))

    def local_interwiki(self, prefix):
        """
        Return whether the interwiki prefix is local.

        A local interwiki prefix is handled by the target site like a normal
        link. So if that link also contains an interwiki link it does follow
        it as long as it's a local link.

        @raises pywikibot.exceptions.SiteDefinitionError: if the url given in
            the interwiki table doesn't match any of the existing families.
        @raises KeyError: if the prefix is not an interwiki prefix.
        """
        return self._interwikimap[prefix].local

    @deprecated('APISite.namespaces.lookup_name', since='20150703')
    def ns_index(self, namespace):
        """
        Return the Namespace for a given namespace name.

        @param namespace: name
        @type namespace: str
        @return: The matching Namespace object on this Site
        @rtype: Namespace, or None if invalid
        """
        return self.namespaces.lookup_name(namespace)

    @deprecated('APISite.namespaces.lookup_name', since='20150703')
    def getNamespaceIndex(self, namespace):
        """DEPRECATED: Return the Namespace for a given namespace name."""
        return self.namespaces.lookup_name(namespace)

    def _build_namespaces(self):
        """Create default namespaces."""
        return Namespace.builtin_namespaces()

    @property
    def namespaces(self):
        """Return dict of valid namespaces on this wiki."""
        if not hasattr(self, '_namespaces'):
            self._namespaces = NamespacesDict(self._build_namespaces())
        return self._namespaces

    def ns_normalize(self, value):
        """
        Return canonical local form of namespace name.

        @param value: A namespace name
        @type value: str

        """
        index = self.namespaces.lookup_name(value)
        return self.namespace(index)

    # for backwards-compatibility
    normalizeNamespace = redirect_func(ns_normalize,
                                       old_name='normalizeNamespace',
                                       class_name='BaseSite',
                                       since='20141001')

    @remove_last_args(('default', ))
    def redirect(self):
        """Return list of localized redirect tags for the site."""
        return ['REDIRECT']

    @remove_last_args(('default', ))
    def pagenamecodes(self):
        """Return list of localized PAGENAME tags for the site."""
        return ['PAGENAME']

    @remove_last_args(('default', ))
    def pagename2codes(self):
        """Return list of localized PAGENAMEE tags for the site."""
        return ['PAGENAMEE']

    def lock_page(self, page, block=True):
        """
        Lock page for writing. Must be called before writing any page.

        We don't want different threads trying to write to the same page
        at the same time, even to different sections.

        @param page: the page to be locked
        @type page: pywikibot.Page
        @param block: if true, wait until the page is available to be locked;
            otherwise, raise an exception if page can't be locked

        """
        title = page.title(with_section=False)
        with self._pagemutex:
            while title in self._locked_pages:
                if not block:
                    raise PageInUse(title)
                self._pagemutex.wait()
            self._locked_pages.add(title)

    def unlock_page(self, page):
        """
        Unlock page. Call as soon as a write operation has completed.

        @param page: the page to be locked
        @type page: pywikibot.Page

        """
        with self._pagemutex:
            self._locked_pages.discard(page.title(with_section=False))
            self._pagemutex.notify_all()

    def disambcategory(self):
        """Return Category in which disambig pages are listed."""
        if self.has_data_repository:
            repo = self.data_repository()
            repo_name = repo.family.name
            try:
                item = self.family.disambcatname[repo.code]
            except KeyError:
                raise Error(
                    'No {repo} qualifier found for disambiguation category '
                    'name in {fam}_family file'.format(repo=repo_name,
                                                       fam=self.family.name))
            else:
                dp = pywikibot.ItemPage(repo, item)
                try:
                    name = dp.getSitelink(self)
                except pywikibot.NoPage:
                    raise Error(
                        'No disambiguation category name found in {repo} '
                        'for {site}'.format(repo=repo_name, site=self))
        else:  # fallback for non WM sites
            try:
                name = '%s:%s' % (Namespace.CATEGORY,
                                  self.family.disambcatname[self.code])
            except KeyError:
                raise Error(
                    'No disambiguation category name found in '
                    '{site.family.name}_family for {site}'.format(site=self))
        return pywikibot.Category(pywikibot.Link(name, self))

    @deprecated('pywikibot.Link', since='20090307', future_warning=True)
    def linkto(self, title, othersite=None):
        """DEPRECATED. Return a wikilink to a page.

        @param title: Title of the page to link to
        @type title: str
        @param othersite: Generate a interwiki link for use on this site.
        @type othersite: BaseSite or None

        @rtype: str
        """
        return pywikibot.Link(title, self).astext(othersite)

    def isInterwikiLink(self, text):
        """Return True if text is in the form of an interwiki link.

        If a link object constructed using "text" as the link text parses as
        belonging to a different site, this method returns True.

        """
        linkfam, linkcode = pywikibot.Link(text, self).parse_site()
        return linkfam != self.family.name or linkcode != self.code

    def redirectRegex(self, pattern=None):
        """Return a compiled regular expression matching on redirect pages.

        Group 1 in the regex match object will be the target title.

        """
        if pattern is None:
            pattern = 'REDIRECT'
        # A redirect starts with hash (#), followed by a keyword, then
        # arbitrary stuff, then a wikilink. The wikilink may contain
        # a label, although this is not useful.
        return re.compile(r'\s*#%(pattern)s\s*:?\s*\[\[(.+?)(?:\|.*?)?\]\]'
                          % {'pattern': pattern},
                          re.IGNORECASE | re.UNICODE | re.DOTALL)

    def sametitle(self, title1, title2):
        """
        Return True if title1 and title2 identify the same wiki page.

        title1 and title2 may be unequal but still identify the same page,
        if they use different aliases for the same namespace.
        """
        def ns_split(title):
            """Separate the namespace from the name."""
            ns, delim, name = title.partition(':')
            if delim:
                ns = self.namespaces.lookup_name(ns)
            if not delim or not ns:
                return default_ns, title
            else:
                return ns, name

        if title1 == title2:
            return True
        # Replace underscores with spaces and multiple combinations of them
        # with only one space
        title1 = re.sub(r'[_ ]+', ' ', title1)
        title2 = re.sub(r'[_ ]+', ' ', title2)
        if title1 == title2:
            return True
        default_ns = self.namespaces[0]
        # determine whether titles contain namespace prefixes
        ns1_obj, name1 = ns_split(title1)
        ns2_obj, name2 = ns_split(title2)
        if ns1_obj != ns2_obj:
            # pages in different namespaces
            return False
        name1 = name1.strip()
        name2 = name2.strip()
        # If the namespace has a case definition it's overriding the site's
        # case definition
        if ns1_obj.case == 'first-letter':
            name1 = first_upper(name1)
            name2 = first_upper(name2)
        return name1 == name2

    # namespace shortcuts for backwards-compatibility

    @deprecated('namespaces.SPECIAL.custom_name', since='20160407')
    def special_namespace(self):
        """Return local name for the Special: namespace."""
        return self.namespace(-1)

    @deprecated('namespaces.FILE.custom_name', since='20160407')
    def image_namespace(self):
        """Return local name for the File namespace."""
        return self.namespace(6)

    @deprecated('namespaces.MEDIAWIKI.custom_name', since='20160407')
    def mediawiki_namespace(self):
        """Return local name for the MediaWiki namespace."""
        return self.namespace(8)

    @deprecated('namespaces.TEMPLATE.custom_name', since='20160407')
    def template_namespace(self):
        """Return local name for the Template namespace."""
        return self.namespace(10)

    @deprecated('namespaces.CATEGORY.custom_name', since='20160407')
    def category_namespace(self):
        """Return local name for the Category namespace."""
        return self.namespace(14)

    @deprecated('list(namespaces.CATEGORY)', since='20150829')
    def category_namespaces(self):
        """Return names for the Category namespace."""
        return list(self.namespace(14, all=True))

    # site-specific formatting preferences

    def category_on_one_line(self):
        # TODO: is this even needed? No family in the framework uses it.
        """Return True if this site wants all category links on one line."""
        return self.code in self.family.category_on_one_line

    def interwiki_putfirst(self):
        """Return list of language codes for ordering of interwiki links."""
        return self.family.interwiki_putfirst.get(self.code, None)

    def getSite(self, code):
        """Return Site object for language 'code' in this Family."""
        return pywikibot.Site(code=code, fam=self.family, user=self.user())

    # deprecated methods for backwards-compatibility

    @deprecated('family attribute', since='20090307', future_warning=True)
    def fam(self):
        """Return Family object for this Site."""
        return self.family

    @deprecated('pywikibot.data.api.encode_url', since='20151211')
    def urlEncode(self, query):
        """DEPRECATED."""
        return api.encode_url(query)

    @deprecated('pywikibot.data.api.Request or pywikibot.comms.http.request',
                since='20141225')
    @deprecated_args(compress=None, no_hostname=None, cookies_only=None,
                     refer=None, back_response=None, retry=None, sysop=None)
    def getUrl(self, path, data=None):
        """DEPRECATED.

        Retained for compatibility only. All arguments except path and data
        are ignored.

        """
        from pywikibot.comms import http
        if data:
            if not isinstance(data, UnicodeType):
                data = urlencode(data)
            return http.request(self, path, method='PUT', body=data)
        else:
            return http.request(self, path)

    @deprecated(since='20141225')
    @remove_last_args(['sysop', 'cookies'])
    def postForm(self, address, predata):
        """DEPRECATED."""
        return self.getUrl(address, data=predata)

    @deprecated(since='20141225')
    @deprecated_args(contentType=None)
    @remove_last_args(['sysop', 'compress', 'cookies'])
    def postData(self, address, data):
        """DEPRECATED."""
        return self.getUrl(address, data=data)


@deprecated_args(right=None)
def must_be(group=None):
    """Decorator to require a certain user status when method is called.

    @param group: The group the logged in user should belong to.
                  This parameter can be overridden by
                  keyword argument 'as_group'.
    @type group: str
    @return: method decorator
    @raises UserRightsError: user is not part of the required user group.
    """
    def decorator(fn):
        def callee(self, *args, **kwargs):
            grp = kwargs.pop('as_group', group)
            if self.obsolete:
                if not self.has_group('steward'):
                    raise UserRightsError(
                        'Site {} has been closed. Only steward '
                        'can perform requested action.'
                        .format(self.sitename))

            elif not self.has_group(grp):
                raise UserRightsError('User "{}" is not part of the required '
                                      'user group "{}"'
                                      .format(self.user(), grp))

            return fn(self, *args, **kwargs)

        if not __debug__:
            return fn

        manage_wrapping(callee, fn)
        return callee

    return decorator


def need_right(right=None):
    """Decorator to require a certain user right when method is called.

    @param right: The right the logged in user should have.
    @type right: str
    @return: method decorator
    @raises UserRightsError: user has insufficient rights.
    """
    def decorator(fn):
        def callee(self, *args, **kwargs):
            if self.obsolete:
                if not self.has_group('steward'):
                    raise UserRightsError(
                        'Site {} has been closed. Only steward '
                        'can perform requested action.'
                        .format(self.sitename))

            elif right is not None and not self.has_right(right):
                raise UserRightsError('User "{}" does not have required '
                                      'user right "{}"'
                                      .format(self.user(), right))
            return fn(self, *args, **kwargs)

        if not __debug__:
            return fn

        manage_wrapping(callee, fn)
        return callee

    return decorator


def need_version(version):
    """Decorator to require a certain MediaWiki version number.

    @param version: the mw version number required
    @type version: str
    @return: a decorator to make sure the requirement is satisfied when
        the decorated function is called.
    """
    def decorator(fn):
        def callee(self, *args, **kwargs):
            if MediaWikiVersion(self.version()) < MediaWikiVersion(version):
                raise NotImplementedError(
                    'Method or function "%s"\n'
                    "isn't implemented in MediaWiki version < %s"
                    % (fn.__name__, version))
            return fn(self, *args, **kwargs)

        if not __debug__:
            return fn

        manage_wrapping(callee, fn)

        return callee
    return decorator


def need_extension(extension):
    """Decorator to require a certain MediaWiki extension.

    @param extension: the MediaWiki extension required
    @type extension: str
    @return: a decorator to make sure the requirement is satisfied when
        the decorated function is called.
    """
    def decorator(fn):
        def callee(self, *args, **kwargs):
            if not self.has_extension(extension):
                raise UnknownExtension(
                    'Method "%s" is not implemented without the extension %s'
                    % (fn.__name__, extension))
            return fn(self, *args, **kwargs)

        if not __debug__:
            return fn

        manage_wrapping(callee, fn)

        return callee
    return decorator


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

    def __init__(self, site):
        """Initialise it with an empty cache."""
        self._site = site
        self._cache = {}

    @staticmethod
    def _get_default(key):
        """
        Return the default value for different properties.

        If the property is 'restrictions' it returns a dictionary with:
         - 'cascadinglevels': 'sysop'
         - 'semiprotectedlevels': 'autoconfirmed'
         - 'levels': '' (everybody), 'autoconfirmed', 'sysop'
         - 'types': 'create', 'edit', 'move', 'upload'
        Otherwise it returns L{pywikibot.tools.EMPTY_DEFAULT}.

        @param key: The property name
        @type key: str
        @return: The default value
        @rtype: dict or L{pywikibot.tools.EmptyDefault}
        """
        if key == 'restrictions':
            # implemented in b73b5883d486db0e9278ef16733551f28d9e096d
            return {
                'cascadinglevels': ['sysop'],
                'semiprotectedlevels': ['autoconfirmed'],
                'levels': ['', 'autoconfirmed', 'sysop'],
                'types': ['create', 'edit', 'move', 'upload']
            }
        elif key == 'fileextensions':
            # the default file extensions in MediaWiki
            return [{'ext': ext} for ext in ['png', 'gif', 'jpg', 'jpeg']]
        else:
            return pywikibot.tools.EMPTY_DEFAULT

    @staticmethod
    def _post_process(prop, data):
        """Do some default handling of data. Directly modifies data."""
        # Be careful with version tests inside this here as it might need to
        # query this method to actually get the version number

        if prop == 'general':
            if 'articlepath' not in data:  # Introduced in 1.16.0
                # Old version of MediaWiki, extract from base
                path = urlparse(data['base'])[2].rsplit('/', 1)[0] + '/$1'
                data['articlepath'] = path

        # Convert boolean props from empty strings to actual boolean values
        if prop in Siteinfo.BOOLEAN_PROPS.keys():
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

    def _get_siteinfo(self, prop, expiry):
        """
        Retrieve a siteinfo property.

        All properties which the site doesn't
        support contain the default value. Because pre-1.12 no data was
        returned when a property doesn't exists, it queries each property
        independetly if a property is invalid.

        @param prop: The property names of the siteinfo.
        @type prop: str or iterable
        @param expiry: The expiry date of the cached request.
        @type expiry: int (days), L{datetime.timedelta}, False (config)
        @return: A dictionary with the properties of the site. Each entry in
            the dictionary is a tuple of the value and a boolean to save if it
            is the default value.
        @rtype: dict (the values)
        @see: U{https://www.mediawiki.org/wiki/API:Meta#siteinfo_.2F_si}
        """
        def warn_handler(mod, message):
            """Return True if the warning is handled."""
            matched = Siteinfo.WARNING_REGEX.match(message)
            if mod == 'siteinfo' and matched:
                invalid_properties.extend(
                    prop.strip() for prop in matched.group(1).split(','))
                return True
            else:
                return False

        if isinstance(prop, UnicodeType):
            props = [prop]
        else:
            props = prop
        if len(props) == 0:
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
        except api.APIError as e:
            if e.code == 'siunknown_siprop':
                if len(props) == 1:
                    pywikibot.log(
                        "Unable to get siprop '{0}'".format(props[0]))
                    return {props[0]: (Siteinfo._get_default(props[0]), False)}
                else:
                    pywikibot.log('Unable to get siteinfo, because at least '
                                  "one property is unknown: '{0}'".format(
                                      "', '".join(props)))
                    results = {}
                    for prop in props:
                        results.update(self._get_siteinfo(prop, expiry))
                    return results
            else:
                raise
        else:
            result = {}
            if invalid_properties:
                for prop in invalid_properties:
                    result[prop] = (Siteinfo._get_default(prop), False)
                pywikibot.log("Unable to get siprop(s) '{0}'".format(
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
        if expire is False:  # can never expire
            return False
        elif not cache_date:  # default values are always expired
            return True
        else:
            # cached date + expiry are in the past if it's expired
            return cache_date + expire < datetime.datetime.utcnow()

    def _get_general(self, key, expiry):
        """
        Return a siteinfo property which is loaded by default.

        The property 'general' will be queried if it wasn't yet or it's forced.
        Additionally all uncached default properties are queried. This way
        multiple default properties are queried with one request. It'll cache
        always all results.

        @param key: The key to search for.
        @type key: str
        @param expiry: If the cache is older than the expiry it ignores the
            cache and queries the server to get the newest value.
        @type expiry: int (days), L{datetime.timedelta}, False (never)
        @return: If that property was retrieved via this method. Returns None
            if the key was not in the retrieved values.
        @rtype: various (the value), bool (if the default value is used)
        """
        if 'general' not in self._cache:
            pywikibot.debug('general siteinfo not loaded yet.', _logger)
            force = True
            props = ['namespaces', 'namespacealiases']
        else:
            force = Siteinfo._is_expired(self._cache['general'][1], expiry)
            props = []
        if force:
            props = [prop for prop in props if prop not in self._cache]
            if props:
                pywikibot.debug(
                    "Load siteinfo properties '{0}' along with 'general'"
                    .format("', '".join(props)), _logger)
            props += ['general']
            default_info = self._get_siteinfo(props, expiry)
            for prop in props:
                self._cache[prop] = default_info[prop]
            if key in default_info:
                return default_info[key]
        if key in self._cache['general'][0]:
            return self._cache['general'][0][key], self._cache['general']
        else:
            return None

    def __getitem__(self, key):
        """Return a siteinfo property, caching and not forcing it."""
        return self.get(key, False)  # caches and doesn't force it

    def get(self, key, get_default=True, cache=True, expiry=False):
        """
        Return a siteinfo property.

        It will never throw an APIError if it only stated, that the siteinfo
        property doesn't exist. Instead it will use the default value.

        @param key: The name of the siteinfo property.
        @type key: str
        @param get_default: Whether to throw an KeyError if the key is invalid.
        @type get_default: bool
        @param cache: Caches the result internally so that future accesses via
            this method won't query the server.
        @type cache: bool
        @param expiry: If the cache is older than the expiry it ignores the
            cache and queries the server to get the newest value.
        @type expiry: int/float (days), L{datetime.timedelta}, False (never)
        @return: The gathered property
        @rtype: various
        @raises KeyError: If the key is not a valid siteinfo property and the
            get_default option is set to False.
        @see: L{_get_siteinfo}
        """
        # expire = 0 (or timedelta(0)) are always expired and their bool is
        # False, so skip them EXCEPT if it's literally False, then they expire
        # never: "expiry is False" is different than "not expiry"!
        # if it's a int convert to timedelta
        if expiry is not False and isinstance(expiry, (int, float)):
            expiry = datetime.timedelta(expiry)
        if expiry or expiry is False:
            try:
                cached = self._get_cached(key)
            except KeyError:
                pass
            else:  # cached value available
                # is a default value, but isn't accepted
                if not cached[1] and not get_default:
                    raise KeyError(key)
                elif not Siteinfo._is_expired(cached[1], expiry):
                    return copy.deepcopy(cached[0])
        preloaded = self._get_general(key, expiry)
        if not preloaded:
            preloaded = self._get_siteinfo(key, expiry)[key]
        else:
            cache = False
        if not preloaded[1] and not get_default:
            raise KeyError(key)
        else:
            if cache:
                self._cache[key] = preloaded
            return copy.deepcopy(preloaded[0])

    def _get_cached(self, key):
        """Return the cached value or a KeyError exception if not cached."""
        if 'general' in self._cache:
            if key in self._cache['general'][0]:
                return (self._cache['general'][0][key],
                        self._cache['general'][1])
            else:
                return self._cache[key]
        raise KeyError(key)

    def __contains__(self, key):
        """Return whether the value is cached."""
        try:
            self._get_cached(key)
        except KeyError:
            return False
        else:
            return True

    def is_recognised(self, key):
        """Return if 'key' is a valid property name. 'None' if not cached."""
        time = self.get_requested_time(key)
        if time is None:
            return None
        else:
            return bool(time)

    def get_requested_time(self, key):
        """
        Return when 'key' was successfully requested from the server.

        If the property is actually in the siprop 'general' it returns the
        last request from the 'general' siprop.

        @param key: The siprop value or a property of 'general'.
        @type key: basestring
        @return: The last time the siprop of 'key' was requested.
        @rtype: None (never), False (default), L{datetime.datetime} (cached)
        """
        try:
            return self._get_cached(key)[1]
        except KeyError:
            return None

    def __call__(self, key='general', force=False, dump=False):
        """DEPRECATED: Return the entry for key or dump the complete cache."""
        issue_deprecation_warning(
            'Calling siteinfo', 'itself as a dictionary', since='20161221'
        )
        if not dump:
            return self.get(key, expiry=0 if force else False)
        else:
            self.get(key, expiry=0 if force else False)
            return self._cache


class TokenWallet(object):

    """Container for tokens."""

    def __init__(self, site):
        """Initializer.

        @type site: pywikibot.site.APISite
        """
        self.site = site
        self._tokens = {}
        self.failed_cache = set()  # cache unavailable tokens.

    def load_tokens(self, types, all=False):
        """
        Preload one or multiple tokens.

        @param types: the types of token.
        @type types: iterable
        @param all: load all available tokens, if None only if it can be done
            in one request.
        @type all: bool
        """
        if self.site.user() is None:
            self.site.login()

        self._tokens.setdefault(self.site.user(), {}).update(
            self.site.get_tokens(types, all=all))

        # Preload all only the first time.
        # When all=True types is extended in site.get_tokens().
        # Keys not recognised as tokens, are cached so they are not requested
        # any longer.
        if all is not False:
            for key in types:
                if key not in self._tokens[self.site.user()]:
                    self.failed_cache.add((self.site.user(), key))

    def __getitem__(self, key):
        """Get token value for the given key."""
        if self.site.user() is None:
            self.site.login()

        user_tokens = self._tokens.setdefault(self.site.user(), {})
        # always preload all for users without tokens
        failed_cache_key = (self.site.user(), key)

        try:
            key = self.site.validate_tokens([key])[0]
        except IndexError:
            raise Error(
                "Requested token '{0}' is invalid on {1} wiki."
                .format(key, self.site))

        if (key not in user_tokens
                and failed_cache_key not in self.failed_cache):
            self.load_tokens([key], all=False if user_tokens else None)

        if key in user_tokens:
            return user_tokens[key]
        else:
            # token not allowed for self.site.user() on self.site
            self.failed_cache.add(failed_cache_key)
            # to be changed back to a plain KeyError?
            raise Error(
                "Action '{0}' is not allowed for user {1} on {2} wiki."
                .format(key, self.site.user(), self.site))

    def __contains__(self, key):
        """Return True if the given token name is cached."""
        return key in self._tokens.setdefault(self.site.user(), {})

    def __str__(self):
        """Return a str representation of the internal tokens dictionary."""
        return self._tokens.__str__()

    def __repr__(self):
        """Return a representation of the internal tokens dictionary."""
        return self._tokens.__repr__()


class RemovedSite(BaseSite):

    """Site removed from a family."""

    @remove_last_args(['sysop'])
    def __init__(self, code, fam, user=None):
        """Initializer."""
        super(RemovedSite, self).__init__(code, fam, user)


_mw_msg_cache = defaultdict(dict)


class APISite(BaseSite):

    """
    API interface to MediaWiki site.

    Do not instantiate directly; use pywikibot.Site function.
    """

    @remove_last_args(['sysop'])
    def __init__(self, code, fam=None, user=None):
        """Initializer."""
        BaseSite.__init__(self, code, fam, user)
        self._msgcache = {}
        self._loginstatus = LoginStatus.NOT_ATTEMPTED
        self._siteinfo = Siteinfo(self)
        self._paraminfo = api.ParamInfo(self)
        self._interwikimap = _InterwikiMap(self)
        self.tokens = TokenWallet(self)

    def __getstate__(self):
        """Remove TokenWallet before pickling, for security reasons."""
        new = super(APISite, self).__getstate__()
        del new['tokens']
        del new['_interwikimap']
        return new

    def __setstate__(self, attrs):
        """Restore things removed in __getstate__."""
        super(APISite, self).__setstate__(attrs)
        self._interwikimap = _InterwikiMap(self)
        self.tokens = TokenWallet(self)

    @classmethod
    def fromDBName(cls, dbname, site=None):
        """
        Create a site from a database name using the sitematrix.

        @param dbname: database name
        @type dbname: str
        @param site: Site to load sitematrix from. (Default meta.wikimedia.org)
        @type site: pywikibot.site.APISite
        @return: site object for the database name
        @rtype: pywikibot.site.APISite
        """
        # TODO this only works for some WMF sites
        if not site:
            site = pywikibot.Site('meta', 'meta')
        req = site._request(expiry=datetime.timedelta(days=10),
                            parameters={'action': 'sitematrix'})
        data = req.submit()
        for key, val in data['sitematrix'].items():
            if key == 'count':
                continue
            if 'code' in val:
                lang = val['code']
                for site in val['site']:
                    if site['dbname'] == dbname:
                        if site['code'] == 'wiki':
                            site['code'] = 'wikipedia'
                        return pywikibot.Site(lang, site['code'])
            else:  # key == 'specials'
                for site in val:
                    if site['dbname'] == dbname:
                        return pywikibot.Site(url=site['url'] + '/w/index.php')
        raise ValueError('Cannot parse a site out of %s.' % dbname)

    @deprecated_args(step=None)
    def _generator(self, gen_class, type_arg=None, namespaces=None,
                   total=None, **args):
        """Convenience method that returns an API generator.

        All generic keyword arguments are passed as MW API parameter except for
        'g_content' which is passed as a normal parameter to the generator's
        Initializer.

        @param gen_class: the type of generator to construct (must be
            a subclass of pywikibot.data.api.QueryGenerator)
        @param type_arg: query type argument to be passed to generator's
            constructor unchanged (not all types require this)
        @type type_arg: str
        @param namespaces: if not None, limit the query to namespaces in this
            list
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param total: if not None, limit the generator to yielding this many
            items in total
        @type total: int
        @return: iterable with parameters set
        @rtype: api.QueryGenerator
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        # TODO: Support parameters/simple modes?
        req_args = {'site': self, 'parameters': args}
        if 'g_content' in args:
            req_args['g_content'] = args.pop('g_content')
        if type_arg is not None:
            gen = gen_class(type_arg, **req_args)
        else:
            gen = gen_class(**req_args)
        if namespaces is not None:
            gen.set_namespace(namespaces)
        gen.set_maximum_items(total)
        return gen

    def _request_class(self, kwargs):
        """
        Get the appropriate class.

        Inside this class kwargs use the parameters mode but QueryGenerator may
        use the old kwargs mode.
        """
        # This checks expiry in kwargs and not kwargs['parameters'] so it won't
        # create a CachedRequest when there is an expiry in an API parameter
        # and kwargs here are actually in parameters mode.
        if 'expiry' in kwargs and kwargs['expiry'] is not None:
            return api.CachedRequest
        else:
            return api.Request

    def _request(self, **kwargs):
        """Create a request by forwarding all parameters directly."""
        if 'expiry' in kwargs and kwargs['expiry'] is None:
            del kwargs['expiry']

        return self._request_class(kwargs)(site=self, **kwargs)

    def _simple_request(self, **kwargs):
        """Create a request by defining all kwargs as parameters."""
        return self._request_class({'parameters': kwargs}).create_simple(
            site=self, **kwargs)

    @remove_last_args(['sysop'])
    def logged_in(self):
        """Verify the bot is logged into the site as the expected user.

        The expected usernames are those provided as the user parameter
        at instantiation.

        @rtype: bool
        """
        if not hasattr(self, '_userinfo'):
            return False
        if 'anon' in self.userinfo or not self.userinfo.get('id'):
            return False

        if not self.userinfo.get('name'):
            return False

        if self.userinfo['name'] != self.username():
            return False

        return True

    @deprecated('Site.user()', since='20090307', future_warning=True)
    @remove_last_args(['sysop'])
    def loggedInAs(self):
        """Return the current username if logged in, otherwise return None.

        DEPRECATED (use .user() method instead)

        @param sysop: if True, test if user is logged in as the sysop user
                     instead of the normal user.
        @type sysop: bool

        @rtype: bool
        """
        return self.logged_in() and self.user()

    def is_oauth_token_available(self):
        """
        Check whether OAuth token is set for this site.

        @rtype: bool
        """
        auth_token = get_authentication(self.base_url(''))
        return auth_token is not None and len(auth_token) == 4

    @deprecated_args(sysop=None)
    def login(self, sysop=None, autocreate=False):
        """
        Log the user in if not already logged in.

        @param autocreate: if true, allow auto-creation of the account
                           using unified login
        @type autocreate: bool

        @raises pywikibot.exceptions.NoUsername: Username is not recognised
            by the site.
        @see: U{https://www.mediawiki.org/wiki/API:Login}
        """
        # TODO: this should include an assert that loginstatus
        #       is not already IN_PROGRESS, however the
        #       login status may be left 'IN_PROGRESS' because
        #       of exceptions or if the first method of login
        #       (below) is successful. Instead, log the problem,
        #       to be increased to 'warning' level once majority
        #       of issues are resolved.
        if self._loginstatus == LoginStatus.IN_PROGRESS:
            pywikibot.log(
                '{!r}.login() called when a previous login was in progress.'
                .format(self))
        # There are several ways that the site may already be
        # logged in, and we do not need to hit the server again.
        # logged_in() is False if _userinfo exists, which means this
        # will have no effect for the invocation from api.py
        if self.logged_in():
            self._loginstatus = LoginStatus.AS_USER
            return
        # check whether a login cookie already exists for this user
        # or check user identity when OAuth enabled
        self._loginstatus = LoginStatus.IN_PROGRESS
        try:
            self.getuserinfo(force=True)
            if self.userinfo['name'] == self.user():
                return
        # May occur if you are not logged in (no API read permissions).
        except api.APIError:
            pass
        except NoUsername as e:
            if not autocreate:
                raise e

        if self.is_oauth_token_available():
            if self.userinfo['name'] != self.username():
                if self.username() is None:
                    raise NoUsername('No username has been defined in your '
                                     'user-config.py: you have to add in this '
                                     'file the following line:\n'
                                     "usernames['{family}']['{lang}'] "
                                     "= '{username}'"
                                     .format(family=self.family,
                                             lang=self.lang,
                                             username=self.userinfo['name']))
                else:
                    raise NoUsername('Logged in on {site} via OAuth as '
                                     '{wrong}, but expect as {right}'
                                     .format(site=self,
                                             wrong=self.userinfo['name'],
                                             right=self.username()))
            else:
                raise NoUsername('Logging in on %s via OAuth failed' % self)
        login_manager = api.LoginManager(site=self, user=self.username())
        if login_manager.login(retry=True, autocreate=autocreate):
            self._username = login_manager.username
            self.getuserinfo(force=True)
            self._loginstatus = LoginStatus.AS_USER
        else:
            self._loginstatus = LoginStatus.NOT_LOGGED_IN  # failure

    # alias for backward-compatibility
    forceLogin = redirect_func(login, old_name='forceLogin',
                               class_name='APISite', since='20141001')

    def _relogin(self):
        """Force a login sequence without logging out, using the current user.

        This is an internal function which is used to re-login when
        the internal login state does not match the state we receive
        from the site.
        """
        del self._userinfo
        self._loginstatus = LoginStatus.NOT_LOGGED_IN
        self.login()

    def logout(self):
        """
        Logout of the site and load details for the logged out user.

        Also logs out of the global account if linked to the user.
        U{https://www.mediawiki.org/wiki/API:Logout}

        @raises APIError: Logout is not available when OAuth enabled.
        """
        if self.is_oauth_token_available():
            pywikibot.warning('Using OAuth suppresses logout function')
        req_params = {'action': 'logout'}
        # csrf token introduced in MW 1.24
        try:
            req_params['token'] = self.tokens['csrf']
        except Error:
            pass
        uirequest = self._simple_request(**req_params)
        uirequest.submit()
        self._loginstatus = LoginStatus.NOT_LOGGED_IN

        # Reset tokens and user properties
        del self._userinfo
        self.tokens = TokenWallet(self)
        self._paraminfo = api.ParamInfo(self)

        # Clear also cookies for site's second level domain (T224712)
        api._invalidate_superior_cookies(self.family)

    def getuserinfo(self, force=False):
        """Retrieve userinfo from site and store in _userinfo attribute.

        self._userinfo will be a dict with the following keys and values:

          - id: user id (numeric str)
          - name: username (if user is logged in)
          - anon: present if user is not logged in
          - groups: list of groups (could be empty)
          - rights: list of rights (could be empty)
          - message: present if user has a new message on talk page
          - blockinfo: present if user is blocked (dict)

        U{https://www.mediawiki.org/wiki/API:Userinfo}

        @param force: force to retrieve userinfo ignoring cache
        @type force: bool
        """
        if force or not hasattr(self, '_userinfo'):
            uirequest = self._simple_request(
                action='query',
                meta='userinfo',
                uiprop='blockinfo|hasmsg|groups|rights'
            )
            uidata = uirequest.submit()
            assert 'query' in uidata, \
                   "API userinfo response lacks 'query' key"
            assert 'userinfo' in uidata['query'], \
                   "API userinfo response lacks 'userinfo' key"
            self._userinfo = uidata['query']['userinfo']
            if 'anon' in self._userinfo or not self._userinfo.get('id'):
                pywikibot.warning('No user is logged in on site {}'
                                  .format(self))
        return self._userinfo

    userinfo = property(fget=getuserinfo, doc=getuserinfo.__doc__)

    def getglobaluserinfo(self):
        """Retrieve globaluserinfo from site and cache it.

        self._globaluserinfo will be a dict with the following keys and values:

          - id: user id (numeric str)
          - home: dbname of home wiki
          - registration: registration date as Timestamp
          - groups: list of groups (could be empty)
          - rights: list of rights (could be empty)
          - editcount: global editcount
        """
        if not hasattr(self, '_globaluserinfo'):
            uirequest = self._simple_request(
                action='query',
                meta='globaluserinfo',
                guiprop='groups|rights|editcount'
            )
            uidata = uirequest.submit()
            assert 'query' in uidata, \
                   "API userinfo response lacks 'query' key"
            assert 'globaluserinfo' in uidata['query'], \
                   "API userinfo response lacks 'userinfo' key"
            self._globaluserinfo = uidata['query']['globaluserinfo']
            ts = self._globaluserinfo['registration']
            iso_ts = pywikibot.Timestamp.fromISOformat(ts)
            self._globaluserinfo['registration'] = iso_ts
        return self._globaluserinfo

    globaluserinfo = property(fget=getglobaluserinfo,
                              doc=getglobaluserinfo.__doc__)

    @remove_last_args(['sysop'])
    def is_blocked(self):
        """
        Return True when logged in user is blocked.

        To check whether a user can perform an action,
        the method has_right should be used.
        U{https://www.mediawiki.org/wiki/API:Userinfo}

        @rtype: bool
        """
        return 'blockinfo' in self.userinfo

    @deprecated('has_right() or is_blocked()', since='20141218')
    @remove_last_args(['sysop'])
    def checkBlocks(self):
        """
        Raise an exception when the user is blocked. DEPRECATED.

        @raises pywikibot.exceptions.UserBlocked: The logged in user account
            is blocked.
        """
        if self.is_blocked():
            raise UserBlocked('User is blocked in site %s' % self)

    def get_searched_namespaces(self, force=False):
        """
        Retrieve the default searched namespaces for the user.

        If no user is logged in, it returns the namespaces used by default.
        Otherwise it returns the user preferences. It caches the last result
        and returns it, if the username or login status hasn't changed.

        @param force: Whether the cache should be discarded.
        @return: The namespaces which are searched by default.
        @rtype: C{set} of L{Namespace}
        """
        # TODO: Integrate into _userinfo
        if (force or not hasattr(self, '_useroptions')
                or self.user() != self._useroptions['_name']):
            uirequest = self._simple_request(
                action='query',
                meta='userinfo',
                uiprop='options'
            )
            uidata = uirequest.submit()
            assert 'query' in uidata, \
                   "API userinfo response lacks 'query' key"
            assert 'userinfo' in uidata['query'], \
                   "API userinfo response lacks 'userinfo' key"
            self._useroptions = uidata['query']['userinfo']['options']
            # To determine if user name has changed
            self._useroptions['_name'] = (
                None if 'anon' in uidata['query']['userinfo'] else
                uidata['query']['userinfo']['name'])
        return {ns for ns in self.namespaces.values() if ns.id >= 0
                and self._useroptions['searchNs{0}'.format(ns.id)]
                in ['1', True]}

    @property
    def article_path(self):
        """Get the nice article path without $1."""
        # Assert and remove the trailing $1 and assert that it'll end in /
        assert self.siteinfo['general']['articlepath'].endswith('/$1'), \
            'articlepath must end with /$1'
        return self.siteinfo['general']['articlepath'][:-2]

    def assert_valid_iter_params(self, msg_prefix, start, end, reverse,
                                 is_ts=True):
        """Validate iterating API parameters.

        @param msg_prefix: The calling method name
        @type msg_prefix: str
        @param start: The start value to compare
        @param end: The end value to compare
        @param reverse: The reverse option
        @type reverse: bool
        @param is_ts: When comparing timestamps (with is_ts=True) the start
            is usually greater than end. Comparing titles this is vice versa.
        @type is_ts: bool
        @raises AssertionError: start/end values are in wrong order
        """
        if reverse ^ is_ts:
            low, high = end, start
            order = 'follow'
        else:
            low, high = start, end
            order = 'precede'
        msg = ('{method}: "start" must {order} "end" '
               'with reverse={reverse} and is_ts={is_ts} '
               'but "start" is "{start}" and "end" is "{end}".')
        assert low < high, fill(msg.format(method=msg_prefix, order=order,
                                           start=start, end=end,
                                           reverse=reverse, is_ts=is_ts))

    @remove_last_args(['sysop'])
    def has_right(self, right):
        """Return true if and only if the user has a specific right.

        Possible values of 'right' may vary depending on wiki settings.
        U{https://www.mediawiki.org/wiki/API:Userinfo}

        @param right: a specific right to be validated
        @type right: str
        """
        return right.lower() in self.userinfo['rights']

    @remove_last_args(['sysop'])
    def has_group(self, group):
        """Return true if and only if the user is a member of specified group.

        Possible values of 'group' may vary depending on wiki settings,
        but will usually include bot.
        U{https://www.mediawiki.org/wiki/API:Userinfo}
        """
        return group.lower() in self.userinfo['groups']

    @remove_last_args(['sysop'])
    def messages(self):
        """Return true if the user has new messages, and false otherwise."""
        return 'messages' in self.userinfo

    @need_extension('Echo')
    def notifications(self, **kwargs):
        """Yield Notification objects from the Echo extension.

        @keyword format: If specified, notifications will be returned formatted
            this way. Its value is either 'model', 'special' or None. Default
            is 'special'.
        @type format: str or None

        Refer API reference for other keywords.
        """
        params = {
            'action': 'query',
            'meta': 'notifications',
            'notformat': 'special',
        }

        for key, value in kwargs.items():
            params['not' + key] = value

        data = self._simple_request(**params).submit()
        notifications = data['query']['notifications']['list']

        # Support API before 1.27.0-wmf.22
        if hasattr(notifications, 'values'):
            notifications = notifications.values()

        return (Notification.fromJSON(self, notification)
                for notification in notifications)

    @need_extension('Echo')
    def notifications_mark_read(self, **kwargs):
        """Mark selected notifications as read.

        @return: whether the action was successful
        @rtype: bool
        """
        # TODO: ensure that the 'echomarkread' action
        # is supported by the site
        kwargs = merge_unique_dicts(kwargs, action='echomarkread',
                                    token=self.tokens['edit'])
        req = self._simple_request(**kwargs)
        data = req.submit()
        try:
            return data['query']['echomarkread']['result'] == 'success'
        except KeyError:
            return False

    def mediawiki_messages(self, keys, lang=None):
        """Fetch the text of a set of MediaWiki messages.

        The returned dict uses each key to store the associated message.

        @see: U{https://www.mediawiki.org/wiki/API:Allmessages}

        @param keys: MediaWiki messages to fetch
        @type keys: iterable of str
        @param lang: a language code, default is self.lang
        @type lang: str or None

        @rtype dict
        """
        amlang = lang or self.lang
        if not all(amlang in _mw_msg_cache
                   and _key in _mw_msg_cache[amlang] for _key in keys):
            parameters = {'meta': 'allmessages',
                          'ammessages': keys,
                          'amlang': amlang,
                          }
            msg_query = api.QueryGenerator(site=self, parameters=parameters)

            for msg in msg_query:
                if 'missing' not in msg:
                    _mw_msg_cache[amlang][msg['name']] = msg['*']

            # Check requested keys
            result = {}
            for key in keys:
                try:
                    result[key] = _mw_msg_cache[amlang][key]
                except KeyError:
                    raise KeyError("No message '{}' found for lang '{}'"
                                   .format(key, amlang))
            else:
                return result

        return {_key: _mw_msg_cache[amlang][_key] for _key in keys}

    @deprecated_args(forceReload=None)
    def mediawiki_message(self, key, lang=None):
        """Fetch the text for a MediaWiki message.

        @param key: name of MediaWiki message
        @type key: str
        @param lang: a language code, default is self.lang
        @type lang: str or None

        @rtype unicode
        """
        return self.mediawiki_messages([key], lang=lang)[key]

    def has_mediawiki_message(self, key, lang=None):
        """Determine if the site defines a MediaWiki message.

        @param key: name of MediaWiki message
        @type key: str
        @param lang: a language code, default is self.lang
        @type lang: str or None

        @rtype: bool
        """
        return self.has_all_mediawiki_messages([key], lang=lang)

    def has_all_mediawiki_messages(self, keys, lang=None):
        """Confirm that the site defines a set of MediaWiki messages.

        @param keys: names of MediaWiki messages
        @type keys: iterable of str
        @param lang: a language code, default is self.lang
        @type lang: str or None

        @rtype: bool
        """
        try:
            self.mediawiki_messages(keys, lang=lang)
        except KeyError:
            return False
        return True

    @property
    def months_names(self):
        """Obtain month names from the site messages.

        The list is zero-indexed, ordered by month in calendar, and should
        be in the original site language.

        @return: list of tuples (month name, abbreviation)
        @rtype: list
        """
        if hasattr(self, '_months_names'):
            return self._months_names

        months_long = ['january', 'february', 'march',
                       'april', 'may_long', 'june',
                       'july', 'august', 'september',
                       'october', 'november', 'december']
        months_short = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
                        'jul', 'aug', 'sep', 'oct', 'nov', 'dec']

        months = self.mediawiki_messages(months_long + months_short)

        self._months_names = []
        for m_l, m_s in zip(months_long, months_short):
            self._months_names.append((months[m_l], months[m_s]))

        return self._months_names

    def list_to_text(self, args):
        """Convert a list of strings into human-readable text.

        The MediaWiki messages 'and' and 'word-separator' are used as separator
        between the last two arguments.
        If more than two arguments are given, other arguments are
        joined using MediaWiki message 'comma-separator'.

        @param args: text to be expanded
        @type args: typing.Iterable[unicode]

        @rtype: str
        """
        needed_mw_messages = ('and', 'comma-separator', 'word-separator')
        if not args:
            return ''
        if PY2 and any(isinstance(arg, str) for arg in args):
            issue_deprecation_warning('arg of type str', 'type unicode',
                                      since='20151014')

        args = [UnicodeType(e) for e in args]
        try:
            msgs = self.mediawiki_messages(needed_mw_messages)
        except KeyError:
            raise NotImplementedError(
                'MediaWiki messages missing: {0}'.format(needed_mw_messages))

        if self.mw_version < '1.16':
            for key, value in msgs.items():
                if key == 'and' and value == ',&#32;and':
                    # v1.14 defined and as ',&#32;and'; fixed in v1.15
                    msgs['and'] = ' and'
                else:
                    msgs[key] = pywikibot.html2UnicodeType(value)

        concat = msgs['and'] + msgs['word-separator']
        return msgs['comma-separator'].join(
            args[:-2] + [concat.join(args[-2:])])

    @deprecated_args(string='text')
    def expand_text(self, text, title=None, includecomments=None):
        """Parse the given text for preprocessing and rendering.

        e.g expand templates and strip comments if includecomments
        parameter is not True. Keeps text inside
        <nowiki></nowiki> tags unchanges etc. Can be used to parse
        magic parser words like {{CURRENTTIMESTAMP}}.

        @param text: text to be expanded
        @type text: str
        @param title: page title without section
        @type title: str
        @param includecomments: if True do not strip comments
        @type includecomments: bool
        @rtype: str
        """
        if not isinstance(text, UnicodeType):
            raise ValueError('text must be a string')
        if not text:
            return ''
        req = self._simple_request(action='expandtemplates', text=text)
        if title is not None:
            req['title'] = title
        if includecomments is True:
            req['includecomments'] = ''
        if self.mw_version > '1.24wmf7':
            key = 'wikitext'
            req['prop'] = key
        else:
            key = '*'
        return req.submit()['expandtemplates'][key]

    getExpandedString = redirect_func(expand_text,
                                      old_name='getExpandedString',
                                      class_name='APISite',
                                      since='20170504')

    def getcurrenttimestamp(self):
        """
        Return the server time as a MediaWiki timestamp string.

        It calls L{server_time} first so it queries the server to get the
        current server time.

        @return: the server time
        @rtype: str (as 'yyyymmddhhmmss')
        """
        return self.server_time().totimestampformat()

    def server_time(self):
        """
        Return a Timestamp object representing the current server time.

        For wikis with a version newer than 1.16 it uses the 'time' property
        of the siteinfo 'general'. It'll force a reload before returning the
        time. It requests to expand the text '{{CURRENTTIMESTAMP}}' for older
        wikis.

        @return: the current server time
        @rtype: L{Timestamp}
        """
        if self.mw_version >= '1.16':
            return pywikibot.Timestamp.fromISOformat(
                self.siteinfo.get('time', expiry=0))
        else:
            return pywikibot.Timestamp.fromtimestampformat(
                self.expand_text('{{CURRENTTIMESTAMP}}'))

    getcurrenttime = redirect_func(server_time, old_name='getcurrenttime',
                                   class_name='APISite', since='20141225')

    def getmagicwords(self, word):
        """Return list of localized "word" magic words for the site."""
        if not hasattr(self, '_magicwords'):
            magicwords = self.siteinfo.get('magicwords', cache=False)
            self._magicwords = {item['name']: item['aliases']
                                for item in magicwords}

        if word in self._magicwords:
            return self._magicwords[word]
        else:
            return [word]

    @deprecated('expand_text', since='20150831')
    def resolvemagicwords(self, wikitext):
        """
        Replace the {{ns:xx}} marks in a wikitext with the namespace names.

        DEPRECATED.
        """
        return self.expand_text(wikitext)

    @remove_last_args(('default', ))
    def redirect(self):
        """Return the localized #REDIRECT keyword."""
        # return the magic word without the preceding '#' character
        return self.getmagicwords('redirect')[0].lstrip('#')

    def redirectRegex(self):
        """Return a compiled regular expression matching on redirect pages.

        Group 1 in the regex match object will be the target title.

        """
        # NOTE: this is needed, since the API can give false positives!
        try:
            keywords = {s.lstrip('#') for s in self.getmagicwords('redirect')}
            keywords.add('REDIRECT')  # just in case
            pattern = '(?:' + '|'.join(keywords) + ')'
        except KeyError:
            # no localized keyword for redirects
            pattern = None
        return BaseSite.redirectRegex(self, pattern)

    @remove_last_args(('default', ))
    def pagenamecodes(self):
        """Return list of localized PAGENAME tags for the site."""
        return self.getmagicwords('pagename')

    @remove_last_args(('default', ))
    def pagename2codes(self):
        """Return list of localized PAGENAMEE tags for the site."""
        return self.getmagicwords('pagenamee')

    def _build_namespaces(self):
        _namespaces = {}

        for nsdata in self.siteinfo.get('namespaces', cache=False).values():
            ns = nsdata.pop('id')
            if ns == 0:
                canonical_name = nsdata.pop('*')
                custom_name = canonical_name
            else:
                custom_name = nsdata.pop('*')
                canonical_name = nsdata.pop('canonical')

            nsdata.setdefault('content', ns == 0)  # mw < 1.16

            default_case = Namespace.default_case(ns)
            if 'case' not in nsdata:
                nsdata['case'] = default_case or self.siteinfo['case']
            elif default_case is not None:
                assert default_case == nsdata['case'], \
                    'Default case is not consistent'

            namespace = Namespace(ns, canonical_name, custom_name, **nsdata)
            _namespaces[ns] = namespace

        for item in self.siteinfo.get('namespacealiases'):
            ns = int(item['id'])
            try:
                namespace = _namespaces[ns]
            except KeyError:
                pywikibot.warning(
                    'Broken namespace alias "{0}" (id: {1}) on {2}'.format(
                        item['*'], item['id'], self))
            if item['*'] not in namespace:
                namespace.aliases.append(item['*'])

        return _namespaces

    @deprecated('has_extension', since='20140819')
    @remove_last_args(('unknown', ))
    def hasExtension(self, name, unknown=None):
        """DEPRECATED. Determine whether extension `name` is loaded."""
        return self.has_extension(name)

    def has_extension(self, name):
        """Determine whether extension `name` is loaded.

        @param name: The extension to check for, case sensitive
        @type name: str
        @return: If the extension is loaded
        @rtype: bool
        """
        extensions = self.siteinfo['extensions']
        for ext in extensions:
            if ext['name'] == name:
                return True
        return False

    @property
    def siteinfo(self):
        """Site information dict."""
        return self._siteinfo

    @deprecated('siteinfo or Namespace instance', since='20150830')
    def case(self):
        """Return this site's capitalization rule."""
        # This is the global setting via $wgCapitalLinks, it is used whenever
        # the namespaces don't propagate the namespace specific value.
        return self.siteinfo['case']

    def dbName(self):
        """Return this site's internal id."""
        return self.siteinfo['wikiid']

    @deprecated('APISite.lang', since='20150629')
    def language(self):
        """Return the code for the language of this Site."""
        return self.lang

    @property
    def lang(self):
        """Return the code for the language of this Site."""
        return self.siteinfo['lang']

    def version(self):
        """
        Return live project version number as a string.

        This overwrites the corresponding family method for APISite class. Use
        L{pywikibot.site.mw_version} to compare MediaWiki versions.
        """
        version = self.force_version()
        if not version:
            try:
                version = self.siteinfo.get('generator',
                                            expiry=1).split(' ')[1]
            except pywikibot.data.api.APIError:
                # May occur if you are not logged in (no API read permissions).
                pywikibot.exception('You have no API read permissions. Seems '
                                    'you are not logged in')
                version = self.family.version(self.code)

        if MediaWikiVersion(version) < MediaWikiVersion('1.19'):
            warn('\n'
                 + fill('Support of MediaWiki {version} will be dropped. '
                        'It is recommended to use MediaWiki 1.19 or above. '
                        'You may use Pywikibot stable release 3.0.20200111 '
                        'for older MediaWiki versions. '
                        'See T245350 for further information.'
                        .format(version=version)), FutureWarning)

        return version

    @property
    def mw_version(self):
        """Return self.version() as a MediaWikiVersion object.

        Cache the result for 24 hours.
        @rtype: MediaWikiVersion
        """
        mw_ver, cache_time = getattr(self, '_mw_version_time', (None, None))
        if mw_ver is None or time.time() - cache_time > 60 * 60 * 24:
            mw_ver = MediaWikiVersion(self.version())
            setattr(self, '_mw_version_time', (mw_ver, time.time()))
        return mw_ver

    @property
    def has_image_repository(self):
        """Return True if site has a shared image repository like Commons."""
        code, fam = self.shared_image_repository()
        return bool(code or fam)

    @property
    def has_data_repository(self):
        """Return True if site has a shared data repository like Wikidata."""
        return self.data_repository() is not None

    @property
    @deprecated('has_data_repository', since='20160405')
    def has_transcluded_data(self):
        """Return True if site has a shared data repository like Wikidata."""
        return self.has_data_repository

    def image_repository(self):
        """Return Site object for image repository e.g. commons."""
        code, fam = self.shared_image_repository()
        if bool(code or fam):
            return pywikibot.Site(code, fam, self.username())

    def data_repository(self):
        """
        Return the data repository connected to this site.

        @return: The data repository if one is connected or None otherwise.
        @rtype: pywikibot.site.DataSite or None
        """
        def handle_warning(mod, warning):
            return (mod == 'query' and re.match(
                r'Unrecognized value for parameter [\'"]meta[\'"]: wikibase',
                warning))

        req = self._request(
            expiry=7, parameters={'action': 'query', 'meta': 'wikibase'})
        req._warning_handler = handle_warning
        data = req.submit()
        if 'query' in data and 'wikibase' in data['query']:
            data = data['query']['wikibase']['repo']['url']
            url = data['base'] + data['scriptpath'] + '/index.php'
            try:
                return pywikibot.Site(url=url, user=self.username(),
                                      interface='DataSite')
            except SiteDefinitionError as e:
                pywikibot.warning('Site "{0}" supports wikibase at "{1}", but '
                                  'creation failed: {2}.'.format(self, url, e))
                return None
        else:
            assert 'warnings' in data
            return None

    def is_image_repository(self):
        """Return True if Site object is the image repository."""
        return self is self.image_repository()

    def is_data_repository(self):
        """Return True if its data repository is itself."""
        return self is self.data_repository()

    def page_from_repository(self, item):
        """
        Return a Page for this site object specified by wikibase item.

        @param item: id number of item, "Q###",
        @type item: str
        @return: Page, or Category object given by wikibase item number
            for this site object.
        @rtype: pywikibot.Page or None

        @raises pywikibot.exceptions.UnknownExtension: site has no wikibase
            extension
        @raises NotimplementedError: method not implemented for a wikibase site
        """
        if not self.has_data_repository:
            raise UnknownExtension(
                'Wikibase is not implemented for {0}.'.format(self))
        if self.is_data_repository():
            raise NotImplementedError(
                'page_from_repository method is not implemented for '
                'Wikibase {0}.'.format(self))
        repo = self.data_repository()
        dp = pywikibot.ItemPage(repo, item)
        try:
            page_title = dp.getSitelink(self)
        except pywikibot.NoPage:
            return None
        page = pywikibot.Page(self, page_title)
        if page.namespace() == Namespace.CATEGORY:
            page = pywikibot.Category(page)
        return page

    def nice_get_address(self, title):
        """Return shorter URL path to retrieve page titled 'title'."""
        # 'title' is expected to be URL-encoded already
        return self.siteinfo['articlepath'].replace('$1', title)

    @need_version('1.21')
    @need_extension('ProofreadPage')
    def _cache_proofreadinfo(self, expiry=False):
        """Retrieve proofreadinfo from site and cache response.

        Applicable only to sites with ProofreadPage extension installed.

        The following info is returned by the query and cached:
        - self._proofread_index_ns: Index Namespace
        - self._proofread_page_ns: Page Namespace
        - self._proofread_levels: a dictionary with:
                keys: int in the range [0, 1, ..., 4]
                values: category name corresponding to the 'key' quality level
            e.g. on en.wikisource:
            {0: 'Without text', 1: 'Not proofread', 2: 'Problematic',
             3: 'Proofread', 4: 'Validated'}

        @param expiry: either a number of days or a datetime.timedelta object
        @type expiry: int (days), L{datetime.timedelta}, False (config)
        @return: A tuple containing _proofread_index_ns,
            self._proofread_page_ns and self._proofread_levels.
        @rtype: Namespace, Namespace, dict
        """
        if (not hasattr(self, '_proofread_index_ns')
                or not hasattr(self, '_proofread_page_ns')
                or not hasattr(self, '_proofread_levels')):

            pirequest = self._request(
                expiry=pywikibot.config.API_config_expiry
                if expiry is False else expiry,
                parameters={'action': 'query', 'meta': 'proofreadinfo',
                            'piprop': 'namespaces|qualitylevels'}
            )

            pidata = pirequest.submit()
            ns_id = pidata['query']['proofreadnamespaces']['index']['id']
            self._proofread_index_ns = self.namespaces[ns_id]

            ns_id = pidata['query']['proofreadnamespaces']['page']['id']
            self._proofread_page_ns = self.namespaces[ns_id]

            self._proofread_levels = {}
            for ql in pidata['query']['proofreadqualitylevels']:
                self._proofread_levels[ql['id']] = ql['category']

    @property
    def proofread_index_ns(self):
        """Return Index namespace for the ProofreadPage extension."""
        if not hasattr(self, '_proofread_index_ns'):
            self._cache_proofreadinfo()
        return self._proofread_index_ns

    @property
    def proofread_page_ns(self):
        """Return Page namespace for the ProofreadPage extension."""
        if not hasattr(self, '_proofread_page_ns'):
            self._cache_proofreadinfo()
        return self._proofread_page_ns

    @property
    def proofread_levels(self):
        """Return Quality Levels for the ProofreadPage extension."""
        if not hasattr(self, '_proofread_levels'):
            self._cache_proofreadinfo()
        return self._proofread_levels

    def namespace(self, num, all=False):
        """Return string containing local name of namespace 'num'.

        If optional argument 'all' is true, return all recognized
        values for this namespace.

        @param num: Namespace constant.
        @type num: int
        @param all: If True return a Namespace object. Otherwise
            return the namespace name.
        @return: local name or Namespace object
        @rtype: str or Namespace
        """
        if all:
            return self.namespaces[num]
        return self.namespaces[num][0]

    @deprecated('version()', since='20140612')
    def live_version(self, force=False):
        """Return the 'real' version number found on [[Special:Version]].

        By default the version number is cached for one day.

        @param force: If the version should be read always from the server and
            never from the cache.
        @type force: bool
        @return: A tuple containing the major, minor version number and any
            text after that. If an error occurred (0, 0, 0) is returned.
        @rtype: int, int, str
        """
        try:
            versionstring = self.siteinfo.get('generator',
                                              expiry=0 if force else 1)
            m = re.match(r'MediaWiki ([0-9]+)\.([0-9]+)(.*)$', versionstring)
            if m:
                return (int(m.group(1)), int(m.group(2)), m.group(3))
        # May occur if you are not logged in (no API read permissions).
        except api.APIError:
            return (0, 0, 0)

    def _update_page(self, page, query):
        for pageitem in query:
            if not self.sametitle(pageitem['title'],
                                  page.title(with_section=False)):
                raise InconsistentTitleReceived(page, pageitem['title'])
            api.update_page(page, pageitem, query.props)

    def loadpageinfo(self, page, preload=False):
        """Load page info from api and store in page attributes.

        @see: U{https://www.mediawiki.org/wiki/API:Info}
        """
        title = page.title(with_section=False)
        inprop = 'protection'
        if preload:
            inprop += '|preload'

        query = self._generator(api.PropertyGenerator,
                                type_arg='info',
                                titles=title.encode(self.encoding()),
                                inprop=inprop)
        self._update_page(page, query)

    @need_extension('GeoData')
    def loadcoordinfo(self, page):
        """Load [[mw:Extension:GeoData]] info."""
        title = page.title(with_section=False)
        query = self._generator(api.PropertyGenerator,
                                type_arg='coordinates',
                                titles=title.encode(self.encoding()),
                                coprop=['type', 'name', 'dim',
                                        'country', 'region',
                                        'globe'],
                                coprimary='all')
        self._update_page(page, query)

    @need_extension('PageImages')
    def loadpageimage(self, page):
        """
        Load [[mw:Extension:PageImages]] info.

        @param page: The page for which to obtain the image
        @type page: pywikibot.Page

        @raises APIError: PageImages extension is not installed
        """
        title = page.title(with_section=False)
        query = self._generator(api.PropertyGenerator,
                                type_arg='pageimages',
                                titles=title.encode(self.encoding()),
                                piprop=['name'])
        self._update_page(page, query)

    def loadpageprops(self, page):
        """Load page props for the given page."""
        title = page.title(with_section=False)
        query = self._generator(api.PropertyGenerator,
                                type_arg='pageprops',
                                titles=title.encode(self.encoding()),
                                )
        self._update_page(page, query)

    @need_extension('Global Usage')
    def globalusage(self, page, total=None):
        """Iterate global image usage for a given FilePage.

        @param page: the page to return global image usage for.
        @type image: pywikibot.FilePage
        @param total: iterate no more than this number of pages in total.
        @raises TypeError: input page is not a FilePage.
        @raises pywikibot.exceptions.SiteDefinitionError: Site could not be
            defined for a returned entry in API response.
        """
        if not isinstance(page, pywikibot.FilePage):
            raise TypeError('Page %s must be a FilePage.' % page)

        title = page.title(with_section=False)
        args = {'titles': title,
                'gufilterlocal': False,
                }
        query = self._generator(api.PropertyGenerator,
                                type_arg='globalusage',
                                guprop=['url', 'pageid', 'namespace'],
                                total=total,  # will set gulimit=total in api,
                                **args)

        for pageitem in query:
            if not self.sametitle(pageitem['title'],
                                  page.title(with_section=False)):
                raise InconsistentTitleReceived(page, pageitem['title'])

            api.update_page(page, pageitem, query.props)

            assert 'globalusage' in pageitem, \
                   "API globalusage response lacks 'globalusage' key"
            for entry in pageitem['globalusage']:
                try:
                    gu_site = pywikibot.Site(url=entry['url'])
                except SiteDefinitionError:
                    pywikibot.warning(
                        'Site could not be defined for global'
                        ' usage for {0}: {1}.'.format(page, entry))
                    continue
                gu_page = pywikibot.Page(gu_site, entry['title'])
                yield gu_page

    def loadimageinfo(self, page, history=False,
                      url_width=None, url_height=None, url_param=None):
        """Load image info from api and save in page attributes.

        Parameters correspond to iiprops in:
        [1] U{https://www.mediawiki.org/wiki/API:Imageinfo}

        Parameters validation and error handling left to the API call.

        @param history: if true, return the image's version history
        @param url_width: see iiurlwidth in [1]
        @param url_height: see iiurlheigth in [1]
        @param url_param: see iiurlparam in [1]

        """
        title = page.title(with_section=False)
        args = {'titles': title,
                'iiurlwidth': url_width,
                'iiurlheight': url_height,
                'iiurlparam': url_param,
                }
        if not history:
            args['total'] = 1
        query = self._generator(api.PropertyGenerator,
                                type_arg='imageinfo',
                                iiprop=['timestamp', 'user', 'comment',
                                        'url', 'size', 'sha1', 'mime',
                                        'metadata', 'archivename'],
                                **args)
        # kept for backward compatibility
        # TODO: when backward compatibility can be broken, adopt
        # self._update_page() pattern and remove return
        for pageitem in query:
            if not self.sametitle(pageitem['title'], title):
                raise InconsistentTitleReceived(page, pageitem['title'])
            api.update_page(page, pageitem, query.props)

            if 'imageinfo' not in pageitem:
                if 'missing' in pageitem:
                    raise NoPage(page)
                raise PageRelatedError(
                    page,
                    'loadimageinfo: Query on %s returned no imageinfo')

        return (pageitem['imageinfo']
                if history else pageitem['imageinfo'][0])

    @deprecated('Check the content model instead', since='20150128')
    def loadflowinfo(self, page):
        """
        Load Flow-related information about a given page.

        Assumes that the Flow extension is installed.

        @see: U{https://www.mediawiki.org/wiki/API:Flowinfo}

        @raises APIError: Flow extension is not installed
        """
        title = page.title(with_section=False)
        query = self._generator(api.PropertyGenerator,
                                type_arg='flowinfo',
                                titles=title.encode(self.encoding()),
                                )
        self._update_page(page, query)

    @deprecated('page.exists()', since='20180218')
    def page_exists(self, page):
        """Return True if and only if page is an existing page on site."""
        return page.pageid > 0

    def page_restrictions(self, page):
        """Return a dictionary reflecting page protections."""
        if not hasattr(page, '_protection'):
            self.loadpageinfo(page)
        return page._protection

    def page_can_be_edited(self, page, action='edit'):
        """Determine if the page can be modified.

        Return True if the bot has the permission of needed restriction level
        for the given action type.

        @param page: a pywikibot.Page object
        @type param: pywikibot.Page
        @param action: a valid restriction type like 'edit', 'move'
        @type action: str
        @rtype: bool

        @raises ValueError: invalid action parameter
        """
        if action not in self.siteinfo['restrictions']['types']:
            raise ValueError('{}.page_can_be_edited(): Invalid value "{}" for '
                             '"action" parameter'
                             .format(self.__class__.__name__, action))
        prot_rights = {
            '': action,
            'autoconfirmed': 'editsemiprotected',
            'sysop': 'editprotected',
            'steward': 'editprotected'
        }
        restriction = self.page_restrictions(page).get(action, ('', None))[0]
        user_rights = self.userinfo['rights']
        if prot_rights.get(restriction, restriction) in user_rights:
            return True
        return False

    def page_isredirect(self, page):
        """Return True if and only if page is a redirect."""
        if not hasattr(page, '_isredir'):
            page._isredir = False  # bug T56684
            self.loadpageinfo(page)
        return page._isredir

    def getredirtarget(self, page):
        """
        Return page object for the redirect target of page.

        @param page: page to search redirects for
        @type page: pywikibot.page.BasePage
        @return: redirect target of page
        @rtype: pywikibot.Page

        @raises pywikibot.exceptions.IsNotRedirectPage: page is not a redirect
        @raises RuntimeError: no redirects found
        @raises pywikibot.exceptions.CircularRedirect: page is a circular
            redirect
        @raises pywikibot.exceptions.InterwikiRedirectPage: the redirect
            target is on another site
        """
        if not self.page_isredirect(page):
            raise IsNotRedirectPage(page)
        if hasattr(page, '_redirtarget'):
            return page._redirtarget

        title = page.title(with_section=False)
        query = self._simple_request(
            action='query',
            prop='info',
            titles=title,
            redirects=True)
        result = query.submit()
        if 'query' not in result or 'redirects' not in result['query']:
            raise RuntimeError(
                "getredirtarget: No 'redirects' found for page {}."
                .format(title))

        redirmap = {item['from']: {'title': item['to'],
                                   'section': '#'
                                   + item['tofragment']
                                   if 'tofragment' in item
                                   and item['tofragment']
                                   else ''}
                    for item in result['query']['redirects']}

        # Normalize title
        for item in result['query'].get('normalized', []):
            if item['from'] == title:
                title = item['to']
                break

        if title not in redirmap:
            raise RuntimeError(
                "getredirtarget: 'redirects' contains no key for page {}."
                .format(title))
        target_title = '%(title)s%(section)s' % redirmap[title]

        if self.sametitle(title, target_title):
            raise CircularRedirect(page)

        if 'pages' not in result['query']:
            # No "pages" element might indicate a circular redirect
            # Check that a "to" link is also a "from" link in redirmap
            for _from, _to in redirmap.items():
                if _to['title'] in redirmap:
                    raise CircularRedirect(page)
            else:
                target = pywikibot.Page(source=page.site, title=target_title)

                # Check if target is on another site.
                if target.site != page.site:
                    raise InterwikiRedirectPage(page, target)
                else:
                    # Redirect to Special: & Media: pages, which do not work
                    # like redirects, but are rendered like a redirect.
                    page._redirtarget = target
                    return page._redirtarget

        pagedata = list(result['query']['pages'].values())[0]
        # There should be only one value in 'pages' (the ultimate
        # target, also in case of double redirects).
        if self.sametitle(pagedata['title'], target_title):
            # target_title is the ultimate target
            target = pywikibot.Page(self, pagedata['title'], pagedata['ns'])
            api.update_page(target, pagedata, ['info'])
        else:
            # Target is an intermediate redirect -> double redirect.
            # Do not bypass double-redirects and return the ultimate target;
            # it would be impossible to detect and fix double-redirects.
            # This handles also redirects to sections, as sametitle()
            # does not ignore sections.
            target = pywikibot.Page(self, target_title)

        # Upcast to proper Page subclass.
        ns = target.namespace()
        if ns == 2:
            target = pywikibot.User(target)
        elif ns == 6:
            target = pywikibot.FilePage(target)
        elif ns == 14:
            target = pywikibot.Category(target)
        page._redirtarget = target

        return page._redirtarget

    def load_pages_from_pageids(self, pageids):
        """
        Return a page generator from pageids.

        Pages are iterated in the same order than in the underlying pageids.

        Pageids are filtered and only one page is returned in case of
        duplicate pageids.

        @param pageids: an iterable that returns pageids (str or int),
            or a comma- or pipe-separated string of pageids
            (e.g. '945097,1483753, 956608' or '945097|483753|956608')
        """
        if not pageids:
            return
        if isinstance(pageids, UnicodeType):
            pageids = pageids.replace('|', ',')
            pageids = pageids.split(',')
            pageids = [p.strip() for p in pageids]

        # Validate pageids.
        gen = (str(int(p)) for p in pageids if int(p) > 0)

        # Find out how many pages can be specified at a time.
        parameter = self._paraminfo.parameter('query+info', 'prop')
        if self.logged_in() and self.has_right('apihighlimits'):
            groupsize = int(parameter['highlimit'])
        else:
            groupsize = int(parameter['limit'])

        for sublist in itergroup(filter_unique(gen), groupsize):
            # Store the order of the input data.
            priority_dict = dict(zip(sublist, range(len(sublist))))

            prio_queue = []
            next_prio = 0
            params = {'pageids': sublist, }
            rvgen = api.PropertyGenerator('info', site=self, parameters=params)

            for pagedata in rvgen:
                title = pagedata['title']
                pageid = str(pagedata['pageid'])
                page = pywikibot.Page(pywikibot.Link(title, source=self))
                api.update_page(page, pagedata)
                priority, page = heapq.heappushpop(prio_queue,
                                                   (priority_dict[pageid],
                                                    page))
                # Smallest priority matches expected one; yield early.
                if priority == next_prio:
                    yield page
                    next_prio += 1
                else:
                    # Push onto the heap.
                    heapq.heappush(prio_queue, (priority, page))

            # Extract data in the same order of the input data.
            while prio_queue:
                priority, page = heapq.heappop(prio_queue)
                yield page

    def preloadpages(self, pagelist, groupsize=50, templates=False,
                     langlinks=False, pageprops=False):
        """Return a generator to a list of preloaded pages.

        Pages are iterated in the same order than in the underlying pagelist.
        In case of duplicates in a groupsize batch, return the first entry.

        @param pagelist: an iterable that returns Page objects
        @param groupsize: how many Pages to query at a time
        @type groupsize: int
        @param templates: preload pages (typically templates) transcluded in
            the provided pages
        @type templates: bool
        @param langlinks: preload all language links from the provided pages
            to other languages
        @type langlinks: bool
        @param pageprops: preload various properties defined in page content
        @type pageprops: bool

        """
        props = 'revisions|info|categoryinfo'
        if templates:
            props += '|templates'
        if langlinks:
            props += '|langlinks'
        if pageprops:
            props += '|pageprops'

        rvprop = ['ids', 'flags', 'timestamp', 'user', 'comment', 'content']

        parameter = self._paraminfo.parameter('query+info', 'prop')
        if self.logged_in() and self.has_right('apihighlimits'):
            max_ids = int(parameter['highlimit'])
        else:
            max_ids = int(parameter['limit'])  # T78333, T161783

        for sublist in itergroup(pagelist, min(groupsize, max_ids)):
            # Do not use p.pageid property as it will force page loading.
            pageids = [str(p._pageid) for p in sublist
                       if hasattr(p, '_pageid') and p._pageid > 0]
            cache = {}
            # In case of duplicates, return the first entry.
            for priority, page in enumerate(sublist):
                try:
                    cache.setdefault(page.title(with_section=False),
                                     (priority, page))
                except pywikibot.InvalidTitle:
                    pywikibot.exception()

            prio_queue = []
            next_prio = 0
            rvgen = api.PropertyGenerator(props, site=self)
            rvgen.set_maximum_items(-1)  # suppress use of "rvlimit" parameter

            if len(pageids) == len(sublist) and len(set(pageids)) <= max_ids:
                # only use pageids if all pages have them
                rvgen.request['pageids'] = set(pageids)
            else:
                rvgen.request['titles'] = list(cache.keys())
            rvgen.request['rvprop'] = rvprop
            pywikibot.output('Retrieving %s pages from %s.'
                             % (len(cache), self))

            for pagedata in rvgen:
                pywikibot.debug('Preloading %s' % pagedata, _logger)
                try:
                    if pagedata['title'] not in cache:
                        # API always returns a "normalized" title which is
                        # usually the same as the canonical form returned by
                        # page.title(), but sometimes not (e.g.,
                        # gender-specific localizations of "User" namespace).
                        # This checks to see if there is a normalized title in
                        # the response that corresponds to the canonical form
                        # used in the query.
                        for key in cache:
                            if self.sametitle(key, pagedata['title']):
                                cache[pagedata['title']] = cache[key]
                                break
                        else:
                            pywikibot.warning(
                                'preloadpages: Query returned unexpected '
                                "title '%s'" % pagedata['title'])
                            continue
                except KeyError:
                    pywikibot.debug("No 'title' in %s" % pagedata, _logger)
                    pywikibot.debug('pageids=%s' % pageids, _logger)
                    pywikibot.debug('titles=%s' % list(cache.keys()), _logger)
                    continue
                priority, page = cache[pagedata['title']]
                api.update_page(page, pagedata, rvgen.props)
                priority, page = heapq.heappushpop(prio_queue,
                                                   (priority, page))
                # Smallest priority matches expected one; yield.
                if priority == next_prio:
                    yield page
                    next_prio += 1
                else:
                    # Push back onto the heap.
                    heapq.heappush(prio_queue, (priority, page))

            # Empty the heap.
            while prio_queue:
                priority, page = heapq.heappop(prio_queue)
                yield page

    def validate_tokens(self, types):
        """Validate if requested tokens are acceptable.

        Valid tokens depend on mw version.
        """
        mw_ver = self.mw_version
        if mw_ver < '1.20':
            types_wiki = self._paraminfo.parameter('query+info',
                                                   'token')['type']
            types_wiki.append('patrol')
            valid_types = [token for token in types if token in types_wiki]

            # Pre 1.17, preload token was the same as the edit token.
            if mw_ver < '1.17':
                if 'patrol' in types and 'edit' not in valid_types:
                    valid_types.append('edit')

        elif mw_ver < '1.24wmf19':
            types_wiki = self._paraminfo.parameter('tokens',
                                                   'type')['type']
            valid_types = [token for token in types if token in types_wiki]
        else:
            types_wiki_old = self._paraminfo.parameter('query+info',
                                                       'token')['type']
            types_wiki_action = self._paraminfo.parameter('tokens',
                                                          'type')['type']
            types_wiki = self._paraminfo.parameter('query+tokens',
                                                   'type')['type']
            valid_types = [token for token in types if token in types_wiki]
            for token in types:
                if (token not in valid_types
                        and (token in types_wiki_old or token
                             in types_wiki_action)):
                    valid_types.append('csrf')
        return valid_types

    def get_tokens(self, types, all=False):
        """Preload one or multiple tokens.

        For all MediaWiki versions prior to 1.20, only one token can be
        retrieved at once.
        For MediaWiki versions since 1.24wmfXXX a new token
        system was introduced which reduced the amount of tokens available.
        Most of them were merged into the 'csrf' token. If the token type in
        the parameter is not known it will default to the 'csrf' token.

        The other token types available are:
         - deleteglobalaccount
         - patrol (*)
         - rollback
         - setglobalaccountstatus
         - userrights
         - watch

         (*) Patrol was added in v1.14.
             Until v1.16, the patrol token is same as the edit token.
             For v1.17-19, the patrol token must be obtained from the query
             list recentchanges.

        @see: U{https://www.mediawiki.org/wiki/API:Tokens}

        @param types: the types of token (e.g., "edit", "move", "delete");
            see API documentation for full list of types
        @type types: iterable
        @param all: load all available tokens, if None only if it can be done
            in one request.
        @type all: bool

        return: a dict with retrieved valid tokens.
        rtype: dict
        """
        def warn_handler(mod, text):
            """Filter warnings for not available tokens."""
            return re.match(
                r'Action \'\w+\' is not allowed for the current user', text)

        user_tokens = {}
        mw_ver = self.mw_version
        if mw_ver < '1.20':
            if all:
                types_wiki = self._paraminfo.parameter('query+info',
                                                       'token')['type']
                types.extend(types_wiki)
            valid_tokens = set(self.validate_tokens(types))
            # don't request patrol
            query = api.PropertyGenerator(
                'info',
                site=self,
                parameters={
                    'intoken': valid_tokens - {'patrol'},
                    'titles': 'Dummy page'})
            query.request._warning_handler = warn_handler

            for item in query:
                pywikibot.debug(UnicodeType(item), _logger)
                for tokentype in valid_tokens:
                    if (tokentype + 'token') in item:
                        user_tokens[tokentype] = item[tokentype + 'token']

            # patrol token require special handling.
            # TODO: try to catch exceptions?
            if 'patrol' in valid_tokens:
                if mw_ver < '1.17':
                    if 'edit' in user_tokens:
                        user_tokens['patrol'] = user_tokens['edit']
                else:
                    req = self._simple_request(action='query',
                                               list='recentchanges',
                                               rctoken='patrol', rclimit=1)

                    req._warning_handler = warn_handler
                    data = req.submit()

                    if 'query' in data:
                        data = data['query']
                    if 'recentchanges' in data:
                        item = data['recentchanges'][0]
                        pywikibot.debug(UnicodeType(item), _logger)
                        if 'patroltoken' in item:
                            user_tokens['patrol'] = item['patroltoken']
        else:
            if mw_ver < '1.24wmf19':
                if all is not False:
                    types_wiki = self._paraminfo.parameter('tokens',
                                                           'type')['type']
                    types.extend(types_wiki)
                req = self._simple_request(action='tokens',
                                           type=self.validate_tokens(types))
            else:
                if all is not False:
                    types_wiki = self._paraminfo.parameter('query+tokens',
                                                           'type')['type']
                    types.extend(types_wiki)

                req = self._simple_request(action='query', meta='tokens',
                                           type=self.validate_tokens(types))

            req._warning_handler = warn_handler
            data = req.submit()

            if 'query' in data:
                data = data['query']

            if 'tokens' in data and data['tokens']:
                user_tokens = {key[:-5]: val
                               for key, val in data['tokens'].items()
                               if val != '+\\'}

        return user_tokens

    @deprecated("the 'tokens' property", since='20140613')
    def token(self, page, tokentype):
        """Return token retrieved from wiki to allow changing page content.

        @param page: the Page for which a token should be retrieved
        @param tokentype: the type of token (e.g., "edit", "move", "delete");
            see API documentation for full list of types
        """
        return self.tokens[tokentype]

    @deprecated("the 'tokens' property", since='20150218')
    @remove_last_args(['sysop'])
    def getToken(self, getalways=True, getagain=False):
        """DEPRECATED: Get edit token."""
        if self.username() != self.user():
            raise ValueError('The token for {0} was requested but only the '
                             'token for {1} can be retrieved.'.format(
                                 self.username(), self.user()))
        if not getalways:
            raise ValueError('In pywikibot/core getToken does not support the '
                             'getalways parameter.')
        token = self.validate_tokens(['edit'])[0]
        if getagain and token in self.tokens:
            # invalidate token
            del self.tokens._tokens[self.user()][token]
        return self.tokens[token]

    @deprecated("the 'tokens' property", since='20150218')
    @remove_last_args(['sysop'])
    def getPatrolToken(self):
        """DEPRECATED: Get patrol token."""
        if self.username() != self.user():
            raise ValueError('The token for {0} was requested but only the '
                             'token for {1} can be retrieved.'.format(
                                 self.username(), self.user()))
        return self.tokens['patrol']

    # following group of methods map more-or-less directly to API queries

    @deprecated_args(
        followRedirects='follow_redirects', filterRedirects='filter_redirects')
    def pagebacklinks(
        self, page, follow_redirects=False, filter_redirects=None,
        namespaces=None, total=None, content=False
    ):
        """Iterate all pages that link to the given page.

        @see: U{https://www.mediawiki.org/wiki/API:Backlinks}

        @param page: The Page to get links to.
        @param follow_redirects: Also return links to redirects pointing to
            the given page.
        @param filter_redirects: If True, only return redirects to the given
            page. If False, only return non-redirect links. If None, return
            both (no filtering).
        @param namespaces: If present, only return links from the namespaces
            in this list.
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param total: Maximum number of pages to retrieve in total.
        @param content: if True, load the current content of each iterated page
            (default False)
        @rtype: typing.Iterable[pywikibot.Page]
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        bltitle = page.title(with_section=False).encode(self.encoding())
        blargs = {'gbltitle': bltitle}
        if filter_redirects is not None:
            blargs['gblfilterredir'] = ('redirects' if filter_redirects
                                        else 'nonredirects')
        blgen = self._generator(api.PageGenerator, type_arg='backlinks',
                                namespaces=namespaces, total=total,
                                g_content=content, **blargs)
        if follow_redirects:
            # links identified by MediaWiki as redirects may not really be,
            # so we have to check each "redirect" page and see if it
            # really redirects to this page
            # see fixed MediaWiki bug T9304
            redirgen = self._generator(api.PageGenerator,
                                       type_arg='backlinks',
                                       gbltitle=bltitle,
                                       gblfilterredir='redirects')
            genlist = {None: blgen}
            for redir in redirgen:
                if redir == page:
                    # if a wiki contains pages whose titles contain
                    # namespace aliases that existed before those aliases
                    # were defined (example: [[WP:Sandbox]] existed as a
                    # redirect to [[Wikipedia:Sandbox]] before the WP: alias
                    # was created) they can be returned as redirects to
                    # themselves; skip these
                    continue
                if redir.getRedirectTarget() == page:
                    genlist[redir.title()] = self.pagebacklinks(
                        redir, follow_redirects=True,
                        filter_redirects=filter_redirects,
                        namespaces=namespaces,
                        content=content
                    )
            return itertools.chain(*list(genlist.values()))
        return blgen

    @deprecated_args(step=None, filterRedirects='filter_redirects')
    def page_embeddedin(self, page, filter_redirects=None, namespaces=None,
                        total=None, content=False):
        """Iterate all pages that embedded the given page as a template.

        @see: U{https://www.mediawiki.org/wiki/API:Embeddedin}

        @param page: The Page to get inclusions for.
        @param filter_redirects: If True, only return redirects that embed
            the given page. If False, only return non-redirect links. If
            None, return both (no filtering).
        @param namespaces: If present, only return links from the namespaces
            in this list.
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param content: if True, load the current content of each iterated page
            (default False)
        @rtype: typing.Iterable[pywikibot.Page]
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        eiargs = {'geititle':
                  page.title(with_section=False).encode(self.encoding())}
        if filter_redirects is not None:
            eiargs['geifilterredir'] = ('redirects' if filter_redirects
                                        else 'nonredirects')
        return self._generator(api.PageGenerator, type_arg='embeddedin',
                               namespaces=namespaces, total=total,
                               g_content=content, **eiargs)

    @deprecated_args(
        step=None, followRedirects='follow_redirects',
        filterRedirects='filter_redirects',
        onlyTemplateInclusion='only_template_inclusion',
        withTemplateInclusion='with_template_inclusion')
    def pagereferences(
        self, page, follow_redirects=False, filter_redirects=None,
        with_template_inclusion=True, only_template_inclusion=False,
        namespaces=None, total=None, content=False
    ):
        """
        Convenience method combining pagebacklinks and page_embeddedin.

        @param namespaces: If present, only return links from the namespaces
            in this list.
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @rtype: typing.Iterable[pywikibot.Page]
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if only_template_inclusion:
            return self.page_embeddedin(page, filter_redirects, namespaces,
                                        total=total, content=content)
        if not with_template_inclusion:
            return self.pagebacklinks(page, follow_redirects, filter_redirects,
                                      namespaces, total=total, content=content)
        return itertools.islice(
            itertools.chain(
                self.pagebacklinks(
                    page, follow_redirects, filter_redirects,
                    namespaces=namespaces, content=content),
                self.page_embeddedin(
                    page, filter_redirects, namespaces=namespaces,
                    content=content)
            ), total)

    @deprecated_args(step=None)
    def pagelinks(self, page, namespaces=None, follow_redirects=False,
                  total=None, content=False):
        """Iterate internal wikilinks contained (or transcluded) on page.

        @see: U{https://www.mediawiki.org/wiki/API:Links}

        @param namespaces: Only iterate pages in these namespaces
            (default: all)
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param follow_redirects: if True, yields the target of any redirects,
            rather than the redirect page
        @param content: if True, load the current content of each iterated page
            (default False)
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        plargs = {}
        if hasattr(page, '_pageid'):
            plargs['pageids'] = str(page._pageid)
        else:
            pltitle = page.title(with_section=False).encode(self.encoding())
            plargs['titles'] = pltitle
        return self._generator(api.PageGenerator, type_arg='links',
                               namespaces=namespaces, total=total,
                               g_content=content, redirects=follow_redirects,
                               **plargs)

    # Sortkey doesn't work with generator
    @deprecated_args(withSortKey=None, step=None)
    def pagecategories(self, page, total=None, content=False):
        """Iterate categories to which page belongs.

        @see: U{https://www.mediawiki.org/wiki/API:Categories}

        @param content: if True, load the current content of each iterated page
            (default False); note that this means the contents of the
            category description page, not the pages contained in the category
        """
        clargs = {}
        if hasattr(page, '_pageid'):
            clargs['pageids'] = str(page._pageid)
        else:
            clargs['titles'] = page.title(
                with_section=False).encode(self.encoding())
        return self._generator(api.PageGenerator,
                               type_arg='categories', total=total,
                               g_content=content, **clargs)

    @deprecated_args(step=None)
    def pageimages(self, page, total=None, content=False):
        """Iterate images used (not just linked) on the page.

        @see: U{https://www.mediawiki.org/wiki/API:Images}

        @param content: if True, load the current content of each iterated page
            (default False); note that this means the content of the image
            description page, not the image itself

        """
        imtitle = page.title(with_section=False).encode(self.encoding())
        return self._generator(api.PageGenerator, type_arg='images',
                               titles=imtitle, total=total,
                               g_content=content)

    @deprecated_args(step=None)
    def pagetemplates(self, page, namespaces=None, total=None, content=False):
        """Iterate templates transcluded (not just linked) on the page.

        @see: U{https://www.mediawiki.org/wiki/API:Templates}

        @param namespaces: Only iterate pages in these namespaces
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param content: if True, load the current content of each iterated page
            (default False)

        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        tltitle = page.title(with_section=False).encode(self.encoding())
        return self._generator(api.PageGenerator, type_arg='templates',
                               titles=tltitle, namespaces=namespaces,
                               total=total, g_content=content)

    @deprecated_args(step=None)
    def categorymembers(self, category, namespaces=None, sortby=None,
                        reverse=False, starttime=None, endtime=None,
                        startsort=None, endsort=None, total=None,
                        content=False, member_type=None,
                        startprefix=None, endprefix=None,
                        ):
        """Iterate members of specified category.

        @see: U{https://www.mediawiki.org/wiki/API:Categorymembers}

        @param category: The Category to iterate.
        @param namespaces: If present, only return category members from
            these namespaces. To yield subcategories or files, use
            parameter member_type instead.
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param sortby: determines the order in which results are generated,
            valid values are "sortkey" (default, results ordered by category
            sort key) or "timestamp" (results ordered by time page was
            added to the category)
        @type sortby: str
        @param reverse: if True, generate results in reverse order
            (default False)
        @param starttime: if provided, only generate pages added after this
            time; not valid unless sortby="timestamp"
        @type starttime: pywikibot.Timestamp
        @param endtime: if provided, only generate pages added before this
            time; not valid unless sortby="timestamp"
        @param startsort: if provided, only generate pages that have a
            sortkey >= startsort; not valid if sortby="timestamp"
            (Deprecated in MW 1.24)
        @type startsort: str
        @param endsort: if provided, only generate pages that have a
            sortkey <= endsort; not valid if sortby="timestamp"
            (Deprecated in MW 1.24)
        @type endsort: str
        @param startprefix: if provided, only generate pages >= this title
            lexically; not valid if sortby="timestamp"; overrides "startsort"
            (requires MW 1.18+)
        @type startprefix: str
        @param endprefix: if provided, only generate pages < this title
            lexically; not valid if sortby="timestamp"; overrides "endsort"
            (requires MW 1.18+)
        @type endprefix: str
        @param content: if True, load the current content of each iterated page
            (default False)
        @type content: bool
        @param member_type: member type; if member_type includes 'page' and is
            used in conjunction with sortby="timestamp", the API may limit
            results to only pages in the first 50 namespaces.
        @type member_type: str or iterable of str;
            values: page, subcat, file

        @rtype: typing.Iterable[pywikibot.Page]
        @raises KeyError: a namespace identifier was not resolved
        @raises NotImplementedError: startprefix or endprefix parameters are
            given but site.version is less than 1.18.
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if category.namespace() != 14:
            raise Error(
                "categorymembers: non-Category page '%s' specified"
                % category.title())
        cmtitle = category.title(with_section=False).encode(self.encoding())
        cmargs = {'type_arg': 'categorymembers', 'gcmtitle': cmtitle,
                  'gcmprop': 'ids|title|sortkey'}
        if sortby in ['sortkey', 'timestamp']:
            cmargs['gcmsort'] = sortby
        elif sortby:
            raise ValueError(
                "categorymembers: invalid sortby value '%s'"
                % sortby)
        if starttime and endtime and starttime > endtime:
            raise ValueError(
                'categorymembers: starttime must be before endtime')
        if startprefix and endprefix and startprefix > endprefix:
            raise ValueError(
                'categorymembers: startprefix must be less than endprefix')
        elif startsort and endsort and startsort > endsort:
            raise ValueError(
                'categorymembers: startsort must be less than endsort')

        if isinstance(member_type, UnicodeType):
            member_type = {member_type}

        if member_type and sortby == 'timestamp':
            # Covert namespaces to a known type
            namespaces = set(self.namespaces.resolve(namespaces or []))

            if 'page' in member_type:
                excluded_namespaces = set()
                if 'file' not in member_type:
                    excluded_namespaces.add(6)
                if 'subcat' not in member_type:
                    excluded_namespaces.add(14)

                if namespaces:
                    if excluded_namespaces.intersection(namespaces):
                        raise ValueError(
                            'incompatible namespaces %r and member_type %r'
                            % (namespaces, member_type))
                    # All excluded namespaces are not present in `namespaces`.
                else:
                    # If the number of namespaces is greater than permitted by
                    # the API, it will issue a warning and use the namespaces
                    # up until the limit, which will usually be sufficient.
                    # TODO: QueryGenerator should detect when the number of
                    # namespaces requested is higher than available, and split
                    # the request into several batches.
                    excluded_namespaces.update([-1, -2])
                    namespaces = set(self.namespaces) - excluded_namespaces
            else:
                if 'file' in member_type:
                    namespaces.add(6)
                if 'subcat' in member_type:
                    namespaces.add(14)

            member_type = None

        if member_type:
            cmargs['gcmtype'] = member_type

        if reverse:
            cmargs['gcmdir'] = 'desc'
            # API wants start/end params in opposite order if using descending
            # sort; we take care of this reversal for the user
            (starttime, endtime) = (endtime, starttime)
            (startsort, endsort) = (endsort, startsort)
            (startprefix, endprefix) = (endprefix, startprefix)
        if starttime and sortby == 'timestamp':
            cmargs['gcmstart'] = starttime
        elif starttime:
            raise ValueError('categorymembers: '
                             "invalid combination of 'sortby' and 'starttime'")
        if endtime and sortby == 'timestamp':
            cmargs['gcmend'] = endtime
        elif endtime:
            raise ValueError('categorymembers: '
                             "invalid combination of 'sortby' and 'endtime'")
        if startprefix and sortby != 'timestamp':
            if self.mw_version < '1.18':
                raise NotImplementedError(
                    'categorymembers: "startprefix" requires MW 1.18+')
            cmargs['gcmstartsortkeyprefix'] = startprefix
        elif startprefix:
            raise ValueError('categorymembers: invalid combination of '
                             "'sortby' and 'startprefix'")
        elif startsort and sortby != 'timestamp':
            cmargs['gcmstartsortkey'] = startsort
        elif startsort:
            raise ValueError('categorymembers: '
                             "invalid combination of 'sortby' and 'startsort'")
        if endprefix and sortby != 'timestamp':
            if self.mw_version < '1.18':
                raise NotImplementedError(
                    'categorymembers: "endprefix" requires MW 1.18+')
            cmargs['gcmendsortkeyprefix'] = endprefix
        elif endprefix:
            raise ValueError('categorymembers: '
                             "invalid combination of 'sortby' and 'endprefix'")
        elif endsort and sortby != 'timestamp':
            cmargs['gcmendsortkey'] = endsort
        elif endsort:
            raise ValueError('categorymembers: '
                             "invalid combination of 'sortby' and 'endsort'")

        return self._generator(api.PageGenerator, namespaces=namespaces,
                               total=total, g_content=content, **cmargs)

    @deprecated_args(getText='content', sysop=None)
    def loadrevisions(self, page, content=False, revids=None,
                      startid=None, endid=None, starttime=None,
                      endtime=None, rvdir=None, user=None, excludeuser=None,
                      section=None, step=None, total=None, rollback=False):
        """Retrieve revision information and store it in page object.

        By default, retrieves the last (current) revision of the page,
        unless any of the optional parameters revids, startid, endid,
        starttime, endtime, rvdir, user, excludeuser, or limit are
        specified. Unless noted below, all parameters not specified
        default to False.

        If rvdir is False or not specified, startid must be greater than
        endid if both are specified; likewise, starttime must be greater
        than endtime. If rvdir is True, these relationships are reversed.

        @see: U{https://www.mediawiki.org/wiki/API:Revisions}

        @param page: retrieve revisions of this Page and hold the data.
        @type page: pywikibot.Page
        @param content: if True, retrieve the wiki-text of each revision;
            otherwise, only retrieve the revision metadata (default)
        @type content: bool
        @param section: if specified, retrieve only this section of the text
            (content must be True); section must be given by number (top of
            the article is section 0), not name
        @type section: int
        @param revids: retrieve only the specified revision ids (raise
            Exception if any of revids does not correspond to page)
        @type revids: an int, a str or a list of ints or strings
        @param startid: retrieve revisions starting with this revid
        @param endid: stop upon retrieving this revid
        @param starttime: retrieve revisions starting at this Timestamp
        @param endtime: stop upon reaching this Timestamp
        @param rvdir: if false, retrieve newest revisions first (default);
            if true, retrieve earliest first
        @param user: retrieve only revisions authored by this user
        @param excludeuser: retrieve all revisions not authored by this user
        @raises ValueError: invalid startid/endid or starttime/endtime values
        @raises pywikibot.Error: revids belonging to a different page
        """
        latest = (revids is None
                  and startid is None
                  and endid is None
                  and starttime is None
                  and endtime is None
                  and rvdir is None
                  and user is None
                  and excludeuser is None
                  and step is None
                  and total is None)  # if True, retrieving current revision

        # check for invalid argument combinations
        if (startid is not None or endid is not None) and \
                (starttime is not None or endtime is not None):
            raise ValueError(
                'loadrevisions: startid/endid combined with starttime/endtime')
        if starttime is not None and endtime is not None:
            if rvdir and starttime >= endtime:
                raise ValueError(
                    'loadrevisions: starttime > endtime with rvdir=True')
            if (not rvdir) and endtime >= starttime:
                raise ValueError(
                    'loadrevisions: endtime > starttime with rvdir=False')
        if startid is not None and endid is not None:
            if rvdir and startid >= endid:
                raise ValueError(
                    'loadrevisions: startid > endid with rvdir=True')
            if (not rvdir) and endid >= startid:
                raise ValueError(
                    'loadrevisions: endid > startid with rvdir=False')

        rvargs = {'type_arg': 'info|revisions'}

        rvargs['rvprop'] = ['ids', 'timestamp', 'flags', 'comment', 'user']
        if self.mw_version >= '1.21':
            rvargs['rvprop'].append('contentmodel')
        if self.mw_version >= '1.19':
            rvargs['rvprop'].append('sha1')
        if content:
            rvargs['rvprop'].append('content')
            if section is not None:
                rvargs['rvsection'] = UnicodeType(section)
        if rollback:
            rvargs['rvtoken'] = 'rollback'
        if revids is None:
            rvtitle = page.title(with_section=False).encode(self.encoding())
            rvargs['titles'] = rvtitle
        else:
            if isinstance(revids, (int, UnicodeType)):
                ids = UnicodeType(revids)
            else:
                ids = '|'.join(UnicodeType(r) for r in revids)
            rvargs['revids'] = ids

        if rvdir:
            rvargs['rvdir'] = 'newer'
        elif rvdir is not None:
            rvargs['rvdir'] = 'older'
        if startid:
            rvargs['rvstartid'] = startid
        if endid:
            rvargs['rvendid'] = endid
        if starttime:
            rvargs['rvstart'] = starttime
        if endtime:
            rvargs['rvend'] = endtime
        if user:
            rvargs['rvuser'] = user
        elif excludeuser:
            rvargs['rvexcludeuser'] = excludeuser

        # assemble API request
        rvgen = self._generator(api.PropertyGenerator, total=total, **rvargs)
        if step:
            rvgen.set_query_increment = step

        if latest or 'revids' in rvgen.request:
            rvgen.set_maximum_items(-1)  # suppress use of rvlimit parameter

        for pagedata in rvgen:
            if not self.sametitle(pagedata['title'],
                                  page.title(with_section=False)):
                raise InconsistentTitleReceived(page, pagedata['title'])
            if 'missing' in pagedata:
                raise NoPage(page)
            api.update_page(page, pagedata, rvgen.props)

    # TODO: expand support to other parameters of action=parse?
    def get_parsed_page(self, page):
        """Retrieve parsed text of the page using action=parse.

        @see: U{https://www.mediawiki.org/wiki/API:Parse}
        """
        req = self._simple_request(action='parse', page=page)
        data = req.submit()
        assert 'parse' in data, "API parse response lacks 'parse' key"
        assert 'text' in data['parse'], "API parse response lacks 'text' key"
        parsed_text = data['parse']['text']['*']
        return parsed_text

    @deprecated_args(step=None)
    def pagelanglinks(self, page, total=None, include_obsolete=False):
        """Iterate all interlanguage links on page, yielding Link objects.

        @see: U{https://www.mediawiki.org/wiki/API:Langlinks}

        @param include_obsolete: if true, yield even Link objects whose
                                 site is obsolete
        """
        lltitle = page.title(with_section=False)
        llquery = self._generator(api.PropertyGenerator,
                                  type_arg='langlinks',
                                  titles=lltitle.encode(self.encoding()),
                                  total=total)
        for pageitem in llquery:
            if not self.sametitle(pageitem['title'], lltitle):
                raise InconsistentTitleReceived(page, pageitem['title'])
            if 'langlinks' not in pageitem:
                continue
            for linkdata in pageitem['langlinks']:
                link = pywikibot.Link.langlinkUnsafe(linkdata['lang'],
                                                     linkdata['*'],
                                                     source=self)
                if link.site.obsolete and not include_obsolete:
                    continue
                else:
                    yield link

    @deprecated_args(step=None)
    def page_extlinks(self, page, total=None):
        """Iterate all external links on page, yielding URL strings.

        @see: U{https://www.mediawiki.org/wiki/API:Extlinks}
        """
        eltitle = page.title(with_section=False)
        elquery = self._generator(api.PropertyGenerator, type_arg='extlinks',
                                  titles=eltitle.encode(self.encoding()),
                                  total=total)
        for pageitem in elquery:
            if not self.sametitle(pageitem['title'], eltitle):
                raise InconsistentTitleReceived(page, pageitem['title'])
            if 'extlinks' not in pageitem:
                continue
            for linkdata in pageitem['extlinks']:
                yield linkdata['*']

    def getcategoryinfo(self, category):
        """Retrieve data on contents of category.

        @see: U{https://www.mediawiki.org/wiki/API:Categoryinfo}
        """
        cititle = category.title(with_section=False)
        ciquery = self._generator(api.PropertyGenerator,
                                  type_arg='categoryinfo',
                                  titles=cititle.encode(self.encoding()))
        self._update_page(category, ciquery)

    def categoryinfo(self, category):
        """Retrieve data on contents of category."""
        if not hasattr(category, '_catinfo'):
            self.getcategoryinfo(category)
        if not hasattr(category, '_catinfo'):
            # a category that exists but has no contents returns no API result
            category._catinfo = {'size': 0, 'pages': 0, 'files': 0,
                                 'subcats': 0}
        return category._catinfo

    @deprecated_args(throttle=None, limit='total', step=None,
                     includeredirects='filterredir')
    def allpages(self, start='!', prefix='', namespace=0, filterredir=None,
                 filterlanglinks=None, minsize=None, maxsize=None,
                 protect_type=None, protect_level=None, reverse=False,
                 total=None, content=False):
        """Iterate pages in a single namespace.

        @see: U{https://www.mediawiki.org/wiki/API:Allpages}

        @param start: Start at this title (page need not exist).
        @param prefix: Only yield pages starting with this string.
        @param namespace: Iterate pages from this (single) namespace
        @type namespace: int or Namespace.
        @param filterredir: if True, only yield redirects; if False (and not
            None), only yield non-redirects (default: yield both)
        @param filterlanglinks: if True, only yield pages with language links;
            if False (and not None), only yield pages without language links
            (default: yield both)
        @param minsize: if present, only yield pages at least this many
            bytes in size
        @param maxsize: if present, only yield pages at most this many bytes
            in size
        @param protect_type: only yield pages that have a protection of the
            specified type
        @type protect_type: str
        @param protect_level: only yield pages that have protection at this
            level; can only be used if protect_type is specified
        @param reverse: if True, iterate in reverse Unicode lexigraphic
            order (default: iterate in forward order)
        @param content: if True, load the current content of each iterated page
            (default False)
        @raises KeyError: the namespace identifier was not resolved
        @raises TypeError: the namespace identifier has an inappropriate
            type such as bool, or an iterable with more than one namespace
        """
        # backward compatibility test
        if filterredir not in (True, False, None):
            old = filterredir
            if filterredir:
                if filterredir == 'only':
                    filterredir = True
                else:
                    filterredir = None
            else:
                filterredir = False
            warn('The value "{0!r}" for "filterredir" is deprecated; use '
                 '{1} instead.'.format(old, filterredir),
                 DeprecationWarning, 3)

        apgen = self._generator(api.PageGenerator, type_arg='allpages',
                                namespaces=namespace,
                                gapfrom=start, total=total,
                                g_content=content)
        if prefix:
            apgen.request['gapprefix'] = prefix
        if filterredir is not None:
            apgen.request['gapfilterredir'] = ('redirects' if filterredir else
                                               'nonredirects')
        if filterlanglinks is not None:
            apgen.request['gapfilterlanglinks'] = ('withlanglinks'
                                                   if filterlanglinks else
                                                   'withoutlanglinks')
        if isinstance(minsize, int):
            apgen.request['gapminsize'] = str(minsize)
        if isinstance(maxsize, int):
            apgen.request['gapmaxsize'] = str(maxsize)
        if isinstance(protect_type, UnicodeType):
            apgen.request['gapprtype'] = protect_type
            if isinstance(protect_level, UnicodeType):
                apgen.request['gapprlevel'] = protect_level
        if reverse:
            apgen.request['gapdir'] = 'descending'
        return apgen

    @deprecated('Site.allpages()', since='20090307', future_warning=True)
    def prefixindex(self, prefix, namespace=0, includeredirects=True):
        """Yield all pages with a given prefix. Deprecated.

        Use allpages() with the prefix= parameter instead of this method.
        """
        if not includeredirects:
            filterredir = False
        elif includeredirects == 'only':
            filterredir = True
        else:
            filterredir = None
        return self.allpages(prefix=prefix, namespace=namespace,
                             filterredir=filterredir)

    @deprecated_args(step=None)
    def alllinks(self, start='!', prefix='', namespace=0, unique=False,
                 fromids=False, total=None):
        """Iterate all links to pages (which need not exist) in one namespace.

        Note that, in practice, links that were found on pages that have
        been deleted may not have been removed from the links table, so this
        method can return false positives.

        @see: U{https://www.mediawiki.org/wiki/API:Alllinks}

        @param start: Start at this title (page need not exist).
        @param prefix: Only yield pages starting with this string.
        @param namespace: Iterate pages from this (single) namespace
        @type namespace: int or Namespace
        @param unique: If True, only iterate each link title once (default:
            iterate once for each linking page)
        @param fromids: if True, include the pageid of the page containing
            each link (default: False) as the '_fromid' attribute of the Page;
            cannot be combined with unique
        @raises KeyError: the namespace identifier was not resolved
        @raises TypeError: the namespace identifier has an inappropriate
            type such as bool, or an iterable with more than one namespace
        """
        if unique and fromids:
            raise Error('alllinks: unique and fromids cannot both be True.')
        algen = self._generator(api.ListGenerator, type_arg='alllinks',
                                namespaces=namespace, alfrom=start,
                                total=total, alunique=unique)
        if prefix:
            algen.request['alprefix'] = prefix
        if fromids:
            algen.request['alprop'] = 'title|ids'
        for link in algen:
            p = pywikibot.Page(self, link['title'], link['ns'])
            if fromids:
                p._fromid = link['fromid']
            yield p

    @deprecated_args(step=None)
    def allcategories(self, start='!', prefix='', total=None,
                      reverse=False, content=False):
        """Iterate categories used (which need not have a Category page).

        Iterator yields Category objects. Note that, in practice, links that
        were found on pages that have been deleted may not have been removed
        from the database table, so this method can return false positives.

        @see: U{https://www.mediawiki.org/wiki/API:Allcategories}

        @param start: Start at this category title (category need not exist).
        @param prefix: Only yield categories starting with this string.
        @param reverse: if True, iterate in reverse Unicode lexigraphic
            order (default: iterate in forward order)
        @param content: if True, load the current content of each iterated page
            (default False); note that this means the contents of the category
            description page, not the pages that are members of the category
        """
        acgen = self._generator(api.PageGenerator,
                                type_arg='allcategories', gacfrom=start,
                                total=total, g_content=content)
        if prefix:
            acgen.request['gacprefix'] = prefix
        if reverse:
            acgen.request['gacdir'] = 'descending'
        return acgen

    @deprecated('Site.allcategories()', since='20090307', future_warning=True)
    def categories(self, number=10, repeat=False):
        """DEPRECATED."""
        if repeat:
            limit = None
        else:
            limit = number
        return self.allcategories(total=limit)

    def isBot(self, username):
        """Return True is username is a bot user."""
        return username in (userdata['name'] for userdata in self.botusers())

    @deprecated_args(step=None)
    def botusers(self, total=None):
        """Iterate bot users.

        Iterated values are dicts containing 'name', 'userid', 'editcount',
        'registration', and 'groups' keys. 'groups' will be present only if
        the user is a member of at least 1 group, and will be a list of
        unicodes; all the other values are unicodes and should always be
        present.
        """
        if not hasattr(self, '_bots'):
            self._bots = {}

        if not self._bots:
            for item in self.allusers(group='bot', total=total):
                self._bots.setdefault(item['name'], item)

        for value in self._bots.values():
            yield value

    @deprecated_args(step=None)
    def allusers(self, start='!', prefix='', group=None, total=None):
        """Iterate registered users, ordered by username.

        Iterated values are dicts containing 'name', 'editcount',
        'registration', and (sometimes) 'groups' keys. 'groups' will be
        present only if the user is a member of at least 1 group, and will
        be a list of unicodes; all the other values are unicodes and should
        always be present.

        @see: U{https://www.mediawiki.org/wiki/API:Allusers}

        @param start: start at this username (name need not exist)
        @param prefix: only iterate usernames starting with this substring
        @param group: only iterate users that are members of this group
        @type group: str
        """
        augen = self._generator(api.ListGenerator, type_arg='allusers',
                                auprop='editcount|groups|registration',
                                aufrom=start, total=total)
        if prefix:
            augen.request['auprefix'] = prefix
        if group:
            augen.request['augroup'] = group
        return augen

    @deprecated_args(step=None)
    def allimages(self, start='!', prefix='', minsize=None, maxsize=None,
                  reverse=False, sha1=None, sha1base36=None,
                  total=None, content=False):
        """Iterate all images, ordered by image title.

        Yields FilePages, but these pages need not exist on the wiki.

        @see: U{https://www.mediawiki.org/wiki/API:Allimages}

        @param start: start at this title (name need not exist)
        @param prefix: only iterate titles starting with this substring
        @param minsize: only iterate images of at least this many bytes
        @param maxsize: only iterate images of no more than this many bytes
        @param reverse: if True, iterate in reverse lexigraphic order
        @param sha1: only iterate image (it is theoretically possible there
            could be more than one) with this sha1 hash
        @param sha1base36: same as sha1 but in base 36
        @param content: if True, load the current content of each iterated page
            (default False); note that this means the content of the image
            description page, not the image itself
        """
        aigen = self._generator(api.PageGenerator,
                                type_arg='allimages', gaifrom=start,
                                total=total, g_content=content)
        if prefix:
            aigen.request['gaiprefix'] = prefix
        if isinstance(minsize, int):
            aigen.request['gaiminsize'] = str(minsize)
        if isinstance(maxsize, int):
            aigen.request['gaimaxsize'] = str(maxsize)
        if reverse:
            aigen.request['gaidir'] = 'descending'
        if sha1:
            aigen.request['gaisha1'] = sha1
        if sha1base36:
            aigen.request['gaisha1base36'] = sha1base36
        return aigen

    @need_version('1.17')
    @deprecated_args(limit='total')  # ignore falimit setting
    def filearchive(self, start=None, end=None, reverse=False, total=None,
                    **kwargs):
        """Iterate archived files.

        Yields dict of file archive informations.

        @see: U{https://www.mediawiki.org/wiki/API:filearchive}

        @param start: start at this title (name need not exist)
        @param end: end at this title (name need not exist)
        @param reverse: if True, iterate in reverse lexigraphic order
        @param total: maximum number of pages to retrieve in total
        @keyword prefix: only iterate titles starting with this substring
        @keyword sha1: only iterate image with this sha1 hash
        @keyword sha1base36: same as sha1 but in base 36
        @keyword prop: Image information to get. Default is timestamp
        """
        if start and end:
            self.assert_valid_iter_params(
                'filearchive', start, end, reverse, is_ts=False)
        fagen = self._generator(api.ListGenerator,
                                type_arg='filearchive',
                                fafrom=start,
                                fato=end,
                                total=total)
        for k, v in kwargs.items():
            fagen.request['fa' + k] = v
        if reverse:
            fagen.request['fadir'] = 'descending'
        return fagen

    @deprecated_args(step=None)
    def blocks(self, starttime=None, endtime=None, reverse=False,
               blockids=None, users=None, iprange=None, total=None):
        """Iterate all current blocks, in order of creation.

        The iterator yields dicts containing keys corresponding to the
        block properties.

        @see: U{https://www.mediawiki.org/wiki/API:Blocks}

        @note: logevents only logs user blocks, while this method
            iterates all blocks including IP ranges.
        @note: C{userid} key will be given for mw 1.18+ only
        @note: C{iprange} parameter cannot be used together with C{users}.

        @param starttime: start iterating at this Timestamp
        @type starttime: pywikibot.Timestamp
        @param endtime: stop iterating at this Timestamp
        @type endtime: pywikibot.Timestamp
        @param reverse: if True, iterate oldest blocks first (default: newest)
        @type reverse: bool
        @param blockids: only iterate blocks with these id numbers. Numbers
            must be separated by '|' if given by a basestring.
        @type blockids: basestring, tuple or list
        @param users: only iterate blocks affecting these usernames or IPs
        @type users: basestring, tuple or list
        @param iprange: a single IP or an IP range. Ranges broader than
            IPv4/16 or IPv6/19 are not accepted.
        @type iprange: str
        @param total: total amount of block entries
        @type total: int
        """
        if starttime and endtime:
            self.assert_valid_iter_params('blocks', starttime, endtime,
                                          reverse)
        bkgen = self._generator(api.ListGenerator, type_arg='blocks',
                                total=total)
        bkgen.request['bkprop'] = ['id', 'user', 'by', 'timestamp', 'expiry',
                                   'reason', 'range', 'flags']
        if self.mw_version >= '1.18':
            bkgen.request['bkprop'] += ['userid']
        if starttime:
            bkgen.request['bkstart'] = starttime
        if endtime:
            bkgen.request['bkend'] = endtime
        if reverse:
            bkgen.request['bkdir'] = 'newer'
        if blockids:
            bkgen.request['bkids'] = blockids
        if users:
            if isinstance(users, UnicodeType):
                users = users.split('|')
            # actual IPv6 addresses (anonymous users) are uppercase, but they
            # have never a :: in the username (so those are registered users)
            users = [user.upper() if is_IP(user) and '::' not in user else user
                     for user in users]
            bkgen.request['bkusers'] = users
        elif iprange:
            bkgen.request['bkip'] = iprange
        return bkgen

    @deprecated_args(step=None)
    def exturlusage(self, url=None, protocol='http', namespaces=None,
                    total=None, content=False):
        """Iterate Pages that contain links to the given URL.

        @see: U{https://www.mediawiki.org/wiki/API:Exturlusage}

        @param url: The URL to search for (without the protocol prefix);
            this may include a '*' as a wildcard, only at the start of the
            hostname
        @param protocol: The protocol prefix (default: "http")

        """
        return self._generator(api.PageGenerator, type_arg='exturlusage',
                               geuquery=url, geuprotocol=protocol,
                               namespaces=namespaces,
                               total=total, g_content=content)

    @deprecated_args(step=None)
    def imageusage(self, image, namespaces=None, filterredir=None,
                   total=None, content=False):
        """Iterate Pages that contain links to the given FilePage.

        @see: U{https://www.mediawiki.org/wiki/API:Imageusage}

        @param image: the image to search for (FilePage need not exist on
            the wiki)
        @type image: pywikibot.FilePage
        @param namespaces: If present, only iterate pages in these namespaces
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param filterredir: if True, only yield redirects; if False (and not
            None), only yield non-redirects (default: yield both)
        @param content: if True, load the current content of each iterated page
            (default False)
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        iuargs = {'giutitle': image.title(with_section=False)}
        if filterredir is not None:
            iuargs['giufilterredir'] = ('redirects' if filterredir else
                                        'nonredirects')
        return self._generator(api.PageGenerator, type_arg='imageusage',
                               namespaces=namespaces,
                               total=total, g_content=content, **iuargs)

    @property
    def logtypes(self):
        """Return a set of log types available on current site."""
        return set(filter(None, self._paraminfo.parameter(
            'query+logevents', 'type')['type']))

    @deprecated_args(step=None)
    def logevents(self, logtype=None, user=None, page=None, namespace=None,
                  start=None, end=None, reverse=False, tag=None, total=None):
        """Iterate all log entries.

        @see: U{https://www.mediawiki.org/wiki/API:Logevents}

        @note: logevents with logtype='block' only logs user blocks whereas
            site.blocks iterates all blocks including IP ranges.

        @param logtype: only iterate entries of this type
            (see mediawiki api documentation for available types)
        @type logtype: basestring
        @param user: only iterate entries that match this user name
        @type user: basestring
        @param page: only iterate entries affecting this page
        @type page: pywikibot.page.Page or basestring
        @param namespace: namespace(s) to retrieve logevents from
        @type namespace: int or Namespace or an iterable of them
        @note: due to an API limitation, if namespace param contains multiple
            namespaces, log entries from all namespaces will be fetched from
            the API and will be filtered later during iteration.
        @param start: only iterate entries from and after this Timestamp
        @type start: Timestamp or ISO date string
        @param end: only iterate entries up to and through this Timestamp
        @type end: Timestamp or ISO date string
        @param reverse: if True, iterate oldest entries first (default: newest)
        @type reverse: bool
        @param tag: only iterate entries tagged with this tag
        @type tag: basestring
        @param total: maximum number of events to iterate
        @type total: int
        @rtype: iterable

        @raises KeyError: the namespace identifier was not resolved
        @raises TypeError: the namespace identifier has an inappropriate
            type such as bool, or an iterable with more than one namespace
        """
        if start and end:
            self.assert_valid_iter_params('logevents', start, end, reverse)

        legen = self._generator(api.LogEntryListGenerator, type_arg=logtype,
                                total=total)
        if logtype is not None:
            legen.request['letype'] = logtype
        if user is not None:
            legen.request['leuser'] = user
        if page is not None:
            legen.request['letitle'] = page
        if start is not None:
            legen.request['lestart'] = start
        if end is not None:
            legen.request['leend'] = end
        if reverse:
            legen.request['ledir'] = 'newer'
        if namespace is not None:
            legen.set_namespace(namespace)
        if tag:
            # Supported in version 1.16+; earlier sites will cause APIError
            legen.request['letag'] = tag

        return legen

    @deprecated('APISite.logevents()', since='20141225')
    @deprecated_args(repeat=None)
    def logpages(self, number=50, mode=None, title=None, user=None,
                 namespace=None, start=None, end=None, tag=None, newer=False,
                 dump=False, offset=None):
        """
        Iterate log pages. DEPRECATED.

        When dump is enabled, the raw API dict is returned.

        @rtype: tuple of Page, str, int, str
        """
        if offset:
            assert not start
            assert isinstance(offset, int)
            offset = datetime.timedelta(hours=offset)
            start = pywikibot.Timestamp.utcnow() - offset

        gen = self.logevents(logtype=mode, page=title, tag=tag,
                             user=user, namespace=namespace,
                             start=start, end=end, reverse=newer,
                             total=number)

        for entry in gen:
            if dump:
                yield entry.data
            else:
                yield (entry.page(),
                       entry.user(),
                       int(entry.timestamp().totimestampformat()),
                       entry.comment())

    @deprecated_args(returndict=None, nobots=None, rcshow=None, rcprop=None,
                     rctype='changetype', revision=None, repeat=None,
                     rcstart='start', rcend='end', rcdir=None, step=None,
                     includeredirects='redirect', namespace='namespaces',
                     rcnamespace='namespaces', number='total', rclimit='total',
                     showMinor='minor', showBot='bot', showAnon='anon',
                     showRedirects='redirect', showPatrolled='patrolled',
                     topOnly='top_only')
    def recentchanges(self, start=None, end=None, reverse=False,
                      namespaces=None, pagelist=None, changetype=None,
                      minor=None, bot=None, anon=None,
                      redirect=None, patrolled=None, top_only=False,
                      total=None, user=None, excludeuser=None, tag=None):
        """Iterate recent changes.

        @see: U{https://www.mediawiki.org/wiki/API:RecentChanges}

        @param start: Timestamp to start listing from
        @type start: pywikibot.Timestamp
        @param end: Timestamp to end listing at
        @type end: pywikibot.Timestamp
        @param reverse: if True, start with oldest changes (default: newest)
        @type reverse: bool
        @param namespaces: only iterate pages in these namespaces
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param pagelist: iterate changes to pages in this list only
        @param pagelist: list of Pages
        @param changetype: only iterate changes of this type ("edit" for
            edits to existing pages, "new" for new pages, "log" for log
            entries)
        @type changetype: basestring
        @param minor: if True, only list minor edits; if False, only list
            non-minor edits; if None, list all
        @type minor: bool or None
        @param bot: if True, only list bot edits; if False, only list
            non-bot edits; if None, list all
        @type bot: bool or None
        @param anon: if True, only list anon edits; if False, only list
            non-anon edits; if None, list all
        @type anon: bool or None
        @param redirect: if True, only list edits to redirect pages; if
            False, only list edits to non-redirect pages; if None, list all
        @type redirect: bool or None
        @param patrolled: if True, only list patrolled edits; if False,
            only list non-patrolled edits; if None, list all
        @type patrolled: bool or None
        @param top_only: if True, only list changes that are the latest
            revision (default False)
        @type top_only: bool
        @param user: if not None, only list edits by this user or users
        @type user: basestring|list
        @param excludeuser: if not None, exclude edits by this user or users
        @type excludeuser: basestring|list
        @param tag: a recent changes tag
        @type tag: str
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if start and end:
            self.assert_valid_iter_params('recentchanges', start, end, reverse)

        rcgen = self._generator(api.ListGenerator, type_arg='recentchanges',
                                rcprop='user|comment|timestamp|title|ids'
                                       '|sizes|redirect|loginfo|flags|tags',
                                namespaces=namespaces,
                                total=total, rctoponly=top_only)
        if start is not None:
            rcgen.request['rcstart'] = start
        if end is not None:
            rcgen.request['rcend'] = end
        if reverse:
            rcgen.request['rcdir'] = 'newer'
        if pagelist:
            if self.mw_version > '1.14':
                pywikibot.warning(
                    'recentchanges: pagelist option is disabled; ignoring.')
            else:
                rcgen.request['rctitles'] = (p.title(with_section=False)
                                             for p in pagelist)
        if changetype:
            rcgen.request['rctype'] = changetype
        filters = {'minor': minor,
                   'bot': bot,
                   'anon': anon,
                   'redirect': redirect,
                   }
        if patrolled is not None and (
                self.has_right('patrol') or self.has_right('patrolmarks')):
            rcgen.request['rcprop'] += ['patrolled']
            filters['patrolled'] = patrolled
        rcgen.request['rcshow'] = api.OptionSet(self, 'recentchanges', 'show',
                                                filters)

        if user:
            rcgen.request['rcuser'] = user

        if excludeuser:
            rcgen.request['rcexcludeuser'] = excludeuser
        rcgen.request['rctag'] = tag
        return rcgen

    @deprecated_args(number='total', step=None, key='searchstring',
                     getredirects='get_redirects')
    def search(self, searchstring, namespaces=None, where='text',
               get_redirects=False, total=None, content=False):
        """Iterate Pages that contain the searchstring.

        Note that this may include non-existing Pages if the wiki's database
        table contains outdated entries.

        @see: U{https://www.mediawiki.org/wiki/API:Search}

        @param searchstring: the text to search for
        @type searchstring: str
        @param where: Where to search; value must be "text", "title" or
            "nearmatch" (many wikis do not support title or nearmatch search)
        @param namespaces: search only in these namespaces (defaults to all)
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param get_redirects: if True, include redirects in results. Since
            version MediaWiki 1.23 it will always return redirects.
        @param content: if True, load the current content of each iterated page
            (default False)
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        where_types = ['text', 'title', 'titles']
        if self.mw_version >= '1.17':
            where_types.append('nearmatch')
        if not searchstring:
            raise Error('search: searchstring cannot be empty')
        if where not in where_types:
            raise Error("search: unrecognized 'where' value: %s" % where)
        if where in ('title', 'titles'):
            if self.has_extension('CirrusSearch'):
                # 'title' search was disabled, use intitle instead
                searchstring = 'intitle:' + searchstring
                issue_deprecation_warning(
                    "where='{0}'".format(where),
                    "searchstring='{0}'".format(searchstring),
                    since='20160224')
                where = None  # default
            else:
                if where == 'titles':
                    issue_deprecation_warning("where='titles'",
                                              "where='title'",
                                              since='20160224')
                where = 'title'
        if not namespaces and namespaces != 0:
            namespaces = [ns_id for ns_id in self.namespaces if ns_id >= 0]
        srgen = self._generator(api.PageGenerator, type_arg='search',
                                gsrsearch=searchstring, gsrwhat=where,
                                namespaces=namespaces,
                                total=total, g_content=content)
        if self.mw_version < '1.23':
            srgen.request['gsrredirects'] = get_redirects
        return srgen

    @deprecated_args(step=None, showMinor='minor')
    def usercontribs(self, user=None, userprefix=None, start=None, end=None,
                     reverse=False, namespaces=None, minor=None,
                     total=None, top_only=False):
        """Iterate contributions by a particular user.

        Iterated values are in the same format as recentchanges.

        @see: U{https://www.mediawiki.org/wiki/API:Usercontribs}

        @param user: Iterate contributions by this user (name or IP)
        @param userprefix: Iterate contributions by all users whose names
            or IPs start with this substring
        @param start: Iterate contributions starting at this Timestamp
        @param end: Iterate contributions ending at this Timestamp
        @param reverse: Iterate oldest contributions first (default: newest)
        @param namespaces: only iterate pages in these namespaces
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param minor: if True, iterate only minor edits; if False and
            not None, iterate only non-minor edits (default: iterate both)
        @param total: limit result to this number of pages
        @type total: int
        @param top_only: if True, iterate only edits which are the latest
            revision (default: False)
        @raises pywikibot.exceptions.Error: either user or userprefix must be
            non-empty
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if not (user or userprefix):
            raise Error(
                'usercontribs: either user or userprefix must be non-empty')

        if start and end:
            self.assert_valid_iter_params('usercontribs', start, end, reverse)

        ucgen = self._generator(api.ListGenerator, type_arg='usercontribs',
                                ucprop='ids|title|timestamp|comment|flags',
                                namespaces=namespaces,
                                total=total, uctoponly=top_only)
        if user:
            ucgen.request['ucuser'] = user
        if userprefix:
            ucgen.request['ucuserprefix'] = userprefix
        if start is not None:
            ucgen.request['ucstart'] = str(start)
        if end is not None:
            ucgen.request['ucend'] = str(end)
        if reverse:
            ucgen.request['ucdir'] = 'newer'
        option_set = api.OptionSet(self, 'usercontribs', 'show')
        option_set['minor'] = minor
        ucgen.request['ucshow'] = option_set
        return ucgen

    @deprecated_args(step=None, showMinor='minor', showAnon='anon',
                     showBot='bot')
    def watchlist_revs(self, start=None, end=None, reverse=False,
                       namespaces=None, minor=None, bot=None,
                       anon=None, total=None):
        """Iterate revisions to pages on the bot user's watchlist.

        Iterated values will be in same format as recentchanges.

        @see: U{https://www.mediawiki.org/wiki/API:Watchlist}

        @param start: Iterate revisions starting at this Timestamp
        @param end: Iterate revisions ending at this Timestamp
        @param reverse: Iterate oldest revisions first (default: newest)
        @param namespaces: only iterate pages in these namespaces
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param minor: if True, only list minor edits; if False (and not
            None), only list non-minor edits
        @param bot: if True, only list bot edits; if False (and not
            None), only list non-bot edits
        @param anon: if True, only list anon edits; if False (and not
            None), only list non-anon edits
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if start and end:
            self.assert_valid_iter_params(
                'watchlist_revs', start, end, reverse)

        wlgen = self._generator(
            api.ListGenerator, type_arg='watchlist',
            wlprop='user|comment|timestamp|title|ids|flags',
            wlallrev='', namespaces=namespaces, total=total)
        # TODO: allow users to ask for "patrol" as well?
        if start is not None:
            wlgen.request['wlstart'] = start
        if end is not None:
            wlgen.request['wlend'] = end
        if reverse:
            wlgen.request['wldir'] = 'newer'
        filters = {'minor': minor, 'bot': bot, 'anon': anon}
        wlgen.request['wlshow'] = api.OptionSet(self, 'watchlist', 'show',
                                                filters)
        return wlgen

    @deprecated_args(step=None, get_text='content', page='titles',
                     limit='total')
    def deletedrevs(self, titles=None, start=None, end=None, reverse=False,
                    content=False, total=None, **kwargs):
        """Iterate deleted revisions.

        Each value returned by the iterator will be a dict containing the
        'title' and 'ns' keys for a particular Page and a 'revisions' key
        whose value is a list of revisions in the same format as
        recentchanges plus a 'content' element with key '*' if requested
        when 'content' parameter is set. For older wikis a 'token' key is
        also given with the content request.

        @see: U{https://www.mediawiki.org/wiki/API:Deletedrevisions}

        @param titles: The page titles to check for deleted revisions
        @type titles: str (multiple titles delimited with '|')
            or pywikibot.Page or typing.Iterable[pywikibot.Page]
            or typing.Iterable[str]
        @keyword revids: Get revisions by their ID

        @note either titles or revids must be set but not both

        @param start: Iterate revisions starting at this Timestamp
        @param end: Iterate revisions ending at this Timestamp
        @param reverse: Iterate oldest revisions first (default: newest)
        @type reverse: bool
        @param content: If True, retrieve the content of each revision
        @param total: number of revisions to retrieve
        @keyword user: List revisions by this user
        @keyword excludeuser: Exclude revisions by this user
        @keyword tag: Only list revision tagged with this tag
        @keyword prop: Which properties to get. Defaults are ids, user,
            comment, flags and timestamp
        """
        def handle_props(props):
            """Translate deletedrev props to deletedrevisions props."""
            if isinstance(props, UnicodeType):
                props = props.split('|')
            if self.mw_version >= '1.25':
                return props

            old_props = []
            for item in props:
                if item == 'ids':
                    old_props += ['revid', 'parentid']
                elif item == 'flags':
                    old_props.append('minor')
                elif item == 'timestamp':
                    pass
                else:
                    old_props.append(item)
                    if item == 'content' and self.mw_version < '1.24':
                        old_props.append('token')
            return old_props

        if start and end:
            self.assert_valid_iter_params('deletedrevs', start, end, reverse)

        if not self.logged_in():
            self.login()

        err = ('deletedrevs: User:{} not authorized to '
               .format(self.user()))
        if not self.has_right('deletedhistory'):
            raise Error(err + 'access deleted revisions.')
        if content:
            if not self.has_right('undelete'):
                raise Error(err + 'view deleted content.')

        revids = kwargs.pop('revids', None)
        if not (bool(titles) ^ (revids is not None)):
            raise Error('deletedrevs: either "titles" or "revids" parameter '
                        'must be given.')
        if revids and self.mw_version < '1.25':
            raise NotImplementedError(
                'deletedrevs: "revid" is not implemented with MediaWiki {}'
                .format(self.mw_version))

        if self.mw_version >= '1.25':
            pre = 'drv'
            type_arg = 'deletedrevisions'
            generator = api.PropertyGenerator
        else:
            pre = 'dr'
            type_arg = 'deletedrevs'
            generator = api.ListGenerator

        gen = self._generator(generator, type_arg=type_arg,
                              titles=titles, revids=revids,
                              total=total)

        gen.request[pre + 'start'] = start
        gen.request[pre + 'end'] = end

        # handle properties
        prop = kwargs.pop('prop',
                          ['ids', 'user', 'comment', 'flags', 'timestamp'])
        if content:
            prop.append('content')
        prop = handle_props(prop)
        gen.request[pre + 'prop'] = prop

        # handle other parameters like user
        for k, v in kwargs.items():
            gen.request[pre + k] = v

        if reverse:
            gen.request[pre + 'dir'] = 'newer'

        if self.mw_version < '1.25':
            # yield from gen
            for data in gen:
                yield data
        else:
            # The dict result is different for both generators
            for data in gen:
                try:
                    data['revisions'] = data.pop('deletedrevisions')
                except KeyError:
                    pass
                else:
                    yield data

    def users(self, usernames):
        """Iterate info about a list of users by name or IP.

        @see: U{https://www.mediawiki.org/wiki/API:Users}

        @param usernames: a list of user names
        @type usernames: list, or other iterable, of unicodes
        """
        usprop = ['blockinfo', 'groups', 'editcount', 'registration',
                  'emailable']
        if self.mw_version >= '1.16':
            usprop.append('gender')
        if self.mw_version >= '1.17':
            usprop.append('rights')
        usgen = api.ListGenerator(
            'users', site=self, parameters={
                'ususers': usernames, 'usprop': usprop})
        return usgen

    @deprecated('Site.randompages(total=1)', since='20130828')
    def randompage(self, redirect=False):
        """
        DEPRECATED.

        @param redirect: Return a random redirect page
        @rtype: pywikibot.Page
        """
        return self.randompages(total=1, redirects=redirect)

    @deprecated('Site.randompages(total=1, redirects=True)', since='20130828')
    def randomredirectpage(self):
        """
        DEPRECATED: Use Site.randompages() instead.

        @return: Return a random redirect page
        """
        return self.randompages(total=1, redirects=True)

    @deprecated_args(step=None)
    def randompages(self, total=None, namespaces=None,
                    redirects=False, content=False):
        """Iterate a number of random pages.

        @see: U{https://www.mediawiki.org/wiki/API:Random}

        Pages are listed in a fixed sequence, only the starting point is
        random.

        @param total: the maximum number of pages to iterate
        @param namespaces: only iterate pages in these namespaces.
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @param redirects: if True, include only redirect pages in results,
            False does not include redirects and None (MW 1.26+) include both
            types. (default: False)
        @type redirects: bool or None
        @param content: if True, load the current content of each iterated page
            (default False)
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        @raises AssertError: unsupported redirects parameter
        """
        mapping = {False: None, True: 'redirects', None: 'all'}
        assert redirects in mapping
        redirects = mapping[redirects]
        params = {}
        if redirects is not None:
            if self.mw_version < '1.26':
                if redirects == 'all':
                    warn("parameter redirects=None to retrieve 'all' random"
                         'page types is not supported by mw version {0}. '
                         'Using default.'.format(self.mw_version),
                         UserWarning)
                params['grnredirect'] = redirects == 'redirects'
            else:
                params['grnfilterredir'] = redirects
        return self._generator(api.PageGenerator, type_arg='random',
                               namespaces=namespaces, total=total,
                               g_content=content, **params)

    # Catalog of editpage error codes, for use in generating messages.
    # The block at the bottom are page related errors.
    _ep_errors = {
        'noapiwrite': 'API editing not enabled on %(site)s wiki',
        'writeapidenied':
            'User %(user)s is not authorized to edit on %(site)s wiki',
        'cantcreate':
            'User %(user)s not authorized to create new pages on %(site)s '
            'wiki',
        'cantcreate-anon':
            'Bot is not logged in, and anon users are not authorized to '
            'create new pages on %(site)s wiki',
        'noimageredirect-anon':
            'Bot is not logged in, and anon users are not authorized to '
            'create image redirects on %(site)s wiki',
        'noimageredirect': 'User %(user)s not authorized to create image '
                           'redirects on %(site)s wiki',
        'filtered': '%(info)s',
        'contenttoobig': '%(info)s',
        'noedit-anon': 'Bot is not logged in, and anon users are not '
                       'authorized to edit on %(site)s wiki',
        'noedit':
            'User %(user)s not authorized to edit pages on %(site)s wiki',
        'missingtitle': NoCreateError,
        'editconflict': EditConflict,
        'articleexists': PageCreatedConflict,
        'pagedeleted': PageDeletedConflict,
        'protectedpage': LockedPage,
        'protectedtitle': LockedNoPage,
        'cascadeprotected': CascadeLockedPage,
        'titleblacklist-forbidden': TitleblacklistError,
        'spamblacklist': SpamblacklistError,
    }
    _ep_text_overrides = {'appendtext', 'prependtext', 'undo'}

    @need_right('edit')
    def editpage(self, page, summary=None, minor=True, notminor=False,
                 bot=True, recreate=True, createonly=False, nocreate=False,
                 watch=None, **kwargs):
        """Submit an edit to be saved to the wiki.

        @see: U{https://www.mediawiki.org/wiki/API:Edit}

        @param page: The Page to be saved.
            By default its .text property will be used
            as the new text to be saved to the wiki
        @param summary: the edit summary
        @param minor: if True (default), mark edit as minor
        @param notminor: if True, override account preferences to mark edit
            as non-minor
        @param recreate: if True (default), create new page even if this
            title has previously been deleted
        @param createonly: if True, raise an error if this title already
            exists on the wiki
        @param nocreate: if True, raise an error if the page does not exist
        @param watch: Specify how the watchlist is affected by this edit, set
            to one of "watch", "unwatch", "preferences", "nochange":
            * watch: add the page to the watchlist
            * unwatch: remove the page from the watchlist
            The following settings are supported by mw >= 1.16 only
            * preferences: use the preference settings (default)
            * nochange: don't change the watchlist
        @param bot: if True, mark edit with bot flag
        @kwarg text: Overrides Page.text
        @type text: str
        @kwarg section: Edit an existing numbered section or
            a new section ('new')
        @type section: int or str
        @kwarg prependtext: Prepend text. Overrides Page.text
        @type text: str
        @kwarg appendtext: Append text. Overrides Page.text.
        @type text: str
        @kwarg undo: Revision id to undo. Overrides Page.text
        @type undo: int
        @return: True if edit succeeded, False if it failed
        @rtype: bool
        @raises pywikibot.exceptions.Error: No text to be saved
        @raises pywikibot.exceptions.NoPage: recreate is disabled and page does
            not exist
        @raises pywikibot.exceptions.CaptchaError: config.solve_captcha is
            False and saving the page requires solving a captcha
        """
        basetimestamp = True
        text_overrides = self._ep_text_overrides.intersection(kwargs.keys())

        if text_overrides:
            if 'text' in kwargs:
                raise ValueError('text can not be used with any of %s'
                                 % ', '.join(text_overrides))
            if len(text_overrides) > 1:
                raise ValueError('Multiple text overrides used: %s'
                                 % ', '.join(text_overrides))
            text = None
            basetimestamp = False
        elif 'text' in kwargs:
            text = kwargs.pop('text')
            if 'section' in kwargs and kwargs['section'] == 'new':
                basetimestamp = False
        elif 'section' in kwargs:
            raise ValueError('text must be used with section')
        else:
            text = page.text
            if text is None:
                raise Error('editpage: no text to be saved')

        if basetimestamp or not recreate:
            try:
                lastrev = page.latest_revision
                basetimestamp = lastrev.timestamp
            except NoPage:
                basetimestamp = False
                if not recreate:
                    raise

        token = self.tokens['edit']
        if bot is None:
            bot = self.has_right('bot')
        params = dict(action='edit', title=page,
                      text=text, token=token, summary=summary, bot=bot,
                      recreate=recreate, createonly=createonly,
                      nocreate=nocreate, minor=minor,
                      notminor=not minor and notminor,
                      **kwargs)

        if basetimestamp and 'basetimestamp' not in kwargs:
            params['basetimestamp'] = basetimestamp

        watch_items = {'watch', 'unwatch', 'preferences', 'nochange'}
        if watch in watch_items:
            if self.mw_version < '1.16':
                if watch in ['preferences', 'nochange']:
                    pywikibot.warning('The watch value {0} is not supported '
                                      'by {1}'.format(watch, self))
                else:
                    params[watch] = True
            else:
                params['watchlist'] = watch
        elif watch:
            pywikibot.warning(
                "editpage: Invalid watch value '%(watch)s' ignored."
                % {'watch': watch})
        req = self._simple_request(**params)

        self.lock_page(page)
        try:
            while True:
                try:
                    result = req.submit()
                    pywikibot.debug('editpage response: %s' % result,
                                    _logger)
                except api.APIError as err:
                    if err.code.endswith('anon') and self.logged_in():
                        pywikibot.debug(
                            "editpage: received '%s' even though bot is "
                            'logged in' % err.code,
                            _logger)
                    if err.code in self._ep_errors:
                        exception = self._ep_errors[err.code]
                        if isinstance(exception, UnicodeType):
                            errdata = {
                                'site': self,
                                'title': page.title(with_section=False),
                                'user': self.user(),
                                'info': err.info
                            }
                            raise Error(exception % errdata)
                        elif issubclass(exception, SpamblacklistError):
                            urls = ', '.join(err.other[err.code]['matches'])
                            exec_string = ('raise exception(page, url="{}")'
                                           .format(urls))
                            if not PY2:
                                exec_string += ' from None'
                            exec(exec_string)
                        else:
                            raise exception(page)
                    pywikibot.debug(
                        "editpage: Unexpected error code '%s' received."
                        % err.code,
                        _logger)
                    raise
                assert 'edit' in result and 'result' in result['edit'], result

                if result['edit']['result'] == 'Success':
                    if 'nochange' in result['edit']:
                        # null edit, page not changed
                        pywikibot.log('Page [[%s]] saved without any changes.'
                                      % page.title())
                        return True
                    page.latest_revision_id = result['edit']['newrevid']
                    # See:
                    # https://www.mediawiki.org/wiki/API:Wikimania_2006_API_discussion#Notes
                    # not safe to assume that saved text is the same as sent
                    del page.text
                    return True

                if result['edit']['result'] == 'Failure':
                    if 'captcha' in result['edit']:
                        if not pywikibot.config.solve_captcha:
                            raise CaptchaError('captcha encountered while '
                                               'config.solve_captcha is False')
                        captcha = result['edit']['captcha']
                        req['captchaid'] = captcha['id']

                        if captcha['type'] in ['math', 'simple']:
                            req['captchaword'] = input(captcha['question'])
                            continue

                        if 'url' in captcha:
                            import webbrowser
                            webbrowser.open('%s://%s%s'
                                            % (self.protocol(),
                                               self.hostname(),
                                               captcha['url']))
                            req['captchaword'] = pywikibot.input(
                                'Please view CAPTCHA in your browser, '
                                'then type answer here:')
                            continue

                        pywikibot.error(
                            'editpage: unknown CAPTCHA response %s, '
                            'page not saved'
                            % captcha)
                        return False

                    if 'spamblacklist' in result['edit']:
                        raise SpamblacklistError(
                            page, result['edit']['spamblacklist'])

                    if 'code' in result['edit'] and 'info' in result['edit']:
                        pywikibot.error(
                            'editpage: %s\n%s, '
                            % (result['edit']['code'], result['edit']['info']))
                        return False

                    pywikibot.error('editpage: unknown failure reason %s'
                                    % str(result))
                    return False

                pywikibot.error(
                    "editpage: Unknown result code '%s' received; "
                    'page not saved' % result['edit']['result'])
                pywikibot.log(str(result))
                return False

        finally:
            self.unlock_page(page)

    OnErrorExc = namedtuple('OnErrorExc', 'exception on_new_page')

    # catalog of merge history errors for use in error messages
    _mh_errors = {
        'noapiwrite': 'API editing not enabled on {site} wiki',
        'writeapidenied':
            'User {user} is not authorized to edit on {site} wiki',
        'mergehistory-fail-invalid-source': 'Source {source} is invalid '
            '(this may be caused by an invalid page ID in the database)',
        'mergehistory-fail-invalid-dest': 'Destination {dest} is invalid '
            '(this may be caused by an invalid page ID in the database)',
        'mergehistory-fail-no-change':
            'History merge did not merge any revisions; '
            'please recheck the page and timestamp parameters',
        'mergehistory-fail-permission':
            'User {user} has insufficient permissions to merge history',
        'mergehistory-fail-timestamps-overlap':
            'Source revisions from {source} overlap or come after '
            'destination revisions of {dest}'
    }

    @need_right('mergehistory')
    @need_version('1.27.0-wmf.13')
    def merge_history(self, source, dest, timestamp=None, reason=None):
        """Merge revisions from one page into another.

        @see: U{https://www.mediawiki.org/wiki/API:Mergehistory}

        Revisions dating up to the given timestamp in the source will be
        moved into the destination page history. History merge fails if
        the timestamps of source and dest revisions overlap (all source
        revisions must be dated before the earliest dest revision).

        @param source: Source page from which revisions will be merged
        @type source: pywikibot.Page
        @param dest: Destination page to which revisions will be merged
        @type dest: pywikibot.Page
        @param timestamp: Revisions from this page dating up to this timestamp
            will be merged into the destination page (if not given or False,
            all revisions will be merged)
        @type timestamp: pywikibot.Timestamp
        @param reason: Optional reason for the history merge
        @type reason: str
        """
        # Data for error messages
        errdata = {
            'site': self,
            'source': source,
            'dest': dest,
            'user': self.user(),
        }

        # Check if pages exist before continuing
        if not source.exists():
            raise NoPage(source,
                         'Cannot merge revisions from source {source} because '
                         'it does not exist on {site}'
                         .format(**errdata))
        if not dest.exists():
            raise NoPage(dest,
                         'Cannot merge revisions to destination {dest} '
                         'because it does not exist on {site}'
                         .format(**errdata))

        if source == dest:  # Same pages
            raise PageSaveRelatedError(
                'Cannot merge revisions of {source} to itself'
                .format(**errdata))

        # Send the merge API request
        token = self.tokens['csrf']
        req = self._simple_request(action='mergehistory',
                                   token=token)
        req['from'] = source
        req['to'] = dest
        if reason:
            req['reason'] = reason
        if timestamp:
            req['timestamp'] = timestamp

        self.lock_page(source)
        self.lock_page(dest)
        try:
            result = req.submit()
            pywikibot.debug('mergehistory response: {result}'
                            .format(result=result),
                            _logger)
        except api.APIError as err:
            if err.code in self._mh_errors:
                on_error = self._mh_errors[err.code]
                raise Error(on_error.format(**errdata))
            else:
                pywikibot.debug(
                    "mergehistory: Unexpected error code '{code}' received"
                    .format(code=err.code),
                    _logger
                )
                raise
        finally:
            self.unlock_page(source)
            self.unlock_page(dest)

        if 'mergehistory' not in result:
            pywikibot.error('mergehistory: {error}'.format(error=result))
            raise Error('mergehistory: unexpected response')

    # catalog of move errors for use in error messages
    _mv_errors = {
        'noapiwrite': 'API editing not enabled on %(site)s wiki',
        'writeapidenied':
            'User %(user)s is not authorized to edit on %(site)s wiki',
        'nosuppress':
            'User %(user)s is not authorized to move pages without '
            'creating redirects',
        'cantmove-anon':
            'Bot is not logged in, and anon users are not authorized to '
            'move pages on %(site)s wiki',
        'cantmove':
            'User %(user)s is not authorized to move pages on %(site)s wiki',
        'immobilenamespace':
            'Pages in %(oldnamespace)s namespace cannot be moved on %(site)s '
            'wiki',
        'articleexists': OnErrorExc(exception=ArticleExistsConflict,
                                    on_new_page=True),
        # "protectedpage" can happen in both directions.
        'protectedpage': OnErrorExc(exception=LockedPage, on_new_page=None),
        'protectedtitle': OnErrorExc(exception=LockedNoPage, on_new_page=True),
        'nonfilenamespace':
            'Cannot move a file to %(newnamespace)s namespace on %(site)s '
            'wiki',
        'filetypemismatch':
            '[[%(newtitle)s]] file extension does not match content of '
            '[[%(oldtitle)s]]',
    }

    @need_right('move')
    def movepage(self, page, newtitle, summary, movetalk=True,
                 noredirect=False):
        """Move a Page to a new title.

        @see: U{https://www.mediawiki.org/wiki/API:Move}

        @param page: the Page to be moved (must exist)
        @param newtitle: the new title for the Page
        @type newtitle: str
        @param summary: edit summary (required!)
        @param movetalk: if True (default), also move the talk page if possible
        @param noredirect: if True, suppress creation of a redirect from the
            old title to the new one
        @return: Page object with the new title
        @rtype: pywikibot.Page
        """
        oldtitle = page.title(with_section=False)
        newlink = pywikibot.Link(newtitle, self)
        newpage = pywikibot.Page(newlink)
        if newlink.namespace:
            newtitle = self.namespace(newlink.namespace) + ':' + newlink.title
        else:
            newtitle = newlink.title
        if oldtitle == newtitle:
            raise Error('Cannot move page %s to its own title.'
                        % oldtitle)
        if not page.exists():
            raise NoPage(page,
                         'Cannot move page %(page)s because it '
                         'does not exist on %(site)s.')
        token = self.tokens['move']
        self.lock_page(page)
        req = self._simple_request(action='move',
                                   noredirect=noredirect,
                                   reason=summary,
                                   movetalk=movetalk,
                                   token=token,
                                   to=newtitle)
        req['from'] = oldtitle  # "from" is a python keyword
        try:
            result = req.submit()
            pywikibot.debug('movepage response: %s' % result,
                            _logger)
        except api.APIError as err:
            if err.code.endswith('anon') and self.logged_in():
                pywikibot.debug(
                    "movepage: received '%s' even though bot is logged in"
                    % err.code,
                    _logger)
            if err.code in self._mv_errors:
                on_error = self._mv_errors[err.code]
                if hasattr(on_error, 'exception'):
                    # LockedPage can be raised both if "from" or "to" page
                    # are locked for the user.
                    # Both pages locked is not considered
                    # (a double failure has low probability)
                    if issubclass(on_error.exception, LockedPage):
                        # we assume "from" is locked unless proven otherwise
                        failed_page = page
                        if newpage.exists():
                            for prot in self.page_restrictions(
                                    newpage).values():
                                if not self.has_group(prot[0]):
                                    failed_page = newpage
                                    break
                    else:
                        failed_page = newpage if on_error.on_new_page else page
                    raise on_error.exception(failed_page)
                else:
                    errdata = {
                        'site': self,
                        'oldtitle': oldtitle,
                        'oldnamespace': self.namespace(page.namespace()),
                        'newtitle': newtitle,
                        'newnamespace': self.namespace(newlink.namespace),
                        'user': self.user(),
                    }
                    raise Error(on_error % errdata)
            pywikibot.debug("movepage: Unexpected error code '%s' received."
                            % err.code,
                            _logger)
            raise
        finally:
            self.unlock_page(page)
        if 'move' not in result:
            pywikibot.error('movepage: %s' % result)
            raise Error('movepage: unexpected response')
        # TODO: Check for talkmove-error messages
        if 'talkmove-error-code' in result['move']:
            pywikibot.warning(
                'movepage: Talk page %s not moved'
                % (page.toggleTalkPage().title(as_link=True)))
        return pywikibot.Page(page, newtitle)

    # catalog of rollback errors for use in error messages
    _rb_errors = {
        'noapiwrite': 'API editing not enabled on %(site)s wiki',
        'writeapidenied': 'User %(user)s not allowed to edit through the API',
        'alreadyrolled':
            'Page [[%(title)s]] already rolled back; action aborted.',
    }  # other errors shouldn't arise because we check for those errors

    @need_right('rollback')
    def rollbackpage(self, page, **kwargs):
        """Roll back page to version before last user's edits.

        @see: U{https://www.mediawiki.org/wiki/API:Rollback}

        The keyword arguments are those supported by the rollback API.

        As a precaution against errors, this method will fail unless
        the page history contains at least two revisions, and at least
        one that is not by the same user who made the last edit.

        @param page: the Page to be rolled back (must exist)

        """
        if len(page._revisions) < 2:
            raise Error(
                'Rollback of %s aborted; load revision history first.'
                % page.title(as_link=True))
        last_rev = page.latest_revision
        last_user = last_rev.user
        for rev in sorted(page._revisions.values(), reverse=True,
                          key=lambda r: r.timestamp):
            # start with most recent revision first
            if rev.user != last_user:
                break
        else:
            raise Error(
                'Rollback of %s aborted; only one user in revision history.'
                % page.title(as_link=True))
        parameters = merge_unique_dicts(kwargs, action='rollback',
                                        title=page,
                                        token=self.tokens['rollback'],
                                        user=last_user)
        self.lock_page(page)
        req = self._simple_request(**parameters)
        try:
            req.submit()
        except api.APIError as err:
            errdata = {
                'site': self,
                'title': page.title(with_section=False),
                'user': self.user(),
            }
            if err.code in self._rb_errors:
                raise Error(self._rb_errors[err.code] % errdata)
            pywikibot.debug("rollback: Unexpected error code '%s' received."
                            % err.code,
                            _logger)
            raise
        finally:
            self.unlock_page(page)

    # catalog of delete errors for use in error messages
    _dl_errors = {
        'noapiwrite': 'API editing not enabled on %(site)s wiki',
        'writeapidenied': 'User %(user)s not allowed to edit through the API',
        'permissiondenied': 'User %(user)s not authorized to (un)delete '
                            'pages on %(site)s wiki.',
        'cantdelete':
            'Could not delete [[%(title)s]]. Maybe it was deleted already.',
        'cantundelete': 'Could not undelete [[%(title)s]]. '
                        'Revision may not exist or was already undeleted.'
    }  # other errors shouldn't occur because of pre-submission checks

    @need_right('delete')
    @deprecate_arg('summary', 'reason')
    def deletepage(self, page, reason):
        """Delete page from the wiki. Requires appropriate privilege level.

        @see: U{https://www.mediawiki.org/wiki/API:Delete}

        @param page: Page to be deleted.
        @type page: pywikibot.page.Page
        @param reason: Deletion reason.
        @type reason: basestring

        """
        token = self.tokens['delete']
        self.lock_page(page)
        req = self._simple_request(action='delete',
                                   token=token,
                                   title=page,
                                   reason=reason)
        try:
            req.submit()
        except api.APIError as err:
            errdata = {
                'site': self,
                'title': page.title(with_section=False),
                'user': self.user(),
            }
            if err.code in self._dl_errors:
                raise Error(self._dl_errors[err.code] % errdata)
            pywikibot.debug("delete: Unexpected error code '%s' received."
                            % err.code,
                            _logger)
            raise
        else:
            page.clear_cache()
        finally:
            self.unlock_page(page)

    @need_right('undelete')
    @deprecate_arg('summary', 'reason')
    def undelete_page(self, page, reason, revisions=None):
        """Undelete page from the wiki. Requires appropriate privilege level.

        @see: U{https://www.mediawiki.org/wiki/API:Undelete}

        @param page: Page to be deleted.
        @type page: pywikibot.BasePage
        @param revisions: List of timestamps to restore.
            If None, restores all revisions.
        @type revisions: list
        @param reason: Undeletion reason.
        @type reason: basestring

        """
        token = self.tokens['delete']
        self.lock_page(page)

        req = self._simple_request(action='undelete',
                                   title=page,
                                   reason=reason,
                                   token=token,
                                   timestamps=revisions)
        try:
            req.submit()
        except api.APIError as err:
            errdata = {
                'site': self,
                'title': page.title(with_section=False),
                'user': self.user(),
            }
            if err.code in self._dl_errors:
                raise Error(self._dl_errors[err.code] % errdata)
            pywikibot.debug("delete: Unexpected error code '%s' received."
                            % err.code,
                            _logger)
            raise
        finally:
            self.unlock_page(page)

    _protect_errors = {
        'noapiwrite': 'API editing not enabled on %(site)s wiki',
        'writeapidenied': 'User %(user)s not allowed to edit through the API',
        'permissiondenied':
            'User %(user)s not authorized to protect pages on %(site)s wiki.',
        'cantedit':
            "User %(user)s can't protect this page because user %(user)s "
            "can't edit it.",
        'protect-invalidlevel': 'Invalid protection level'
    }

    def protection_types(self):
        """
        Return the protection types available on this site.

        @return: protection types available
        @rtype: set of unicode instances
        @see: L{Siteinfo._get_default()}
        """
        return set(self.siteinfo.get('restrictions')['types'])

    def protection_levels(self):
        """
        Return the protection levels available on this site.

        @return: protection types available
        @rtype: set of unicode instances
        @see: L{Siteinfo._get_default()}
        """
        # implemented in b73b5883d486db0e9278ef16733551f28d9e096d
        return set(self.siteinfo.get('restrictions')['levels'])

    @need_right('protect')
    @deprecate_arg('summary', 'reason')
    def protect(self, page, protections, reason, expiry=None, **kwargs):
        """(Un)protect a wiki page. Requires administrator status.

        @see: U{https://www.mediawiki.org/wiki/API:Protect}

        @param protections: A dict mapping type of protection to protection
            level of that type. Valid types of protection are 'edit', 'move',
            'create', and 'upload'. Valid protection levels (in MediaWiki 1.12)
            are '' (equivalent to 'none'), 'autoconfirmed', and 'sysop'.
            If None is given, however, that protection will be skipped.
        @type protections: dict
        @param reason: Reason for the action
        @type reason: basestring
        @param expiry: When the block should expire. This expiry will be
            applied to all protections. If None, 'infinite', 'indefinite',
            'never', or '' is given, there is no expiry.
        @type expiry: pywikibot.Timestamp, string in GNU timestamp format
            (including ISO 8601).
        """
        token = self.tokens['protect']
        self.lock_page(page)

        protections = [ptype + '=' + level
                       for ptype, level in protections.items()
                       if level is not None]
        parameters = merge_unique_dicts(kwargs, action='protect', title=page,
                                        token=token,
                                        protections=protections, reason=reason,
                                        expiry=expiry)

        req = self._simple_request(**parameters)
        try:
            result = req.submit()
        except api.APIError as err:
            errdata = {
                'site': self,
                'user': self.user(),
            }
            if err.code in self._protect_errors:
                raise Error(self._protect_errors[err.code] % errdata)
            pywikibot.debug("protect: Unexpected error code '%s' received."
                            % err.code,
                            _logger)
            raise
        else:
            protection = {}
            for d in result['protect']['protections']:
                expiry = d.pop('expiry')
                ptype, level = d.popitem()
                if level:
                    protection[ptype] = (level, expiry)
            page._protection = protection
        finally:
            self.unlock_page(page)

    # TODO: implement undelete

    _patrol_errors = {
        'nosuchrcid': 'There is no change with rcid %(rcid)s',
        'nosuchrevid': 'There is no change with revid %(revid)s',
        'patroldisabled': 'Patrolling is disabled on %(site)s wiki',
        'noautopatrol': 'User %(user)s has no permission to patrol its own '
                        'changes, "autopatrol" is needed',
        'notpatrollable':
            "The revision %(revid)s can't be patrolled as it's too old."
    }

    @need_right('patrol')
    @deprecated_args(token=None)
    def patrol(self, rcid=None, revid=None, revision=None):
        """Return a generator of patrolled pages.

        @see: U{https://www.mediawiki.org/wiki/API:Patrol}

        Pages to be patrolled are identified by rcid, revid or revision.
        At least one of the parameters is mandatory.
        See https://www.mediawiki.org/wiki/API:Patrol.

        @param rcid: an int/string/iterable/iterator providing rcid of pages
            to be patrolled.
        @type rcid: iterable/iterator which returns a number or string which
             contains only digits; it also supports a string (as above) or int
        @param revid: an int/string/iterable/iterator providing revid of pages
            to be patrolled.
        @type revid: iterable/iterator which returns a number or string which
             contains only digits; it also supports a string (as above) or int.
        @param revision: an Revision/iterable/iterator providing Revision
            object of pages to be patrolled.
        @type revision: iterable/iterator which returns a Revision object; it
            also supports a single Revision.
        @rtype: iterator of dict with 'rcid', 'ns' and 'title'
            of the patrolled page.

        """
        # If patrol is not enabled, attr will be set the first time a
        # request is done.
        if hasattr(self, '_patroldisabled'):
            if self._patroldisabled:
                return

        if all(_ is None for _ in [rcid, revid, revision]):
            raise Error('No rcid, revid or revision provided.')

        if isinstance(rcid, (int, UnicodeType)):
            rcid = {rcid}
        if isinstance(revid, (int, UnicodeType)):
            revid = {revid}
        if isinstance(revision, pywikibot.page.Revision):
            revision = {revision}

        # Handle param=None.
        rcid = rcid or set()
        revid = revid or set()
        revision = revision or set()

        # TODO: remove exception for mw < 1.22
        if (revid or revision) and self.mw_version < '1.22':
            raise NotImplementedError(
                'Support of "revid" parameter\n'
                'is not implemented in MediaWiki version < "1.22"')
        else:
            combined_revid = set(revid) | {r.revid for r in revision}

        gen = itertools.chain(
            zip_longest(rcid, [], fillvalue='rcid'),
            zip_longest(combined_revid, [], fillvalue='revid'))

        token = self.tokens['patrol']

        for idvalue, idtype in gen:
            req = self._request(parameters={'action': 'patrol',
                                            'token': token,
                                            idtype: idvalue})

            try:
                result = req.submit()
            except api.APIError as err:
                # patrol is disabled, store in attr to avoid other requests
                if err.code == 'patroldisabled':
                    self._patroldisabled = True
                    return

                errdata = {
                    'site': self,
                    'user': self.user(),
                }
                errdata[idtype] = idvalue
                if err.code in self._patrol_errors:
                    raise Error(self._patrol_errors[err.code] % errdata)
                pywikibot.debug("protect: Unexpected error code '%s' received."
                                % err.code,
                                _logger)
                raise

            yield result['patrol']

    @need_right('block')
    def blockuser(self, user, expiry, reason, anononly=True, nocreate=True,
                  autoblock=True, noemail=False, reblock=False,
                  allowusertalk=False):
        """
        Block a user for certain amount of time and for a certain reason.

        @see: U{https://www.mediawiki.org/wiki/API:Block}

        @param user: The username/IP to be blocked without a namespace.
        @type user: L{pywikibot.User}
        @param expiry: The length or date/time when the block expires. If
            'never', 'infinite', 'indefinite' it never does. If the value is
            given as a basestring it's parsed by php's strtotime function:

                U{http://php.net/manual/en/function.strtotime.php}

            The relative format is described there:

                U{http://php.net/manual/en/datetime.formats.relative.php}

            It is recommended to not use a basestring if possible to be
            independent of the API.
        @type expiry: Timestamp/datetime (absolute),
            basestring (relative/absolute) or False ('never')
        @param reason: The reason for the block.
        @type reason: basestring
        @param anononly: Disable anonymous edits for this IP.
        @type anononly: boolean
        @param nocreate: Prevent account creation.
        @type nocreate: boolean
        @param autoblock: Automatically block the last used IP address and all
            subsequent IP addresses from which this account logs in.
        @type autoblock: boolean
        @param noemail: Prevent user from sending email through the wiki.
        @type noemail: boolean
        @param reblock: If the user is already blocked, overwrite the existing
            block.
        @type reblock: boolean
        @param allowusertalk: Whether the user can edit their talk page while
            blocked.
        @type allowusertalk: boolean
        @return: The data retrieved from the API request.
        @rtype: dict
        """
        token = self.tokens['block']
        if expiry is False:
            expiry = 'never'
        req = self._simple_request(action='block', user=user.username,
                                   expiry=expiry, reason=reason, token=token,
                                   anononly=anononly, nocreate=nocreate,
                                   autoblock=autoblock, noemail=noemail,
                                   reblock=reblock,
                                   allowusertalk=allowusertalk)

        data = req.submit()
        return data

    @need_right('unblock')
    def unblockuser(self, user, reason=None):
        """
        Remove the block for the user.

        @see: U{https://www.mediawiki.org/wiki/API:Block}

        @param user: The username/IP without a namespace.
        @type user: L{pywikibot.User}
        @param reason: Reason for the unblock.
        @type reason: basestring
        """
        req = self._simple_request(action='unblock',
                                   user=user.username,
                                   token=self.tokens['block'],
                                   reason=reason)

        data = req.submit()
        return data

    @need_right('editmywatchlist')
    def watch(self, pages, unwatch=False):
        """Add or remove pages from watchlist.

        @see: U{https://www.mediawiki.org/wiki/API:Watch}

        @param pages: A single page or a sequence of pages.
        @type pages: A page object, a page-title string, or sequence of them.
            Also accepts a single pipe-separated string like 'title1|title2'.
        @param unwatch: If True, remove pages from watchlist;
            if False add them (default).
        @return: True if API returned expected response; False otherwise
        @rtype: bool
        @raises KeyError: 'watch' isn't in API response

        """
        parameters = {'action': 'watch',
                      'token': self.tokens['watch'],
                      'unwatch': unwatch}
        unwatch = 'unwatched' if unwatch else 'watched'
        if self.mw_version >= '1.23':
            parameters['titles'] = pages
            req = self._simple_request(**parameters)
            results = req.submit()
            return all(unwatch in r for r in results['watch'])

        # MW version < 1.23
        if isinstance(pages, str):
            if '|' in pages:
                pages = pages.split('|')
            else:
                pages = (pages,)

        for page in pages:
            parameters['title'] = page
            req = self._simple_request(**parameters)
            result = req.submit()
            if unwatch not in result['watch']:
                return False
        return True

    @need_right('editmywatchlist')
    @deprecated('Site().watch', since='20160102')
    def watchpage(self, page, unwatch=False):
        """
        Add or remove page from watchlist.

        DEPRECATED: Use Site().watch() instead.

        @param page: A single page.
        @type page: A page object, a page-title string.
        @param unwatch: If True, remove page from watchlist;
            if False (default), add it.
        @return: True if API returned expected response; False otherwise
        @rtype: bool

        """
        try:
            result = self.watch(page, unwatch)
        except KeyError:
            pywikibot.error('watchpage: Unexpected API response')
            result = False
        return result

    @need_right('purge')
    def purgepages(
        self, pages, forcelinkupdate=False, forcerecursivelinkupdate=False,
        converttitles=False, redirects=False
    ):
        """
        Purge the server's cache for one or multiple pages.

        @param pages: list of Page objects
        @param redirects: Automatically resolve redirects.
        @type redirects: bool
        @param converttitles: Convert titles to other variants if necessary.
            Only works if the wiki's content language supports variant
            conversion.
        @type converttitles: bool
        @param forcelinkupdate: Update the links tables.
        @type forcelinkupdate: bool
        @param forcerecursivelinkupdate: Update the links table, and update the
            links tables for any page that uses this page as a template.
        @type forcerecursivelinkupdate: bool
        @return: True if API returned expected response; False otherwise
        @rtype: bool
        """
        req = self._simple_request(action='purge', titles=list(set(pages)))
        if converttitles:
            req['converttitles'] = True
        if redirects:
            req['redirects'] = True
        if forcelinkupdate:
            req['forcelinkupdate'] = True
        if forcerecursivelinkupdate:
            req['forcerecursivelinkupdate'] = True
        result = req.submit()
        try:
            result = result['purge']
        except KeyError:
            pywikibot.error(
                'purgepages: Unexpected API response:\n%s' % result)
            return False
        if not all('purged' in page for page in result):
            return False
        if forcelinkupdate or forcerecursivelinkupdate:
            return all('linkupdate' in page for page in result)
        return True

    @deprecated('Site().exturlusage', since='20090529', future_warning=True)
    def linksearch(self, siteurl, limit=None, euprotocol=None):
        """Backwards-compatible interface to exturlusage()."""
        return self.exturlusage(siteurl, total=limit, protocol=euprotocol)

    def _get_titles_with_hash(self, hash_found=None):
        """Helper for the deprecated method get(Files|Images)FromAnHash."""
        # This should be removed with together with get(Files|Images)FromHash
        if hash_found is None:
            # This makes absolutely NO sense.
            pywikibot.warning(
                'The "hash_found" parameter in "getFilesFromAnHash" and '
                '"getImagesFromAnHash" are not optional.')
            return
        return [image.title(with_ns=False)
                for image in self.allimages(sha1=hash_found)]

    @deprecated('Site().allimages', since='20141219')
    def getFilesFromAnHash(self, hash_found=None):
        """
        Return all files that have the same hash.

        DEPRECATED: Use L{APISite.allimages} instead using 'sha1'.
        """
        return self._get_titles_with_hash(hash_found)

    @deprecated('Site().allimages', since='20141219')
    def getImagesFromAnHash(self, hash_found=None):
        """
        Return all images that have the same hash.

        DEPRECATED: Use L{APISite.allimages} instead using 'sha1'.
        """
        return self._get_titles_with_hash(hash_found)

    @need_right('edit')
    def is_uploaddisabled(self):
        """Return True if upload is disabled on site.

        When the version is at least 1.27wmf9, uses general siteinfo.
        If not called directly, it is cached by the first attempted
        upload action.

        """
        if self.mw_version >= '1.27wmf9':
            return not self._siteinfo.get('general')['uploadsenabled']

        if hasattr(self, '_uploaddisabled'):
            return self._uploaddisabled

        # attempt a fake upload; on enabled sites will fail for:
        # missingparam: One of the parameters
        #    filekey, file, url, statuskey is required
        # TODO: is there another way?
        try:
            req = self._request(throttle=False,
                                parameters={'action': 'upload',
                                            'token': self.tokens['edit']})
            req.submit()
        except api.APIError as error:
            if error.code == 'uploaddisabled':
                self._uploaddisabled = True
            elif error.code == 'missingparam':
                # If the upload module is enabled, the above dummy request
                # does not have sufficient parameters and will cause a
                # 'missingparam' error.
                self._uploaddisabled = False
            else:
                # Unexpected error
                raise
            return self._uploaddisabled
        raise RuntimeError(
            'Unexpected success of upload action without parameters.')

    def stash_info(self, file_key, props=False):
        """Get the stash info for a given file key.

        @see: U{https://www.mediawiki.org/wiki/API:Stashimageinfo}
        """
        if not props:
            props = False
        req = self._simple_request(
            action='query', prop='stashimageinfo', siifilekey=file_key,
            siiprop=props)
        return req.submit()['query']['stashimageinfo'][0]

    @deprecate_arg('imagepage', 'filepage')
    def upload(self, filepage, source_filename=None, source_url=None,
               comment=None, text=None, watch=False, ignore_warnings=False,
               chunk_size=0, _file_key=None, _offset=0, _verify_stash=None,
               report_success=None):
        """
        Upload a file to the wiki.

        @see: U{https://www.mediawiki.org/wiki/API:Upload}

        Either source_filename or source_url, but not both, must be provided.

        @param filepage: a FilePage object from which the wiki-name of the
            file will be obtained.
        @param source_filename: path to the file to be uploaded
        @param source_url: URL of the file to be uploaded
        @param comment: Edit summary; if this is not provided, then
            filepage.text will be used. An empty summary is not permitted.
            This may also serve as the initial page text (see below).
        @param text: Initial page text; if this is not set, then
            filepage.text will be used, or comment.
        @param watch: If true, add filepage to the bot user's watchlist
        @param ignore_warnings: It may be a static boolean, a callable
            returning a boolean or an iterable. The callable gets a list of
            UploadWarning instances and the iterable should contain the warning
            codes for which an equivalent callable would return True if all
            UploadWarning codes are in thet list. If the result is False it'll
            not continue uploading the file and otherwise disable any warning
            and reattempt to upload the file. NOTE: If report_success is True
            or None it'll raise an UploadWarning exception if the static
            boolean is False.
        @type ignore_warnings: bool or callable or iterable of str
        @param chunk_size: The chunk size in bytesfor chunked uploading (see
            U{https://www.mediawiki.org/wiki/API:Upload#Chunked_uploading}). It
            will only upload in chunks, if the version number is 1.20 or higher
            and the chunk size is positive but lower than the file size.
        @type chunk_size: int
        @param _file_key: Reuses an already uploaded file using the filekey. If
            None (default) it will upload the file.
        @type _file_key: str or None
        @param _offset: When file_key is not None this can be an integer to
            continue a previously canceled chunked upload. If False it treats
            that as a finished upload. If True it requests the stash info from
            the server to determine the offset. By default starts at 0.
        @type _offset: int or bool
        @param _verify_stash: Requests the SHA1 and file size uploaded and
            compares it to the local file. Also verifies that _offset is
            matching the file size if the _offset is an int. If _offset is
            False if verifies that the file size match with the local file. If
            None it'll verifies the stash when a file key and offset is given.
        @type _verify_stash: bool or None
        @param report_success: If the upload was successful it'll print a
            success message and if ignore_warnings is set to False it'll
            raise an UploadWarning if a warning occurred. If it's None
            (default) it'll be True if ignore_warnings is a bool and False
            otherwise. If it's True or None ignore_warnings must be a bool.
        @return: It returns True if the upload was successful and False
            otherwise.
        @rtype: bool
        """
        def create_warnings_list(response):
            return [
                api.UploadWarning(
                    warning,
                    upload_warnings.get(warning, '%(msg)s') % {'msg': data},
                    _file_key, response['offset'])
                for warning, data in response['warnings'].items()]

        upload_warnings = {
            # map API warning codes to user error messages
            # %(msg)s will be replaced by message string from API response
            'duplicate-archive':
                'The file is a duplicate of a deleted file %(msg)s.',
            'was-deleted': 'The file %(msg)s was previously deleted.',
            'emptyfile': 'File %(msg)s is empty.',
            'exists': 'File %(msg)s already exists.',
            'duplicate': 'Uploaded file is a duplicate of %(msg)s.',
            'badfilename': 'Target filename is invalid.',
            'filetype-unwanted-type': 'File %(msg)s type is unwanted type.',
            'exists-normalized': 'File exists with different extension as '
                                 '"%(msg)s".',
            'bad-prefix': 'Target filename has a bad prefix %(msg)s.',
            'page-exists':
                'Target filename exists but with a different file %(msg)s.',

            # API-returned message string will be timestamps, not much use here
            'nochange': 'The upload is an exact duplicate of the current '
                        'version of this file.',
            'duplicateversions': 'The upload is an exact duplicate of older '
                                 'version(s) of this file.',
        }

        # An offset != 0 doesn't make sense without a file key
        assert(_offset == 0 or _file_key is not None)
        # check for required user right
        if not self.has_right('upload'):
            raise Error(
                "User '%s' does not have upload rights on site %s."
                % (self.user(), self))
        # check for required parameters
        if bool(source_filename) == bool(source_url):
            raise ValueError('APISite.upload: must provide either '
                             'source_filename or source_url, not both.')
        if comment is None:
            comment = filepage.text
        if not comment:
            raise ValueError('APISite.upload: cannot upload file without '
                             'a summary/description.')
        if report_success is None:
            report_success = isinstance(ignore_warnings, bool)
        if report_success is True:
            if not isinstance(ignore_warnings, bool):
                raise ValueError('report_success may only be set to True when '
                                 'ignore_warnings is a boolean')
            issue_deprecation_warning('"ignore_warnings" as a boolean and '
                                      '"report_success" is True or None',
                                      '"report_success=False" or define '
                                      '"ignore_warnings" as callable/iterable',
                                      3, since='20150823')
        if isinstance(ignore_warnings, Iterable):
            ignored_warnings = ignore_warnings

            def ignore_warnings(warnings):
                return all(w.code in ignored_warnings for w in warnings)

        ignore_all_warnings = not callable(ignore_warnings) and ignore_warnings
        if text is None:
            text = filepage.text
        if not text:
            text = comment
        token = self.tokens['edit']
        result = None
        file_page_title = filepage.title(with_ns=False)
        file_size = None
        offset = _offset
        # make sure file actually exists
        if source_filename:
            if os.path.isfile(source_filename):
                file_size = os.path.getsize(source_filename)
            elif offset is not False:
                raise ValueError("File '%s' does not exist."
                                 % source_filename)

        if source_filename and _file_key:
            assert offset is False or file_size is not None
            if _verify_stash is None:
                _verify_stash = True
            if (offset is not False and offset is not True
                    and offset > file_size):
                raise ValueError(
                    'For the file key "{0}" the offset was set to {1} '
                    'while the file is only {2} bytes large.'.format(
                        _file_key, offset, file_size))

        if _verify_stash or offset is True:
            if not _file_key:
                raise ValueError('Without a file key it cannot request the '
                                 'stash information')
            if not source_filename:
                raise ValueError('Can request stash information only when '
                                 'using a file name.')
            props = ['size']
            if _verify_stash:
                props += ['sha1']
            stash_info = self.stash_info(_file_key, props)
            if offset is True:
                offset = stash_info['size']
            elif offset is False:
                if file_size != stash_info['size']:
                    raise ValueError(
                        'For the file key "{0}" the server reported a size '
                        '{1} while the file size is {2}'
                        .format(_file_key, stash_info['size'], file_size))
            elif offset is not False and offset != stash_info['size']:
                raise ValueError(
                    'For the file key "{0}" the server reported a size {1} '
                    'while the offset was {2}'.format(
                        _file_key, stash_info['size'], offset))

            if _verify_stash:
                # The SHA1 was also requested so calculate and compare it
                assert 'sha1' in stash_info, \
                    'sha1 not in stash info: {0}'.format(stash_info)
                sha1 = compute_file_hash(source_filename, bytes_to_read=offset)
                if sha1 != stash_info['sha1']:
                    raise ValueError(
                        'The SHA1 of {0} bytes of the stashed "{1}" is {2} '
                        'while the local file is {3}'.format(
                            offset, _file_key, stash_info['sha1'], sha1))

        assert offset is not True
        if _file_key and file_size is None:
            assert offset is False

        if _file_key and offset is False or offset == file_size:
            pywikibot.log('Reused already upload file using '
                          'filekey "{0}"'.format(_file_key))
            # TODO: Use sessionkey instead of filekey if necessary
            final_request = self._simple_request(action='upload', token=token,
                                                 filename=file_page_title,
                                                 comment=comment, text=text,
                                                 filekey=_file_key)
        elif source_filename:
            # TODO: Dummy value to allow also Unicode names, see bug T75661
            mime_filename = 'FAKE-NAME'
            # upload local file
            throttle = True
            filesize = os.path.getsize(source_filename)
            chunked_upload = (
                0 < chunk_size < filesize and self.mw_version >= '1.20')
            with open(source_filename, 'rb') as f:
                final_request = self._request(
                    throttle=throttle, parameters={
                        'action': 'upload', 'token': token, 'text': text,
                        'filename': file_page_title, 'comment': comment})
                if chunked_upload:
                    if offset > 0:
                        pywikibot.log('Continuing upload from byte '
                                      '{0}'.format(offset))
                    while True:
                        f.seek(offset)
                        chunk = f.read(chunk_size)
                        req = self._request(
                            throttle=throttle, mime=True,
                            parameters={
                                'action': 'upload',
                                'token': token,
                                'stash': True,
                                'filesize': filesize,
                                'offset': offset,
                                'filename': file_page_title,
                                'ignorewarnings': ignore_all_warnings})
                        req.mime_params['chunk'] = (
                            chunk, ('application', 'octet-stream'),
                            {'filename': mime_filename})
                        if _file_key:
                            req['filekey'] = _file_key
                        try:
                            data = req.submit()['upload']
                            self._uploaddisabled = False
                        except api.APIError as error:
                            # TODO: catch and process foreseeable errors
                            if error.code == 'uploaddisabled':
                                self._uploaddisabled = True
                            elif error.code == 'stashfailed' and \
                                    'offset' in error.other:
                                # TODO: Ask MediaWiki to change this
                                # ambiguous error code.

                                new_offset = int(error.other['offset'])
                                # If the offset returned from the server
                                # (the offset it expects now) is equal to
                                # the offset we sent it, there must be
                                # something else that prevented the upload,
                                # instead of simple offset mismatch. This
                                # also prevents infinite loops when we
                                # upload the same chunk again and again,
                                # every time ApiError.
                                if offset != new_offset:
                                    pywikibot.log(
                                        'Old offset: {0}; Returned '
                                        'offset: {1}; Chunk size: '
                                        '{2}'.format(offset, new_offset,
                                                     len(chunk)))
                                    pywikibot.warning('Attempting to correct '
                                                      'automatically from '
                                                      'offset mismatch error.')
                                    offset = new_offset
                                    continue
                            raise error
                        if 'nochange' in data:  # in simulation mode
                            break
                        _file_key = data['filekey']
                        if 'warnings' in data and not ignore_all_warnings:
                            if callable(ignore_warnings):
                                restart = False
                                if 'offset' not in data:
                                    # This is a result of a warning in the
                                    # first chunk. The chunk is not actually
                                    # stashed so upload must be restarted if
                                    # the warning is allowed.
                                    # T112416 and T112405#1637544
                                    restart = True
                                    data['offset'] = True
                                if ignore_warnings(create_warnings_list(data)):
                                    # Future warnings of this run
                                    # can be ignored
                                    if restart:
                                        return self.upload(
                                            filepage, source_filename,
                                            source_url, comment, text, watch,
                                            True, chunk_size, None, 0,
                                            report_success=False)

                                    ignore_warnings = True
                                    ignore_all_warnings = True
                                    offset = data['offset']
                                    continue
                                else:
                                    return False
                            result = data
                            result.setdefault('offset', 0)
                            break
                        throttle = False
                        if 'offset' in data:
                            new_offset = int(data['offset'])
                            if offset + len(chunk) != new_offset:
                                pywikibot.log('Old offset: {0}; Returned '
                                              'offset: {1}; Chunk size: '
                                              '{2}'.format(offset, new_offset,
                                                           len(chunk)))
                                pywikibot.warning('Unexpected offset.')
                            offset = new_offset
                        else:
                            pywikibot.warning('Offset was not supplied.')
                            offset += len(chunk)
                        if data['result'] != 'Continue':  # finished
                            pywikibot.log('Finished uploading last chunk.')
                            final_request['filekey'] = _file_key
                            break
                else:  # not chunked upload
                    if _file_key:
                        final_request['filekey'] = _file_key
                    else:
                        file_contents = f.read()
                        filetype = (mimetypes.guess_type(source_filename)[0]
                                    or 'application/octet-stream')
                        final_request.mime_params = {
                            'file': (file_contents, filetype.split('/'),
                                     {'filename': mime_filename})
                        }
        else:
            # upload by URL
            if not self.has_right('upload_by_url'):
                raise Error(
                    "User '%s' is not authorized to upload by URL on site %s."
                    % (self.user(), self))
            final_request = self._simple_request(
                action='upload', filename=file_page_title,
                url=source_url, comment=comment, text=text, token=token)
        if not result:
            final_request['watch'] = watch
            final_request['ignorewarnings'] = ignore_all_warnings
            try:
                result = final_request.submit()
                self._uploaddisabled = False
            except api.APIError as error:
                # TODO: catch and process foreseeable errors
                if error.code == 'uploaddisabled':
                    self._uploaddisabled = True
                raise error
            result = result['upload']
            pywikibot.debug(result, _logger)

        if 'warnings' in result and not ignore_all_warnings:
            if 'filekey' in result:
                _file_key = result['filekey']
            elif 'sessionkey' in result:
                # TODO: Probably needs to be reflected in the API call above
                _file_key = result['sessionkey']
                pywikibot.warning('Using sessionkey instead of filekey.')
            else:
                _file_key = None
                pywikibot.warning('No filekey defined.')
            if not report_success:
                result.setdefault('offset', True)
                if ignore_warnings(create_warnings_list(result)):
                    return self.upload(
                        filepage, source_filename, source_url, comment, text,
                        watch, True, chunk_size, _file_key,
                        result['offset'], report_success=False)
                else:
                    return False
            warn('When ignore_warnings=False in APISite.upload will change '
                 'from raising an UploadWarning into behaving like being a '
                 'callable returning False.', DeprecationWarning, 3)
            if len(result['warnings']) > 1:
                warn('The upload returned {0} warnings: '
                     '{1}'.format(len(result['warnings']),
                                  ', '.join(result['warnings'])),
                     UserWarning, 3)
            warning = list(result['warnings'].keys())[0]
            message = result['warnings'][warning]
            raise api.UploadWarning(warning, upload_warnings[warning]
                                    % {'msg': message},
                                    file_key=_file_key,
                                    offset=result.get('offset', False))
        elif 'result' not in result:
            pywikibot.output('Upload: unrecognized response: %s' % result)
        if result['result'] == 'Success':
            if report_success:
                pywikibot.output('Upload successful.')
            # If we receive a nochange, that would mean we're in simulation
            # mode, don't attempt to access imageinfo
            if 'nochange' not in result:
                filepage._load_file_revisions([result['imageinfo']])
        return result['result'] == 'Success'

    @deprecated_args(number='total', repeat=None, namespace='namespaces',
                     rcshow=None, rc_show=None, get_redirect=None, step=None,
                     showBot='bot', showRedirects='redirect',
                     showPatrolled='patrolled')
    def newpages(self, user=None, returndict=False,
                 start=None, end=None, reverse=False, bot=False,
                 redirect=False, excludeuser=None,
                 patrolled=None, namespaces=None, total=None):
        """Yield new articles (as Page objects) from recent changes.

        Starts with the newest article and fetches the number of articles
        specified in the first argument.

        The objects yielded are dependent on parameter returndict.
        When true, it yields a tuple composed of a Page object and a dict of
        attributes.
        When false, it yields a tuple composed of the Page object,
        timestamp (unicode), length (int), an empty unicode string, username
        or IP address (str), comment (unicode).

        @param namespaces: only iterate pages in these namespaces
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        # TODO: update docstring

        # N.B. API still provides no way to access Special:Newpages content
        # directly, so we get new pages indirectly through 'recentchanges'

        gen = self.recentchanges(
            start=start, end=end, reverse=reverse,
            namespaces=namespaces, changetype='new', user=user,
            excludeuser=excludeuser, bot=bot,
            redirect=redirect, patrolled=patrolled,
            total=total
        )
        for pageitem in gen:
            newpage = pywikibot.Page(self, pageitem['title'])
            if returndict:
                yield (newpage, pageitem)
            else:
                yield (newpage, pageitem['timestamp'], pageitem['newlen'],
                       '', pageitem['user'], pageitem['comment'])

    @deprecated('APISite.logevents(logtype="upload")', since='20170619')
    @deprecated_args(lestart='start', leend='end', leuser='user', letitle=None,
                     repeat=None, number='total', step=None)
    def newfiles(self, user=None, start=None, end=None, reverse=False,
                 total=None):
        """Yield information about newly uploaded files.

        DEPRECATED: Use logevents(logtype='upload') instead.

        Yields a tuple of FilePage, Timestamp, user(unicode), comment(unicode).

        N.B. the API does not provide direct access to Special:Newimages, so
        this is derived from the "upload" log events instead.
        """
        for event in self.logevents(logtype='upload', user=user,
                                    start=start, end=end, reverse=reverse,
                                    total=total):
            filepage = event.page()
            date = event.timestamp()
            user = event.user()
            comment = event.comment() or ''
            yield (filepage, date, user, comment)

    @deprecated('APISite.logevents(logtype="upload")', since='20140808')
    @deprecated_args(number='total', repeat=None)
    def newimages(self, *args, **kwargs):
        """
        Yield information about newly uploaded files.

        DEPRECATED: Use logevents(logtype='upload') instead.
        """
        return self.newfiles(*args, **kwargs)

    def querypage(self, special_page, total=None):
        """Yield Page objects retrieved from Special:{special_page}.

        @see: U{https://www.mediawiki.org/wiki/API:Querypage}

        Generic function for all special pages supported by the site MW API.

        @param special_page: Special page to query
        @param total: number of pages to return
        @raise AssertionError: special_page is not supported in SpecialPages.
        """
        param = self._paraminfo.parameter('query+querypage', 'page')
        assert special_page in param['type'], (
            '{0} not in {1}'.format(special_page, param['type']))

        return self._generator(api.PageGenerator,
                               type_arg='querypage', gqppage=special_page,
                               total=total)

    @deprecated_args(number='total', step=None, repeat=None)
    def longpages(self, total=None):
        """Yield Pages and lengths from Special:Longpages.

        Yields a tuple of Page object, length(int).

        @param total: number of pages to return
        """
        lpgen = self._generator(api.ListGenerator,
                                type_arg='querypage', qppage='Longpages',
                                total=total)
        for pageitem in lpgen:
            yield (pywikibot.Page(self, pageitem['title']),
                   int(pageitem['value']))

    @deprecated_args(number='total', step=None, repeat=None)
    def shortpages(self, total=None):
        """Yield Pages and lengths from Special:Shortpages.

        Yields a tuple of Page object, length(int).

        @param total: number of pages to return
        """
        spgen = self._generator(api.ListGenerator,
                                type_arg='querypage', qppage='Shortpages',
                                total=total)
        for pageitem in spgen:
            yield (pywikibot.Page(self, pageitem['title']),
                   int(pageitem['value']))

    @deprecated_args(number='total', step=None, repeat=None)
    def deadendpages(self, total=None):
        """Yield Page objects retrieved from Special:Deadendpages.

        @param total: number of pages to return
        """
        return self.querypage('Deadendpages', total)

    @deprecated_args(number='total', step=None, repeat=None)
    def ancientpages(self, total=None):
        """Yield Pages, datestamps from Special:Ancientpages.

        @param total: number of pages to return
        """
        apgen = self._generator(api.ListGenerator,
                                type_arg='querypage', qppage='Ancientpages',
                                total=total)
        for pageitem in apgen:
            yield (pywikibot.Page(self, pageitem['title']),
                   pywikibot.Timestamp.fromISOformat(pageitem['timestamp']))

    @deprecated_args(number='total', step=None, repeat=None)
    def lonelypages(self, total=None):
        """Yield Pages retrieved from Special:Lonelypages.

        @param total: number of pages to return
        """
        return self.querypage('Lonelypages', total)

    @deprecated_args(number='total', step=None, repeat=None)
    def unwatchedpages(self, total=None):
        """Yield Pages from Special:Unwatchedpages (requires Admin privileges).

        @param total: number of pages to return
        """
        return self.querypage('Unwatchedpages', total)

    @need_version('1.18')
    @deprecated_args(step=None)
    def wantedpages(self, total=None):
        """Yield Pages from Special:Wantedpages.

        @param total: number of pages to return
        """
        return self.querypage('Wantedpages', total)

    @need_version('1.18')
    def wantedfiles(self, total=None):
        """Yield Pages from Special:Wantedfiles.

        @param total: number of pages to return
        """
        return self.querypage('Wantedfiles', total)

    @need_version('1.18')
    def wantedtemplates(self, total=None):
        """Yield Pages from Special:Wantedtemplates.

        @param total: number of pages to return
        """
        return self.querypage('Wantedtemplates', total)

    @need_version('1.18')
    @deprecated_args(number='total', step=None, repeat=None)
    def wantedcategories(self, total=None):
        """Yield Pages from Special:Wantedcategories.

        @param total: number of pages to return
        """
        return self.querypage('Wantedcategories', total)

    @deprecated_args(number='total', step=None, repeat=None)
    def uncategorizedcategories(self, total=None):
        """Yield Categories from Special:Uncategorizedcategories.

        @param total: number of pages to return
        """
        return self.querypage('Uncategorizedcategories', total)

    @deprecated_args(number='total', step=None, repeat=None)
    def uncategorizedimages(self, total=None):
        """Yield FilePages from Special:Uncategorizedimages.

        @param total: number of pages to return
        """
        return self.querypage('Uncategorizedimages', total)

    # synonym
    uncategorizedfiles = uncategorizedimages

    @deprecated_args(number='total', step=None, repeat=None)
    def uncategorizedpages(self, total=None):
        """Yield Pages from Special:Uncategorizedpages.

        @param total: number of pages to return
        """
        return self.querypage('Uncategorizedpages', total)

    @deprecated_args(number='total', step=None, repeat=None)
    def uncategorizedtemplates(self, total=None):
        """Yield Pages from Special:Uncategorizedtemplates.

        @param total: number of pages to return
        """
        return self.querypage('Uncategorizedtemplates', total)

    @deprecated_args(number='total', step=None, repeat=None)
    def unusedcategories(self, total=None):
        """Yield Category objects from Special:Unusedcategories.

        @param total: number of pages to return
        """
        return self.querypage('Unusedcategories', total)

    @deprecated_args(extension=None, number='total', step=None, repeat=None)
    def unusedfiles(self, total=None):
        """Yield FilePage objects from Special:Unusedimages.

        @param total: number of pages to return
        """
        return self.querypage('Unusedimages', total)

    @deprecated('Site().unusedfiles()', since='20140808')
    @deprecated_args(extension=None, number='total', step=None, repeat=None)
    def unusedimages(self, total=None):
        """Yield FilePage objects from Special:Unusedimages.

        DEPRECATED: Use L{APISite.unusedfiles} instead.
        """
        return self.unusedfiles(total)

    @deprecated_args(number='total', step=None, repeat=None)
    def withoutinterwiki(self, total=None):
        """Yield Pages without language links from Special:Withoutinterwiki.

        @param total: number of pages to return
        """
        return self.querypage('Withoutinterwiki', total)

    @need_version('1.18')
    @deprecated_args(step=None)
    def broken_redirects(self, total=None):
        """Yield Pages with broken redirects from Special:BrokenRedirects.

        @param total: number of pages to return
        """
        return self.querypage('BrokenRedirects', total)

    @need_version('1.18')
    @deprecated_args(step=None)
    def double_redirects(self, total=None):
        """Yield Pages with double redirects from Special:DoubleRedirects.

        @param total: number of pages to return
        """
        return self.querypage('DoubleRedirects', total)

    @need_version('1.18')
    @deprecated_args(step=None)
    def redirectpages(self, total=None):
        """Yield redirect pages from Special:ListRedirects.

        @param total: number of pages to return
        """
        return self.querypage('Listredirects', total)

    @deprecated_args(step=None)
    @need_extension('WikibaseClient')
    def unconnected_pages(self, total=None):
        """Yield Page objects from Special:UnconnectedPages.

        @param total: number of pages to return
        """
        return self.querypage('UnconnectedPages', total)

    @deprecated_args(lvl='level')
    def protectedpages(self, namespace=0, type='edit', level=False,
                       total=None):
        """
        Return protected pages depending on protection level and type.

        For protection types which aren't 'create' it uses L{APISite.allpages},
        while it uses for 'create' the 'query+protectedtitles' module.

        @see: U{https://www.mediawiki.org/wiki/API:Protectedtitles}

        @param namespaces: The searched namespace.
        @type namespaces: int or Namespace or str
        @param type: The protection type to search for (default 'edit').
        @type type: str
        @param level: The protection level (like 'autoconfirmed'). If False it
            shows all protection levels.
        @type level: str or False
        @return: The pages which are protected.
        @rtype: typing.Iterable[pywikibot.Page]
        """
        namespaces = self.namespaces.resolve(namespace)
        # always assert that, so we are be sure that type could be 'create'
        assert 'create' in self.protection_types(), \
            "'create' should be a valid protection type."
        if type == 'create':
            if self.mw_version < '1.15':
                raise NotImplementedError(
                    'protectedpages(type=create) requires MW 1.15+')

            return self._generator(
                api.PageGenerator, type_arg='protectedtitles',
                namespaces=namespaces, gptlevel=level, total=total)
        else:
            return self.allpages(namespace=namespaces[0], protect_level=level,
                                 protect_type=type, total=total)

    @need_version('1.21')
    def get_property_names(self, force=False):
        """
        Get property names for pages_with_property().

        @see: U{https://www.mediawiki.org/wiki/API:Pagepropnames}

        @param force: force to retrieve userinfo ignoring cache
        @type force: bool
        """
        if force or not hasattr(self, '_property_names'):
            ppngen = self._generator(api.ListGenerator, 'pagepropnames')
            self._property_names = [pn['propname'] for pn in ppngen]
        return self._property_names

    @need_version('1.21')
    def pages_with_property(self, propname, total=None):
        """Yield Page objects from Special:PagesWithProp.

        @see: U{https://www.mediawiki.org/wiki/API:Pageswithprop}

        @param propname: must be a valid property.
        @type propname: str
        @param total: number of pages to return
        @type total: int or None
        @return: return a generator of Page objects
        @rtype: iterator
        """
        if propname not in self.get_property_names():
            raise NotImplementedError(
                '"{0}" is not a valid page property'.format(propname))
        return self._generator(api.PageGenerator, type_arg='pageswithprop',
                               gpwppropname=propname, total=total)

    @need_version('1.18')
    def compare(self, old, diff):
        """
        Corresponding method to the 'action=compare' API action.

        @see: U{https://www.mediawiki.org/wiki/API:Compare}

        See: https://en.wikipedia.org/w/api.php?action=help&modules=compare
        Use pywikibot.diff's html_comparator() method to parse result.
        @param old: starting revision ID, title, Page, or Revision
        @type old: int, str, pywikibot.Page, or pywikibot.Page.Revision
        @param diff: ending revision ID, title, Page, or Revision
        @type diff: int, str, pywikibot.Page, or pywikibot.Page.Revision
        @return: Returns an HTML string of a diff between two revisions.
        @rtype: str
        """
        # check old and diff types
        def get_param(item):
            if isinstance(item, UnicodeType):
                return 'title', item
            elif isinstance(item, pywikibot.Page):
                return 'title', item.title()
            elif isinstance(item, int):
                return 'rev', item
            elif isinstance(item, pywikibot.page.Revision):
                return 'rev', item.revid
            else:
                return None

        old = get_param(old)
        if not old:
            raise TypeError('old parameter is of invalid type')
        diff = get_param(diff)
        if not diff:
            raise TypeError('diff parameter is of invalid type')

        params = {'action': 'compare',
                  'from{0}'.format(old[0]): old[1],
                  'to{0}'.format(diff[0]): diff[1]}

        req = self._simple_request(**params)
        data = req.submit()
        comparison = data['compare']['*']
        return comparison

    @need_extension('Linter')
    def linter_pages(self, lint_categories=None, total=None,
                     namespaces=None, pageids=None, lint_from=None):
        """Return a generator to pages containing linter errors.

        @param lint_categories: categories of lint errors
        @type lntcategories: an iterable that returns values (str),
            or a pipe-separated string of values.

        @param total: if not None, yielding this many items in total
        @type total: int

        @param namespaces: only iterate pages in these namespaces
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.

        @param pageids: only include lint errors from the specified pageids
        @type pageids: an iterable that returns pageids (str or int),
            or a comma- or pipe-separated string of pageids
            (e.g. '945097,1483753, 956608' or '945097|483753|956608')

        @param lint_from: Lint ID to start querying from
        @type lint_from: str representing digit or integer

        @return: pages with Linter errors.
        @rtype: typing.Iterable[pywikibot.Page]

        """
        query = self._generator(api.ListGenerator, type_arg='linterrors',
                                total=total,  # Will set lntlimit
                                namespaces=namespaces)

        if lint_categories:
            if isinstance(lint_categories, UnicodeType):
                lint_categories = lint_categories.split('|')
                lint_categories = [p.strip() for p in lint_categories]
            query.request['lntcategories'] = '|'.join(lint_categories)

        if pageids:
            if isinstance(pageids, UnicodeType):
                pageids = pageids.split('|')
                pageids = [p.strip() for p in pageids]
            # Validate pageids.
            pageids = (str(int(p)) for p in pageids if int(p) > 0)
            query.request['lntpageid'] = '|'.join(pageids)

        if lint_from:
            query.request['lntfrom'] = int(lint_from)

        for pageitem in query:
            page = pywikibot.Page(self, pageitem['title'])
            api.update_page(page, pageitem)
            yield page

    # Thanks API calls
    @need_extension('Thanks')
    def thank_revision(self, revid, source=None):
        """Corresponding method to the 'action=thank' API action.

        @param revid: Revision ID for the revision to be thanked.
        @type revid: int
        @param source: A source for the thanking operation.
        @type source: str
        @raise APIError: On thanking oneself or other API errors.
        @return: The API response.
        """
        token = self.tokens['csrf']
        req = self._simple_request(action='thank', rev=revid, token=token,
                                   source=source)
        data = req.submit()
        if data['result']['success'] != 1:
            raise api.APIError('Thanking unsuccessful')
        return data

    @need_extension('Flow')
    @need_extension('Thanks')
    def thank_post(self, post):
        """Corresponding method to the 'action=flowthank' API action.

        @param post: The post to be thanked for.
        @type post: Post
        @raise APIError: On thanking oneself or other API errors.
        @return: The API response.
        """
        post_id = post.uuid
        token = self.tokens['csrf']
        req = self._simple_request(action='flowthank',
                                   postid=post_id, token=token)
        data = req.submit()
        if data['result']['success'] != 1:
            raise api.APIError('Thanking unsuccessful')
        return data

    # Flow API calls
    @need_extension('Flow')
    def load_board(self, page):
        """
        Retrieve the data for a Flow board.

        @param page: A Flow board
        @type page: Board
        @return: A dict representing the board's metadata.
        @rtype: dict
        """
        req = self._simple_request(action='flow', page=page,
                                   submodule='view-topiclist',
                                   vtllimit=1)
        data = req.submit()
        return data['flow']['view-topiclist']['result']['topiclist']

    @need_extension('Flow')
    def load_topiclist(self, page, format='wikitext', limit=100,
                       sortby='newest', toconly=False, offset=None,
                       offset_id=None, reverse=False, include_offset=False):
        """
        Retrieve the topiclist of a Flow board.

        @param page: A Flow board
        @type page: Board
        @param format: The content format to request the data in.
        @type format: str (either 'wikitext', 'html', or 'fixed-html')
        @param limit: The number of topics to fetch in each request.
        @type limit: int
        @param sortby: Algorithm to sort topics by.
        @type sortby: str (either 'newest' or 'updated')
        @param toconly: Whether to only include information for the TOC.
        @type toconly: bool
        @param offset: The timestamp to start at (when sortby is 'updated').
        @type offset: Timestamp or equivalent str
        @param offset_id: The topic UUID to start at (when sortby is 'newest').
        @type offset_id: str (in the form of a UUID)
        @param reverse: Whether to reverse the topic ordering.
        @type reverse: bool
        @param include_offset: Whether to include the offset topic.
        @type include_offset: bool
        @return: A dict representing the board's topiclist.
        @rtype: dict
        """
        if offset:
            offset = pywikibot.Timestamp.fromtimestampformat(offset)
        offset_dir = 'rev' if reverse else 'fwd'

        params = {'action': 'flow', 'submodule': 'view-topiclist',
                  'page': page,
                  'vtlformat': format, 'vtlsortby': sortby,
                  'vtllimit': limit, 'vtloffset-dir': offset_dir,
                  'vtloffset': offset, 'vtloffset-id': offset_id,
                  'vtlinclude-offset': include_offset, 'vtltoconly': toconly}
        req = self._request(parameters=params)
        data = req.submit()
        return data['flow']['view-topiclist']['result']['topiclist']

    @need_extension('Flow')
    def load_topic(self, page, format):
        """
        Retrieve the data for a Flow topic.

        @param page: A Flow topic
        @type page: Topic
        @param format: The content format to request the data in.
        @type format: str (either 'wikitext', 'html', or 'fixed-html')
        @return: A dict representing the topic's data.
        @rtype: dict
        """
        req = self._simple_request(action='flow', page=page,
                                   submodule='view-topic',
                                   vtformat=format)
        data = req.submit()
        return data['flow']['view-topic']['result']['topic']

    @need_extension('Flow')
    def load_post_current_revision(self, page, post_id, format):
        """
        Retrieve the data for a post to a Flow topic.

        @param page: A Flow topic
        @type page: Topic
        @param post_id: The UUID of the Post
        @type post_id: str
        @param format: The content format used for the returned content
        @type format: str (either 'wikitext', 'html', or 'fixed-html')
        @return: A dict representing the post data for the given UUID.
        @rtype: dict
        """
        req = self._simple_request(action='flow', page=page,
                                   submodule='view-post', vppostId=post_id,
                                   vpformat=format)
        data = req.submit()
        return data['flow']['view-post']['result']['topic']

    @need_right('edit')
    @need_extension('Flow')
    def create_new_topic(self, page, title, content, format):
        """
        Create a new topic on a Flow board.

        @param page: A Flow board
        @type page: Board
        @param title: The title of the new topic (must be in plaintext)
        @type title: str
        @param content: The content of the topic's initial post
        @type content: str
        @param format: The content format of the value supplied for content
        @type format: str (either 'wikitext' or 'html')
        @return: The metadata of the new topic
        @rtype: dict
        """
        token = self.tokens['csrf']
        params = {'action': 'flow', 'page': page, 'token': token,
                  'submodule': 'new-topic', 'ntformat': format,
                  'nttopic': title, 'ntcontent': content}
        req = self._request(parameters=params, use_get=False)
        data = req.submit()
        return data['flow']['new-topic']['committed']['topiclist']

    @need_right('edit')
    @need_extension('Flow')
    def reply_to_post(self, page, reply_to_uuid, content, format):
        """Reply to a post on a Flow topic.

        @param page: A Flow topic
        @type page: Topic
        @param reply_to_uuid: The UUID of the Post to create a reply to
        @type reply_to_uuid: str
        @param content: The content of the reply
        @type content: str
        @param format: The content format used for the supplied content
        @type format: str (either 'wikitext' or 'html')
        @return: Metadata returned by the API
        @rtype: dict
        """
        token = self.tokens['csrf']
        params = {'action': 'flow', 'page': page, 'token': token,
                  'submodule': 'reply', 'repreplyTo': reply_to_uuid,
                  'repcontent': content, 'repformat': format}
        req = self._request(parameters=params, use_get=False)
        data = req.submit()
        return data['flow']['reply']['committed']['topic']

    @need_right('flow-lock')
    @need_extension('Flow')
    def lock_topic(self, page, lock, reason):
        """
        Lock or unlock a Flow topic.

        @param page: A Flow topic
        @type page: Topic
        @param lock: Whether to lock or unlock the topic
        @type lock: bool (True corresponds to locking the topic.)
        @param reason: The reason to lock or unlock the topic
        @type reason: str
        @return: Metadata returned by the API
        @rtype: dict
        """
        status = 'lock' if lock else 'unlock'
        token = self.tokens['csrf']
        params = {'action': 'flow', 'page': page, 'token': token,
                  'submodule': 'lock-topic', 'cotreason': reason,
                  'cotmoderationState': status}
        req = self._request(parameters=params, use_get=False)
        data = req.submit()
        return data['flow']['lock-topic']['committed']['topic']

    @need_right('edit')
    @need_extension('Flow')
    def moderate_topic(self, page, state, reason):
        """
        Moderate a Flow topic.

        @param page: A Flow topic
        @type page: Topic
        @param state: The new moderation state
        @type state: str
        @param reason: The reason to moderate the topic
        @type reason: str
        @return: Metadata returned by the API
        @rtype: dict
        """
        token = self.tokens['csrf']
        params = {'action': 'flow', 'page': page, 'token': token,
                  'submodule': 'moderate-topic', 'mtreason': reason,
                  'mtmoderationState': state}
        req = self._request(parameters=params, use_get=False)
        data = req.submit()
        return data['flow']['moderate-topic']['committed']['topic']

    @need_right('flow-delete')
    @need_extension('Flow')
    def delete_topic(self, page, reason):
        """
        Delete a Flow topic.

        @param page: A Flow topic
        @type page: Topic
        @param reason: The reason to delete the topic
        @type reason: str
        @return: Metadata returned by the API
        @rtype: dict
        """
        return self.moderate_topic(page, 'delete', reason)

    @need_right('flow-hide')
    @need_extension('Flow')
    def hide_topic(self, page, reason):
        """
        Hide a Flow topic.

        @param page: A Flow topic
        @type page: Topic
        @param reason: The reason to hide the topic
        @type reason: str
        @return: Metadata returned by the API
        @rtype: dict
        """
        return self.moderate_topic(page, 'hide', reason)

    @need_right('flow-suppress')
    @need_extension('Flow')
    def suppress_topic(self, page, reason):
        """
        Suppress a Flow topic.

        @param page: A Flow topic
        @type page: Topic
        @param reason: The reason to suppress the topic
        @type reason: str
        @return: Metadata returned by the API
        @rtype: dict
        """
        return self.moderate_topic(page, 'suppress', reason)

    @need_right('edit')
    @need_extension('Flow')
    def restore_topic(self, page, reason):
        """
        Restore a Flow topic.

        @param page: A Flow topic
        @type page: Topic
        @param reason: The reason to restore the topic
        @type reason: str
        @return: Metadata returned by the API
        @rtype: dict
        """
        return self.moderate_topic(page, 'restore', reason)

    @need_right('edit')
    @need_extension('Flow')
    def moderate_post(self, post, state, reason):
        """
        Moderate a Flow post.

        @param post: A Flow post
        @type post: Post
        @param state: The new moderation state
        @type state: str
        @param reason: The reason to moderate the topic
        @type reason: str
        @return: Metadata returned by the API
        @rtype: dict
        """
        page = post.page
        uuid = post.uuid
        token = self.tokens['csrf']
        params = {'action': 'flow', 'page': page, 'token': token,
                  'submodule': 'moderate-post', 'mpreason': reason,
                  'mpmoderationState': state, 'mppostId': uuid}
        req = self._request(parameters=params, use_get=False)
        data = req.submit()
        return data['flow']['moderate-post']['committed']['topic']

    @need_right('flow-delete')
    @need_extension('Flow')
    def delete_post(self, post, reason):
        """
        Delete a Flow post.

        @param post: A Flow post
        @type post: Post
        @param reason: The reason to delete the post
        @type reason: str
        @return: Metadata returned by the API
        @rtype: dict
        """
        return self.moderate_post(post, 'delete', reason)

    @need_right('flow-hide')
    @need_extension('Flow')
    def hide_post(self, post, reason):
        """
        Hide a Flow post.

        @param post: A Flow post
        @type post: Post
        @param reason: The reason to hide the post
        @type reason: str
        @return: Metadata returned by the API
        @rtype: dict
        """
        return self.moderate_post(post, 'hide', reason)

    @need_right('flow-suppress')
    @need_extension('Flow')
    def suppress_post(self, post, reason):
        """
        Suppress a Flow post.

        @param post: A Flow post
        @type post: Post
        @param reason: The reason to suppress the post
        @type reason: str
        @return: Metadata returned by the API
        @rtype: dict
        """
        return self.moderate_post(post, 'suppress', reason)

    @need_right('edit')
    @need_extension('Flow')
    def restore_post(self, post, reason):
        """
        Restore a Flow post.

        @param post: A Flow post
        @type post: Post
        @param reason: The reason to restore the post
        @type reason: str
        @return: Metadata returned by the API
        @rtype: dict
        """
        return self.moderate_post(post, 'restore', reason)

    @deprecated_args(step=None, sysop=None)
    def watched_pages(self, force=False, total=None):
        """
        Return watchlist.

        @see: U{https://www.mediawiki.org/wiki/API:Watchlistraw}

        @param force_reload: Reload watchlist
        @type force_reload: bool
        @param total: if not None, limit the generator to yielding this many
            items in total
        @type total: int
        @return: list of pages in watchlist
        @rtype: list of pywikibot.Page objects
        """
        expiry = None if force else pywikibot.config.API_config_expiry
        gen = api.PageGenerator(site=self, generator='watchlistraw',
                                expiry=expiry)
        gen.set_maximum_items(total)
        return gen

    @need_extension('UrlShortener')
    def create_short_link(self, url):
        """
        Return a shortened link.

        Note that on Wikimedia wikis only metawiki supports this action,
        and this wiki can process links to all WM domains.

        @param url: The link to reduce, with propotol prefix.
        @type url: str
        @return: The reduced link, without protocol prefix.
        @rtype: str
        """
        req = self._simple_request(action='shortenurl', url=url)
        data = req.submit()
        return data['shortenurl']['shorturl']

    # aliases for backwards compatibility
    isBlocked = redirect_func(is_blocked, old_name='isBlocked',
                              class_name='APISite', since='20141218')
    isAllowed = redirect_func(has_right, old_name='isAllowed',
                              class_name='APISite', since='20141218')


class ClosedSite(APISite):
    """Site closed to read-only mode."""

    @remove_last_args(['sysop'])
    def __init__(self, code, fam, user=None):
        """Initializer."""
        super(ClosedSite, self).__init__(code, fam, user)

    def _closed_error(self, notice=''):
        """An error instead of pointless API call."""
        pywikibot.error('Site {} has been closed. {}'.format(self.sitename,
                                                             notice))

    def page_restrictions(self, page):
        """Return a dictionary reflecting page protections."""
        if not self.page_exists(page):
            raise NoPage(page)
        if not hasattr(page, '_protection'):
            page._protection = {'edit': ('steward', 'infinity'),
                                'move': ('steward', 'infinity'),
                                'delete': ('steward', 'infinity'),
                                'upload': ('steward', 'infinity'),
                                'create': ('steward', 'infinity')}
        return page._protection

    def recentchanges(self, **kwargs):
        """An error instead of pointless API call."""
        self._closed_error('No recent changes can be returned.')

    def is_uploaddisabled(self):
        """Return True if upload is disabled on site."""
        if not hasattr(self, '_uploaddisabled'):
            self._uploaddisabled = True
        return self._uploaddisabled

    def newpages(self, **kwargs):
        """An error instead of pointless API call."""
        self._closed_error('No new pages can be returned.')

    def newfiles(self, **kwargs):
        """An error instead of pointless API call."""
        self._closed_error('No new files can be returned.')

    def newimages(self, *args, **kwargs):
        """An error instead of pointless API call."""
        self._closed_error('No new images can be returned.')


class DataSite(APISite):

    """Wikibase data capable site."""

    def __init__(self, *args, **kwargs):
        """Initializer."""
        super(DataSite, self).__init__(*args, **kwargs)
        self._item_namespace = None
        self._property_namespace = None
        self._type_to_class = {
            'item': pywikibot.ItemPage,
            'property': pywikibot.PropertyPage,
        }

    def _cache_entity_namespaces(self):
        """Find namespaces for each known wikibase entity type."""
        self._entity_namespaces = {}
        for entity_type in self._type_to_class.keys():
            for namespace in self.namespaces.values():
                if not hasattr(namespace, 'defaultcontentmodel'):
                    continue

                content_model = namespace.defaultcontentmodel
                if content_model == ('wikibase-' + entity_type):
                    self._entity_namespaces[entity_type] = namespace
                    break

    def get_namespace_for_entity_type(self, entity_type):
        """
        Return namespace for given entity type.

        @return: corresponding namespace
        @rtype: Namespace
        """
        if not hasattr(self, '_entity_namespaces'):
            self._cache_entity_namespaces()
        if entity_type in self._entity_namespaces:
            return self._entity_namespaces[entity_type]
        raise EntityTypeUnknownException(
            '{0!r} does not support entity type "{1}"'
            .format(self, entity_type))

    @property
    def item_namespace(self):
        """
        Return namespace for items.

        @return: item namespace
        @rtype: Namespace
        """
        if self._item_namespace is None:
            self._item_namespace = self.get_namespace_for_entity_type('item')
        return self._item_namespace

    @property
    def property_namespace(self):
        """
        Return namespace for properties.

        @return: property namespace
        @rtype: Namespace
        """
        if self._property_namespace is None:
            self._property_namespace = self.get_namespace_for_entity_type(
                'property')
        return self._property_namespace

    def get_entity_for_entity_id(self, entity_id):
        """
        Return a new instance for given entity id.

        @raises pywikibot.exceptions.NoWikibaseEntity: there is no entity
            with the id
        @return: a WikibaseEntity subclass
        @rtype: WikibaseEntity
        """
        for cls in self._type_to_class.values():
            if cls.is_valid_id(entity_id):
                return cls(self, entity_id)

        raise NoWikibaseEntity(pywikibot.page.WikibaseEntity(self, entity_id))

    @property
    @need_version('1.28-wmf.3')
    def sparql_endpoint(self):
        """
        Return the sparql endpoint url, if any has been set.

        @return: sparql endpoint url
        @rtype: str|None
        """
        return self.siteinfo['general'].get('wikibase-sparql')

    @property
    @need_version('1.28-wmf.23')
    def concept_base_uri(self):
        """
        Return the base uri for concepts/entities.

        @return: concept base uri
        @rtype: str
        """
        return self.siteinfo['general']['wikibase-conceptbaseuri']

    def _get_baserevid(self, claim, baserevid):
        """Check that claim.on_item is set and matches baserevid if used."""
        if not claim.on_item:
            issue_deprecation_warning('claim without on_item set', depth=3,
                                      since='20160309')
            if not baserevid:
                warn('Neither claim.on_item nor baserevid provided',
                     UserWarning, 3)
            return baserevid

        if not baserevid:
            return claim.on_item.latest_revision_id

        issue_deprecation_warning(
            'Site method with baserevid', 'claim with on_item set', depth=3,
            since='20150910')
        if baserevid != claim.on_item.latest_revision_id:
            warn('Using baserevid {0} instead of claim baserevid {1}'
                 ''.format(baserevid, claim.on_item.latest_revision_id),
                 UserWarning, 3)

        return baserevid

    def __getattr__(self, attr):
        """
        Provide data access methods.

        Methods provided are get_info, get_sitelinks, get_aliases,
        get_labels, get_descriptions, and get_urls.
        """
        if hasattr(self.__class__, attr):
            return getattr(self.__class__, attr)
        if attr.startswith('get_'):
            props = attr.replace('get_', '')
            if props in ['info', 'sitelinks', 'aliases', 'labels',
                         'descriptions', 'urls']:
                if props == 'info':
                    instead = (
                        '\n'
                        "{'lastrevid': ItemPage.latest_revision_id,\n"
                        " 'pageid': ItemPage.pageid,\n"
                        " 'title': ItemPage.title(),\n"
                        " 'modified': ItemPage._timestamp,\n"
                        " 'ns': ItemPage.namespace(),\n"
                        " 'type': ItemPage.entity_type, # for subclasses\n"
                        " 'id': ItemPage.id"
                        '}\n')
                elif props == 'sitelinks':
                    instead = 'ItemPage.sitelinks'
                elif props in ('aliases', 'labels', 'descriptions'):
                    instead = ('ItemPage.{0} after ItemPage.get()'
                               .format(attr))
                else:  # urls
                    instead = None
                issue_deprecation_warning('DataSite.{0}()'.format(attr),
                                          instead, since='20151022')
                if props == 'urls':
                    props = 'sitelinks/urls'
                method = self._get_propertyitem
                f = functools.partial(method, props)
                if hasattr(method, '__doc__'):
                    f.__doc__ = method.__doc__
                return f

        return super(APISite, self).__getattr__(attr)

    def _get_propertyitem(self, props, source, **params):
        """Generic method to get the data for multiple Wikibase items."""
        wbdata = self._get_item(source, props=props, **params)
        if props == 'info':
            return wbdata

        if props == 'sitelinks/urls':
            props = 'sitelinks'

        assert props in wbdata, \
            'API wbgetentities response lacks %s key' % props
        return wbdata[props]

    @deprecated('pywikibot.ItemPage', since='20130307')
    def get_item(self, source, **params):
        """Get the data for multiple Wikibase items."""
        return self._get_item(source, **params)

    # Only separated from get_item to avoid the deprecation message via
    # _get_propertyitem
    def _get_item(self, source, **params):
        assert set(params) <= {'props'}, \
            'Only "props" is a valid kwarg, not {0}'.format(set(params)
                                                            - {'props'})
        if isinstance(source, int) or \
           isinstance(source, UnicodeType) and source.isdigit():
            ids = 'q' + str(source)
            params = merge_unique_dicts(params, action='wbgetentities',
                                        ids=ids)
            wbrequest = self._simple_request(**params)
            wbdata = wbrequest.submit()
            assert 'success' in wbdata, \
                "API wbgetentities response lacks 'success' key"
            assert wbdata['success'] == 1, "API 'success' key is not 1"
            assert 'entities' in wbdata, \
                "API wbgetentities response lacks 'entities' key"

            if ids.upper() in wbdata['entities']:
                ids = ids.upper()

            assert ids in wbdata['entities'], \
                'API wbgetentities response lacks %s key' % ids

            return wbdata['entities'][ids]
        else:
            # not implemented yet
            raise NotImplementedError

    def data_repository(self):
        """
        Override parent method.

        This avoids pointless API queries since the data repository
        is this site by definition.

        @return: this Site object
        @rtype: pywikibot.site.DataSite
        """
        return self

    def geo_shape_repository(self):
        """Return Site object for the geo-shapes repository e.g. commons."""
        url = self.siteinfo['general'].get('wikibase-geoshapestoragebaseurl')
        if url:
            return pywikibot.Site(url=url, user=self.username())
        # todo: should this raise?
        return None

    def tabular_data_repository(self):
        """Return Site object for the tabular-datas repository e.g. commons."""
        url = self.siteinfo['general'].get(
            'wikibase-tabulardatastoragebaseurl')
        if url:
            return pywikibot.Site(url=url, user=self.username())
        # todo: should this raise?
        return None

    def loadcontent(self, identification, *props):
        """
        Fetch the current content of a Wikibase item.

        This is called loadcontent since
        wbgetentities does not support fetching old
        revisions. Eventually this will get replaced by
        an actual loadrevisions.

        @param identification: Parameters used to identify the page(s)
        @type identification: dict
        @param props: the optional properties to fetch.
        """
        params = merge_unique_dicts(identification, action='wbgetentities',
                                    # TODO: When props is empty it results in
                                    # an empty string ('&props=') but it should
                                    # result in a missing entry.
                                    props=props if props else False)
        req = self._simple_request(**params)
        data = req.submit()
        if 'success' not in data:
            raise api.APIError(data['errors'])
        return data['entities']

    def preload_entities(self, pagelist, groupsize=50):
        """
        Yield subclasses of WikibasePage's with content prefilled.

        Note that pages will be iterated in a different order
        than in the underlying pagelist.

        @param pagelist: an iterable that yields either WikibasePage objects,
                         or Page objects linked to an ItemPage.
        @param groupsize: how many pages to query at a time
        @type groupsize: int
        """
        if not hasattr(self, '_entity_namespaces'):
            self._cache_entity_namespaces()
        for sublist in itergroup(pagelist, groupsize):
            req = {'ids': [], 'titles': [], 'sites': []}
            for p in sublist:
                if isinstance(p, pywikibot.page.WikibasePage):
                    ident = p._defined_by()
                    for key in ident:
                        req[key].append(ident[key])
                else:
                    if p.site == self and p.namespace() in (
                            self._entity_namespaces.values()):
                        req['ids'].append(p.title(with_ns=False))
                    else:
                        assert p.site.has_data_repository, \
                            'Site must have a data repository'
                        req['sites'].append(p.site.dbName())
                        req['titles'].append(p._link._text)

            req = self._simple_request(action='wbgetentities', **req)
            data = req.submit()
            for entity in data['entities']:
                if 'missing' in data['entities'][entity]:
                    continue
                cls = self._type_to_class[data['entities'][entity]['type']]
                page = cls(self, entity)
                # No api call is made because item._content is given
                page._content = data['entities'][entity]
                try:
                    page.get()  # cannot provide get_redirect=True (T145971)
                except pywikibot.IsRedirectPage:
                    pass
                yield page

    @deprecated('DataSite.preload_entities', since='20170314')
    def preloaditempages(self, pagelist, groupsize=50):
        """DEPRECATED."""
        return self.preload_entities(pagelist, groupsize)

    def getPropertyType(self, prop):
        """
        Obtain the type of a property.

        This is used specifically because we can cache
        the value for a much longer time (near infinite).
        """
        params = {'action': 'wbgetentities', 'ids': prop.getID(),
                  'props': 'datatype'}
        expiry = datetime.timedelta(days=365 * 100)
        # Store it for 100 years
        req = self._request(expiry=expiry, parameters=params)
        data = req.submit()

        # the IDs returned from the API can be upper or lowercase, depending
        # on the version. See bug T55894 for more information.
        try:
            dtype = data['entities'][prop.getID()]['datatype']
        except KeyError:
            dtype = data['entities'][prop.getID().lower()]['datatype']

        return dtype

    @deprecated_args(identification='entity')
    @need_right('edit')
    def editEntity(self, entity, data, bot=True, **kwargs):
        """
        Edit entity.

        Note: This method is unable to create entities other than 'item'
        if dict with API parameters was passed to 'entity' parameter.

        @param entity: Page to edit, or dict with API parameters
            to use for entity identification
        @type entity: WikibasePage or dict
        @param data: data updates
        @type data: dict
        @param bot: Whether to mark the edit as a bot edit
        @type bot: bool
        @return: New entity data
        @rtype: dict
        """
        # this changes the reference to a new object
        data = dict(data)
        if isinstance(entity, pywikibot.page.WikibasePage):
            params = entity._defined_by(singular=True)
            if 'id' in params and params['id'] == '-1':
                del params['id']
            if not params:
                params['new'] = entity.entity_type
                data_for_new_entity = entity.get_data_for_new_entity()
                data.update(data_for_new_entity)
        else:
            if 'id' in entity and entity['id'] == '-1':
                del entity['id']
            params = dict(entity)
            if not params:  # If no identification was provided
                params['new'] = 'item'

        params['action'] = 'wbeditentity'
        if bot:
            params['bot'] = 1
        if 'baserevid' in kwargs and kwargs['baserevid']:
            params['baserevid'] = kwargs['baserevid']
        params['token'] = self.tokens['edit']

        for arg in kwargs:
            if arg in ['clear', 'summary']:
                params[arg] = kwargs[arg]
            elif arg != 'baserevid':
                warn('Unknown wbeditentity parameter {0} ignored'.format(arg),
                     UserWarning, 2)

        params['data'] = json.dumps(data)
        req = self._simple_request(**params)
        data = req.submit()
        return data

    @need_right('edit')
    def addClaim(self, entity, claim, bot=True, summary=None):
        """
        Add a claim.

        @param entity: Entity to modify
        @type entity: WikibasePage
        @param claim: Claim to be added
        @type claim: pywikibot.Claim
        @param bot: Whether to mark the edit as a bot edit
        @type bot: bool
        @param summary: Edit summary
        @type summary: str
        """
        claim.snak = entity.getID() + '$' + str(uuid.uuid4())
        params = {'action': 'wbsetclaim',
                  'claim': json.dumps(claim.toJSON()),
                  'baserevid': entity.latest_revision_id,
                  'summary': summary,
                  'token': self.tokens['edit'],
                  'bot': bot,
                  }
        req = self._simple_request(**params)
        data = req.submit()
        # Update the item
        if claim.getID() in entity.claims:
            entity.claims[claim.getID()].append(claim)
        else:
            entity.claims[claim.getID()] = [claim]
        entity.latest_revision_id = data['pageinfo']['lastrevid']

    @need_right('edit')
    def changeClaimTarget(self, claim, snaktype='value',
                          bot=True, summary=None):
        """
        Set the claim target to the value of the provided claim target.

        @param claim: The source of the claim target value
        @type claim: pywikibot.Claim
        @param snaktype: An optional snaktype. Default: 'value'
        @type snaktype: str ('value', 'novalue' or 'somevalue')
        @param bot: Whether to mark the edit as a bot edit
        @type bot: bool
        @param summary: Edit summary
        @type summary: str
        """
        if claim.isReference or claim.isQualifier:
            raise NotImplementedError
        if not claim.snak:
            # We need to already have the snak value
            raise NoPage(claim)
        params = {'action': 'wbsetclaimvalue', 'claim': claim.snak,
                  'snaktype': snaktype, 'summary': summary, 'bot': bot,
                  'token': self.tokens['edit']}

        if snaktype == 'value':
            params['value'] = json.dumps(claim._formatValue())

        params['baserevid'] = claim.on_item.latest_revision_id
        req = self._simple_request(**params)
        data = req.submit()
        return data

    @need_right('edit')
    def save_claim(self, claim, summary=None, bot=True):
        """
        Save the whole claim to the wikibase site.

        @param claim: The claim to save
        @type claim: pywikibot.Claim
        @param bot: Whether to mark the edit as a bot edit
        @type bot: bool
        @param summary: Edit summary
        @type summary: str
        """
        if claim.isReference or claim.isQualifier:
            raise NotImplementedError
        if not claim.snak:
            # We need to already have the snak value
            raise NoPage(claim)
        params = {'action': 'wbsetclaim',
                  'claim': json.dumps(claim.toJSON()),
                  'token': self.tokens['edit'],
                  'baserevid': claim.on_item.latest_revision_id,
                  'summary': summary,
                  'bot': bot,
                  }

        req = self._simple_request(**params)
        data = req.submit()
        claim.on_item.latest_revision_id = data['pageinfo']['lastrevid']
        return data

    @need_right('edit')
    def editSource(self, claim, source, new=False,
                   bot=True, summary=None, baserevid=None):
        """
        Create/Edit a source.

        @param claim: A Claim object to add the source to
        @type claim: pywikibot.Claim
        @param source: A Claim object to be used as a source
        @type source: pywikibot.Claim
        @param new: Whether to create a new one if the "source" already exists
        @type new: bool
        @param bot: Whether to mark the edit as a bot edit
        @type bot: bool
        @param summary: Edit summary
        @type summary: str
        @param baserevid: Base revision id override, used to detect conflicts.
            When omitted, revision of claim.on_item is used. DEPRECATED.
        @type baserevid: long
        """
        if claim.isReference or claim.isQualifier:
            raise ValueError('The claim cannot have a source.')
        params = {'action': 'wbsetreference', 'statement': claim.snak,
                  'baserevid': self._get_baserevid(claim, baserevid),
                  'summary': summary, 'bot': bot, 'token': self.tokens['edit']}

        # build up the snak
        if isinstance(source, list):
            sources = source
        else:
            sources = [source]

        snak = {}
        for sourceclaim in sources:
            datavalue = sourceclaim._formatDataValue()
            valuesnaks = []
            if sourceclaim.getID() in snak:
                valuesnaks = snak[sourceclaim.getID()]
            valuesnaks.append({'snaktype': 'value',
                               'property': sourceclaim.getID(),
                               'datavalue': datavalue,
                               },
                              )

            snak[sourceclaim.getID()] = valuesnaks
            # set the hash if the source should be changed.
            # if present, all claims of one source have the same hash
            if not new and hasattr(sourceclaim, 'hash'):
                params['reference'] = sourceclaim.hash
        params['snaks'] = json.dumps(snak)

        req = self._simple_request(**params)
        data = req.submit()
        return data

    @need_right('edit')
    def editQualifier(self, claim, qualifier, new=False, bot=True,
                      summary=None, baserevid=None):
        """
        Create/Edit a qualifier.

        @param claim: A Claim object to add the qualifier to
        @type claim: pywikibot.Claim
        @param qualifier: A Claim object to be used as a qualifier
        @type qualifier: pywikibot.Claim
        @param bot: Whether to mark the edit as a bot edit
        @type bot: bool
        @param summary: Edit summary
        @type summary: str
        @param baserevid: Base revision id override, used to detect conflicts.
            When omitted, revision of claim.on_item is used. DEPRECATED.
        @type baserevid: long
        """
        if claim.isReference or claim.isQualifier:
            raise ValueError('The claim cannot have a qualifier.')
        params = {'action': 'wbsetqualifier', 'claim': claim.snak,
                  'baserevid': self._get_baserevid(claim, baserevid),
                  'summary': summary, 'bot': bot}

        if (not new and hasattr(qualifier, 'hash')
                and qualifier.hash is not None):
            params['snakhash'] = qualifier.hash
        params['token'] = self.tokens['edit']
        # build up the snak
        if qualifier.getSnakType() == 'value':
            params['value'] = json.dumps(qualifier._formatValue())
        params['snaktype'] = qualifier.getSnakType()
        params['property'] = qualifier.getID()

        req = self._simple_request(**params)
        data = req.submit()
        return data

    @need_right('edit')
    def removeClaims(self, claims, bot=True, summary=None, baserevid=None):
        """
        Remove claims.

        @param claims: Claims to be removed
        @type claims: List[pywikibot.Claim]
        @param bot: Whether to mark the edit as a bot edit
        @type bot: bool
        @param summary: Edit summary
        @type summary: str
        @param baserevid: Base revision id override, used to detect conflicts.
            When omitted, revision of claim.on_item is used. DEPRECATED.
        @type baserevid: long
        """
        # Check on_item vs baserevid for all additional claims
        for claim in claims:
            baserevid = self._get_baserevid(claim, baserevid)

        items = {claim.on_item for claim in claims if claim.on_item}
        assert len(items) == 1

        params = {
            'action': 'wbremoveclaims', 'baserevid': baserevid,
            'summary': summary,
            'bot': bot,
            'claim': '|'.join(claim.snak for claim in claims),
            'token': self.tokens['edit'],
        }

        req = self._simple_request(**params)
        data = req.submit()
        return data

    @need_right('edit')
    def removeSources(self, claim, sources,
                      bot=True, summary=None, baserevid=None):
        """
        Remove sources.

        @param claim: A Claim object to remove the sources from
        @type claim: pywikibot.Claim
        @param sources: A list of Claim objects that are sources
        @type sources: pywikibot.Claim
        @param bot: Whether to mark the edit as a bot edit
        @type bot: bool
        @param summary: Edit summary
        @type summary: str
        @param baserevid: Base revision id override, used to detect conflicts.
            When omitted, revision of claim.on_item is used. DEPRECATED.
        @type baserevid: long
        """
        params = {
            'action': 'wbremovereferences',
            'baserevid': self._get_baserevid(claim, baserevid),
            'summary': summary, 'bot': bot,
            'statement': claim.snak,
            'references': '|'.join(source.hash for source in sources),
            'token': self.tokens['edit'],
        }

        req = self._simple_request(**params)
        data = req.submit()
        return data

    @need_right('edit')
    def remove_qualifiers(self, claim, qualifiers,
                          bot=True, summary=None, baserevid=None):
        """
        Remove qualifiers.

        @param claim: A Claim object to remove the qualifier from
        @type claim: pywikibot.Claim
        @param qualifiers: Claim objects currently used as a qualifiers
        @type qualifiers: List[pywikibot.Claim]
        @param bot: Whether to mark the edit as a bot edit
        @type bot: bool
        @param summary: Edit summary
        @type summary: str
        @param baserevid: Base revision id override, used to detect conflicts.
            When omitted, revision of claim.on_item is used. DEPRECATED.
        @type baserevid: long
        """
        params = {
            'action': 'wbremovequalifiers',
            'claim': claim.snak,
            'baserevid': self._get_baserevid(claim, baserevid),
            'summary': summary,
            'bot': bot,
            'qualifiers': [qualifier.hash for qualifier in qualifiers],
            'token': self.tokens['edit']
        }

        req = self._simple_request(**params)
        data = req.submit()
        return data

    @need_right('edit')
    def linkTitles(self, page1, page2, bot=True):
        """
        Link two pages together.

        @param page1: First page to link
        @type page1: pywikibot.Page
        @param page2: Second page to link
        @type page2: pywikibot.Page
        @param bot: Whether to mark the edit as a bot edit
        @type bot: bool
        @return: dict API output
        @rtype: dict
        """
        params = {
            'action': 'wblinktitles',
            'tosite': page1.site.dbName(),
            'totitle': page1.title(),
            'fromsite': page2.site.dbName(),
            'fromtitle': page2.title(),
            'token': self.tokens['edit']
        }
        if bot:
            params['bot'] = 1
        req = self._simple_request(**params)
        data = req.submit()
        return data

    @need_right('item-merge')
    @deprecated_args(ignoreconflicts='ignore_conflicts', fromItem='from_item',
                     toItem='to_item')
    def mergeItems(self, from_item, to_item, ignore_conflicts=None,
                   summary=None, bot=True):
        """
        Merge two items together.

        @param from_item: Item to merge from
        @type from_item: pywikibot.ItemPage
        @param to_item: Item to merge into
        @type to_item: pywikibot.ItemPage
        @param ignore_conflicts: Which type of conflicts
            ('description', 'sitelink', and 'statement')
            should be ignored
        @type ignore_conflicts: list of str
        @param summary: Edit summary
        @type summary: str
        @param bot: Whether to mark the edit as a bot edit
        @type bot: bool
        @return: dict API output
        @rtype: dict
        """
        params = {
            'action': 'wbmergeitems',
            'fromid': from_item.getID(),
            'toid': to_item.getID(),
            'ignoreconflicts': ignore_conflicts,
            'token': self.tokens['edit'],
            'summary': summary,
        }
        if bot:
            params['bot'] = 1
        req = self._simple_request(**params)
        data = req.submit()
        return data

    @need_right('item-redirect')
    def set_redirect_target(self, from_item, to_item, bot=True):
        """
        Make a redirect to another item.

        @param to_item: title of target item.
        @type to_item: pywikibot.ItemPage
        @param from_item: Title of the item to be redirected.
        @type from_item: pywikibot.ItemPage
        @param bot: Whether to mark the edit as a bot edit
        @type bot: bool
        """
        params = {
            'action': 'wbcreateredirect',
            'from': from_item.getID(),
            'to': to_item.getID(),
            'token': self.tokens['edit'],
            'bot': bot,
        }
        req = self._simple_request(**params)
        data = req.submit()
        return data

    @need_right('edit')
    def createNewItemFromPage(self, page, bot=True, **kwargs):
        """
        Create a new Wikibase item for a provided page.

        @param page: page to fetch links from
        @type page: pywikibot.Page
        @param bot: Whether to mark the edit as a bot edit
        @type bot: bool
        @return: pywikibot.ItemPage of newly created item
        @rtype: pywikibot.ItemPage
        """
        sitelinks = {
            page.site.dbName(): {
                'site': page.site.dbName(),
                'title': page.title(),
            }
        }
        labels = {
            page.site.lang: {
                'language': page.site.lang,
                'value': page.title(),
            }
        }
        for link in page.iterlanglinks():
            sitelinks[link.site.dbName()] = {
                'site': link.site.dbName(),
                'title': link.title,
            }
            labels[link.site.lang] = {
                'language': link.site.lang,
                'value': link.title,
            }
        data = {
            'sitelinks': sitelinks,
            'labels': labels,
        }
        result = self.editEntity({}, data, bot=bot, **kwargs)
        return pywikibot.ItemPage(self, result['entity']['id'])

    @deprecated_args(limit='total')
    def search_entities(self, search, language, total=None, **kwargs):
        """
        Search for pages or properties that contain the given text.

        @param search: Text to find.
        @type search: str
        @param language: Language to search in.
        @type language: str
        @param total: Maximum number of pages to retrieve in total, or None in
            case of no limit.
        @type total: int or None
        @return: 'search' list from API output.
        @rtype: api.APIGenerator
        """
        lang_codes = [lang['code'] for lang in self._siteinfo.get('languages')]
        if language not in lang_codes:
            raise ValueError('Data site used does not support provided '
                             'language.')

        if 'site' in kwargs:
            if kwargs['site'].sitename != self.sitename:
                raise ValueError('The site given in the kwargs is different.')
            else:
                warn('search_entities should not get a site via kwargs.',
                     UserWarning, 2)
                del kwargs['site']

        parameters = dict(search=search, language=language, **kwargs)
        gen = api.APIGenerator('wbsearchentities', data_name='search',
                               site=self, parameters=parameters)
        gen.set_maximum_items(total)
        return gen
