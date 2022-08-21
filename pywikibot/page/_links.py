"""Objects representing internal or interwiki link in wikitext.

.. note::
   `Link` objects defined here represent a wiki-page's title, while
   :class:`pywikibot.Page` objects represent the page itself, including
   its contents.
"""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import re
import unicodedata
from html.entities import name2codepoint

import pywikibot
from pywikibot import textlib
from pywikibot.exceptions import InvalidTitleError, SiteDefinitionError
from pywikibot.site import Namespace
from pywikibot.tools import ComparableMixin, first_upper, is_ip_address


__all__ = (
    'BaseLink',
    'Link',
    'SiteLink',
    'html2unicode',
)


class BaseLink(ComparableMixin):

    """
    A MediaWiki link (local or interwiki).

    Has the following attributes:

      - title: The title of the page linked to (str); does not include
        namespace or section
      - namespace: The Namespace object of the page linked to
      - site: The Site object for the wiki linked to
    """

    # Components used for __repr__
    _items = ('title', 'namespace', '_sitekey')

    def __init__(self, title: str, namespace=None, site=None) -> None:
        """
        Initializer.

        :param title: the title of the page linked to (str); does not
            include namespace or section
        :param namespace: the namespace of the page linked to. Can be provided
            as either an int, a Namespace instance or a str, defaults to the
            MAIN namespace.
        :type namespace: int, pywikibot.Namespace or str
        :param site: the Site object for the wiki linked to. Can be provided as
            either a Site instance or a db key, defaults to pywikibot.Site().
        :type site: pywikibot.Site or str
        """
        self.title = title

        if isinstance(namespace, pywikibot.site.Namespace):
            self._namespace = namespace
        else:
            # postpone evaluation of namespace until needed
            self._nskey = namespace

        site = site or pywikibot.Site()
        if isinstance(site, pywikibot.site.BaseSite):
            self._site = site
            self._sitekey = site.dbName()
        else:
            self._sitekey = site

    def __repr__(self) -> str:
        """Return a more complete string representation."""
        assert isinstance(self._items, tuple)
        assert all(isinstance(item, str) for item in self._items)

        attrs = ('{!r}'.format(getattr(self, attr)) for attr in self._items)
        return 'pywikibot.page.{}({})'.format(type(self).__name__,
                                              ', '.join(attrs))

    def lookup_namespace(self):
        """
        Look up the namespace given the provided namespace id or name.

        :rtype: pywikibot.Namespace
        """
        default_nskey = Namespace.MAIN
        self._nskey = self._nskey or default_nskey

        if isinstance(self._nskey, str):
            ns = self.site.namespaces.lookup_name(self._nskey)
            if ns:
                return ns
            self._nskey = default_nskey

        if isinstance(self._nskey, int):
            try:
                ns = self.site.namespaces[self._nskey]
            except KeyError:
                ns = self.site.namespaces[default_nskey]
            return ns

        raise TypeError(
            'Invalid type "{}" for Page._nskey. Must be int or str.'
            .format(type(self._nskey)))

    @property
    def site(self):
        """
        Return the site of the link.

        :rtype: pywikibot.Site
        """
        if not hasattr(self, '_site'):
            self._site = pywikibot.site.APISite.fromDBName(self._sitekey)
        return self._site

    @property
    def namespace(self):
        """
        Return the namespace of the link.

        :rtype: pywikibot.Namespace
        """
        if not hasattr(self, '_namespace'):
            self._namespace = self.lookup_namespace()
        return self._namespace

    def canonical_title(self):
        """Return full page title, including localized namespace."""
        # Avoid that ':' will be added to the title for Main ns.
        if self.namespace != Namespace.MAIN:
            return '{}:{}'.format(self.site.namespace(self.namespace),
                                  self.title)
        return self.title

    def ns_title(self, onsite=None):
        """
        Return full page title, including namespace.

        :param onsite: site object
            if specified, present title using onsite local namespace,
            otherwise use self canonical namespace.

        :raise pywikibot.exceptions.InvalidTitleError: no corresponding
            namespace is found in onsite
        """
        if onsite is None:
            name = self.namespace.canonical_name
        else:
            # look for corresponding ns in onsite by name comparison
            for alias in self.namespace:
                namespace = onsite.namespaces.lookup_name(alias)
                if namespace is not None:
                    name = namespace.custom_name
                    break
            else:
                raise InvalidTitleError(
                    'No corresponding title found for namespace {} on {}.'
                    .format(self.namespace, onsite))

        if self.namespace != Namespace.MAIN:
            return '{}:{}'.format(name, self.title)
        return self.title

    def astext(self, onsite=None) -> str:
        """
        Return a text representation of the link.

        :param onsite: if specified, present as a (possibly interwiki) link
            from the given site; otherwise, present as an internal link on
            the site.
        """
        if onsite is None:
            onsite = self.site
        title = self.title
        if self.namespace != Namespace.MAIN:
            title = onsite.namespace(self.namespace) + ':' + title
        if onsite == self.site:
            return '[[{}]]'.format(title)
        if onsite.family == self.site.family:
            return '[[{}:{}]]'.format(self.site.code, title)
        if self.site.family.name == self.site.code:
            # use this form for sites like commons, where the
            # code is the same as the family name
            return '[[{}:{}]]'.format(self.site.code, title)
        return '[[{}:{}]]'.format(self.site.sitename, title)

    def _cmpkey(self):
        """
        Key for comparison of BaseLink objects.

        BaseLink objects are "equal" if and only if they are on the same site
        and have the same normalized title.

        BaseLink objects are sortable by site, then namespace, then title.
        """
        return (self.site, self.namespace, self.title)

    def __str__(self) -> str:
        """Return a str string representation."""
        return self.astext()

    def __hash__(self):
        """A stable identifier to be used as a key in hash-tables."""
        return hash((self.site.sitename, self.canonical_title()))

    @classmethod
    def fromPage(cls, page):  # noqa: N802
        """
        Create a BaseLink to a Page.

        :param page: target pywikibot.page.Page
        :type page: pywikibot.page.Page

        :rtype: pywikibot.page.BaseLink
        """
        title = page.title(with_ns=False,
                           allow_interwiki=False,
                           with_section=False)

        return cls(title, namespace=page.namespace(), site=page.site)


