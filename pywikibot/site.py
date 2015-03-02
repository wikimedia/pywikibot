# -*- coding: utf-8  -*-
"""
Objects representing MediaWiki sites (wikis).

This module also includes functions to load families, which are
groups of wikis on the same topic in different languages.
"""
#
# (C) Pywikibot team, 2008-2015
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import datetime
import itertools
import os
import re
import sys
import threading
import time
import json
import copy
import mimetypes

from collections import Iterable, Container, namedtuple
from warnings import warn

import pywikibot
import pywikibot.family
from pywikibot.tools import (
    itergroup, UnicodeMixin, ComparableMixin, SelfCallDict, SelfCallString,
    deprecated, deprecate_arg, deprecated_args, remove_last_args,
    redirect_func, manage_wrapping, MediaWikiVersion, normalize_username,
)
from pywikibot.throttle import Throttle
from pywikibot.data import api
from pywikibot.exceptions import (
    Error,
    PageRelatedError,
    EditConflict,
    PageCreatedConflict,
    PageDeletedConflict,
    ArticleExistsConflict,
    IsNotRedirectPage,
    CircularRedirect,
    InterwikiRedirectPage,
    LockedPage,
    CascadeLockedPage,
    LockedNoPage,
    NoPage,
    UnknownSite,
    SiteDefinitionError,
    FamilyMaintenanceWarning,
    NoUsername,
    SpamfilterError,
    NoCreateError,
    UserBlocked,
    EntityTypeUnknownException,
)

from pywikibot.echo import Notification

if sys.version_info[0] > 2:
    from urllib.parse import urlencode
    basestring = (str,)
    unicode = str
    from itertools import zip_longest
else:
    from urllib import urlencode
    from itertools import izip_longest as zip_longest


_logger = "wiki.site"


class PageInUse(pywikibot.Error):

    """Page cannot be reserved for writing due to existing lock."""


class LoginStatus(object):

    """Enum for Login statuses.

    >>> LoginStatus.NOT_ATTEMPTED
    -3
    >>> LoginStatus.AS_USER
    0
    >>> LoginStatus.name(-3)
    'NOT_ATTEMPTED'
    >>> LoginStatus.name(0)
    'AS_USER'
    """

    NOT_ATTEMPTED = -3
    IN_PROGRESS = -2
    NOT_LOGGED_IN = -1
    AS_USER = 0
    AS_SYSOP = 1

    @classmethod
    def name(cls, search_value):
        """Return the name of a LoginStatus by it's value."""
        for key, value in cls.__dict__.items():
            if key == key.upper() and value == search_value:
                return key
        raise KeyError("Value %r could not be found in this enum"
                       % search_value)

    def __init__(self, state):
        """Constructor."""
        self.state = state

    def __repr__(self):
        """Return internal representation."""
        return 'LoginStatus(%s)' % (LoginStatus.name(self.state))


Family = redirect_func(pywikibot.family.Family.load,
                       target_module='pywikibot.family.Family',
                       old_name='Family')