class Link(BaseLink):

    """
    A MediaWiki wikitext link (local or interwiki).

    Constructs a Link object based on a wikitext link and a source site.

    Extends BaseLink by the following attributes:

      - section: The section of the page linked to (str or None); this
        contains any text following a '#' character in the title
      - anchor: The anchor text (str or None); this contains any text
        following a '|' character inside the link
    """

    # Components used for __repr__
    _items = ('title', 'site')

    illegal_titles_pattern = re.compile(
        # Matching titles will be held as illegal.
        r'[\x00-\x1f\x23\x3c\x3e\x5b\x5d\x7b\x7c\x7d\x7f]'
        # URL percent encoding sequences interfere with the ability
        # to round-trip titles -- you can't link to them consistently.
        '|%[0-9A-Fa-f]{2}'
        # XML/HTML character references produce similar issues.
        '|&[A-Za-z0-9\x80-\xff]+;'
        '|&#[0-9]+;'
        '|&#x[0-9A-Fa-f]+;'
    )

    def __init__(self, text, source=None, default_namespace=0) -> None:
        """
        Initializer.

        :param text: the link text (everything appearing between [[ and ]]
            on a wiki page)
        :type text: str
        :param source: the Site on which the link was found (not necessarily
            the site to which the link refers)
        :type source: Site or BasePage
        :param default_namespace: a namespace to use if the link does not
            contain one (defaults to 0)
        :type default_namespace: int

        :raises UnicodeError: text could not be converted to unicode.
        """
        source_is_page = isinstance(source, pywikibot.page.BasePage)

        if source_is_page:
            self._source = source.site
        else:
            self._source = source or pywikibot.Site()

        assert isinstance(self._source, pywikibot.site.BaseSite), \
            'source parameter should be either a Site or Page object'

        self._text = text
        # See bug T104864, default_namespace might have been deleted.
        try:
            self._defaultns = self._source.namespaces[default_namespace]
        except KeyError:
            self._defaultns = default_namespace

        # preprocess text (these changes aren't site-dependent)
        # First remove anchor, which is stored unchanged, if there is one
        if '|' in self._text:
            self._text, self._anchor = self._text.split('|', 1)
        else:
            self._anchor = None

        self._text = self._text.strip()

        # Convert URL-encoded characters to unicode
        self._text = pywikibot.tools.chars.url2string(
            self._text, encodings=self._source.encodings())

        # Clean up the name, it can come from anywhere.
        # Convert HTML entities to unicode
        t = html2unicode(self._text)

        # Normalize unicode string to a NFC (composed) format to allow
        # proper string comparisons to strings output from MediaWiki API.
        t = unicodedata.normalize('NFC', t)

        # This code was adapted from Title.php : secureAndSplit()
        if '\ufffd' in t:
            raise InvalidTitleError(
                '{!r} contains illegal char {!r}'.format(t, '\ufffd'))

        # Cleanup whitespace
        sep = self._source.family.title_delimiter_and_aliases[0]
        t = re.sub(
            '[{}\xa0\u1680\u180E\u2000-\u200A\u2028\u2029\u202F\u205F\u3000]+'
            .format(self._source.family.title_delimiter_and_aliases),
            sep, t)
        # Strip spaces at both ends
        t = t.strip()
        # Remove left-to-right and right-to-left markers.
        t = t.replace('\u200e', '').replace('\u200f', '')
        self._text = t

        if source_is_page:
            self._text = source.title(with_section=False) + self._text

    def parse_site(self) -> tuple:
        """
        Parse only enough text to determine which site the link points to.

        This method does not parse anything after the first ":"; links
        with multiple interwiki prefixes (such as "wikt:fr:Parlais") need
        to be re-parsed on the first linked wiki to get the actual site.

        :return: The family name and site code for the linked site. If the site
            is not supported by the configured families it returns None instead
            of a str.
        """
        t = self._text
        fam = self._source.family
        code = self._source.code
        while ':' in t:
            # Initial colon
            if t.startswith(':'):
                # remove the colon but continue processing
                # remove any subsequent whitespace
                t = t.lstrip(':').lstrip(' ')
                continue
            prefix = t[:t.index(':')].lower()  # part of text before :
            ns = self._source.namespaces.lookup_name(prefix)
            if ns:
                # The prefix is a namespace in the source wiki
                return (fam.name, code)
            if prefix in fam.langs:
                # prefix is a language code within the source wiki family
                return (fam.name, prefix)
            try:
                newsite = self._source.interwiki(prefix)
            except KeyError:
                break  # text before : doesn't match any known prefix
            except SiteDefinitionError:
                return (None, None)
            else:
                return (newsite.family.name, newsite.code)
        return (fam.name, code)  # text before : doesn't match any known prefix

    def parse(self):
        """
        Parse wikitext of the link.

        Called internally when accessing attributes.
        """
        self._site = self._source
        self._namespace = self._defaultns
        self._is_interwiki = False
        ns_prefix = False

        old_position = int(self._text.startswith(':'))
        colon_position = self._text.find(':', old_position)
        first_other_site = None
        while colon_position >= 0:
            prefix = self._text[old_position:colon_position].lower()
            # All spaces after a prefix are discarded
            colon_position += 1
            while (len(self._text) > colon_position
                    and self._text[colon_position] == ' '):
                colon_position += 1
            ns = self._site.namespaces.lookup_name(prefix)
            if ns:
                if len(self._text) <= colon_position:
                    raise InvalidTitleError(
                        "'{}' has no title.".format(self._text))
                self._namespace = ns
                ns_prefix = True
                old_position = colon_position
                break

            try:
                newsite = self._site.interwiki(prefix)
            except KeyError:
                break  # text before : doesn't match any known prefix
            except SiteDefinitionError as e:
                raise SiteDefinitionError(
                    '{} is not a local page on {}, and the interwiki '
                    'prefix {} is not supported by Pywikibot!\n{}'
                    .format(self._text, self._site, prefix, e))
            else:
                if first_other_site:
                    if not self._site.local_interwiki(prefix):
                        raise InvalidTitleError(
                            '{} links to a non local site {} via an '
                            'interwiki link to {}.'.format(
                                self._text, newsite, first_other_site))
                elif newsite != self._source:
                    first_other_site = newsite
                self._site = newsite
                self._is_interwiki = True
            old_position = colon_position
            colon_position = self._text.find(':', old_position)

        # Remove any namespaces/interwiki prefixes
        t = self._text[old_position:]

        if '#' in t:
            t, sec = t.split('#', 1)
            t, self._section = t.rstrip(), sec.lstrip()
        else:
            self._section = None

        if ns_prefix:
            # 'namespace:' is not a valid title
            if not t:
                raise InvalidTitleError(
                    "'{}' has no title.".format(self._text))

            if ':' in t and self._namespace >= 0:  # < 0 don't have talk
                other_ns = self._site.namespaces[self._namespace - 1
                                                 if self._namespace % 2 else
                                                 self._namespace + 1]
                if '' in other_ns:  # other namespace uses empty str as ns
                    next_ns = t[:t.index(':')]
                    if self._site.namespaces.lookup_name(next_ns):
                        raise InvalidTitleError(
                            "The (non-)talk page of '{}' is a valid title "
                            'in another namespace.'.format(self._text))

        # Reject illegal characters.
        m = Link.illegal_titles_pattern.search(t)
        if m:
            raise InvalidTitleError('{!r} contains illegal char(s) {!r}'
                                    .format(t, m.group(0)))

        # Pages with "/./" or "/../" appearing in the URLs will
        # often be unreachable due to the way web browsers deal
        # * with 'relative' URLs. Forbid them explicitly.

        if '.' in t and (t in ('.', '..')
                         or t.startswith(('./', '../'))
                         or '/./' in t
                         or '/../' in t
                         or t.endswith(('/.', '/..'))):
            raise InvalidTitleError(
                "(contains . / combinations): '{}'"
                .format(self._text))

        # Magic tilde sequences? Nu-uh!
        if '~~~' in t:
            raise InvalidTitleError("(contains ~~~): '{}'"
                                    .format(self._text))

        if self._namespace != -1 and len(t) > 255:
            raise InvalidTitleError("(over 255 bytes): '{}'".format(t))

        # "empty" local links can only be self-links
        # with a fragment identifier.
        if not t.strip(' ') and not self._is_interwiki:  # T197642
            raise InvalidTitleError(
                'The link [[{}]] does not contain a page title'
                .format(self._text))

        # MediaWiki uses uppercase IP addresses
        if self._namespace in (2, 3) and is_ip_address(t):
            t = t.upper()
        elif self._site.namespaces[self._namespace].case == 'first-letter':
            t = first_upper(t)

        self._title = t

    # define attributes, to be evaluated lazily

    @property
    def site(self):
        """
        Return the site of the link.

        :rtype: pywikibot.Site
        """
        if not hasattr(self, '_site'):
            self.parse()
        return self._site

    @property
    def namespace(self):
        """
        Return the namespace of the link.

        :rtype: pywikibot.Namespace
        """
        if not hasattr(self, '_namespace'):
            self.parse()
        return self._namespace

    @property
    def title(self) -> str:
        """Return the title of the link."""
        if not hasattr(self, '_title'):
            self.parse()
        return self._title

    @property
    def section(self) -> str:
        """Return the section of the link."""
        if not hasattr(self, '_section'):
            self.parse()
        return self._section

    @property
    def anchor(self) -> str:
        """Return the anchor of the link."""
        if not hasattr(self, '_anchor'):
            self.parse()
        return self._anchor

    def astext(self, onsite=None):
        """
        Return a text representation of the link.

        :param onsite: if specified, present as a (possibly interwiki) link
            from the given site; otherwise, present as an internal link on
            the source site.
        """
        if onsite is None:
            onsite = self._source
        text = super().astext(onsite)
        if self.section:
            text = '{}#{}]]'.format(text.rstrip(']'), self.section)

        return text

    def _cmpkey(self):
        """
        Key for comparison of Link objects.

        Link objects are "equal" if and only if they are on the same site
        and have the same normalized title, including section if any.

        Link objects are sortable by site, then namespace, then title.
        """
        return (self.site, self.namespace, self.title)

    @classmethod
    def fromPage(cls, page, source=None):  # noqa: N802
        """
        Create a Link to a Page.

        :param page: target Page
        :type page: pywikibot.page.Page
        :param source: Link from site source
        :param source: Site

        :rtype: pywikibot.page.Link
        """
        base_link = BaseLink.fromPage(page)
        link = cls.__new__(cls)
        link._site = base_link.site
        link._title = base_link.title
        link._namespace = base_link.namespace

        link._section = page.section()
        link._anchor = None
        link._source = source or pywikibot.Site()

        return link

    @classmethod
    def langlinkUnsafe(cls, lang, title, source):  # noqa: N802
        """
        Create a "lang:title" Link linked from source.

        Assumes that the lang & title come clean, no checks are made.

        :param lang: target site code (language)
        :type lang: str
        :param title: target Page
        :type title: str
        :param source: Link from site source
        :param source: Site

        :rtype: pywikibot.page.Link
        """
        link = cls.__new__(cls)
        if source.family.interwiki_forward:
            link._site = pywikibot.Site(lang, source.family.interwiki_forward)
        else:
            link._site = pywikibot.Site(lang, source.family.name)
        link._section = None
        link._source = source

        link._namespace = link._site.namespaces[0]
        if ':' in title:
            ns, t = title.split(':', 1)
            ns = link._site.namespaces.lookup_name(ns)
            if ns:
                link._namespace = ns
                title = t

        if '#' in title:
            t, sec = title.split('#', 1)
            title, link._section = t.rstrip(), sec.lstrip()
        else:
            link._section = None
        link._title = title
        return link

    @classmethod
    def create_separated(cls, link, source, default_namespace=0, section=None,
                         label=None):
        """
        Create a new instance but overwrite section or label.

        The returned Link instance is already parsed.

        :param link: The original link text.
        :type link: str
        :param source: The source of the link.
        :type source: Site
        :param default_namespace: The namespace this link uses when no
            namespace is defined in the link text.
        :type default_namespace: int
        :param section: The new section replacing the one in link. If None
            (default) it doesn't replace it.
        :type section: None or str
        :param label: The new label replacing the one in link. If None
            (default) it doesn't replace it.
        """
        link = cls(link, source, default_namespace)
        link.parse()
        if section:
            link._section = section
        elif section is not None:
            link._section = None
        if label:
            link._anchor = label
        elif label is not None:
            link._anchor = ''
        return link


class SiteLink(BaseLink):

    """
    A single sitelink in a Wikibase item.

    Extends BaseLink by the following attribute:

      - badges: Any badges associated with the sitelink

    .. versionadded:: 3.0
    """

    # Components used for __repr__
    _items = ('_sitekey', '_rawtitle', 'badges')

    def __init__(self, title, site=None, badges=None) -> None:
        """
        Initializer.

        :param title: the title of the linked page including namespace
        :type title: str
        :param site: the Site object for the wiki linked to. Can be provided as
            either a Site instance or a db key, defaults to pywikibot.Site().
        :type site: pywikibot.Site or str
        :param badges: list of badges
        :type badges: [pywikibot.ItemPage]
        """
        # split of namespace from title
        namespace = None
        self._rawtitle = title
        if ':' in title:
            site, namespace, title = SiteLink._parse_namespace(title, site)

        super().__init__(title, namespace, site)

        badges = badges or []
        self._badges = set(badges)

    @staticmethod
    def _parse_namespace(title, site=None):
        """
        Parse enough of a title with a ':' to determine the namespace.

        :param site: the Site object for the wiki linked to. Can be provided as
            either a Site instance or a db key, defaults to pywikibot.Site().
        :type site: pywikibot.Site or str
        :param title: the title of the linked page including namespace
        :type title: str

        :return: a (site, namespace, title) tuple
        :rtype: (pywikibot.Site, pywikibot.Namespace or None, str)
        """
        # need a Site instance to evaluate local namespaces
        site = site or pywikibot.Site()
        if not isinstance(site, pywikibot.site.BaseSite):
            site = pywikibot.site.APISite.fromDBName(site)

        prefix = title[:title.index(':')].lower()  # part of text before :
        ns = site.namespaces.lookup_name(prefix)
        if ns:  # The prefix is a namespace in the source wiki
            namespace, _, title = title.partition(':')
        else:  # The ':' is part of the actual title see e.g. Q3700510
            namespace = None

        return (site, namespace, title)

    @property
    def badges(self):
        """
        Return a list of all badges associated with the link.

        :rtype: [pywikibot.ItemPage]
        """
        return list(self._badges)

    @classmethod
    def fromJSON(cls, data: dict, site=None):  # noqa: N802
        """
        Create a SiteLink object from JSON returned in the API call.

        :param data: JSON containing SiteLink data
        :param site: The Wikibase site
        :type site: pywikibot.site.DataSite

        :rtype: pywikibot.page.SiteLink
        """
        sl = cls(data['title'], data['site'])
        repo = site or sl.site.data_repository()
        for badge in data.get('badges', []):
            sl._badges.add(pywikibot.ItemPage(repo, badge))
        return sl

    def toJSON(self) -> dict:  # noqa: N802
        """
        Convert the SiteLink to a JSON object for the Wikibase API.

        :return: Wikibase JSON
        """
        json = {
            'site': self._sitekey,
            'title': self._rawtitle,
            'badges': [badge.title() for badge in self.badges]
        }
        return json