class Namespace(Iterable, ComparableMixin, UnicodeMixin):

    """Namespace site data object.

    This is backwards compatible with the structure of entries
    in site._namespaces which were a list of::

        [customised namespace,
         canonical namespace name?,
         namespace alias*]

    If the canonical_name is not provided for a namespace between -2
    and 15, the MediaWiki 1.14+ built-in names are used.
    Enable use_image_name to use built-in names from MediaWiki 1.13
    and earlier as the details.

    Image and File are aliases of each other by default.

    If only one of canonical_name and custom_name are available, both
    properties will have the same value.
    """

    # These are the MediaWiki built-in names for MW 1.14+.
    # Namespace prefixes are always case-insensitive, but the
    # canonical forms are capitalized.
    canonical_namespaces = {
        -2: u"Media",
        -1: u"Special",
        0: u"",
        1: u"Talk",
        2: u"User",
        3: u"User talk",
        4: u"Project",
        5: u"Project talk",
        6: u"File",
        7: u"File talk",
        8: u"MediaWiki",
        9: u"MediaWiki talk",
        10: u"Template",
        11: u"Template talk",
        12: u"Help",
        13: u"Help talk",
        14: u"Category",
        15: u"Category talk",
    }

    def __init__(self, id, canonical_name=None, custom_name=None,
                 aliases=None, use_image_name=False, **kwargs):
        """Constructor.

        @param custom_name: Name defined in server LocalSettings.php
        @type custom_name: unicode
        @param canonical_name: Canonical name
        @type canonical_name: str
        @param aliases: Aliases
        @type aliases: list of unicode
        @param use_image_name: Use 'Image' as default canonical
                               for 'File' namespace
        @param use_image_name: bool

        """
        self.id = id

        if aliases is None:
            self.aliases = list()
        else:
            self.aliases = aliases

        if not canonical_name and id in self.canonical_namespaces:
            if use_image_name:
                if id == 6:
                    canonical_name = u'Image'
                elif id == 7:
                    canonical_name = u"Image talk"

            if not canonical_name:
                canonical_name = self.canonical_namespaces[id]

        assert(custom_name is not None or canonical_name is not None)

        self.custom_name = custom_name if custom_name is not None else canonical_name
        self.canonical_name = canonical_name if canonical_name is not None else custom_name

        if not aliases:
            if id in (6, 7):
                if use_image_name:
                    alias = u'File'
                else:
                    alias = u'Image'
                if id == 7:
                    alias += u' talk'
                self.aliases = [alias]
            else:
                self.aliases = list()
        else:
            self.aliases = aliases

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
        return name in [x.lower() for x in self._distinct()]

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
            return u':'
        elif id in (6, 14):
            return u':' + name + u':'
        else:
            return u'' + name + u':'

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
        elif isinstance(other, Namespace):
            return self.id == other.id
        elif isinstance(other, basestring):
            return other in self

    def __ne__(self, other):
        """Compare whether two namespace objects are not equal."""
        return not self.__eq__(other)

    def __mod__(self, other):
        """Apply modulo on the namespace id."""
        return self.id.__mod__(other)

    def __sub__(self, other):
        """Apply subtraction on the namespace id."""
        return -(other) + self.id

    def __add__(self, other):
        """Apply addition on the namespace id."""
        return other + self.id

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
            kwargs = ', ' + ', '.join([key + '=' + repr(value)
                                       for (key, value) in
                                       extra])
        else:
            kwargs = ''

        return '%s(id=%d, custom_name=%r, canonical_name=%r, aliases=%r%s)' \
               % (self.__class__.__name__, self.id, self.custom_name,
                  self.canonical_name, self.aliases, kwargs)

    @classmethod
    def builtin_namespaces(cls, use_image_name=False):
        """Return a dict of the builtin namespaces."""
        return dict((i, cls(i, use_image_name=use_image_name, case='first-letter'))
                     for i in range(-2, 16))

    @staticmethod
    def normalize_name(name):
        """Remove an optional colon before and after name.

        TODO: reject illegal characters.
        """
        if name == '':
            return ''

        parts = name.split(':', 4)
        count = len(parts)
        if count > 3:
            return False
        elif count == 3:
            if parts[2] != '':
                return False

        # Discard leading colon
        if count >= 2 and parts[0] == '' and parts[1]:
            return parts[1].strip()
        elif parts[0]:
            return parts[0].strip()
        return False

    @classmethod
    def lookup_name(cls, name, namespaces=None):
        """Find the Namespace for a name.

        @param name: Name of the namespace.
        @type name: basestring
        @param namespaces: namespaces to search
                           default: builtins only
        @type namespaces: dict of Namespace
        @return: Namespace or None
        """
        if not namespaces:
            namespaces = cls.builtin_namespaces()

        name = cls.normalize_name(name)
        if name is False:
            return None
        name = name.lower()

        for namespace in namespaces.values():
            if namespace._contains_lowercase_name(name):
                return namespace

        return None

    @staticmethod
    def resolve(identifiers, namespaces=None):
        """
        Resolve namespace identifiers to obtain Namespace objects.

        Identifiers may be any value for which int() produces a valid
        namespace id, except bool, or any string which Namespace.lookup_name
        successfully finds.  A numerical string is resolved as an integer.

        @param identifiers: namespace identifiers
        @type identifiers: iterable of basestring or Namespace key,
            or a single instance of those types
        @param namespaces: namespaces to search (default: builtins only)
        @type namespaces: dict of Namespace
        @return: list of Namespace objects in the same order as the
            identifiers
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if not namespaces:
            namespaces = Namespace.builtin_namespaces()

        if isinstance(identifiers, (basestring, Namespace)):
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
                  Namespace.lookup_name(ns, namespaces)
                  if isinstance(ns, basestring) and
                      not ns.lstrip('-').isdigit() else
                  namespaces[int(ns)] if int(ns) in namespaces
                  else None
                  for ns in identifiers]

        if NotImplemented in result:
            raise TypeError('identifiers contains inappropriate types: %r'
                            % identifiers)

        # Namespace.lookup_name returns None if the name is not recognised
        if None in result:
            raise KeyError(u'Namespace identifier(s) not recognised: %s'
                           % u','.join([str(identifier) for identifier, ns
                                        in zip(identifiers, result)
                                        if ns is None]))

        return result


class BaseSite(ComparableMixin):

    """Site methods that are independent of the communication interface."""

    def __init__(self, code, fam=None, user=None, sysop=None):
        """
        Constructor.

        @param code: the site's language code
        @type code: str
        @param fam: wiki family name (optional)
        @type fam: str or Family
        @param user: bot user name (optional)
        @type user: str
        @param sysop: sysop account user name (optional)
        @type sysop: str

        """
        if code.lower() != code:
            # Note the Site function in __init__ also emits a UserWarning
            # for this condition, showing the callers file and line no.
            pywikibot.log(u'BaseSite: code "%s" converted to lowercase' % code)
            code = code.lower()
        if not all(x in pywikibot.family.CODE_CHARACTERS for x in str(code)):
            pywikibot.log(u'BaseSite: code "%s" contains invalid characters'
                          % code)
        self.__code = code
        if isinstance(fam, basestring) or fam is None:
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
                pywikibot.log(u'Site %s instantiated using code %s'
                              % (self, code))
            else:
                # no such language anymore
                self.obsolete = True
                pywikibot.log(u'Site %s instantiated and marked "obsolete" '
                              u'to prevent access' % self)
        elif self.__code not in self.languages():
            if self.__family.name in list(self.__family.langs.keys()) and \
               len(self.__family.langs) == 1:
                self.__code = self.__family.name
                if self.__family == pywikibot.config.family \
                        and code == pywikibot.config.mylang:
                    pywikibot.config.mylang = self.__code
                    warn(u'Global configuration variable "mylang" changed to '
                         u'"%s" while instantiating site %s'
                         % (self.__code, self), UserWarning)
            else:
                raise UnknownSite(u"Language '%s' does not exist in family %s"
                                  % (self.__code, self.__family.name))

        self._username = [normalize_username(user), normalize_username(sysop)]

        self.use_hard_category_redirects = (
            self.code in self.family.use_hard_category_redirects)

        # following are for use with lock_page and unlock_page methods
        self._pagemutex = threading.Lock()
        self._locked_pages = []

    @property
    @deprecated("APISite.siteinfo['case'] or Namespace.case == 'case-sensitive'")
    def nocapitalize(self):
        return self.siteinfo['case'] == 'case-sensitive'

    @property
    def throttle(self):
        """Return this Site's throttle.  Initialize a new one if needed."""
        if not hasattr(self, "_throttle"):
            self._throttle = Throttle(self, multiplydelay=True)
        return self._throttle

    @property
    def family(self):
        """The Family object for this Site's wiki family."""
        return self.__family

    @property
    def code(self):
        """The identifying code for this Site.

        By convention, this is usually an ISO language code, but it does
        not have to be.

        """
        return self.__code

    @property
    def lang(self):
        """The ISO language code for this Site.

        Presumed to be equal to the wiki prefix, but this can be overridden.

        """
        return self.__code

    @property
    def doc_subpage(self):
        """Return the documentation subpage for this Site.

        @return: tuple

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
                        warn(u"Site {0} has no language defined in "
                             u"doc_subpages dict in {1}_family.py file"
                             .format(self, self.family.name),
                             FamilyMaintenanceWarning, 2)
            # doc_subpages not defined in x_family.py file
            except AttributeError:
                doc = ()  # default
                warn(u"Site {0} has no doc_subpages dict in {1}_family.py file"
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
        return new

    def __setstate__(self, attrs):
        """Restore things removed in __getstate__."""
        self.__dict__.update(attrs)
        self._pagemutex = threading.Lock()

    def user(self):
        """Return the currently-logged in bot user, or None."""
        if self.logged_in(True):
            return self._username[True]
        elif self.logged_in(False):
            return self._username[False]

    def username(self, sysop=False):
        """Return the username/sysopname used for the site."""
        return self._username[sysop]

    def __getattr__(self, attr):
        """Delegate undefined methods calls to the Family object."""
        if hasattr(self.__class__, attr):
            return getattr(self.__class__, attr)
        try:
            method = getattr(self.family, attr)
            f = lambda *args, **kwargs: method(self.code, *args, **kwargs)
            if hasattr(method, "__doc__"):
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
        return 'Site("%s", "%s")' % (self.code, self.family.name)

    def __hash__(self):
        return hash(repr(self))

    def languages(self):
        """Return list of all valid language codes for this site's Family."""
        return list(self.family.langs.keys())

    def validLanguageLinks(self):
        """Return list of language codes that can be used in interwiki links."""
        nsnames = [name for name in self.namespaces().values()]
        return [lang for lang in self.languages()
                if lang[:1].upper() + lang[1:] not in nsnames]

    def _cache_interwikimap(self, force=False):
        """Cache the interwikimap with usable site instances."""
        # _iw_sites is a local cache to return a APISite instance depending
        # on the interwiki prefix of that site
        if force or not hasattr(self, '_iw_sites'):
            self._iw_sites = {}
            for iw in self.siteinfo['interwikimap']:
                try:
                    site = (pywikibot.Site(url=iw['url']), 'local' in iw)
                except Error:
                    site = (None, False)
                self._iw_sites[iw['prefix']] = site

    def interwiki(self, prefix):
        """
        Return the site for a corresponding interwiki prefix.

        @raise SiteDefinitionError: if the url given in the interwiki table
            doesn't match any of the existing families.
        @raise KeyError: if the prefix is not an interwiki prefix.
        """
        self._cache_interwikimap()
        if prefix in self._iw_sites:
            site = self._iw_sites[prefix]
            if site[0]:
                return site[0]
            else:
                raise SiteDefinitionError(
                    u"No family/site found for prefix '{0}'".format(prefix))
        else:
            raise KeyError(u"'{0}' is not an interwiki prefix.".format(prefix))

    def interwiki_prefix(self, site):
        """
        Return the interwiki prefixes going to that site.

        The interwiki prefixes are ordered first by length (shortest first)
        and then alphabetically.

        @param site: The targeted site, which might be it's own.
        @type site: L{BaseSite}
        @return: The interwiki prefixes
        @rtype: list (guaranteed to be not empty)
        @raise KeyError: if there is no interwiki prefix for that site.
        """
        assert(site is not None)
        self._cache_interwikimap()
        prefixes = set([prefix
                        for prefix, cache_entry in self._iw_sites.items()
                        if cache_entry[0] == site])
        if not prefixes:
            raise KeyError(
                u"There is no interwiki prefix to '{0}'".format(site))
        return sorted(prefixes, key=lambda p: (len(p), p))

    def local_interwiki(self, prefix):
        """
        Return whether the interwiki prefix is local.

        A local interwiki prefix is handled by the target site like a normal
        link. So if that link also contains an interwiki link it does follow
        it as long as it's a local link.

        @raise SiteDefinitionError: if the url given in the interwiki table
            doesn't match any of the existing families.
        @raise KeyError: if the prefix is not an interwiki prefix.
        """
        # Request if necessary
        self.interwiki(prefix)
        return self._iw_sites[prefix][1]

    def ns_index(self, namespace):
        """
        Return the Namespace for a given namespace name.

        @param namespace: name
        @type namespace: unicode
        @return: The matching Namespace object on this Site
        @rtype: Namespace, or None if invalid
        """
        return Namespace.lookup_name(namespace, self.namespaces)

    # for backwards-compatibility
    getNamespaceIndex = redirect_func(ns_index, old_name='getNamespaceIndex',
                                      class_name='BaseSite')

    @property
    def namespaces(self):
        """Return dict of valid namespaces on this wiki."""
        if not hasattr(self, '_namespaces'):
            use_image_name = MediaWikiVersion(self.version()) < MediaWikiVersion("1.14")
            self._namespaces = SelfCallDict(
                Namespace.builtin_namespaces(use_image_name))
        return self._namespaces

    def ns_normalize(self, value):
        """Return canonical local form of namespace name.

        @param value: A namespace name
        @type value: unicode

        """
        index = self.ns_index(value)
        return self.namespace(index)

    # for backwards-compatibility
    normalizeNamespace = redirect_func(ns_normalize,
                                       old_name='normalizeNamespace',
                                       class_name='BaseSite')

    @remove_last_args(('default', ))
    def redirect(self):
        """Return list of localized redirect tags for the site."""
        return [u"REDIRECT"]

    @remove_last_args(('default', ))
    def pagenamecodes(self):
        """Return list of localized PAGENAME tags for the site."""
        return [u"PAGENAME"]

    @remove_last_args(('default', ))
    def pagename2codes(self):
        """Return list of localized PAGENAMEE tags for the site."""
        return [u"PAGENAMEE"]

    def lock_page(self, page, block=True):
        """Lock page for writing.  Must be called before writing any page.

        We don't want different threads trying to write to the same page
        at the same time, even to different sections.

        @param page: the page to be locked
        @type page: pywikibot.Page
        @param block: if true, wait until the page is available to be locked;
            otherwise, raise an exception if page can't be locked

        """
        self._pagemutex.acquire()
        try:
            while page.title(withSection=False) in self._locked_pages:
                if not block:
                    raise PageInUse(page.title(withSection=False))
                time.sleep(.25)
            self._locked_pages.append(page.title(withSection=False))
        finally:
            self._pagemutex.release()

    def unlock_page(self, page):
        """Unlock page.  Call as soon as a write operation has completed.

        @param page: the page to be locked
        @type page: pywikibot.Page

        """
        self._pagemutex.acquire()
        try:
            self._locked_pages.remove(page.title(withSection=False))
        finally:
            self._pagemutex.release()

    def disambcategory(self):
        """Return Category in which disambig pages are listed."""
        try:
            name = '%s:%s' % (self.namespace(14),
                              self.family.disambcatname[self.code])
        except KeyError:
            raise Error(u"No disambiguation category name found for %(site)s"
                        % {'site': self})
        return pywikibot.Category(pywikibot.Link(name, self))

    @deprecated("pywikibot.Link")
    def linkto(self, title, othersite=None):
        """DEPRECATED. Return a wikilink to a page.

        @param title: Title of the page to link to
        @type title: unicode
        @param othersite: Generate a interwiki link for use on this site.
        @type othersite: Site (optional)

        @return: unicode
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
            pattern = "REDIRECT"
        # A redirect starts with hash (#), followed by a keyword, then
        # arbitrary stuff, then a wikilink. The wikilink may contain
        # a label, although this is not useful.
        return re.compile(r'\s*#%(pattern)s\s*:?\s*\[\[(.+?)(?:\|.*?)?\]\]'
                          % locals(),
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
                ns = Namespace.lookup_name(ns, self.namespaces)
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
            name1 = name1[:1].upper() + name1[1:]
            name2 = name2[:1].upper() + name2[1:]
        return name1 == name2

    # namespace shortcuts for backwards-compatibility

    def special_namespace(self):
        """Return local name for the Special: namespace."""
        return self.namespace(-1)

    def image_namespace(self):
        """Return local name for the File namespace."""
        return self.namespace(6)

    def mediawiki_namespace(self):
        """Return local name for the MediaWiki namespace."""
        return self.namespace(8)

    def template_namespace(self):
        """Return local name for the Template namespace."""
        return self.namespace(10)

    def category_namespace(self):
        """Return local name for the Category namespace."""
        return self.namespace(14)

    def category_namespaces(self):
        """Return names for the Category namespace."""
        return self.namespace(14, all=True)

    # site-specific formatting preferences

    def category_on_one_line(self):
        """Return True if this site wants all category links on one line."""
        return self.code in self.family.category_on_one_line

    def interwiki_putfirst(self):
        """Return list of language codes for ordering of interwiki links."""
        return self.family.interwiki_putfirst.get(self.code, None)

    def interwiki_putfirst_doubled(self, list_of_links):
        # TODO: is this even needed?  No family in the framework has this
        # dictionary defined!
        if self.lang in self.family.interwiki_putfirst_doubled:
            if (len(list_of_links) >=
                    self.family.interwiki_putfirst_doubled[self.lang][0]):
                links2 = [lang.language() for lang in list_of_links]
                result = []
                for lang in self.family.interwiki_putfirst_doubled[self.lang][1]:
                    try:
                        result.append(list_of_links[links2.index(lang)])
                    except ValueError:
                        pass
                return result
            else:
                return False
        else:
            return False

    def getSite(self, code):
        """Return Site object for language 'code' in this Family."""
        return pywikibot.Site(code=code, fam=self.family, user=self.user())

    # deprecated methods for backwards-compatibility

    @deprecated("family attribute")
    def fam(self):
        """Return Family object for this Site."""
        return self.family

    @deprecated("urllib.urlencode()")
    def urlEncode(self, query):
        """DEPRECATED."""
        return urlencode(query)

    @deprecated("pywikibot.comms.http.request")
    def getUrl(self, path, retry=True, sysop=False, data=None,
               compress=True, no_hostname=False, cookie_only=False):
        """DEPRECATED.

        Retained for compatibility only. All arguments except path and data
        are ignored.

        """
        from pywikibot.comms import http
        if data:
            if not isinstance(data, basestring):
                data = urlencode(data)
            return http.request(self, path, method="PUT", body=data)
        else:
            return http.request(self, path)

    @deprecated()
    def postForm(self, address, predata, sysop=False, cookies=None):
        """DEPRECATED."""
        return self.getUrl(address, data=predata)

    @deprecated()
    def postData(self, address, data, contentType=None, sysop=False,
                 compress=True, cookies=None):
        """DEPRECATED."""
        return self.getUrl(address, data=data)


def must_be(group=None, right=None):
    """Decorator to require a certain user status when method is called.

    @param group: The group the logged in user should belong to
                  this parameter can be overridden by
                  keyword argument 'as_group'.
    @type group: str ('user' or 'sysop')
    @param right: The rights the logged in user should have.
                  Not supported yet and thus ignored.

    @return: method decorator
    """
    def decorator(fn):
        def callee(self, *args, **kwargs):
            if self.obsolete:
                raise UnknownSite("Language %s in family %s is obsolete"
                                  % (self.code, self.family.name))
            grp = kwargs.pop('as_group', group)
            if grp == 'user':
                self.login(False)
            elif grp == 'sysop':
                self.login(True)
            else:
                raise Exception("Not implemented")
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
                    u'Method or function "%s"\n'
                    u"isn't implemented in MediaWiki version < %s"
                    % (fn.__name__, version))
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

    WARNING_REGEX = re.compile(u"^Unrecognized values? for parameter "
                               u"'siprop': ([^,]+(?:, [^,]+)*)$")

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
        else:
            return pywikibot.tools.EMPTY_DEFAULT

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

        if isinstance(prop, basestring):
            props = [prop]
        else:
            props = prop
        if len(props) == 0:
            raise ValueError('At least one property name must be provided.')
        invalid_properties = []
        try:
            request = pywikibot.data.api.CachedRequest(
                expiry=pywikibot.config.API_config_expiry if expiry is False else expiry,
                site=self._site,
                action='query',
                meta='siteinfo',
                siprop=props)
            # With 1.25wmf5 it'll require continue or rawcontinue. As we don't
            # continue anyway we just always use continue.
            request['continue'] = True
            # warnings are handled later
            request._warning_handler = warn_handler
            data = request.submit()
        except api.APIError as e:
            if e.code == 'siunknown_siprop':
                if len(props) == 1:
                    pywikibot.log(u"Unable to get siprop '{0}'".format(props[0]))
                    return {props[0]: (Siteinfo._get_default(props[0]), False)}
                else:
                    pywikibot.log(u"Unable to get siteinfo, because at least "
                                  u"one property is unknown: '{0}'".format(
                                  u"', '".join(props)))
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
                pywikibot.log(u"Unable to get siprop(s) '{0}'".format(
                    u"', '".join(invalid_properties)))
            if 'query' in data:
                cache_time = datetime.datetime.utcnow()
                for prop in props:
                    if prop in data['query']:
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
            return cache_date + expire >= datetime.datetime.utcnow()

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
        @return: If that property was retrived via this method. Returns None if
            the key was not in the retreived values.
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
                    u"Load siteinfo properties '{0}' along with 'general'".format(
                        u"', '".join(props)), _logger)
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
        @param cache: Caches the result interally so that future accesses via
            this method won't query the server.
        @type cache: bool
        @param expiry: If the cache is older than the expiry it ignores the
            cache and queries the server to get the newest value.
        @type expiry: int/float (days), L{datetime.timedelta}, False (never)
        @return: The gathered property
        @rtype: various
        @raise KeyError: If the key is not a valid siteinfo property and the
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
                cached = None
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
                return self._cache['general'][0][key], self._cache['general'][1]
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


class TokenWallet(object):

    """Container for tokens."""

    def __init__(self, site):
        """Constructor."""
        self.site = site
        self._tokens = {}
        self.failed_cache = set()  # cache unavailable tokens.

    def load_tokens(self, types, all=False):
        """
        Preload one or multiple tokens.

        @param types: the types of token.
        @type  types: iterable
        @param all: load all available tokens, if None only if it can be done
            in one request.
        @type all: bool
        """
        assert(self.site.user())

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
        assert(self.site.user())

        user_tokens = self._tokens.setdefault(self.site.user(), {})
        # always preload all for users without tokens
        failed_cache_key = (self.site.user(), key)

        try:
            key = self.site.validate_tokens([key])[0]
        except IndexError:
            raise Error(
                u"Requested token '{0}' is invalid on {1} wiki."
                .format(key, self.site))

        if (key not in user_tokens and
                failed_cache_key not in self.failed_cache):
                    self.load_tokens([key], all=False if user_tokens else None)

        if key in user_tokens:
            return user_tokens[key]
        else:
            # token not allowed for self.site.user() on self.site
            self.failed_cache.add(failed_cache_key)
            # to be changed back to a plain KeyError?
            raise Error(
                u"Action '{0}' is not allowed for user {1} on {2} wiki."
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


class APISite(BaseSite):

    """API interface to MediaWiki site.

    Do not use directly; use pywikibot.Site function.

    """

#    Site methods from version 1.0 (as these are implemented in this file,
#    or declared deprecated/obsolete, they will be removed from this list)
#########
#    cookies: return user's cookies as a string
#
#    urlEncode: Encode a query to be sent using an http POST request.
#    postForm: Post form data to an address at this site.
#    postData: Post encoded form data to an http address at this site.
#
#    checkCharset(charset): Warn if charset doesn't match family file.
#
#    linktrail: Return regex for trailing chars displayed as part of a link.
#    disambcategory: Category in which disambiguation pages are listed.
#
#    Methods that yield Page objects derived from a wiki's Special: pages
#    (note, some methods yield other information in a tuple along with the
#    Pages; see method docs for details) --
#

    # Constants for token management.
    # For all MediaWiki versions prior to 1.20.
    # 'patrol' is indirectly supported via 'edit' token or recentchanges.
    # It will be converted in site.validate_tokens()/site.get_tokens().
    TOKENS_0 = set(['edit',
                    'delete',
                    'protect',
                    'move',
                    'block',
                    'unblock',
                    'email',
                    'import',
                    'watch',
                    'patrol',
                    ])

    # For all MediaWiki versions, with 1.20 <= version < 1.24wmf19
    TOKENS_1 = set(['block',
                    'centralauth',
                    'delete',
                    'deleteglobalaccount',
                    'undelete',
                    'edit',
                    'email',
                    'import',
                    'move',
                    'options',
                    'patrol',
                    'protect',
                    'setglobalaccountstatus',
                    'unblock',
                    'watch',
                    ])

    # For all MediaWiki versions >= 1.24wmf19
    TOKENS_2 = set(['csrf',
                    'deleteglobalaccount',
                    'patrol',
                    'rollback',
                    'setglobalaccountstatus',
                    'userrights',
                    'watch',
                    ])

    def __init__(self, code, fam=None, user=None, sysop=None):
        """Constructor."""
        BaseSite.__init__(self, code, fam, user, sysop)
        self._msgcache = {}
        self._loginstatus = LoginStatus.NOT_ATTEMPTED
        self._siteinfo = Siteinfo(self)
        self._paraminfo = api.ParamInfo(self)
        self.tokens = TokenWallet(self)

    def __getstate__(self):
        """Remove TokenWallet before pickling, for security reasons."""
        new = super(APISite, self).__getstate__()
        del new['tokens']
        return new

    def __setstate__(self, attrs):
        """Restore things removed in __getstate__."""
        super(APISite, self).__setstate__(attrs)
        self.tokens = TokenWallet(self)

    @classmethod
    def fromDBName(cls, dbname):
        # TODO this only works for some WMF sites
        req = api.CachedRequest(datetime.timedelta(days=10),
                                site=pywikibot.Site('meta', 'meta'),
                                action='sitematrix')
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
                        return cls(lang, site['code'])
            else:
                for site in val:
                    if site['dbname'] == dbname:
                        return cls(site['code'], site['code'])
        raise ValueError("Cannot parse a site out of %s." % dbname)

    def _generator(self, gen_class, type_arg=None, namespaces=None,
                   step=None, total=None, **args):
        """Convenience method that returns an API generator.

        All keyword args not listed below are passed to the generator's
        constructor unchanged.

        @param gen_class: the type of generator to construct (must be
            a subclass of pywikibot.data.api.QueryGenerator)
        @param type_arg: query type argument to be passed to generator's
            constructor unchanged (not all types require this)
        @type type_arg: str
        @param namespaces: if not None, limit the query to namespaces in this
            list
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types.  May be a '|' separated
            list of namespace identifiers.
        @param step: if not None, limit each API call to this many items
        @type step: int
        @param total: if not None, limit the generator to yielding this many
            items in total
        @type total: int
        @return: iterable with parameters set
        @rtype: QueryGenerator
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if type_arg is not None:
            gen = gen_class(type_arg, site=self, **args)
        else:
            gen = gen_class(site=self, **args)
        if namespaces is not None:
            gen.set_namespace(namespaces)
        if step is not None and int(step) > 0:
            gen.set_query_increment(int(step))
        if total is not None and int(total) > 0:
            gen.set_maximum_items(int(total))
        return gen

    def logged_in(self, sysop=False):
        """Verify the bot is logged into the site as the expected user.

        The expected usernames are those provided as either the user or sysop
        parameter at instantiation.

        @param sysop: if True, test if user is logged in as the sysop user
                     instead of the normal user.
        @type sysop: bool

        @return: bool
        """
        if not hasattr(self, "_userinfo"):
            return False

        if sysop and 'sysop' not in self.userinfo['groups']:
            return False

        if 'name' not in self.userinfo or not self.userinfo['name']:
            return False

        if self.userinfo['name'] != self._username[sysop]:
            return False

        return True

    @deprecated("Site.user()")
    def loggedInAs(self, sysop=False):
        """Return the current username if logged in, otherwise return None.

        DEPRECATED (use .user() method instead)

        @param sysop: if True, test if user is logged in as the sysop user
                     instead of the normal user.
        @type sysop: bool

        @return: bool
        """
        return self.logged_in(sysop) and self.user()

    def login(self, sysop=False):
        """Log the user in if not already logged in."""
        # TODO: this should include an assert that loginstatus
        #       is not already IN_PROGRESS, however the
        #       login status may be left 'IN_PROGRESS' because
        #       of exceptions or if the first method of login
        #       (below) is successful.  Instead, log the problem,
        #       to be increased to 'warning' level once majority
        #       of issues are resolved.
        if self._loginstatus == LoginStatus.IN_PROGRESS:
            pywikibot.log(
                u'%r.login(%r) called when a previous login was in progress.'
                % (self, sysop)
            )
        # There are several ways that the site may already be
        # logged in, and we do not need to hit the server again.
        # logged_in() is False if _userinfo exists, which means this
        # will have no effect for the invocation from api.py
        if self.logged_in(sysop):
            self._loginstatus = (LoginStatus.AS_SYSOP
                                 if sysop else LoginStatus.AS_USER)
            return
        # check whether a login cookie already exists for this user
        self._loginstatus = LoginStatus.IN_PROGRESS
        if hasattr(self, "_userinfo"):
            del self._userinfo
        try:
            self.getuserinfo()
            if self.userinfo['name'] == self._username[sysop] and \
               self.logged_in(sysop):
                return
        except api.APIError:  # May occur if you are not logged in (no API read permissions).
            pass
        loginMan = api.LoginManager(site=self, sysop=sysop,
                                    user=self._username[sysop])
        if loginMan.login(retry=True):
            self._username[sysop] = loginMan.username
            if hasattr(self, "_userinfo"):
                del self._userinfo
            self.getuserinfo()
            self._loginstatus = (LoginStatus.AS_SYSOP
                                 if sysop else LoginStatus.AS_USER)
        else:
            self._loginstatus = LoginStatus.NOT_LOGGED_IN  # failure

    # alias for backward-compatibility
    forceLogin = redirect_func(login, old_name='forceLogin',
                               class_name='APISite')

    def logout(self):
        """Logout of the site and load details for the logged out user.

        Also logs out of the global account if linked to the user.
        """
        uirequest = api.Request(site=self, action="logout")
        uirequest.submit()
        self._loginstatus = LoginStatus.NOT_LOGGED_IN
        if hasattr(self, "_userinfo"):
            del self._userinfo
        self.getuserinfo()

    def getuserinfo(self):
        """Retrieve userinfo from site and store in _userinfo attribute.

        self._userinfo will be a dict with the following keys and values:

          - id: user id (numeric str)
          - name: username (if user is logged in)
          - anon: present if user is not logged in
          - groups: list of groups (could be empty)
          - rights: list of rights (could be empty)
          - message: present if user has a new message on talk page
          - blockinfo: present if user is blocked (dict)

        """
        if (not hasattr(self, '_userinfo') or
                'rights' not in self._userinfo or
                self._userinfo['name'] != self._username['sysop' in self._userinfo['groups']]):
            uirequest = api.Request(
                site=self,
                action="query",
                meta="userinfo",
                uiprop="blockinfo|hasmsg|groups|rights"
            )
            uidata = uirequest.submit()
            assert 'query' in uidata, \
                   "API userinfo response lacks 'query' key"
            assert 'userinfo' in uidata['query'], \
                   "API userinfo response lacks 'userinfo' key"
            self._userinfo = uidata['query']['userinfo']
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
        if not hasattr(self, "_globaluserinfo"):
            uirequest = api.Request(
                site=self,
                action="query",
                meta="globaluserinfo",
                guiprop="groups|rights|editcount"
            )
            uidata = uirequest.submit()
            assert 'query' in uidata, \
                   "API userinfo response lacks 'query' key"
            assert 'globaluserinfo' in uidata['query'], \
                   "API userinfo response lacks 'userinfo' key"
            self._globaluserinfo = uidata['query']['globaluserinfo']
            ts = self._globaluserinfo['registration']
            self._globaluserinfo['registration'] = pywikibot.Timestamp.fromISOformat(ts)
        return self._globaluserinfo

    globaluserinfo = property(fget=getglobaluserinfo, doc=getuserinfo.__doc__)

    def is_blocked(self, sysop=False):
        """Return true if and only if user is blocked.

        @param sysop: If true, log in to sysop account (if available)

        """
        if not self.logged_in(sysop):
            self.login(sysop)
        return 'blockinfo' in self._userinfo

    @deprecated('is_blocked()')
    def isBlocked(self, sysop=False):
        """DEPRECATED."""
        return self.is_blocked(sysop)

    def checkBlocks(self, sysop=False):
        """Check if the user is blocked, and raise an exception if so."""
        if self.is_blocked(sysop):
            # User blocked
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
        if (force or not hasattr(self, '_useroptions') or
                self.user() != self._useroptions['_name']):
            uirequest = api.Request(
                site=self,
                action="query",
                meta="userinfo",
                uiprop="options"
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
        return set(ns for ns in self.namespaces().values() if ns.id >= 0 and
                   self._useroptions['searchNs{0}'.format(ns.id)] in ['1', True])

    def assert_valid_iter_params(self, msg_prefix, start, end, reverse):
        """Validate iterating API parameters."""
        if reverse:
            if end < start:
                raise Error(
                    "%s: end must be later than start with reverse=True" % msg_prefix)
        else:
            if start < end:
                raise Error(
                    "%s: start must be later than end with reverse=False" % msg_prefix)

    def has_right(self, right, sysop=False):
        """Return true if and only if the user has a specific right.

        Possible values of 'right' may vary depending on wiki settings,
        but will usually include:

        * Actions: edit, move, delete, protect, upload
        * User levels: autoconfirmed, sysop, bot

        """
        if not self.logged_in(sysop):
            self.login(sysop)
        return right.lower() in self._userinfo['rights']

    @deprecated("Site.has_right()")
    def isAllowed(self, right, sysop=False):
        """DEPRECATED."""
        return self.has_right(right, sysop)

    def has_group(self, group, sysop=False):
        """Return true if and only if the user is a member of specified group.

        Possible values of 'group' may vary depending on wiki settings,
        but will usually include bot.

        """
        if not self.logged_in(sysop):
            self.login(sysop)
        return group.lower() in self._userinfo['groups']

    def messages(self, sysop=False):
        """Return true if the user has new messages, and false otherwise."""
        if not self.logged_in(sysop):
            self.login(sysop)
        return 'hasmsg' in self._userinfo

    def notifications(self, **kwargs):
        """Yield Notification objects from the Echo extension."""
        if self.has_extension('Echo'):
            params = dict(site=self, action='query',
                          meta='notifications',
                          notprop='list', notformat='text')

            for key in kwargs:
                params['not' + key] = kwargs[key]

            data = api.Request(**params).submit()
            for notif in data['query']['notifications']['list'].values():
                yield Notification.fromJSON(self, notif)

    def notifications_mark_read(self, **kwargs):
        """Mark selected notifications as read.

        @return: whether the action was successful
        @rtype: bool
        """
        if self.has_extension('Echo'):
            # TODO: ensure that the 'echomarkread' action
            # is supported by the site
            req = api.Request(site=self,
                              action='echomarkread',
                              token=self.tokens['edit'],
                              **kwargs)
            data = req.submit()
            try:
                return data['query']['echomarkread']['result'] == 'success'
            except KeyError:
                return False

    def mediawiki_messages(self, keys):
        """Fetch the text of a set of MediaWiki messages.

        If keys is '*' or ['*'], all messages will be fetched.
        The returned dict uses each key to store the associated message.

        @param keys: MediaWiki messages to fetch
        @type keys: set of str, '*' or ['*']

        @return: dict
        """
        if not all(_key in self._msgcache for _key in keys):
            msg_query = api.QueryGenerator(
                site=self,
                meta="allmessages",
                ammessages='|'.join(keys),
                amlang=self.lang,
            )

            for msg in msg_query:
                if 'missing' not in msg:
                    self._msgcache[msg['name']] = msg['*']

            # Return all messages
            if keys == u'*' or keys == [u'*']:
                return self._msgcache
            else:
                # Check requested keys
                for key in keys:
                    if key not in self._msgcache:
                        raise KeyError("Site %s has no message '%s'"
                                       % (self, key))

        return dict((_key, self._msgcache[_key]) for _key in keys)

    def mediawiki_message(self, key):
        """Fetch the text for a MediaWiki message.

        @param key: name of MediaWiki message
        @type key: str

        @return: unicode
        """
        return self.mediawiki_messages([key])[key]

    def has_mediawiki_message(self, key):
        """Determine if the site defines a MediaWiki message.

        @param key: name of MediaWiki message
        @type key: str

        @return: bool
        """
        return self.has_all_mediawiki_messages([key])

    def has_all_mediawiki_messages(self, keys):
        """Confirm that the site defines a set of MediaWiki messages.

        @param keys: names of MediaWiki messages
        @type keys: set of str

        @return: bool
        """
        try:
            self.mediawiki_messages(keys)
            return True
        except KeyError:
            return False

    @property
    def months_names(self):
        """Obtain month names from the site messages.

        The list is zero-indexed, ordered by month in calendar, and should
        be in the original site language.

        @return: list of tuples (month name, abbreviation)
        """
        if hasattr(self, "_months_names"):
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

        The MediaWiki message 'and' is used as separator
        between the last two arguments.
        If present, other arguments are joined using a comma.

        @param args: text to be expanded
        @type args: iterable

        @return: unicode
        """
        if not args:
            return u''
        args = [unicode(e) for e in args]
        msgs = {
            'and': ',',
            'comma-separator': ', ',
            'word-separator': ' '
        }
        try:
            self.mediawiki_messages(list(msgs.keys()))
        except KeyError:
            pass
        for msg in msgs:
            try:
                msgs[msg] = self.mediawiki_message(msg)
            except KeyError:
                pass
        concat = msgs['and'] + msgs['word-separator']
        return msgs['comma-separator'].join(args[:-2] + [concat.join(args[-2:])])

    @need_version("1.12")
    def expand_text(self, text, title=None, includecomments=None):
        """Parse the given text for preprocessing and rendering.

        e.g expand templates and strip comments if includecomments
        parameter is not True. Keeps text inside
        <nowiki></nowiki> tags unchanges etc. Can be used to parse
        magic parser words like {{CURRENTTIMESTAMP}}.

        @param text: text to be expanded
        @type text: unicode
        @param title: page title without section
        @type title: unicode
        @param includecomments: if True do not strip comments
        @type includecomments: bool
        @return: unicode

        """
        if not isinstance(text, basestring):
            raise ValueError('text must be a string')
        if not text:
            return ''
        req = api.Request(site=self, action='expandtemplates', text=text)
        if title is not None:
            req['title'] = title
        if includecomments is True:
            req['includecomments'] = u''
        if MediaWikiVersion(self.version()) > MediaWikiVersion("1.24wmf7"):
            key = 'wikitext'
            req['prop'] = key
        else:
            key = '*'
        return req.submit()['expandtemplates'][key]

    def getcurrenttimestamp(self):
        """
        Return the server time as a MediaWiki timestamp string.

        It calls L{getcurrenttime} first so it queries the server to get the
        current server time.

        @return: the server time
        @rtype: str (as 'yyyymmddhhmmss')
        """
        return self.getcurrenttime().totimestampformat()

    def getcurrenttime(self):
        """
        Return a Timestamp object representing the current server time.

        For wikis with a version newer than 1.16 it uses the 'time' property
        of the siteinfo 'general'. It'll force a reload before returning the
        time. It requests to expand the text '{{CURRENTTIMESTAMP}}' for older
        wikis.

        @return: the current server time
        @rtype: L{Timestamp}
        """
        if MediaWikiVersion(self.version()) >= MediaWikiVersion("1.16"):
            return pywikibot.Timestamp.fromISOformat(
                self.siteinfo.get('time', expiry=0))
        else:
            return pywikibot.Timestamp.fromtimestampformat(
                self.expand_text("{{CURRENTTIMESTAMP}}"))

    @need_version("1.14")
    def getmagicwords(self, word):
        """Return list of localized "word" magic words for the site."""
        if not hasattr(self, "_magicwords"):
            magicwords = self.siteinfo.get("magicwords", cache=False)
            self._magicwords = dict((item["name"], item["aliases"])
                                        for item in magicwords)

        if word in self._magicwords:
            return self._magicwords[word]
        else:
            return [word]

    @remove_last_args(('default', ))
    def redirect(self):
        """Return the localized #REDIRECT keyword."""
        # return the magic word without the preceding '#' character
        return self.getmagicwords("redirect")[0].lstrip("#")

    def redirectRegex(self):
        """Return a compiled regular expression matching on redirect pages.

        Group 1 in the regex match object will be the target title.

        """
        # NOTE: this is needed, since the API can give false positives!
        try:
            keywords = set(s.lstrip("#")
                           for s in self.getmagicwords("redirect"))
            keywords.add("REDIRECT")  # just in case
            pattern = "(?:" + "|".join(keywords) + ")"
        except KeyError:
            # no localized keyword for redirects
            pattern = None
        return BaseSite.redirectRegex(self, pattern)

    @remove_last_args(('default', ))
    def pagenamecodes(self):
        """Return list of localized PAGENAME tags for the site."""
        return self.getmagicwords("pagename")

    @remove_last_args(('default', ))
    def pagename2codes(self):
        """Return list of localized PAGENAMEE tags for the site."""
        return self.getmagicwords("pagenamee")

    def _build_namespaces(self):
        _namespaces = SelfCallDict()

        # In MW 1.14, API siprop 'namespaces' added 'canonical',
        # and Image became File with Image as an alias.
        # For versions lower than 1.14, APISite needs to override
        # the defaults defined in Namespace.
        is_mw114 = MediaWikiVersion(self.version()) >= MediaWikiVersion('1.14')

        for nsdata in self.siteinfo.get('namespaces', cache=False).values():
            ns = nsdata.pop('id')
            custom_name = None
            canonical_name = None
            if ns == 0:
                canonical_name = nsdata.pop('*')
                custom_name = canonical_name
            else:
                custom_name = nsdata.pop('*')
                if is_mw114:
                    canonical_name = nsdata.pop('canonical')

            if 'case' not in nsdata:
                nsdata['case'] = self.siteinfo['case']

            namespace = Namespace(ns, canonical_name, custom_name,
                                  use_image_name=not is_mw114,
                                  **nsdata)
            _namespaces[ns] = namespace

        for item in self.siteinfo.get('namespacealiases'):
            ns = int(item['id'])
            if item['*'] not in _namespaces[ns]:
                _namespaces[ns].aliases.append(item['*'])

        self._namespaces = _namespaces

    @need_version("1.14")
    @deprecated("has_extension")
    def hasExtension(self, name, unknown=None):
        """Determine whether extension `name` is loaded.

        Use L{has_extension} instead!

        @param name: The extension to check for, case insensitive
        @type name: str
        @param unknown: Old parameter which shouldn't be used anymore.
        @return: If the extension is loaded
        @rtype: bool
        """
        if unknown is not None:
            pywikibot.debug(u'unknown argument of hasExtension is deprecated.',
                            _logger)
        return self.has_extension(name)

    @need_version("1.14")
    def has_extension(self, name):
        """Determine whether extension `name` is loaded.

        @param name: The extension to check for, case insensitive
        @type name: str
        @return: If the extension is loaded
        @rtype: bool
        """
        extensions = self.siteinfo['extensions']
        for ext in extensions:
            if ext['name'].lower() == name.lower():
                return True
        return False

    @property
    def siteinfo(self):
        """Site information dict."""
        return self._siteinfo

    @deprecated('use siteinfo or Namespace instance')
    def case(self):
        """Return this site's capitalization rule."""
        # This is the global setting via $wgCapitalLinks, it is used whenever
        # the namespaces don't propagate the namespace specific value.
        return self.siteinfo['case']

    def dbName(self):
        """Return this site's internal id."""
        return self.siteinfo['wikiid']

    def language(self):
        """Return the code for the language of this Site."""
        return self.siteinfo['lang']

    lang = property(fget=language, doc=language.__doc__)

    def version(self):
        """
        Return live project version number as a string.

        This overwrites the corresponding family method for APISite class. Use
        L{pywikibot.tools.MediaWikiVersion} to compare MediaWiki versions.
        """
        version = self.force_version()
        if not version:
            try:
                version = self.siteinfo.get('generator', expiry=1).split(' ')[1]
            except pywikibot.data.api.APIError:
                # May occur if you are not logged in (no API read permissions).
                pywikibot.exception('You have no API read permissions. Seems '
                                    'you are not logged in')
                version = self.family.version(self.code)
        return version

    @property
    def has_image_repository(self):
        """Return True if site has a shared image repository like Commons."""
        code, fam = self.shared_image_repository()
        return bool(code or fam)

    @property
    def has_data_repository(self):
        """Return True if site has a shared data repository like Wikidata."""
        code, fam = self.shared_data_repository()
        return bool(code or fam)

    @property
    def has_transcluded_data(self):
        """Return True if site has a shared data repository like Wikidata."""
        code, fam = self.shared_data_repository(True)
        return bool(code or fam)

    def image_repository(self):
        """Return Site object for image repository e.g. commons."""
        code, fam = self.shared_image_repository()
        if bool(code or fam):
            return pywikibot.Site(code, fam, self.username())

    def data_repository(self):
        """Return Site object for data repository e.g. Wikidata."""
        code, fam = self.shared_data_repository()
        if bool(code or fam):
            return pywikibot.Site(code, fam, self.username(),
                                  interface="DataSite")

    def is_image_repository(self):
        """Return True if Site object is the image repository."""
        return self is self.image_repository()

    def is_data_repository(self):
        """Return True if Site object is the data repository."""
        return self is self.data_repository()

    def nice_get_address(self, title):
        """Return shorter URL path to retrieve page titled 'title'."""
        # 'title' is expected to be URL-encoded already
        return self.siteinfo["articlepath"].replace("$1", title)

    @property
    def namespaces(self):
        """Return dict of valid namespaces on this wiki."""
        if not hasattr(self, '_namespaces'):
            self._build_namespaces()
        return self._namespaces

    def namespace(self, num, all=False):
        """Return string containing local name of namespace 'num'.

        If optional argument 'all' is true, return a list of all recognized
        values for this namespace.

        """
        if all:
            return self.namespaces[num]
        return self.namespaces[num][0]

    @deprecated("version()")
    def live_version(self, force=False):
        """Return the 'real' version number found on [[Special:Version]].

        By default the version number is cached for one day.

        @param force: If the version should be read always from the server and
            never from the cache.
        @type force: bool
        @return: A tuple containing the major, minor version number and any
            text after that. If an error occured (0, 0, 0) is returned.
        @rtype: int, int, str
        """
        try:
            versionstring = self.siteinfo.get('generator',
                                              expiry=0 if force else 1)
            m = re.match(r"^MediaWiki ([0-9]+)\.([0-9]+)(.*)$", versionstring)
            if m:
                return (int(m.group(1)), int(m.group(2)), m.group(3))
        except api.APIError:  # May occur if you are not logged in (no API read permissions).
            return (0, 0, 0)

    def _update_page(self, page, query, method_name):
        for pageitem in query:
            if not self.sametitle(pageitem['title'],
                                  page.title(withSection=False)):
                pywikibot.warning(
                    u"{0}: Query on {1} returned data on '{2}'".format(
                    method_name, page, pageitem['title']))
                continue
            api.update_page(page, pageitem, query.props)

    def loadpageinfo(self, page, preload=False):
        """Load page info from api and store in page attributes."""
        title = page.title(withSection=False)
        inprop = 'protection'
        if preload:
            inprop += '|preload'

        query = self._generator(api.PropertyGenerator,
                                type_arg="info",
                                titles=title.encode(self.encoding()),
                                inprop=inprop)
        self._update_page(page, query, 'loadpageinfo')

    def loadcoordinfo(self, page):
        """Load [[mw:Extension:GeoData]] info."""
        title = page.title(withSection=False)
        query = self._generator(api.PropertyGenerator,
                                type_arg="coordinates",
                                titles=title.encode(self.encoding()),
                                coprop=['type', 'name', 'dim',
                                        'country', 'region',
                                        'globe'],
                                coprimary='all')
        self._update_page(page, query, 'loadcoordinfo')

    def loadpageprops(self, page):
        """Load page props for the given page."""
        title = page.title(withSection=False)
        query = self._generator(api.PropertyGenerator,
                                type_arg="pageprops",
                                titles=title.encode(self.encoding()),
                                )
        self._update_page(page, query, 'loadpageprops')

    def loadimageinfo(self, page, history=False):
        """Load image info from api and save in page attributes.

        @param history: if true, return the image's version history

        """
        title = page.title(withSection=False)
        args = {"titles": title}
        if not history:
            args["total"] = 1
        query = self._generator(api.PropertyGenerator,
                                type_arg="imageinfo",
                                iiprop=["timestamp", "user", "comment",
                                        "url", "size", "sha1", "mime",
                                        "metadata", "archivename"],
                                **args)
        # kept for backward compatibility
        # TODO: when backward compatibility can be broken, adopt
        # self._update_page() pattern and remove return
        for pageitem in query:
            if not self.sametitle(pageitem['title'], title):
                raise Error(
                    u"loadimageinfo: Query on %s returned data on '%s'"
                    % (page, pageitem['title']))
            api.update_page(page, pageitem, query.props)

            if "imageinfo" not in pageitem:
                if "missing" in pageitem:
                    raise NoPage(page)
                raise PageRelatedError(
                    page,
                    u"loadimageinfo: Query on %s returned no imageinfo")

        return (pageitem['imageinfo']
                if history else pageitem['imageinfo'][0])

    @deprecated('Check the content model instead')
    def loadflowinfo(self, page):
        """
        Load Flow-related information about a given page.

        FIXME: Assumes that the Flow extension is installed.
        """
        title = page.title(withSection=False)
        query = self._generator(api.PropertyGenerator,
                                type_arg="flowinfo",
                                titles=title.encode(self.encoding()),
                                )
        self._update_page(page, query, 'loadflowinfo')

    def page_exists(self, page):
        """Return True if and only if page is an existing page on site."""
        if not hasattr(page, "_pageid"):
            self.loadpageinfo(page)
        return page._pageid > 0

    def page_restrictions(self, page):
        """Return a dictionary reflecting page protections."""
        if not self.page_exists(page):
            raise NoPage(page)
        if not hasattr(page, "_protection"):
            self.loadpageinfo(page)
        return page._protection

    def page_can_be_edited(self, page):
        """
        Determine if the page can be edited.

        Return True if and only if:
          - page is unprotected, and bot has an account for this site, or
          - page is protected, and bot has a sysop account for this site.

        @return: bool
        """
        rest = self.page_restrictions(page)
        sysop_protected = "edit" in rest and rest['edit'][0] == 'sysop'
        try:
            api.LoginManager(site=self, sysop=sysop_protected)
        except NoUsername:
            return False
        return True

    def page_isredirect(self, page):
        """Return True if and only if page is a redirect."""
        if not hasattr(page, "_isredir"):
            page._isredir = False  # bug 54684
            self.loadpageinfo(page)
        return page._isredir

    def getredirtarget(self, page):
        """
        Return page object for the redirect target of page.

        @param page: page to search redirects for
        @type page: BasePage
        @return: redirect target of page
        @rtype: BasePage

        @raise IsNotRedirectPage: page is not a redirect
        @raise RuntimeError: no redirects found
        @raise CircularRedirect: page is a circular redirect
        @raise InterwikiRedirectPage: the redirect target is
            on another site
        """
        if not self.page_isredirect(page):
            raise IsNotRedirectPage(page)
        if hasattr(page, '_redirtarget'):
            return page._redirtarget

        title = page.title(withSection=False)
        query = api.Request(site=self, action="query", prop="info",
                            inprop="protection|talkid|subjectid",
                            titles=title.encode(self.encoding()),
                            redirects="")
        result = query.submit()
        if "query" not in result or "redirects" not in result["query"]:
            raise RuntimeError(
                "getredirtarget: No 'redirects' found for page %s."
                % title.encode(self.encoding()))

        redirmap = dict((item['from'],
                         {'title': item['to'],
                          'section': u'#' + item['tofragment']
                          if 'tofragment' in item and item['tofragment']
                          else ''})
                        for item in result['query']['redirects'])

        # Normalize title
        for item in result['query'].get('normalized', []):
            if item['from'] == title:
                title = item['to']
                break

        if title not in redirmap:
            raise RuntimeError(
                "getredirtarget: 'redirects' contains no key for page %s."
                % title.encode(self.encoding()))
        target_title = u'%(title)s%(section)s' % redirmap[title]

        if self.sametitle(title, target_title):
            raise CircularRedirect(page)

        if "pages" not in result['query']:
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
            page._redirtarget = target
        else:
            # Target is an intermediate redirect -> double redirect.
            # Do not bypass double-redirects and return the ultimate target;
            # it would be impossible to detect and fix double-redirects.
            # This handles also redirects to sections, as sametitle()
            # does not ignore sections.
            target = pywikibot.Page(self, target_title)
            page._redirtarget = target

        return page._redirtarget

    def preloadpages(self, pagelist, groupsize=50, templates=False,
                     langlinks=False):
        """Return a generator to a list of preloaded pages.

        Note that [at least in current implementation] pages may be iterated
        in a different order than in the underlying pagelist.

        @param pagelist: an iterable that returns Page objects
        @param groupsize: how many Pages to query at a time
        @type groupsize: int
        @param templates: preload list of templates in the pages
        @param langlinks: preload list of language links found in the pages

        """
        for sublist in itergroup(pagelist, groupsize):
            pageids = [str(p._pageid) for p in sublist
                       if hasattr(p, "_pageid") and p._pageid > 0]
            cache = dict((p.title(withSection=False), p) for p in sublist)

            props = "revisions|info|categoryinfo"
            if templates:
                props += '|templates'
            if langlinks:
                props += '|langlinks'
            rvgen = api.PropertyGenerator(props, site=self)
            rvgen.set_maximum_items(-1)  # suppress use of "rvlimit" parameter
            if len(pageids) == len(sublist):
                # only use pageids if all pages have them
                rvgen.request["pageids"] = "|".join(pageids)
            else:
                rvgen.request["titles"] = "|".join(list(cache.keys()))
            rvgen.request[u"rvprop"] = u"ids|flags|timestamp|user|comment|content"
            pywikibot.output(u"Retrieving %s pages from %s."
                             % (len(cache), self))
            for pagedata in rvgen:
                pywikibot.debug(u"Preloading %s" % pagedata, _logger)
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
                                u"preloadpages: Query returned unexpected "
                                u"title '%s'" % pagedata['title'])
                            continue
                except KeyError:
                    pywikibot.debug(u"No 'title' in %s" % pagedata, _logger)
                    pywikibot.debug(u"pageids=%s" % pageids, _logger)
                    pywikibot.debug(u"titles=%s" % list(cache.keys()), _logger)
                    continue
                page = cache[pagedata['title']]
                api.update_page(page, pagedata, rvgen.props)
                yield page

    def validate_tokens(self, types):
        """Validate if requested tokens are acceptable.

        Valid tokens depend on mw version.

        """
        _version = MediaWikiVersion(self.version())
        if _version < MediaWikiVersion('1.20'):
            valid_types = [token for token in types if token in self.TOKENS_0]

            # Pre 1.17, preload token was the same as the edit token.
            if _version < MediaWikiVersion('1.17'):
                if 'patrol' in types and 'edit' not in valid_types:
                    valid_types.append('edit')

        elif _version < MediaWikiVersion('1.24wmf19'):
            valid_types = [token for token in types if token in self.TOKENS_1]
        else:
            valid_types = []
            for token in types:
                if ((token in self.TOKENS_0 or token in self.TOKENS_1) and
                        token not in self.TOKENS_2):
                    token = 'csrf'
                if token in self.TOKENS_2:
                    valid_types.append(token)

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

        @param types: the types of token (e.g., "edit", "move", "delete");
            see API documentation for full list of types
        @type  types: iterable
        @param all: load all available tokens, if None only if it can be done
            in one request.
        @type all: bool

        return: a dict with retrieved valid tokens.

        """
        def warn_handler(mod, text):
            """Filter warnings for not available tokens."""
            return re.match(r'Action \'\w+\' is not allowed for the current user',
                            text)

        user_tokens = {}
        _version = MediaWikiVersion(self.version())
        if _version < MediaWikiVersion('1.20'):
            if all:
                types.extend(self.TOKENS_0)
            valid_tokens = set(self.validate_tokens(types))
            # don't request patrol
            query = api.PropertyGenerator('info',
                                          titles='Dummy page',
                                          intoken=valid_tokens - set(['patrol']),
                                          site=self)
            query.request._warning_handler = warn_handler

            for item in query:
                pywikibot.debug(unicode(item), _logger)
                for tokentype in valid_tokens:
                    if (tokentype + 'token') in item:
                        user_tokens[tokentype] = item[tokentype + 'token']

            # patrol token require special handling.
            # TODO: try to catch exceptions?
            if 'patrol' in valid_tokens:
                if MediaWikiVersion('1.14') <= _version < MediaWikiVersion('1.17'):
                    user_tokens['patrol'] = user_tokens['edit']
                else:
                    req = api.Request(site=self, action='query',
                                      list='recentchanges',
                                      rctoken='patrol', rclimit=1)

                    req._warning_handler = warn_handler
                    data = req.submit()

                    if 'query' in data:
                        data = data['query']
                    if 'recentchanges' in data:
                        item = data['recentchanges'][0]
                        pywikibot.debug(unicode(item), _logger)
                        if 'patroltoken' in item:
                            user_tokens['patrol'] = item['patroltoken']
        else:
            if _version < MediaWikiVersion('1.24wmf19'):
                if all is not False:
                    types.extend(self.TOKENS_1)
                req = api.Request(site=self, action='tokens',
                                   type='|'.join(self.validate_tokens(types)))
            else:
                if all is not False:
                    types.extend(self.TOKENS_2)

                req = api.Request(site=self, action='query', meta='tokens',
                                   type='|'.join(self.validate_tokens(types)))

            req._warning_handler = warn_handler
            data = req.submit()

            if 'query' in data:
                data = data['query']

            if 'tokens' in data and data['tokens']:
                user_tokens = dict((key[:-5], val)
                                    for key, val in data['tokens'].items()
                                    if val != '+\\')

        return user_tokens

    @deprecated("the 'tokens' property")
    def token(self, page, tokentype):
        """Return token retrieved from wiki to allow changing page content.

        @param page: the Page for which a token should be retrieved
        @param tokentype: the type of token (e.g., "edit", "move", "delete");
            see API documentation for full list of types

        """
        return self.tokens[tokentype]

    # following group of methods map more-or-less directly to API queries

    def pagebacklinks(self, page, followRedirects=False, filterRedirects=None,
                      namespaces=None, step=None, total=None, content=False):
        """Iterate all pages that link to the given page.

        @param page: The Page to get links to.
        @param followRedirects: Also return links to redirects pointing to
            the given page.
        @param filterRedirects: If True, only return redirects to the given
            page. If False, only return non-redirect links. If None, return
            both (no filtering).
        @param namespaces: If present, only return links from the namespaces
            in this list.
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types.  May be a '|' separated
            list of namespace identifiers.
        @param step: Limit on number of pages to retrieve per API query.
        @param total: Maximum number of pages to retrieve in total.
        @param content: if True, load the current content of each iterated page
            (default False)
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        bltitle = page.title(withSection=False).encode(self.encoding())
        blargs = {"gbltitle": bltitle}
        if filterRedirects is not None:
            blargs["gblfilterredir"] = (filterRedirects and "redirects" or
                                        "nonredirects")
        blgen = self._generator(api.PageGenerator, type_arg="backlinks",
                                namespaces=namespaces, step=step, total=total,
                                g_content=content, **blargs)
        if followRedirects:
            # bug: see https://bugzilla.wikimedia.org/show_bug.cgi?id=7304
            # links identified by MediaWiki as redirects may not really be,
            # so we have to check each "redirect" page and see if it
            # really redirects to this page
            redirgen = self._generator(api.PageGenerator,
                                       type_arg="backlinks",
                                       gbltitle=bltitle,
                                       gblfilterredir="redirects")
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
                        redir, followRedirects=True,
                        filterRedirects=filterRedirects,
                        namespaces=namespaces,
                        content=content
                    )
            return itertools.chain(*list(genlist.values()))
        return blgen

    def page_embeddedin(self, page, filterRedirects=None, namespaces=None,
                        step=None, total=None, content=False):
        """Iterate all pages that embedded the given page as a template.

        @param page: The Page to get inclusions for.
        @param filterRedirects: If True, only return redirects that embed
            the given page. If False, only return non-redirect links. If
            None, return both (no filtering).
        @param namespaces: If present, only return links from the namespaces
            in this list.
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types.  May be a '|' separated
            list of namespace identifiers.
        @param content: if True, load the current content of each iterated page
            (default False)
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        eiargs = {"geititle":
                  page.title(withSection=False).encode(self.encoding())}
        if filterRedirects is not None:
            eiargs["geifilterredir"] = (filterRedirects and "redirects" or
                                        "nonredirects")
        eigen = self._generator(api.PageGenerator, type_arg="embeddedin",
                                namespaces=namespaces, step=step, total=total,
                                g_content=content, **eiargs)
        return eigen

    def pagereferences(self, page, followRedirects=False, filterRedirects=None,
                       withTemplateInclusion=True, onlyTemplateInclusion=False,
                       namespaces=None, step=None, total=None, content=False):
        """
        Convenience method combining pagebacklinks and page_embeddedin.

        @param namespaces: If present, only return links from the namespaces
            in this list.
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types.  May be a '|' separated
            list of namespace identifiers.
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if onlyTemplateInclusion:
            return self.page_embeddedin(page, namespaces=namespaces,
                                        filterRedirects=filterRedirects,
                                        step=step, total=total, content=content)
        if not withTemplateInclusion:
            return self.pagebacklinks(page, followRedirects=followRedirects,
                                      filterRedirects=filterRedirects,
                                      namespaces=namespaces,
                                      step=step, total=total, content=content)
        return itertools.islice(
            itertools.chain(
                self.pagebacklinks(
                    page, followRedirects, filterRedirects,
                    namespaces=namespaces, step=step, content=content),
                self.page_embeddedin(
                    page, filterRedirects, namespaces=namespaces,
                    step=step, content=content)
            ), total)

    def pagelinks(self, page, namespaces=None, follow_redirects=False,
                  step=None, total=None, content=False):
        """Iterate internal wikilinks contained (or transcluded) on page.

        @param namespaces: Only iterate pages in these namespaces (default: all)
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types.  May be a '|' separated
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
        if hasattr(page, "_pageid"):
            plargs['pageids'] = str(page._pageid)
        else:
            pltitle = page.title(withSection=False).encode(self.encoding())
            plargs['titles'] = pltitle
        plgen = self._generator(api.PageGenerator, type_arg="links",
                                namespaces=namespaces, step=step, total=total,
                                g_content=content, redirects=follow_redirects,
                                **plargs)
        return plgen

    @deprecate_arg("withSortKey", None)  # Sortkey doesn't work with generator
    def pagecategories(self, page, step=None, total=None, content=False):
        """Iterate categories to which page belongs.

        @param content: if True, load the current content of each iterated page
            (default False); note that this means the contents of the
            category description page, not the pages contained in the category

        """
        clargs = {}
        if hasattr(page, "_pageid"):
            clargs['pageids'] = str(page._pageid)
        else:
            clargs['titles'] = page.title(
                withSection=False).encode(self.encoding())
        clgen = self._generator(api.CategoryPageGenerator,
                                type_arg="categories", step=step, total=total,
                                g_content=content, **clargs)
        return clgen

    def pageimages(self, page, step=None, total=None, content=False):
        """Iterate images used (not just linked) on the page.

        @param content: if True, load the current content of each iterated page
            (default False); note that this means the content of the image
            description page, not the image itself

        """
        imtitle = page.title(withSection=False).encode(self.encoding())
        imgen = self._generator(api.ImagePageGenerator, type_arg="images",
                                titles=imtitle, step=step, total=total,
                                g_content=content)
        return imgen

    def pagetemplates(self, page, namespaces=None, step=None, total=None,
                      content=False):
        """Iterate templates transcluded (not just linked) on the page.

        @param namespaces: Only iterate pages in these namespaces
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types.  May be a '|' separated
            list of namespace identifiers.
        @param content: if True, load the current content of each iterated page
            (default False)

        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        tltitle = page.title(withSection=False).encode(self.encoding())
        tlgen = self._generator(api.PageGenerator, type_arg="templates",
                                titles=tltitle, namespaces=namespaces,
                                step=step, total=total, g_content=content)
        return tlgen

    def categorymembers(self, category, namespaces=None, sortby=None,
                        reverse=False, starttime=None, endtime=None,
                        startsort=None, endsort=None, step=None, total=None,
                        content=False, member_type=None):
        """Iterate members of specified category.

        @param category: The Category to iterate.
        @param namespaces: If present, only return category members from
            these namespaces. To yield subcategories or files, use
            parameter member_type instead.
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types.  May be a '|' separated
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
        @type endtime: pywikibot.Timestamp
        @param startsort: if provided, only generate pages >= this title
            lexically; not valid if sortby="timestamp"
        @type startsort: str
        @param endsort: if provided, only generate pages <= this title
            lexically; not valid if sortby="timestamp"
        @type endsort: str
        @param content: if True, load the current content of each iterated page
            (default False)
        @type content: bool
        @param member_type: member type; if member_type includes 'page' and is
            used in conjunction with sortby="timestamp", the API may limit
            results to only pages in the first 50 namespaces.
        @type member_type: str or iterable of str; values: page, subcat, file

        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if category.namespace() != 14:
            raise Error(
                u"categorymembers: non-Category page '%s' specified"
                % category.title())
        cmtitle = category.title(withSection=False).encode(self.encoding())
        cmargs = dict(type_arg="categorymembers",
                      gcmtitle=cmtitle,
                      gcmprop="ids|title|sortkey")
        if sortby in ["sortkey", "timestamp"]:
            cmargs["gcmsort"] = sortby
        elif sortby:
            raise ValueError(
                "categorymembers: invalid sortby value '%s'"
                % sortby)
        if starttime and endtime and starttime > endtime:
            raise ValueError(
                "categorymembers: starttime must be before endtime")
        if startsort and endsort and startsort > endsort:
            raise ValueError(
                "categorymembers: startsort must be less than endsort")

        if isinstance(member_type, basestring):
            member_type = set([member_type])

        if (member_type and
                (sortby == 'timestamp' or
                 MediaWikiVersion(self.version()) < MediaWikiVersion("1.12"))):
            # Retrofit cmtype/member_type, available on MW API 1.12+,
            # to use namespaces available on earlier versions.

            # Covert namespaces to a known type
            namespaces = set(Namespace.resolve(namespaces or [],
                                               self.namespaces()))

            if 'page' in member_type:
                excluded_namespaces = set()
                if 'file' not in member_type:
                    excluded_namespaces.add(6)
                if 'subcat' not in member_type:
                    excluded_namespaces.add(14)

                if namespaces:
                    if excluded_namespaces.intersect(namespaces):
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
                    excluded_namespaces.add([-1, -2])
                    namespaces = set(self.namespaces()) - excluded_namespaces
            else:
                if 'file' in member_type:
                    namespaces.add(6)
                if 'subcat' in member_type:
                    namespaces.add(14)

            member_type = None

        if member_type:
            cmargs['gcmtype'] = member_type

        if reverse:
            cmargs["gcmdir"] = "desc"
            # API wants start/end params in opposite order if using descending
            # sort; we take care of this reversal for the user
            (starttime, endtime) = (endtime, starttime)
            (startsort, endsort) = (endsort, startsort)
        if starttime and sortby == "timestamp":
            cmargs["gcmstart"] = starttime
        elif starttime:
            raise ValueError("categorymembers: "
                             "invalid combination of 'sortby' and 'starttime'")
        if endtime and sortby == "timestamp":
            cmargs["gcmend"] = endtime
        elif endtime:
            raise ValueError("categorymembers: "
                             "invalid combination of 'sortby' and 'endtime'")
        if startsort and sortby != "timestamp":
            cmargs["gcmstartsortkey"] = startsort
        elif startsort:
            raise ValueError("categorymembers: "
                             "invalid combination of 'sortby' and 'startsort'")
        if endsort and sortby != "timestamp":
            cmargs["gcmendsortkey"] = endsort
        elif endsort:
            raise ValueError("categorymembers: "
                             "invalid combination of 'sortby' and 'endsort'")

        cmgen = self._generator(api.PageGenerator, namespaces=namespaces,
                                step=step, total=total, g_content=content,
                                **cmargs)
        return cmgen

    def loadrevisions(self, page, getText=False, revids=None,
                      startid=None, endid=None, starttime=None,
                      endtime=None, rvdir=None, user=None, excludeuser=None,
                      section=None, sysop=False, step=None, total=None, rollback=False):
        """Retrieve and store revision information.

        By default, retrieves the last (current) revision of the page,
        unless any of the optional parameters revids, startid, endid,
        starttime, endtime, rvdir, user, excludeuser, or limit are
        specified. Unless noted below, all parameters not specified
        default to False.

        If rvdir is False or not specified, startid must be greater than
        endid if both are specified; likewise, starttime must be greater
        than endtime. If rvdir is True, these relationships are reversed.

        @param page: retrieve revisions of this Page (required unless ids
            is specified)
        @param getText: if True, retrieve the wiki-text of each revision;
            otherwise, only retrieve the revision metadata (default)
        @param section: if specified, retrieve only this section of the text
            (getText must be True); section must be given by number (top of
            the article is section 0), not name
        @type section: int
        @param revids: retrieve only the specified revision ids (raise
            Exception if any of revids does not correspond to page
        @type revids: an int, a str or a list of ints or strings
        @param startid: retrieve revisions starting with this revid
        @param endid: stop upon retrieving this revid
        @param starttime: retrieve revisions starting at this Timestamp
        @param endtime: stop upon reaching this Timestamp
        @param rvdir: if false, retrieve newest revisions first (default);
            if true, retrieve earliest first
        @param user: retrieve only revisions authored by this user
        @param excludeuser: retrieve all revisions not authored by this user
        @param sysop: if True, switch to sysop account (if available) to
            retrieve this page

        """
        latest = (revids is None and
                  startid is None and
                  endid is None and
                  starttime is None and
                  endtime is None and
                  rvdir is None and
                  user is None and
                  excludeuser is None and
                  step is None and
                  total is None)  # if True, retrieving current revision

        # check for invalid argument combinations
        if (startid is not None or endid is not None) and \
                (starttime is not None or endtime is not None):
            raise ValueError(
                "loadrevisions: startid/endid combined with starttime/endtime")
        if starttime is not None and endtime is not None:
            if rvdir and starttime >= endtime:
                raise ValueError(
                    "loadrevisions: starttime > endtime with rvdir=True")
            if (not rvdir) and endtime >= starttime:
                raise ValueError(
                    "loadrevisions: endtime > starttime with rvdir=False")
        if startid is not None and endid is not None:
            if rvdir and startid >= endid:
                raise ValueError(
                    "loadrevisions: startid > endid with rvdir=True")
            if (not rvdir) and endid >= startid:
                raise ValueError(
                    "loadrevisions: endid > startid with rvdir=False")

        rvargs = dict(type_arg=u"info|revisions")

        if getText:
            rvargs[u"rvprop"] = u"ids|flags|timestamp|user|comment|content"
            if section is not None:
                rvargs[u"rvsection"] = unicode(section)
        if rollback:
            self.login(sysop=sysop)
            rvargs[u"rvtoken"] = "rollback"
        if revids is None:
            rvtitle = page.title(withSection=False).encode(self.encoding())
            rvargs[u"titles"] = rvtitle
        else:
            if isinstance(revids, (int, basestring)):
                ids = unicode(revids)
            else:
                ids = u"|".join(unicode(r) for r in revids)
            rvargs[u"revids"] = ids

        if rvdir:
            rvargs[u"rvdir"] = u"newer"
        elif rvdir is not None:
            rvargs[u"rvdir"] = u"older"
        if startid:
            rvargs[u"rvstartid"] = startid
        if endid:
            rvargs[u"rvendid"] = endid
        if starttime:
            rvargs[u"rvstart"] = starttime
        if endtime:
            rvargs[u"rvend"] = endtime
        if user:
            rvargs[u"rvuser"] = user
        elif excludeuser:
            rvargs[u"rvexcludeuser"] = excludeuser
        # TODO if sysop: something

        # assemble API request
        rvgen = self._generator(api.PropertyGenerator,
                                step=step, total=total, **rvargs)

        if latest or "revids" in rvgen.request:
            rvgen.set_maximum_items(-1)  # suppress use of rvlimit parameter

        for pagedata in rvgen:
            if not self.sametitle(pagedata['title'],
                                  page.title(withSection=False)):
                raise Error(
                    u"loadrevisions: Query on %s returned data on '%s'"
                    % (page, pagedata['title']))
            if "missing" in pagedata:
                raise NoPage(page)
            api.update_page(page, pagedata, rvgen.props)

    def pageinterwiki(self, page):
        # No such function in the API (this method isn't called anywhere)
        raise NotImplementedError

    def pagelanglinks(self, page, step=None, total=None,
                      include_obsolete=False):
        """Iterate all interlanguage links on page, yielding Link objects.

        @param include_obsolete: if true, yield even Link objects whose
                                 site is obsolete

        """
        lltitle = page.title(withSection=False)
        llquery = self._generator(api.PropertyGenerator,
                                  type_arg="langlinks",
                                  titles=lltitle.encode(self.encoding()),
                                  step=step, total=total)
        for pageitem in llquery:
            if not self.sametitle(pageitem['title'], lltitle):
                raise Error(
                    u"getlanglinks: Query on %s returned data on '%s'"
                    % (page, pageitem['title']))
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

    def page_extlinks(self, page, step=None, total=None):
        """Iterate all external links on page, yielding URL strings."""
        eltitle = page.title(withSection=False)
        elquery = self._generator(api.PropertyGenerator, type_arg="extlinks",
                                  titles=eltitle.encode(self.encoding()),
                                  step=step, total=total)
        for pageitem in elquery:
            if not self.sametitle(pageitem['title'], eltitle):
                raise RuntimeError(
                    "getlanglinks: Query on %s returned data on '%s'"
                    % (page, pageitem['title']))
            if 'extlinks' not in pageitem:
                continue
            for linkdata in pageitem['extlinks']:
                yield linkdata['*']

    def getcategoryinfo(self, category):
        """Retrieve data on contents of category."""
        cititle = category.title(withSection=False)
        ciquery = self._generator(api.PropertyGenerator,
                                  type_arg="categoryinfo",
                                  titles=cititle.encode(self.encoding()))
        self._update_page(category, ciquery, 'categoryinfo')

    def categoryinfo(self, category):
        if not hasattr(category, "_catinfo"):
            self.getcategoryinfo(category)
        if not hasattr(category, "_catinfo"):
            # a category that exists but has no contents returns no API result
            category._catinfo = {'size': 0, 'pages': 0, 'files': 0,
                                 'subcats': 0}
        return category._catinfo

    @deprecated_args(throttle=None, limit="total", includeredirects="filterredir")
    def allpages(self, start="!", prefix="", namespace=0, filterredir=None,
                 filterlanglinks=None, minsize=None, maxsize=None,
                 protect_type=None, protect_level=None, reverse=False,
                 includeredirects=None, step=None, total=None, content=False):
        """Iterate pages in a single namespace.

        Note: parameters includeRedirects and throttle are deprecated and
        included only for backwards compatibility.

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
        @param includeredirects: DEPRECATED, use filterredir instead
        @param content: if True, load the current content of each iterated page
            (default False)
        @raises KeyError: the namespace identifier was not resolved
        @raises TypeError: the namespace identifier has an inappropriate
            type such as bool, or an iterable with more than one namespace
        """
        if includeredirects is not None:
            if includeredirects:
                if includeredirects == "only":
                    filterredir = True
                else:
                    filterredir = None
            else:
                filterredir = False

        apgen = self._generator(api.PageGenerator, type_arg="allpages",
                                namespaces=namespace,
                                gapfrom=start, step=step, total=total,
                                g_content=content)
        if prefix:
            apgen.request["gapprefix"] = prefix
        if filterredir is not None:
            apgen.request['gapfilterredir'] = ('redirects' if filterredir else
                                               'nonredirects')
        if filterlanglinks is not None:
            apgen.request['gapfilterlanglinks'] = ('withlanglinks'
                                                   if filterlanglinks else
                                                   'withoutlanglinks')
        if isinstance(minsize, int):
            apgen.request["gapminsize"] = str(minsize)
        if isinstance(maxsize, int):
            apgen.request["gapmaxsize"] = str(maxsize)
        if isinstance(protect_type, basestring):
            apgen.request["gapprtype"] = protect_type
            if isinstance(protect_level, basestring):
                apgen.request["gapprlevel"] = protect_level
        if reverse:
            apgen.request["gapdir"] = "descending"
        return apgen

    @deprecated("Site.allpages()")
    def prefixindex(self, prefix, namespace=0, includeredirects=True):
        """Yield all pages with a given prefix. Deprecated.

        Use allpages() with the prefix= parameter instead of this method.

        """
        return self.allpages(prefix=prefix, namespace=namespace,
                             includeredirects=includeredirects)

    def alllinks(self, start="!", prefix="", namespace=0, unique=False,
                 fromids=False, step=None, total=None):
        """Iterate all links to pages (which need not exist) in one namespace.

        Note that, in practice, links that were found on pages that have
        been deleted may not have been removed from the links table, so this
        method can return false positives.

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
            raise Error("alllinks: unique and fromids cannot both be True.")
        algen = self._generator(api.ListGenerator, type_arg="alllinks",
                                namespaces=namespace, alfrom=start,
                                step=step, total=total, alunique=unique)
        if prefix:
            algen.request["alprefix"] = prefix
        if fromids:
            algen.request["alprop"] = "title|ids"
        for link in algen:
            p = pywikibot.Page(self, link['title'], link['ns'])
            if fromids:
                p._fromid = link['fromid']
            yield p

    def allcategories(self, start="!", prefix="", step=None, total=None,
                      reverse=False, content=False):
        """Iterate categories used (which need not have a Category page).

        Iterator yields Category objects. Note that, in practice, links that
        were found on pages that have been deleted may not have been removed
        from the database table, so this method can return false positives.

        @param start: Start at this category title (category need not exist).
        @param prefix: Only yield categories starting with this string.
        @param reverse: if True, iterate in reverse Unicode lexigraphic
            order (default: iterate in forward order)
        @param content: if True, load the current content of each iterated page
            (default False); note that this means the contents of the category
            description page, not the pages that are members of the category

        """
        acgen = self._generator(api.CategoryPageGenerator,
                                type_arg="allcategories", gacfrom=start,
                                step=step, total=total, g_content=content)
        if prefix:
            acgen.request["gacprefix"] = prefix
        if reverse:
            acgen.request["gacdir"] = "descending"
        return acgen

    @deprecated("Site.allcategories()")
    def categories(self, number=10, repeat=False):
        """DEPRECATED."""
        if repeat:
            limit = None
        else:
            limit = number
        return self.allcategories(total=limit)

    def isBot(self, username):
        """Return True is username is a bot user."""
        return username in [userdata['name'] for userdata in self.botusers()]

    def botusers(self, step=None, total=None):
        """Iterate bot users.

        Iterated values are dicts containing 'name', 'userid', 'editcount',
        'registration', and 'groups' keys. 'groups' will be present only if
        the user is a member of at least 1 group, and will be a list of
        unicodes; all the other values are unicodes and should always be
        present.

        """
        if not hasattr(self, "_bots"):
            self._bots = {}

        if not self._bots:
            for item in self.allusers(group='bot', step=step, total=total):
                self._bots.setdefault(item['name'], item)

        for value in self._bots.values():
            yield value

    def allusers(self, start="!", prefix="", group=None, step=None,
                 total=None):
        """Iterate registered users, ordered by username.

        Iterated values are dicts containing 'name', 'editcount',
        'registration', and (sometimes) 'groups' keys. 'groups' will be
        present only if the user is a member of at least 1 group, and will
        be a list of unicodes; all the other values are unicodes and should
        always be present.

        @param start: start at this username (name need not exist)
        @param prefix: only iterate usernames starting with this substring
        @param group: only iterate users that are members of this group
        @type group: str

        """
        augen = self._generator(api.ListGenerator, type_arg="allusers",
                                auprop="editcount|groups|registration",
                                aufrom=start, step=step, total=total)
        if prefix:
            augen.request["auprefix"] = prefix
        if group:
            augen.request["augroup"] = group
        return augen

    def allimages(self, start="!", prefix="", minsize=None, maxsize=None,
                  reverse=False, sha1=None, sha1base36=None, step=None,
                  total=None, content=False):
        """Iterate all images, ordered by image title.

        Yields FilePages, but these pages need not exist on the wiki.

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
        aigen = self._generator(api.ImagePageGenerator,
                                type_arg="allimages", gaifrom=start,
                                step=step, total=total, g_content=content)
        if prefix:
            aigen.request["gaiprefix"] = prefix
        if isinstance(minsize, int):
            aigen.request["gaiminsize"] = str(minsize)
        if isinstance(maxsize, int):
            aigen.request["gaimaxsize"] = str(maxsize)
        if reverse:
            aigen.request["gaidir"] = "descending"
        if sha1:
            aigen.request["gaisha1"] = sha1
        if sha1base36:
            aigen.request["gaisha1base36"] = sha1base36
        return aigen

    def blocks(self, starttime=None, endtime=None, reverse=False,
               blockids=None, users=None, step=None, total=None):
        """Iterate all current blocks, in order of creation.

        Note that logevents only logs user blocks, while this method
        iterates all blocks including IP ranges.  The iterator yields dicts
        containing keys corresponding to the block properties (see
        https://www.mediawiki.org/wiki/API:Query_-_Lists for documentation).

        @param starttime: start iterating at this Timestamp
        @param endtime: stop iterating at this Timestamp
        @param reverse: if True, iterate oldest blocks first (default: newest)
        @param blockids: only iterate blocks with these id numbers
        @param users: only iterate blocks affecting these usernames or IPs

        """
        if starttime and endtime:
            if reverse:
                if starttime > endtime:
                    raise Error(
                        "blocks: "
                        "starttime must be before endtime with reverse=True")
            else:
                if endtime > starttime:
                    raise Error(
                        "blocks: "
                        "endtime must be before starttime with reverse=False")
        bkgen = self._generator(api.ListGenerator, type_arg="blocks",
                                step=step, total=total)
        bkgen.request["bkprop"] = "id|user|by|timestamp|expiry|reason|range|flags"
        if starttime:
            bkgen.request["bkstart"] = starttime
        if endtime:
            bkgen.request["bkend"] = endtime
        if reverse:
            bkgen.request["bkdir"] = "newer"
        if blockids:
            bkgen.request["bkids"] = blockids
        if users:
            bkgen.request["bkusers"] = users
        return bkgen

    def exturlusage(self, url, protocol="http", namespaces=None,
                    step=None, total=None, content=False):
        """Iterate Pages that contain links to the given URL.

        @param url: The URL to search for (without the protocol prefix);
            this many include a '*' as a wildcard, only at the start of the
            hostname
        @param protocol: The protocol prefix (default: "http")

        """
        eugen = self._generator(api.PageGenerator, type_arg="exturlusage",
                                geuquery=url, geuprotocol=protocol,
                                namespaces=namespaces, step=step,
                                total=total, g_content=content)
        return eugen

    def imageusage(self, image, namespaces=None, filterredir=None,
                   step=None, total=None, content=False):
        """Iterate Pages that contain links to the given FilePage.

        @param image: the image to search for (FilePage need not exist on
            the wiki)
        @type image: FilePage
        @param namespaces: If present, only iterate pages in these namespaces
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types.  May be a '|' separated
            list of namespace identifiers.
        @param filterredir: if True, only yield redirects; if False (and not
            None), only yield non-redirects (default: yield both)
        @param content: if True, load the current content of each iterated page
            (default False)
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        iuargs = dict(giutitle=image.title(withSection=False))
        if filterredir is not None:
            iuargs['giufilterredir'] = ('redirects' if filterredir else
                                        'nonredirects')
        iugen = self._generator(api.PageGenerator, type_arg="imageusage",
                                namespaces=namespaces, step=step,
                                total=total, g_content=content, **iuargs)
        return iugen

    def logevents(self, logtype=None, user=None, page=None, namespace=None,
                  start=None, end=None, reverse=False, step=None, total=None):
        """Iterate all log entries.

        @param logtype: only iterate entries of this type (see wiki
            documentation for available types, which will include "block",
            "protect", "rights", "delete", "upload", "move", "import",
            "patrol", "merge")
        @param user: only iterate entries that match this user name
        @param page: only iterate entries affecting this page
        @param namespace: namespace to retrieve logevents from
        @type namespace: int or Namespace
        @param start: only iterate entries from and after this Timestamp
        @param end: only iterate entries up to and through this Timestamp
        @param reverse: if True, iterate oldest entries first (default: newest)
        @raises KeyError: the namespace identifier was not resolved
        @raises TypeError: the namespace identifier has an inappropriate
            type such as bool, or an iterable with more than one namespace
        """
        if start and end:
            self.assert_valid_iter_params('logevents', start, end, reverse)

        legen = self._generator(api.LogEntryListGenerator, type_arg=logtype,
                                step=step, total=total)
        if logtype is not None:
            legen.request["letype"] = logtype
        if user is not None:
            legen.request["leuser"] = user
        if page is not None:
            legen.request["letitle"] = page.title(withSection=False)
        if start is not None:
            legen.request["lestart"] = start
        if end is not None:
            legen.request["leend"] = end
        if reverse:
            legen.request["ledir"] = "newer"
        if namespace:
            legen.request["lenamespace"] = namespace
        return legen

    def recentchanges(self, start=None, end=None, reverse=False,
                      namespaces=None, pagelist=None, changetype=None,
                      showMinor=None, showBot=None, showAnon=None,
                      showRedirects=None, showPatrolled=None, topOnly=False,
                      step=None, total=None, user=None, excludeuser=None):
        """Iterate recent changes.

        @param start: Timestamp to start listing from
        @type start: pywikibot.Timestamp
        @param end: Timestamp to end listing at
        @type end: pywikibot.Timestamp
        @param reverse: if True, start with oldest changes (default: newest)
        @type reverse: bool
        @param namespaces: only iterate pages in these namespaces
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types.  May be a '|' separated
            list of namespace identifiers.
        @param pagelist: iterate changes to pages in this list only
        @param pagelist: list of Pages
        @param changetype: only iterate changes of this type ("edit" for
            edits to existing pages, "new" for new pages, "log" for log
            entries)
        @type changetype: basestring
        @param showMinor: if True, only list minor edits; if False, only list
            non-minor edits; if None, list all
        @type showMinor: bool or None
        @param showBot: if True, only list bot edits; if False, only list
            non-bot edits; if None, list all
        @type showBot: bool or None
        @param showAnon: if True, only list anon edits; if False, only list
            non-anon edits; if None, list all
        @type showAnon: bool or None
        @param showRedirects: if True, only list edits to redirect pages; if
            False, only list edits to non-redirect pages; if None, list all
        @type showRedirects: bool or None
        @param showPatrolled: if True, only list patrolled edits; if False,
            only list non-patrolled edits; if None, list all
        @type showPatrolled: bool or None
        @param topOnly: if True, only list changes that are the latest revision
            (default False)
        @type topOnly: bool
        @param user: if not None, only list edits by this user or users
        @type user: basestring|list
        @param excludeuser: if not None, exclude edits by this user or users
        @type excludeuser: basestring|list
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if start and end:
            self.assert_valid_iter_params('recentchanges', start, end, reverse)

        rcgen = self._generator(api.ListGenerator, type_arg="recentchanges",
                                rcprop="user|comment|timestamp|title|ids"
                                       "|sizes|redirect|loginfo|flags",
                                namespaces=namespaces, step=step,
                                total=total, rctoponly=topOnly)
        if start is not None:
            rcgen.request["rcstart"] = start
        if end is not None:
            rcgen.request["rcend"] = end
        if reverse:
            rcgen.request["rcdir"] = "newer"
        if pagelist:
            if MediaWikiVersion(self.version()) > MediaWikiVersion("1.14"):
                pywikibot.warning(
                    u"recentchanges: pagelist option is disabled; ignoring.")
            else:
                rcgen.request["rctitles"] = (p.title(withSection=False)
                                             for p in pagelist)
        if changetype:
            rcgen.request["rctype"] = changetype
        filters = {'minor': showMinor,
                   'bot': showBot,
                   'anon': showAnon,
                   'redirect': showRedirects,
                   }
        if showPatrolled is not None and (
                self.has_right('patrol') or self.has_right('patrolmarks')):
            rcgen.request['rcprop'] += ['patrolled']
            filters['patrolled'] = showPatrolled
        rcgen.request['rcshow'] = api.OptionSet(self, 'recentchanges', 'show',
                                                filters)

        if user:
            rcgen.request['rcuser'] = user

        if excludeuser:
            rcgen.request['rcexcludeuser'] = excludeuser

        return rcgen

    @deprecated_args(number="total")
    def search(self, searchstring, namespaces=None, where="text",
               getredirects=False, step=None, total=None, content=False):
        """Iterate Pages that contain the searchstring.

        Note that this may include non-existing Pages if the wiki's database
        table contains outdated entries.

        @param searchstring: the text to search for
        @type searchstring: unicode
        @param where: Where to search; value must be "text" or "titles" (many
            wikis do not support title search)
        @param namespaces: search only in these namespaces (defaults to all)
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types.  May be a '|' separated
            list of namespace identifiers.
        @param getredirects: if True, include redirects in results. Since
            version MediaWiki 1.23 it will always return redirects.
        @param content: if True, load the current content of each iterated page
            (default False)
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if not searchstring:
            raise Error("search: searchstring cannot be empty")
        if where not in ("text", "titles"):
            raise Error("search: unrecognized 'where' value: %s" % where)
        if namespaces == []:
            namespaces = [ns for ns in list(self.namespaces().keys()) if ns >= 0]
        if not namespaces:
            pywikibot.warning(u"search: namespaces cannot be empty; using [0].")
            namespaces = [0]
        srgen = self._generator(api.PageGenerator, type_arg="search",
                                gsrsearch=searchstring, gsrwhat=where,
                                namespaces=namespaces, step=step,
                                total=total, g_content=content)
        if MediaWikiVersion(self.version()) < MediaWikiVersion('1.23'):
            srgen.request['gsrredirects'] = getredirects
        return srgen

    def usercontribs(self, user=None, userprefix=None, start=None, end=None,
                     reverse=False, namespaces=None, showMinor=None,
                     step=None, total=None, top_only=False):
        """Iterate contributions by a particular user.

        Iterated values are in the same format as recentchanges.

        @param user: Iterate contributions by this user (name or IP)
        @param userprefix: Iterate contributions by all users whose names
            or IPs start with this substring
        @param start: Iterate contributions starting at this Timestamp
        @param end: Iterate contributions ending at this Timestamp
        @param reverse: Iterate oldest contributions first (default: newest)
        @param namespaces: only iterate pages in these namespaces
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types.  May be a '|' separated
            list of namespace identifiers.
        @param showMinor: if True, iterate only minor edits; if False and
            not None, iterate only non-minor edits (default: iterate both)
        @param top_only: if True, iterate only edits which are the latest
            revision
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if not (user or userprefix):
            raise Error(
                "usercontribs: either user or userprefix must be non-empty")

        if start and end:
            self.assert_valid_iter_params('usercontribs', start, end, reverse)

        ucgen = self._generator(api.ListGenerator, type_arg="usercontribs",
                                ucprop="ids|title|timestamp|comment|flags",
                                namespaces=namespaces, step=step,
                                total=total, uctoponly=top_only)
        if user:
            ucgen.request["ucuser"] = user
        if userprefix:
            ucgen.request["ucuserprefix"] = userprefix
        if start is not None:
            ucgen.request["ucstart"] = str(start)
        if end is not None:
            ucgen.request["ucend"] = str(end)
        if reverse:
            ucgen.request["ucdir"] = "newer"
        option_set = api.OptionSet(self, 'usercontribs', 'show')
        option_set['minor'] = showMinor
        ucgen.request['ucshow'] = option_set
        return ucgen

    def watchlist_revs(self, start=None, end=None, reverse=False,
                       namespaces=None, showMinor=None, showBot=None,
                       showAnon=None, step=None, total=None):
        """Iterate revisions to pages on the bot user's watchlist.

        Iterated values will be in same format as recentchanges.

        @param start: Iterate revisions starting at this Timestamp
        @param end: Iterate revisions ending at this Timestamp
        @param reverse: Iterate oldest revisions first (default: newest)
        @param namespaces: only iterate pages in these namespaces
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types.  May be a '|' separated
            list of namespace identifiers.
        @param showMinor: if True, only list minor edits; if False (and not
            None), only list non-minor edits
        @param showBot: if True, only list bot edits; if False (and not
            None), only list non-bot edits
        @param showAnon: if True, only list anon edits; if False (and not
            None), only list non-anon edits
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if start and end:
            self.assert_valid_iter_params('watchlist_revs', start, end, reverse)

        wlgen = self._generator(api.ListGenerator, type_arg="watchlist",
                                wlprop="user|comment|timestamp|title|ids|flags",
                                wlallrev="", namespaces=namespaces,
                                step=step, total=total)
        # TODO: allow users to ask for "patrol" as well?
        if start is not None:
            wlgen.request["wlstart"] = start
        if end is not None:
            wlgen.request["wlend"] = end
        if reverse:
            wlgen.request["wldir"] = "newer"
        filters = {'minor': showMinor,
                   'bot': showBot,
                   'anon': showAnon}
        wlgen.request['wlshow'] = api.OptionSet(self, 'watchlist', 'show',
                                                filters)
        return wlgen

    # TODO: T75370
    def deletedrevs(self, page, start=None, end=None, reverse=None,
                    get_text=False, step=None, total=None):
        """Iterate deleted revisions.

        Each value returned by the iterator will be a dict containing the
        'title' and 'ns' keys for a particular Page and a 'revisions' key
        whose value is a list of revisions in the same format as
        recentchanges (plus a 'content' element if requested). If get_text
        is true, the toplevel dict will contain a 'token' key as well.

        @param page: The page to check for deleted revisions
        @param start: Iterate revisions starting at this Timestamp
        @param end: Iterate revisions ending at this Timestamp
        @param reverse: Iterate oldest revisions first (default: newest)
        @param get_text: If True, retrieve the content of each revision and
            an undelete token

        """
        if start and end:
            self.assert_valid_iter_params('deletedrevs', start, end, reverse)

        if not self.logged_in():
            self.login()
        if "deletedhistory" not in self.userinfo['rights']:
            try:
                self.login(True)
            except NoUsername:
                pass
            if "deletedhistory" not in self.userinfo['rights']:
                raise Error(
                    "deletedrevs: "
                    "User:%s not authorized to access deleted revisions."
                    % self.user())
        if get_text:
            if "undelete" not in self.userinfo['rights']:
                try:
                    self.login(True)
                except NoUsername:
                    pass
                if "undelete" not in self.userinfo['rights']:
                    raise Error(
                        "deletedrevs: "
                        "User:%s not authorized to view deleted content."
                        % self.user())

        drgen = self._generator(api.ListGenerator, type_arg="deletedrevs",
                                titles=page.title(withSection=False),
                                drprop="revid|user|comment|minor",
                                step=step, total=total)
        if get_text:
            drgen.request['drprop'] = (drgen.request['drprop'] +
                                       "|content|token")
        if start is not None:
            drgen.request["drstart"] = start
        if end is not None:
            drgen.request["drend"] = end
        if reverse:
            drgen.request["drdir"] = "newer"
        return drgen

    def users(self, usernames):
        """Iterate info about a list of users by name or IP.

        @param usernames: a list of user names
        @type usernames: list, or other iterable, of unicodes

        """
        if not isinstance(usernames, basestring):
            usernames = u"|".join(usernames)
        usgen = api.ListGenerator(
            "users", ususers=usernames, site=self,
            usprop="blockinfo|groups|editcount|registration|emailable"
        )
        return usgen

    @deprecated("Site.randompages()")
    def randompage(self, redirect=False):
        """
        DEPRECATED.

        @param redirect: Return a random redirect page
        @return: pywikibot.Page
        """
        return self.randompages(total=1, redirects=redirect)

    @deprecated("Site.randompages()")
    def randomredirectpage(self):
        """
        DEPRECATED: Use Site.randompages() instead.

        @return: Return a random redirect page
        """
        return self.randompages(total=1, redirects=True)

    def randompages(self, step=None, total=10, namespaces=None,
                    redirects=False, content=False):
        """Iterate a number of random pages.

        Pages are listed in a fixed sequence, only the starting point is
        random.

        @param total: the maximum number of pages to iterate (default: 1)
        @param namespaces: only iterate pages in these namespaces.
        @type namespaces: iterable of basestring or Namespace key,
            or a single instance of those types.  May be a '|' separated
            list of namespace identifiers.
        @param redirects: if True, include only redirect pages in results
            (default: include only non-redirects)
        @param content: if True, load the current content of each iterated page
            (default False)
        @raises KeyError: a namespace identifier was not resolved
        @raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        rngen = self._generator(api.PageGenerator, type_arg="random",
                                namespaces=namespaces, step=step, total=total,
                                g_content=content, grnredirect=redirects)
        return rngen

    # Catalog of editpage error codes, for use in generating messages.
    # The block at the bottom are page related errors.
    _ep_errors = {
        "noapiwrite": "API editing not enabled on %(site)s wiki",
        "writeapidenied": "User %(user)s is not authorized to edit on %(site)s wiki",
        "cantcreate": "User %(user)s not authorized to create new pages on %(site)s wiki",
        "cantcreate-anon":
            "Bot is not logged in, and anon users are not authorized to create "
            "new pages on %(site)s wiki",
        "noimageredirect-anon":
            "Bot is not logged in, and anon users are not authorized to create "
            "image redirects on %(site)s wiki",
        "noimageredirect": "User %(user)s not authorized to create image redirects on %(site)s wiki",
        "filtered": "%(info)s",
        "contenttoobig": "%(info)s",
        "noedit-anon": "Bot is not logged in, and anon users are not authorized to edit on %(site)s wiki",
        "noedit": "User %(user)s not authorized to edit pages on %(site)s wiki",

        "missingtitle": NoCreateError,
        "editconflict": EditConflict,
        "articleexists": PageCreatedConflict,
        "pagedeleted": PageDeletedConflict,
        "protectedpage": LockedPage,
        "protectedtitle": LockedNoPage,
        "cascadeprotected": CascadeLockedPage,
    }

    @must_be(group='user')
    def editpage(self, page, summary, minor=True, notminor=False,
                 bot=True, recreate=True, createonly=False, nocreate=False,
                 watch=None):
        """Submit an edited Page object to be saved to the wiki.

        @param page: The Page to be saved; its .text property will be used
            as the new text to be saved to the wiki
        @param summary: the edit summary (required!)
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
        @return: True if edit succeeded, False if it failed

        """
        text = page.text
        if text is None:
            raise Error("editpage: no text to be saved")
        try:
            lastrev = page.latest_revision
        except NoPage:
            lastrev = None
            if not recreate:
                raise
        token = self.tokens['edit']
        if bot is None:
            bot = ("bot" in self.userinfo["rights"])
        self.lock_page(page)
        params = dict(action="edit",
                      title=page.title(withSection=False),
                      text=text, token=token, summary=summary, bot=bot,
                      recreate=recreate, createonly=createonly,
                      nocreate=nocreate, minor=minor,
                      notminor=not minor and notminor)

        if lastrev is not None:
            params['basetimestamp'] = lastrev.timestamp

        watch_items = set(["watch", "unwatch", "preferences", "nochange"])
        if watch in watch_items:
            if MediaWikiVersion(self.version()) < MediaWikiVersion("1.16"):
                if watch in ['preferences', 'nochange']:
                    pywikibot.warning(u'The watch value {0} is not supported '
                                      'by {1}'.format(watch, self))
                else:
                    params[watch] = True
            else:
                params['watchlist'] = watch
        elif watch:
            pywikibot.warning(
                u"editpage: Invalid watch value '%(watch)s' ignored."
                % locals())
        req = api.Request(site=self, **params)
        while True:
            try:
                result = req.submit()
                pywikibot.debug(u"editpage response: %s" % result,
                                _logger)
            except api.APIError as err:
                self.unlock_page(page)
                if err.code.endswith("anon") and self.logged_in():
                    pywikibot.debug(
                        u"editpage: received '%s' even though bot is logged in"
                        % err.code,
                        _logger)
                if err.code in self._ep_errors:
                    if isinstance(self._ep_errors[err.code], basestring):
                        errdata = {
                            'site': self,
                            'title': page.title(withSection=False),
                            'user': self.user(),
                            'info': err.info
                        }
                        raise Error(self._ep_errors[err.code] % errdata)
                    else:
                        raise self._ep_errors[err.code](page)
                pywikibot.debug(
                    u"editpage: Unexpected error code '%s' received."
                    % err.code,
                    _logger)
                raise
            assert ("edit" in result and "result" in result["edit"]), result
            if result["edit"]["result"] == "Success":
                self.unlock_page(page)
                if "nochange" in result["edit"]:
                    # null edit, page not changed
                    pywikibot.log(u"Page [[%s]] saved without any changes."
                                  % page.title())
                    return True
                page._revid = result["edit"]["newrevid"]
                # see https://www.mediawiki.org/wiki/API:Wikimania_2006_API_discussion#Notes
                # not safe to assume that saved text is the same as sent
                self.loadrevisions(page, getText=True)
                return True
            elif result["edit"]["result"] == "Failure":
                if "captcha" in result["edit"]:
                    captcha = result["edit"]["captcha"]
                    req['captchaid'] = captcha['id']
                    if captcha["type"] == "math":
                        # TODO: Should the input be parsed through eval in py3?
                        req['captchaword'] = input(captcha["question"])
                        continue
                    elif "url" in captcha:
                        import webbrowser
                        webbrowser.open('%s://%s%s'
                                        % (self.protocol(),
                                           self.hostname(),
                                           captcha["url"]))
                        req['captchaword'] = pywikibot.input(
                            "Please view CAPTCHA in your browser, "
                            "then type answer here:")
                        continue
                    else:
                        self.unlock_page(page)
                        pywikibot.error(
                            u"editpage: unknown CAPTCHA response %s, "
                            u"page not saved"
                            % captcha)
                        return False
                elif 'spamblacklist' in result['edit']:
                    raise SpamfilterError(page, result['edit']['spamblacklist'])
                elif 'code' in result['edit'] and 'info' in result['edit']:
                    self.unlock_page(page)
                    pywikibot.error(
                        u"editpage: %s\n%s, "
                        % (result['edit']['code'], result['edit']['info']))
                    return False
                else:
                    self.unlock_page(page)
                    pywikibot.error(u"editpage: unknown failure reason %s"
                                    % str(result))
                    return False
            else:
                self.unlock_page(page)
                pywikibot.error(
                    u"editpage: Unknown result code '%s' received; "
                    u"page not saved" % result["edit"]["result"])
                pywikibot.log(str(result))
                return False

    OnErrorExc = namedtuple('OnErrorExc', 'exception on_new_page')
    # catalog of move errors for use in error messages
    _mv_errors = {
        "noapiwrite": "API editing not enabled on %(site)s wiki",
        "writeapidenied":
"User %(user)s is not authorized to edit on %(site)s wiki",
        "nosuppress":
"User %(user)s is not authorized to move pages without creating redirects",
        "cantmove-anon":
"""Bot is not logged in, and anon users are not authorized to move pages on
%(site)s wiki""",
        "cantmove":
"User %(user)s is not authorized to move pages on %(site)s wiki",
        "immobilenamespace":
"Pages in %(oldnamespace)s namespace cannot be moved on %(site)s wiki",
        "articleexists": OnErrorExc(exception=ArticleExistsConflict, on_new_page=True),
        # "protectedpage" can happen in both directions.
        "protectedpage": OnErrorExc(exception=LockedPage, on_new_page=None),
        "protectedtitle": OnErrorExc(exception=LockedNoPage, on_new_page=True),
        "nonfilenamespace":
"Cannot move a file to %(newnamespace)s namespace on %(site)s wiki",
        "filetypemismatch":
"[[%(newtitle)s]] file extension does not match content of [[%(oldtitle)s]]",
    }

    @must_be(group='user')
    def movepage(self, page, newtitle, summary, movetalk=True,
                 noredirect=False):
        """Move a Page to a new title.

        @param page: the Page to be moved (must exist)
        @param newtitle: the new title for the Page
        @type newtitle: unicode
        @param summary: edit summary (required!)
        @param movetalk: if True (default), also move the talk page if possible
        @param noredirect: if True, suppress creation of a redirect from the
            old title to the new one
        @return: Page object with the new title

        """
        oldtitle = page.title(withSection=False)
        newlink = pywikibot.Link(newtitle, self)
        newpage = pywikibot.Page(newlink)
        if newlink.namespace:
            newtitle = self.namespace(newlink.namespace) + ":" + newlink.title
        else:
            newtitle = newlink.title
        if oldtitle == newtitle:
            raise Error("Cannot move page %s to its own title."
                        % oldtitle)
        if not page.exists():
            raise NoPage(page,
                         "Cannot move page %(page)s because it "
                         "does not exist on %(site)s.")
        token = self.tokens['move']
        self.lock_page(page)
        req = api.Request(site=self, action="move", to=newtitle,
                          token=token, reason=summary, movetalk=movetalk,
                          noredirect=noredirect)
        req['from'] = oldtitle  # "from" is a python keyword
        try:
            result = req.submit()
            pywikibot.debug(u"movepage response: %s" % result,
                            _logger)
        except api.APIError as err:
            if err.code.endswith("anon") and self.logged_in():
                pywikibot.debug(
                    u"movepage: received '%s' even though bot is logged in"
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
                            for prot in self.page_restrictions(newpage).values():
                                if prot[0] not in self._userinfo['groups']:
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
            pywikibot.debug(u"movepage: Unexpected error code '%s' received."
                            % err.code,
                            _logger)
            raise
        finally:
            self.unlock_page(page)
        if "move" not in result:
            pywikibot.error(u"movepage: %s" % result)
            raise Error("movepage: unexpected response")
        # TODO: Check for talkmove-error messages
        if "talkmove-error-code" in result["move"]:
            pywikibot.warning(
                u"movepage: Talk page %s not moved"
                % (page.toggleTalkPage().title(asLink=True)))
        return pywikibot.Page(page, newtitle)

    # catalog of rollback errors for use in error messages
    _rb_errors = {
        "noapiwrite": "API editing not enabled on %(site)s wiki",
        "writeapidenied": "User %(user)s not allowed to edit through the API",
        "alreadyrolled": "Page [[%(title)s]] already rolled back; action aborted.",
    }  # other errors shouldn't arise because we check for those errors

    def rollbackpage(self, page, **kwargs):
        """Roll back page to version before last user's edits.

        The keyword arguments are those supported by the rollback API.

        As a precaution against errors, this method will fail unless
        the page history contains at least two revisions, and at least
        one that is not by the same user who made the last edit.

        @param page: the Page to be rolled back (must exist)

        """
        if len(page._revisions) < 2:
            raise Error(
                u"Rollback of %s aborted; load revision history first."
                % page.title(asLink=True))
        last_rev = page.latest_revision
        last_user = last_rev.user
        for rev in sorted(list(page._revisions.keys()), reverse=True):
            # start with most recent revision first
            if rev.user != last_user:
                break
        else:
            raise Error(
                u"Rollback of %s aborted; only one user in revision history."
                % page.title(asLink=True))
        token = self.tokens["rollback"]
        self.lock_page(page)
        req = api.Request(site=self, action="rollback",
                          title=page.title(withSection=False),
                          user=last_user,
                          token=token,
                          **kwargs)
        try:
            req.submit()
        except api.APIError as err:
            errdata = {
                'site': self,
                'title': page.title(withSection=False),
                'user': self.user(),
            }
            if err.code in self._rb_errors:
                raise Error(self._rb_errors[err.code] % errdata)
            pywikibot.debug(u"rollback: Unexpected error code '%s' received."
                            % err.code,
                            _logger)
            raise
        finally:
            self.unlock_page(page)

    # catalog of delete errors for use in error messages
    _dl_errors = {
        "noapiwrite": "API editing not enabled on %(site)s wiki",
        "writeapidenied": "User %(user)s not allowed to edit through the API",
        "permissiondenied": "User %(user)s not authorized to (un)delete "
                            "pages on %(site)s wiki.",
        "cantdelete": "Could not delete [[%(title)s]]. Maybe it was deleted already.",
        "cantundelete": "Could not undelete [[%(title)s]]. "
                        "Revision may not exist or was already undeleted."
    }  # other errors shouldn't occur because of pre-submission checks

    @must_be(group='sysop')
    @deprecate_arg("summary", "reason")
    def deletepage(self, page, reason):
        """Delete page from the wiki. Requires appropriate privilege level.

        @param page: Page to be deleted.
        @type page: Page
        @param reason: Deletion reason.
        @type reason: basestring

        """
        token = self.tokens['delete']
        self.lock_page(page)
        req = api.Request(site=self, action="delete", token=token,
                          title=page.title(withSection=False),
                          reason=reason)
        try:
            req.submit()
        except api.APIError as err:
            errdata = {
                'site': self,
                'title': page.title(withSection=False),
                'user': self.user(),
            }
            if err.code in self._dl_errors:
                raise Error(self._dl_errors[err.code] % errdata)
            pywikibot.debug(u"delete: Unexpected error code '%s' received."
                            % err.code,
                            _logger)
            raise
        finally:
            self.unlock_page(page)

    @must_be(group='sysop')
    @deprecate_arg("summary", "reason")
    def undelete_page(self, page, reason, revisions=None):
        """Undelete page from the wiki. Requires appropriate privilege level.

        @param page: Page to be deleted.
        @type page: Page
        @param revisions: List of timestamps to restore. If None, restores all revisions.
        @type revisions: list
        @param reason: Undeletion reason.
        @type reason: basestring

        """
        token = self.tokens['undelete']
        self.lock_page(page)

        if revisions is None:
            req = api.Request(site=self, action='undelete', token=token,
                              title=page.title(withSection=False), reason=reason)
        else:
            req = api.Request(site=self, action='undelete', token=token,
                              title=page.title(withSection=False),
                              timestamps=revisions, reason=reason)
        try:
            req.submit()
        except api.APIError as err:
            errdata = {
                'site': self,
                'title': page.title(withSection=False),
                'user': self.user(),
            }
            if err.code in self._dl_errors:
                raise Error(self._dl_errors[err.code] % errdata)
            pywikibot.debug(u"delete: Unexpected error code '%s' received."
                            % err.code,
                            _logger)
            raise
        finally:
            self.unlock_page(page)

    _protect_errors = {
        "noapiwrite": "API editing not enabled on %(site)s wiki",
        "writeapidenied": "User %(user)s not allowed to edit through the API",
        "permissiondenied": "User %(user)s not authorized to protect pages on %(site)s wiki.",
        "cantedit": "User %(user) can't protect this page because user %(user) can't edit it.",
        "protect-invalidlevel": "Invalid protection level"
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

    @must_be(group='sysop')
    @deprecate_arg("summary", "reason")
    def protect(self, page, protections, reason, expiry=None, **kwargs):
        """(Un)protect a wiki page. Requires administrator status.

        @param protections: A dict mapping type of protection to protection
            level of that type. Valid types of protection are 'edit', 'move',
            'create', and 'upload'. Valid protection levels (in MediaWiki 1.12)
            are '' (equivalent to 'none'), 'autoconfirmed', and 'sysop'.
            If None is given, however, that protection will be skipped.
        @type  protections: dict
        @param reason: Reason for the action
        @type  reason: basestring
        @param expiry: When the block should expire. This expiry will be applied
            to all protections. If None, 'infinite', 'indefinite', 'never', or ''
            is given, there is no expiry.
        @type expiry: pywikibot.Timestamp, string in GNU timestamp format
            (including ISO 8601).
        """
        token = self.tokens['protect']
        self.lock_page(page)

        protectList = [ptype + '=' + level for ptype, level in protections.items()
                       if level is not None]
        req = api.Request(site=self, action='protect', token=token,
                          title=page.title(withSection=False),
                          protections=protectList,
                          reason=reason,
                          **kwargs)
        if expiry:
            req['expiry'] = expiry
        try:
            req.submit()
        except api.APIError as err:
            errdata = {
                'site': self,
                'user': self.user(),
            }
            if err.code in self._protect_errors:
                raise Error(self._protect_errors[err.code] % errdata)
            pywikibot.debug(u"protect: Unexpected error code '%s' received."
                            % err.code,
                            _logger)
            raise
        finally:
            self.unlock_page(page)

    # TODO: implement undelete

    _patrol_errors = {
        "nosuchrcid": "There is no change with rcid %(rcid)s",
        "nosuchrevid": "There is no change with revid %(revid)s",
        "patroldisabled": "Patrolling is disabled on %(site)s wiki",
        "noautopatrol": "User %(user)s has no permission to patrol its own changes, 'autopatrol' is needed",
        "notpatrollable": "The revision %(revid)s can't be patrolled as it's too old."
    }

    def patrol(self, rcid=None, revid=None, revision=None):
        """Return a generator of patrolled pages.

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
        @param revision: an Revision/iterable/iterator providing Revision object
            of pages to be patrolled.
        @type revision: iterable/iterator which returns a Revision object; it
            also supports a single Revision.
        @rtype: iterator of dict with 'rcid', 'ns' and 'title'
            of the patrolled page.

        """
        # If patrol is not enabled, attr will be set the first time a
        # request is done.
        if hasattr(self, u'_patroldisabled'):
            if self._patroldisabled:
                return

        if all(_ is None for _ in [rcid, revid, revision]):
            raise Error('No rcid, revid or revision provided.')

        if isinstance(rcid, int) or isinstance(rcid, basestring):
            rcid = set([rcid])
        if isinstance(revid, int) or isinstance(revid, basestring):
            revid = set([revid])
        if isinstance(revision, pywikibot.page.Revision):
            revision = set([revision])

        # Handle param=None.
        rcid = rcid or set()
        revid = revid or set()
        revision = revision or set()

        # TODO: remove exeception for mw < 1.22
        if (revid or revision) and MediaWikiVersion(self.version()) < MediaWikiVersion("1.22"):
            raise NotImplementedError(
                u'Support of "revid" parameter\n'
                u'is not implemented in MediaWiki version < "1.22"')
        else:
            combined_revid = set(revid) | set(r.revid for r in revision)

        gen = itertools.chain(
            zip_longest(rcid, [], fillvalue='rcid'),
            zip_longest(combined_revid, [], fillvalue='revid'))

        token = self.tokens['patrol']

        for idvalue, idtype in gen:
            req = api.Request(site=self, action='patrol',
                              token=token, **{idtype: idvalue})

            try:
                result = req.submit()
            except api.APIError as err:
                # patrol is disabled, store in attr to avoid other requests
                if err.code == u'patroldisabled':
                    self._patroldisabled = True
                    return

                errdata = {
                    'site': self,
                    'user': self.user(),
                }
                errdata[idtype] = idvalue
                if err.code in self._patrol_errors:
                    raise Error(self._patrol_errors[err.code] % errdata)
                pywikibot.debug(u"protect: Unexpected error code '%s' received."
                                % err.code,
                                _logger)
                raise

            yield result['patrol']

    @must_be(group='sysop')
    def blockuser(self, user, expiry, reason, anononly=True, nocreate=True,
                  autoblock=True, noemail=False, reblock=False):
        """
        Block a user for certain amount of time and for a certain reason.

        @param user: The username/IP to be blocked without a namespace.
        @type user: User
        @param expiry: The length or date/time when the block expires. If
            'never', 'infinite', 'indefinite' it never does. If the value is
            given as a basestring it's parsed by php's strtotime function:
                http://php.net/manual/en/function.strtotime.php
            The relative format is described there:
                http://php.net/manual/en/datetime.formats.relative.php
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
        @return: The data retrieved from the API request.
        @rtype: dict
        """
        token = self.tokens['block']
        if expiry is False:
            expiry = 'never'
        req = api.Request(site=self, action='block', user=user.username,
                          expiry=expiry, reason=reason, token=token,
                          anononly=anononly, nocreate=nocreate,
                          autoblock=autoblock, noemail=noemail,
                          reblock=reblock)

        data = req.submit()
        return data

    @must_be(group='sysop')
    def unblockuser(self, user, reason):
        """
        Remove the block for the user.

        @param user: The username/IP without a namespace.
        @type user: User
        @param reason: Reason for the unblock.
        @type reason: basestring
        """
        token = self.tokens['block']
        req = api.Request(site=self, action='unblock', user=user.username,
                          reason=reason, token=token)

        data = req.submit()
        return data

    def watchpage(self, page, unwatch=False):
        """Add or remove page from watchlist.

        @param unwatch: If True, remove page from watchlist; if False (default),
            add it.
        @return: True if API returned expected response; False otherwise

        """
        token = self.tokens['watch']
        req = api.Request(action="watch", token=token,
                          title=page.title(withSection=False), unwatch=unwatch)
        result = req.submit()
        if "watch" not in result:
            pywikibot.error(u"watchpage: Unexpected API response:\n%s" % result)
            return False
        return ('unwatched' if unwatch else 'watched') in result["watch"]

    @must_be(group='user')
    def purgepages(self, pages, **kwargs):
        """Purge the server's cache for one or multiple pages.

        @param pages: list of Page objects
        @return: True if API returned expected response; False otherwise

        """
        req = api.Request(site=self, action='purge')
        req['titles'] = [page.title(withSection=False) for page in set(pages)]
        linkupdate = False
        linkupdate_args = ['forcelinkupdate', 'forcerecursivelinkupdate']
        for arg in kwargs:
            if arg in linkupdate_args + ['redirects', 'converttitles']:
                req[arg] = kwargs[arg]
            if arg in linkupdate_args:
                linkupdate = True
        result = req.submit()
        if 'purge' not in result:
            pywikibot.error(u'purgepages: Unexpected API response:\n%s' % result)
            return False
        result = result['purge']
        purged = ['purged' in page for page in result]
        if linkupdate:
            purged += ['linkupdate' in page for page in result]
        return all(purged)

    @deprecated("Site().exturlusage")
    def linksearch(self, siteurl, limit=None):
        """Backwards-compatible interface to exturlusage()."""
        return self.exturlusage(siteurl, total=limit)

    def _get_titles_with_hash(self, hash_found=None):
        """Helper for the deprecated method get(Files|Images)FromAnHash."""
        # This should be removed with together with get(Files|Images)FromHash
        if hash_found is None:
            # This makes absolutely NO sense.
            pywikibot.warning(
                'The "hash_found" parameter in "getFilesFromAnHash" and '
                '"getImagesFromAnHash" are not optional.')
            return
        return [image.title(withNamespace=False)
                for image in self.allimages(sha1=hash_found)]

    @deprecated('Site().allimages')
    def getFilesFromAnHash(self, hash_found=None):
        """
        Return all files that have the same hash.

        DEPRECATED: Use L{APISite.allimages} instead using 'sha1'.
        """
        return self._get_titles_with_hash(hash_found)

    @deprecated('Site().allimages')
    def getImagesFromAnHash(self, hash_found=None):
        """
        Return all images that have the same hash.

        DEPRECATED: Use L{APISite.allimages} instead using 'sha1'.
        """
        return self._get_titles_with_hash(hash_found)

    @must_be(group='user')
    def is_uploaddisabled(self):
        """Return True if upload is disabled on site.

        If not called directly, it is cached by the first attempted
        upload action.

        """
        if hasattr(self, '_uploaddisabled'):
            return self._uploaddisabled
        else:
            # attempt a fake upload; on enabled sites will fail for:
            # missingparam: One of the parameters
            #    filekey, file, url, statuskey is required
            # TODO: is there another way?
            try:
                token = self.tokens['edit']
                req = api.Request(site=self, action="upload",
                                  token=token, throttle=False)
                req.submit()
            except api.APIError as error:
                if error.code == u'uploaddisabled':
                    self._uploaddisabled = True
                elif error.code == u'missingparam':
                    # If the upload module is enabled, the above dummy request
                    # does not have sufficient parameters and will cause a
                    # 'missingparam' error.
                    self._uploaddisabled = False
                else:
                    # Unexpected error
                    raise
                return self._uploaddisabled

    @deprecate_arg('imagepage', 'filepage')
    def upload(self, filepage, source_filename=None, source_url=None,
               comment=None, text=None, watch=False, ignore_warnings=False,
               chunk_size=0):
        """Upload a file to the wiki.

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
        @param ignore_warnings: if true, ignore API warnings and force
            upload (for example, to overwrite an existing file); default False
        @param chunk_size: The chunk size in bytesfor chunked uploading (see
            U{https://www.mediawiki.org/wiki/API:Upload#Chunked_uploading}). It
            will only upload in chunks, if the version number is 1.20 or higher
            and the chunk size is positive but lower than the file size.
        @type chunk_size: int
        """
        upload_warnings = {
            # map API warning codes to user error messages
            # %(msg)s will be replaced by message string from API responsse
            'duplicate-archive': "The file is a duplicate of a deleted file %(msg)s.",
            'was-deleted': "The file %(msg)s was previously deleted.",
            'emptyfile': "File %(msg)s is empty.",
            'exists': "File %(msg)s already exists.",
            'duplicate': "Uploaded file is a duplicate of %(msg)s.",
            'badfilename': "Target filename is invalid.",
            'filetype-unwanted-type': "File %(msg)s type is unwanted type.",
        }

        # check for required user right
        if "upload" not in self.userinfo["rights"]:
            raise Error(
                "User '%s' does not have upload rights on site %s."
                % (self.user(), self))
        # check for required parameters
        if bool(source_filename) == bool(source_url):
            raise ValueError("APISite.upload: must provide either "
                             "source_filename or source_url, not both.")
        if comment is None:
            comment = filepage.text
        if not comment:
            raise ValueError("APISite.upload: cannot upload file without "
                             "a summary/description.")
        if text is None:
            text = filepage.text
        if not text:
            text = comment
        token = self.tokens['edit']
        result = None
        file_page_title = filepage.title(withNamespace=False)
        if source_filename:
            # TODO: Dummy value to allow also Unicode names, see bug 73661
            mime_filename = 'FAKE-NAME'
            # upload local file
            # make sure file actually exists
            if not os.path.isfile(source_filename):
                raise ValueError("File '%s' does not exist."
                                 % source_filename)
            additional_parameters = {}
            throttle = True
            filesize = os.path.getsize(source_filename)
            chunked_upload = (chunk_size > 0 and chunk_size < filesize and
                              MediaWikiVersion(self.version()) >= MediaWikiVersion('1.20'))
            with open(source_filename, 'rb') as f:
                if chunked_upload:
                    offset = 0
                    file_key = None
                    while True:
                        f.seek(offset)
                        chunk = f.read(chunk_size)
                        req = api.Request(site=self, action='upload', token=token,
                                          stash=True, offset=offset, filesize=filesize,
                                          filename=file_page_title,
                                          ignorewarnings=ignore_warnings,
                                          mime_params={}, throttle=throttle)
                        req.mime_params['chunk'] = (chunk,
                                                    ("application", "octet-stream"),
                                                    {'filename': mime_filename})
                        if file_key:
                            req['filekey'] = file_key
                        try:
                            data = req.submit()['upload']
                            self._uploaddisabled = False
                        except api.APIError as error:
                            # TODO: catch and process foreseeable errors
                            if error.code == u'uploaddisabled':
                                self._uploaddisabled = True
                            raise error
                        if 'warnings' in data and not ignore_warnings:
                            result = data
                            break
                        file_key = data['filekey']
                        throttle = False
                        if 'offset' in data:
                            new_offset = int(data['offset'])
                            if offset + len(chunk) != new_offset:
                                pywikibot.warning('Unexpected offset.')
                            offset = new_offset
                        else:
                            pywikibot.warning('Offset was not supplied.')
                            offset += len(chunk)
                        if data['result'] != 'Continue':  # finished
                            additional_parameters['filekey'] = file_key
                            break
                else:  # not chunked upload
                    file_contents = f.read()
                    filetype = (mimetypes.guess_type(source_filename)[0] or
                                'application/octet-stream')
                    additional_parameters = {
                        'mime_params': {
                            'file': (file_contents,
                                     filetype.split('/'),
                                     {'filename': mime_filename})
                        }
                    }
            req = api.Request(site=self, action="upload", token=token,
                              filename=file_page_title,
                              comment=comment, text=text, throttle=throttle,
                              **additional_parameters)
        else:
            # upload by URL
            if "upload_by_url" not in self.userinfo["rights"]:
                raise Error(
                    "User '%s' is not authorized to upload by URL on site %s."
                    % (self.user(), self))
            req = api.Request(site=self, action="upload", token=token,
                              filename=file_page_title,
                              url=source_url, comment=comment, text=text)
        if not result:
            req['watch'] = watch
            req['ignorewarnings'] = ignore_warnings
            try:
                result = req.submit()
                self._uploaddisabled = False
            except api.APIError as error:
                # TODO: catch and process foreseeable errors
                if error.code == u'uploaddisabled':
                    self._uploaddisabled = True
                raise error
            result = result["upload"]
            pywikibot.debug(result, _logger)

        if "warnings" in result and not ignore_warnings:
            # TODO: Handle multiple warnings at the same time
            warning = list(result["warnings"].keys())[0]
            message = result["warnings"][warning]
            raise pywikibot.UploadWarning(warning, upload_warnings[warning]
                                          % {'msg': message})
        elif "result" not in result:
            pywikibot.output(u"Upload: unrecognized response: %s" % result)
        if result["result"] == "Success":
            pywikibot.output(u"Upload successful.")
            # If we receive a nochange, that would mean we're in simulation
            # mode, don't attempt to access imageinfo
            if "nochange" not in result:
                filepage._imageinfo = result["imageinfo"]
            return

    @deprecated_args(number="step",
                     repeat=None,
                     namespace="namespaces",
                     rc_show=None,
                     get_redirect=None)  # 20120822
    def newpages(self, user=None, returndict=False,
                 start=None, end=None, reverse=False, showBot=False,
                 showRedirects=False, excludeuser=None,
                 showPatrolled=None, namespaces=None, step=None, total=None):
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
            or a single instance of those types.  May be a '|' separated
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
            namespaces=namespaces, changetype="new", user=user,
            excludeuser=excludeuser, showBot=showBot,
            showRedirects=showRedirects, showPatrolled=showPatrolled,
            step=step, total=total
        )
        for pageitem in gen:
            newpage = pywikibot.Page(self, pageitem['title'])
            if returndict:
                yield (newpage, pageitem)
            else:
                yield (newpage, pageitem['timestamp'], pageitem['newlen'],
                       u'', pageitem['user'], pageitem['comment'])

    def newfiles(self, user=None, start=None, end=None, reverse=False,
                 step=None, total=None):
        """Yield information about newly uploaded files.

        Yields a tuple of FilePage, Timestamp, user(unicode), comment(unicode).

        N.B. the API does not provide direct access to Special:Newimages, so
        this is derived from the "upload" log events instead.

        """
        # TODO: update docstring
        for event in self.logevents(logtype="upload", user=user,
                                    start=start, end=end, reverse=reverse,
                                    step=step, total=total):
            # event.title() actually returns a Page
            filepage = pywikibot.FilePage(event.title())
            date = event.timestamp()
            user = event.user()
            comment = event.comment() or u''
            yield (filepage, date, user, comment)

    @deprecated("Site().newfiles()")
    @deprecated_args(number=None, repeat=None)
    def newimages(self, *args, **kwargs):
        """
        Yield information about newly uploaded files.

        DEPRECATED: Use newfiles() instead.
        """
        return self.newfiles(*args, **kwargs)

    @deprecated_args(number=None, repeat=None)
    def longpages(self, step=None, total=None):
        """Yield Pages and lengths from Special:Longpages.

        Yields a tuple of Page object, length(int).

        @param step: request batch size
        @param total: number of pages to return
        """
        lpgen = self._generator(api.ListGenerator,
                                type_arg="querypage", qppage="Longpages",
                                step=step, total=total)
        for pageitem in lpgen:
            yield (pywikibot.Page(self, pageitem['title']),
                   int(pageitem['value']))

    @deprecated_args(number="total", repeat=None)
    def shortpages(self, step=None, total=None):
        """Yield Pages and lengths from Special:Shortpages.

        Yields a tuple of Page object, length(int).

        @param step: request batch size
        @param total: number of pages to return
        """
        spgen = self._generator(api.ListGenerator,
                                type_arg="querypage", qppage="Shortpages",
                                step=step, total=total)
        for pageitem in spgen:
            yield (pywikibot.Page(self, pageitem['title']),
                   int(pageitem['value']))

    @deprecated_args(number=None, repeat=None)
    def deadendpages(self, step=None, total=None):
        """Yield Page objects retrieved from Special:Deadendpages.

        @param step: request batch size
        @param total: number of pages to return
        """
        degen = self._generator(api.PageGenerator,
                                type_arg="querypage", gqppage="Deadendpages",
                                step=step, total=total)
        return degen

    @deprecated_args(number=None, repeat=None)
    def ancientpages(self, step=None, total=None):
        """Yield Pages, datestamps from Special:Ancientpages.

        @param step: request batch size
        @param total: number of pages to return
        """
        apgen = self._generator(api.ListGenerator,
                                type_arg="querypage", qppage="Ancientpages",
                                step=step, total=total)
        for pageitem in apgen:
            yield (pywikibot.Page(self, pageitem['title']),
                   pywikibot.Timestamp.fromISOformat(pageitem['timestamp']))

    @deprecated_args(number=None, repeat=None)
    def lonelypages(self, step=None, total=None):
        """Yield Pages retrieved from Special:Lonelypages.

        @param step: request batch size
        @param total: number of pages to return
        """
        lpgen = self._generator(api.PageGenerator,
                                type_arg="querypage", gqppage="Lonelypages",
                                step=step, total=total)
        return lpgen

    @deprecated_args(number=None, repeat=None)
    def unwatchedpages(self, step=None, total=None):
        """Yield Pages from Special:Unwatchedpages (requires Admin privileges).

        @param step: request batch size
        @param total: number of pages to return
        """
        uwgen = self._generator(api.PageGenerator,
                                type_arg="querypage", gqppage="Unwatchedpages",
                                step=step, total=total)
        return uwgen

    def wantedpages(self, step=None, total=None):
        """Yield Pages from Special:Wantedpages.

        @param step: request batch size
        @param total: number of pages to return
        """
        wpgen = self._generator(api.PageGenerator,
                                type_arg="querypage", gqppage="Wantedpages",
                                step=step, total=total)
        return wpgen

    def wantedcategories(self, step=None, total=None):
        """Yield Pages from Special:Wantedcategories.

        @param step: request batch size
        @param total: number of pages to return
        """
        wcgen = self._generator(api.CategoryPageGenerator,
                                type_arg="querypage", gqppage="Wantedcategories",
                                step=step, total=total)

        return wcgen

    @deprecated_args(number=None, repeat=None)
    def uncategorizedcategories(self, number=None, repeat=True,
                                step=None, total=None):
        """Yield Categories from Special:Uncategorizedcategories.

        @param step: request batch size
        @param total: number of pages to return
        """
        ucgen = self._generator(api.CategoryPageGenerator,
                                type_arg="querypage",
                                gqppage="Uncategorizedcategories",
                                step=step, total=total)
        return ucgen

    @deprecated_args(number=None, repeat=None)
    def uncategorizedimages(self, number=None, repeat=True,
                            step=None, total=None):
        """Yield FilePages from Special:Uncategorizedimages.

        @param step: request batch size
        @param total: number of pages to return
        """
        uigen = self._generator(api.ImagePageGenerator,
                                type_arg="querypage",
                                gqppage="Uncategorizedimages",
                                step=step, total=total)
        return uigen

    # synonym
    uncategorizedfiles = uncategorizedimages

    @deprecated_args(number=None, repeat=None)
    def uncategorizedpages(self, number=None, repeat=True,
                           step=None, total=None):
        """Yield Pages from Special:Uncategorizedpages.

        @param step: request batch size
        @param total: number of pages to return
        """
        upgen = self._generator(api.PageGenerator,
                                type_arg="querypage",
                                gqppage="Uncategorizedpages",
                                step=step, total=total)
        return upgen

    @deprecated_args(number=None, repeat=None)
    def uncategorizedtemplates(self, number=None, repeat=True, step=None,
                               total=None):
        """Yield Pages from Special:Uncategorizedtemplates.

        @param step: request batch size
        @param total: number of pages to return
        """
        utgen = self._generator(api.PageGenerator,
                                type_arg="querypage",
                                gqppage="Uncategorizedtemplates",
                                step=step, total=total)
        return utgen

    @deprecated_args(number=None, repeat=None)
    def unusedcategories(self, step=None, total=None):
        """Yield Category objects from Special:Unusedcategories.

        @param step: request batch size
        @param total: number of pages to return
        """
        ucgen = self._generator(api.CategoryPageGenerator,
                                type_arg="querypage",
                                gqppage="Unusedcategories",
                                step=step, total=total)
        return ucgen

    def unusedfiles(self, step=None, total=None):
        """Yield FilePage objects from Special:Unusedimages.

        @param step: request batch size
        @param total: number of pages to return
        """
        uigen = self._generator(api.ImagePageGenerator,
                                type_arg="querypage",
                                gqppage="Unusedimages",
                                step=step, total=total)
        return uigen

    @deprecated("Site().unusedfiles()")
    @deprecated_args(number=None, repeat=None)
    def unusedimages(self, *args, **kwargs):
        """Yield FilePage objects from Special:Unusedimages.

        DEPRECATED: Use L{APISite.unusedfiles} instead.
        """
        return self.unusedfiles(*args, **kwargs)

    @deprecated_args(number=None, repeat=None)
    def withoutinterwiki(self, step=None, total=None):
        """Yield Pages without language links from Special:Withoutinterwiki.

        @param step: request batch size
        @param total: number of pages to return
        """
        wigen = self._generator(api.PageGenerator,
                                type_arg="querypage",
                                gqppage="Withoutinterwiki",
                                step=step, total=total)
        return wigen

    @need_version("1.18")
    def broken_redirects(self, step=None, total=None):
        """Yield Pages without language links from Special:BrokenRedirects.

        @param step: request batch size
        @param total: number of pages to return
        """
        brgen = self._generator(api.PageGenerator,
                                type_arg="querypage",
                                gqppage="BrokenRedirects",
                                step=step, total=total)
        return brgen

    @need_version("1.18")
    def double_redirects(self, step=None, total=None):
        """Yield Pages without language links from Special:BrokenRedirects.

        @param step: request batch size
        @param total: number of pages to return
        """
        drgen = self._generator(api.PageGenerator,
                                type_arg="querypage",
                                gqppage="DoubleRedirects",
                                step=step, total=total)
        return drgen

    @need_version("1.18")
    def redirectpages(self, step=None, total=None):
        """Yield redirect pages from Special:ListRedirects.

        @param step: request batch size
        @param total: number of pages to return
        """
        lrgen = self._generator(api.PageGenerator,
                                type_arg="querypage",
                                gqppage="Listredirects",
                                step=step, total=total)
        return lrgen

    def compare(self, fromrev, torev):
        """Implementation of the 'action=compare' API method
        which will show a diff between to revision."""
        params = dict(action = 'compare',
                      fromrev = fromrev,
                      torev = torev)
        req = api.Request(site=self, **params)
        data = req.submit()
        return data


class DataSite(APISite):

    """Wikibase data capable site."""

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(DataSite, self).__init__(*args, **kwargs)
        self._item_namespace = None
        self._property_namespace = None

    def _cache_entity_namespaces(self):
        """Find namespaces for each known wikibase entity type."""
        self._item_namespace = False
        self._property_namespace = False

        for namespace in self.namespaces().values():
            if not hasattr(namespace, 'defaultcontentmodel'):
                continue

            content_model = namespace.defaultcontentmodel
            if content_model == 'wikibase-item':
                self._item_namespace = namespace
            elif content_model == 'wikibase-property':
                self._property_namespace = namespace

    @property
    def item_namespace(self):
        """
        Return namespace for items.

        @return: item namespace
        @rtype: Namespace
        """
        if self._item_namespace is None:
            self._cache_entity_namespaces()

        if isinstance(self._item_namespace, Namespace):
            return self._item_namespace
        else:
            raise EntityTypeUnknownException(
                '%r does not support entity type "item"'
                % self)

    @property
    def property_namespace(self):
        """
        Return namespace for properties.

        @return: property namespace
        @rtype: Namespace
        """
        if self._property_namespace is None:
            self._cache_entity_namespaces()

        if isinstance(self._property_namespace, Namespace):
            return self._property_namespace
        else:
            raise EntityTypeUnknownException(
                '%r does not support entity type "property"'
                % self)

    def __getattr__(self, attr):
        """Provide data access methods.

        Methods provided are get_info, get_sitelinks, get_aliases,
        get_labels, get_descriptions, and get_urls.
        """
        if hasattr(self.__class__, attr):
            return getattr(self.__class__, attr)
        if attr.startswith("get_"):
            props = attr.replace("get_", "")
            if props in ['info', 'sitelinks', 'aliases', 'labels',
                         'descriptions', 'urls']:
                if props == 'urls':
                    props = 'sitelinks/urls'
                method = self._get_propertyitem
                f = lambda *args, **params: \
                    method(props, *args, **params)
                if hasattr(method, "__doc__"):
                    f.__doc__ = method.__doc__
                return f
        return super(APISite, self).__getattr__(attr)

    def __repr__(self):
        return 'DataSite("%s", "%s")' % (self.code, self.family.name)

    @deprecated("pywikibot.PropertyPage")
    def _get_propertyitem(self, props, source, **params):
        """Generic method to get the data for multiple Wikibase items."""
        wbdata = self.get_item(source, props=props, **params)
        assert props in wbdata, \
               "API wbgetentities response lacks %s key" % props
        return wbdata[props]

    @deprecated("pywikibot.WikibasePage")
    def get_item(self, source, **params):
        """Get the data for multiple Wikibase items."""
        if isinstance(source, int) or \
           isinstance(source, basestring) and source.isdigit():
            ids = 'q' + str(source)
            wbrequest = api.Request(site=self, action="wbgetentities", ids=ids,
                                    **params)
            wbdata = wbrequest.submit()
            assert 'success' in wbdata, \
                   "API wbgetentities response lacks 'success' key"
            assert wbdata['success'] == 1, "API 'success' key is not 1"
            assert 'entities' in wbdata, \
                   "API wbgetentities response lacks 'entities' key"
            assert ids in wbdata['entities'], \
                   "API wbgetentities response lacks %s key" % ids
            return wbdata['entities'][ids]
        else:
            # not implemented yet
            raise NotImplementedError

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
        params = dict(**identification)
        params['action'] = 'wbgetentities'
        if props:
            params['props'] = '|'.join(props)
        req = api.Request(site=self, **params)
        data = req.submit()
        if 'success' not in data:
            raise api.APIError(data['errors'])
        return data['entities']

    def preloaditempages(self, pagelist, groupsize=50):
        """Yield ItemPages with content prefilled.

        Note that pages will be iterated in a different order
        than in the underlying pagelist.

        @param pagelist: an iterable that yields either WikibasePage objects,
                         or Page objects linked to an ItemPage.
        @param groupsize: how many pages to query at a time
        @type groupsize: int
        """
        for sublist in itergroup(pagelist, groupsize):
            req = {'ids': [], 'titles': [], 'sites': []}
            for p in sublist:
                if isinstance(p, pywikibot.page.WikibasePage):
                    ident = p._defined_by()
                    for key in ident:
                        req[key].append(ident[key])
                else:
                    assert(p.site.has_data_repository)
                    if (p.site == p.site.data_repository() and
                            p.namespace() == p.data_repository.item_namespace):
                        req['ids'].append(p.title(withNamespace=False))
                    else:
                        req['sites'].append(p.site.dbName())
                        req['titles'].append(p._link._text)

            req = api.Request(site=self, action='wbgetentities', **req)
            data = req.submit()
            for qid in data['entities']:
                item = pywikibot.ItemPage(self, qid)
                item._content = data['entities'][qid]
                yield item

    def getPropertyType(self, prop):
        """
        Obtain the type of a property.

        This is used specifically because we can cache
        the value for a much longer time (near infinite).
        """
        params = dict(
            action='wbgetentities',
            ids=prop.getID(),
            props='datatype',
        )
        expiry = datetime.timedelta(days=365 * 100)
        # Store it for 100 years
        req = api.CachedRequest(expiry, site=self, **params)
        data = req.submit()

        # the IDs returned from the API can be upper or lowercase, depending
        # on the version. See for more information:
        # https://bugzilla.wikimedia.org/show_bug.cgi?id=53894
        # https://lists.wikimedia.org/pipermail/wikidata-tech/2013-September/000296.html
        try:
            dtype = data['entities'][prop.getID()]['datatype']
        except KeyError:
            dtype = data['entities'][prop.getID().lower()]['datatype']

        return dtype

    @must_be(group='user')
    def editEntity(self, identification, data, bot=True, **kwargs):
        if "id" in identification and identification["id"] == "-1":
            del identification["id"]
        params = dict(**identification)
        if not params:  # If no identification was provided
            params['new'] = 'item'  # TODO create properties+queries
        params['action'] = 'wbeditentity'
        if bot:
            params['bot'] = 1
        if 'baserevid' in kwargs and kwargs['baserevid']:
            params['baserevid'] = kwargs['baserevid']
        params['token'] = self.tokens['edit']
        for arg in kwargs:
            if arg in ['clear', 'data', 'exclude', 'summary']:
                params[arg] = kwargs[arg]
        params['data'] = json.dumps(data)
        req = api.Request(site=self, **params)
        data = req.submit()
        return data

    @must_be(group='user')
    def addClaim(self, item, claim, bot=True, **kwargs):

        params = dict(action='wbcreateclaim',
                      entity=item.getID(),
                      baserevid=item.latest_revision_id,
                      snaktype=claim.getSnakType(),
                      property=claim.getID(),
                      )
        if bot:
            params['bot'] = 1
        if claim.getSnakType() == 'value':
            params['value'] = json.dumps(claim._formatValue())
        if 'summary' in kwargs:
            params['summary'] = kwargs['summary']
        params['token'] = self.tokens['edit']
        req = api.Request(site=self, **params)
        data = req.submit()
        claim.snak = data['claim']['id']
        # Update the item
        if claim.getID() in item.claims:
            item.claims[claim.getID()].append(claim)
        else:
            item.claims[claim.getID()] = [claim]
        item.lastrevid = data['pageinfo']['lastrevid']

    @must_be(group='user')
    def changeClaimTarget(self, claim, snaktype='value', bot=True, **kwargs):
        """
        Set the claim target to the value of the provided claim target.

        @param claim: The source of the claim target value
        @type claim: Claim
        @param snaktype: An optional snaktype. Default: 'value'
        @type snaktype: str ('value', 'novalue' or 'somevalue')
        """
        if claim.isReference or claim.isQualifier:
            raise NotImplementedError
        if not claim.snak:
            # We need to already have the snak value
            raise NoPage(claim)
        params = dict(action='wbsetclaimvalue',
                      claim=claim.snak,
                      snaktype=snaktype,
                      )
        if bot:
            params['bot'] = 1
        if 'summary' in kwargs:
            params['summary'] = kwargs['summary']
        params['token'] = self.tokens['edit']
        if snaktype == 'value':
            params['value'] = json.dumps(claim._formatValue())

        params['baserevid'] = claim.on_item.lastrevid
        req = api.Request(site=self, **params)
        data = req.submit()
        return data

    @must_be(group='user')
    def editSource(self, claim, source, new=False, bot=True, **kwargs):
        """
        Create/Edit a source.

        @param claim: A Claim object to add the source to
        @type claim: Claim
        @param source: A Claim object to be used as a source
        @type source: Claim
        @param new: Whether to create a new one if the "source" already exists
        @type new: bool
        """
        if claim.isReference or claim.isQualifier:
            raise ValueError("The claim cannot have a source.")
        params = dict(action='wbsetreference',
                      statement=claim.snak,
                      )
        if claim.on_item:  # I think this wouldn't be false, but lets be safe
            params['baserevid'] = claim.on_item.lastrevid
        if bot:
            params['bot'] = 1
        params['token'] = self.tokens['edit']
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
        for arg in kwargs:
            if arg in ['baserevid', 'summary']:
                params[arg] = kwargs[arg]

        req = api.Request(site=self, **params)
        data = req.submit()
        return data

    @must_be(group='user')
    def editQualifier(self, claim, qualifier, new=False, bot=True, **kwargs):
        """
        Create/Edit a qualifier.

        @param claim: A Claim object to add the qualifier to
        @type claim: Claim
        @param qualifier: A Claim object to be used as a qualifier
        @type qualifier: Claim
        """
        if claim.isReference or claim.isQualifier:
            raise ValueError("The claim cannot have a qualifier.")
        params = dict(action='wbsetqualifier',
                      claim=claim.snak,
                      )
        if claim.on_item:  # I think this wouldn't be false, but lets be safe
            params['baserevid'] = claim.on_item.lastrevid
        if bot:
            params['bot'] = 1
        if (not new and
                hasattr(qualifier, 'hash') and
                qualifier.hash is not None):
            params['snakhash'] = qualifier.hash
        params['token'] = self.tokens['edit']
        # build up the snak
        if qualifier.getSnakType() == 'value':
            params['value'] = json.dumps(qualifier._formatValue())
        params['snaktype'] = qualifier.getSnakType()
        params['property'] = qualifier.getID()

        for arg in kwargs:
            if arg in ['baserevid', 'summary']:
                params[arg] = kwargs[arg]

        req = api.Request(site=self, **params)
        data = req.submit()
        return data

    @must_be(group='user')
    def removeClaims(self, claims, bot=True, **kwargs):
        params = dict(action='wbremoveclaims')
        if bot:
            params['bot'] = 1
        params['claim'] = '|'.join(claim.snak for claim in claims)
        params['token'] = self.tokens['edit']
        for kwarg in kwargs:
            if kwarg in ['baserevid', 'summary']:
                params[kwarg] = kwargs[kwarg]
        req = api.Request(site=self, **params)
        data = req.submit()
        return data

    @must_be(group='user')
    def removeSources(self, claim, sources, bot=True, **kwargs):
        """
        Remove sources.

        @param claim: A Claim object to remove the sources from
        @type claim: Claim
        @param sources: A list of Claim objects that are sources
        @type sources: Claim
        """
        params = dict(action='wbremovereferences')
        if bot:
            params['bot'] = 1
        params['statement'] = claim.snak
        params['references'] = '|'.join(source.hash for source in sources)
        params['token'] = self.tokens['edit']
        for kwarg in kwargs:
            if kwarg in ['baserevid', 'summary']:
                params[kwarg] = kwargs[kwarg]
        req = api.Request(site=self, **params)
        data = req.submit()
        return data

    def linkTitles(self, page1, page2, bot=True):
        """
        Link two pages together.

        @param page1: First page to link
        @type page1: pywikibot.Page
        @param page2: Second page to link
        @type page2: pywikibot.Page
        @param bot: whether to mark edit as bot
        @return: dict API output
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
        req = api.Request(site=self, **params)
        data = req.submit()
        return data

    def mergeItems(self, fromItem, toItem, **kwargs):
        """
        Merge two items together.

        @param fromItem: Item to merge from
        @type fromItem: pywikibot.ItemPage
        @param toItem: Item to merge into
        @type toItem: pywikibot.ItemPage
        @return: dict API output
        """
        params = {
            'action': 'wbmergeitems',
            'fromid': fromItem.getID(),
            'toid': toItem.getID(),
            'token': self.tokens['edit']
        }
        for kwarg in kwargs:
            if kwarg in ['ignoreconflicts', 'summary']:
                params[kwarg] = kwargs[kwarg]
        req = api.Request(site=self, **params)
        data = req.submit()
        return data

    def createNewItemFromPage(self, page, bot=True, **kwargs):
        """
        Create a new Wikibase item for a provided page.

        @param page: page to fetch links from
        @type page: pywikibot.Page
        @param bot: whether to mark the edit as bot
        @return: pywikibot.ItemPage of newly created item
        """
        sitelinks = {
            page.site.dbName(): {
                'site': page.site.dbName(),
                'title': page.title(),
            }
        }
        labels = {
            page.site.language(): {
                'language': page.site.language(),
                'value': page.title(),
            }
        }
        for link in page.iterlanglinks():
            sitelinks[link.site.dbName()] = {
                'site': link.site.dbName(),
                'title': link.title,
            }
            labels[link.site.language()] = {
                'language': link.site.language(),
                'value': link.title,
            }
        data = {
            'sitelinks': sitelinks,
            'labels': labels,
        }
        result = self.editEntity({}, data, bot=bot, **kwargs)
        return pywikibot.ItemPage(self, result['entity']['id'])

    def search_entities(self, search, language, limit=None, **kwargs):
        """
        Search for pages or properties that contain the given text.

        @param search: Text to find.
        @type search: str
        @param language: Language to search in.
        @type language: str
        @param limit: Maximum number of pages to retrieve in total, or None in
            case of no limit.
        @type limit: int or None
        @return: 'search' list from API output.
        """
        lang_codes = [lang['code'] for lang in self._siteinfo.get('languages')]
        if language not in lang_codes:
            raise ValueError(u'Data site used does not support provided '
                             u'language.')

        gen = api.APIGenerator('wbsearchentities', data_name='search',
                               search=search, language=language, **kwargs)
        gen.set_query_increment(50)
        if limit is not None:
            gen.set_maximum_items(limit)
        return gen

    # deprecated BaseSite methods
    def fam(self):
        raise NotImplementedError

    def urlEncode(self, *args, **kwargs):
        raise NotImplementedError

    def getUrl(self, *args, **kwargs):
        raise NotImplementedError

    def linkto(self, *args, **kwargs):
        raise NotImplementedError

    def loggedInAs(self, *args, **kwargs):
        raise NotImplementedError

    def postData(self, *args, **kwargs):
        raise NotImplementedError

    def postForm(self, *args, **kwargs):
        raise NotImplementedError

    # deprecated APISite methods
    def isBlocked(self, *args, **kwargs):
        raise NotImplementedError

    def isAllowed(self, *args, **kwargs):
        raise NotImplementedError

    def prefixindex(self, *args, **kwargs):
        raise NotImplementedError

    def categories(self, *args, **kwargs):
        raise NotImplementedError

    def linksearch(self, *args, **kwargs):
        raise NotImplementedError

    def newimages(self, *args, **kwargs):
        raise NotImplementedError