# Utility functions for parsing page titles

# This regular expression will match any decimal and hexadecimal entity and
# also entities that might be named entities.
_ENTITY_SUB = re.compile(
    r'&(#(?P<decimal>\d+)|#x(?P<hex>[0-9a-fA-F]+)|(?P<name>[A-Za-z]+));').sub
# These characters are Html-illegal, but sadly you *can* find some of
# these and converting them to chr(decimal) is unsuitable
_ILLEGAL_HTML_ENTITIES_MAPPING = {
    128: 8364,  # €
    130: 8218,  # ‚
    131: 402,   # ƒ
    132: 8222,  # „
    133: 8230,  # …
    134: 8224,  # †
    135: 8225,  # ‡
    136: 710,   # ˆ
    137: 8240,  # ‰
    138: 352,   # Š
    139: 8249,  # ‹
    140: 338,   # Œ
    142: 381,   # Ž
    145: 8216,  # ‘
    146: 8217,  # ’
    147: 8220,  # “
    148: 8221,  # ”
    149: 8226,  # •
    150: 8211,  # –
    151: 8212,  # —
    152: 732,   # ˜
    153: 8482,  # ™
    154: 353,   # š
    155: 8250,  # ›
    156: 339,   # œ
    158: 382,   # ž
    159: 376    # Ÿ
}


def html2unicode(text: str, ignore=None, exceptions=None) -> str:
    """
    Replace HTML entities with equivalent unicode.

    :param ignore: HTML entities to ignore
    :param ignore: list of int
    """
    if ignore is None:
        ignore = []
    # ensuring that illegal &#129; &#141; and &#157, which have no known
    # values, don't get converted to chr(129), chr(141) or chr(157)
    ignore = {_ILLEGAL_HTML_ENTITIES_MAPPING.get(x, x)
              for x in ignore} | {129, 141, 157}

    def handle_entity(match):
        if textlib.isDisabled(match.string, match.start(), tags=exceptions):
            # match.string stores original text so we do not need
            # to pass it to handle_entity, ♥ Python
            return match.group(0)

        if match.group('decimal'):
            unicode_codepoint = int(match.group('decimal'))
        elif match.group('hex'):
            unicode_codepoint = int(match.group('hex'), 16)
        elif match.group('name'):
            name = match.group('name')
            unicode_codepoint = name2codepoint.get(name, False)

        unicode_codepoint = _ILLEGAL_HTML_ENTITIES_MAPPING.get(
            unicode_codepoint, unicode_codepoint)

        if unicode_codepoint and unicode_codepoint not in ignore:
            return chr(unicode_codepoint)

        # Leave the entity unchanged
        return match.group(0)

    return _ENTITY_SUB(handle_entity, text)
