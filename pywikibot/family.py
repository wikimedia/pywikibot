"""Objects representing MediaWiki families."""
#
# (C) Pywikibot team, 2004-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import collections
import inspect
import logging
import string
import sys
import types
import urllib.parse as urlparse
import warnings
from importlib import import_module
from itertools import chain
from os.path import basename, dirname, splitext
from textwrap import fill
from typing import TYPE_CHECKING

import pywikibot
from pywikibot import config
from pywikibot.backports import DefaultDict, Mapping, Sequence, removesuffix
from pywikibot.data import wikistats
from pywikibot.exceptions import FamilyMaintenanceWarning, UnknownFamilyError
from pywikibot.tools import classproperty, deprecated


logger = logging.getLogger('pywiki.wiki.family')

if TYPE_CHECKING:
    CrossnamespaceType = DefaultDict[str, dict[str, list[int]]]

# Legal characters for Family.name and Family.langs keys
NAME_CHARACTERS = string.ascii_letters + string.digits
# nds_nl code alias requires "_"n
# dash must be the last char to be reused as regex
CODE_CHARACTERS = string.ascii_lowercase + string.digits + '_-'


class Family:

    """Parent singleton class for all wiki families.

    Families are immutable and initializer is unsupported. Any class
    modification should go to :meth:`__post_init__` class method.

    .. versionchanged:: 3.0
       the family class is immutable. Having an ``__init__`` initializer
       method a ``NotImplementedWarning`` will be given.
    .. versionchanged:: 8.0
       ``alphabetic``, ``alphabetic_revised`` and ``fyinterwiki``
       attributes where removed.
    .. versionchanged:: 8.2
       :attr:`obsolete` setter was removed.
    .. versionchanged:: 8.3
       Having an initializer method a ``FutureWarning`` will be given.
    .. versionchanged:: 9.0
       raises RuntimeError if an initializer method was found;
       :meth:`__post_init__` classmethod should be used instead.
    """

    def __new__(cls):
        """Allocator."""
        # any Family class defined in this file are abstract
        if cls in globals().values():
            raise TypeError(f'Abstract Family class {cls.__name__} cannot be'
                            ' instantiated;  subclass it instead')

        # Override classproperty
        cls.instance = super().__new__(cls)
        cls.__new__ = lambda cls: cls.instance  # shortcut

        # don't use hasattr() here. consider only the class itself
        if '__init__' in cls.__dict__:
            raise RuntimeError(fill(
                f'Family class {cls.__module__}.{cls.__name__} cannot be'
                ' instantiated; use __post_init__() classmethod to modify'
                ' your family class. Refer the documentation.', width=66))

        if '__post_init__' not in cls.__dict__:
            pass
        elif inspect.ismethod(cls.__post_init__):  # classmethod check
            cls.__post_init__()
        else:
            raise RuntimeError(fill(
                f'__post_init__() method of {cls.__module__}.{cls.__name__}'
                ' class or its superclass must be a classmethod. Please  check'
                ' your family file.', width=66))

        return cls.instance

    @classproperty
    def instance(cls):
        """Get the singleton instance.

        This is a placeholder to invoke allocator before it's allocated.
        Allocator will override this classproperty.
        """
        return cls()

    #: The family name
    name: str | None = None

    #: Not open for edits; stewards can still edit.
    closed_wikis: list[str] = []

    #: Completely removed sites.
    removed_wikis: list[str] = []

    code_aliases: dict[str, str] = {}
    """Code mappings which are only an alias, and there is no 'old' wiki.
    For all except 'nl_nds', subdomains do exist as a redirect, but that
    should not be relied upon.
    """

    langs: dict[str, str] = {}

    #: A list of category redirect template names in different languages.
    category_redirect_templates: dict[str, Sequence[str]] = {
        '_default': []
    }

    #: A list of disambiguation template names in different languages.
    disambiguationTemplates: dict[str, Sequence[str]] = {
        '_default': []
    }

    edit_restricted_templates: dict[str, tuple[str, ...]] = {}
    """A dict of tuples for different sites with names of templates that
    indicate an edit should be avoided.
    """

    archived_page_templates: dict[str, tuple[str, ...]] = {}
    """A dict of tuples for different sites with names of archive
    templates that indicate an edit of non-archive bots should be
    avoided.
    """

    #: A set of projects that share cross-project sessions.
    cross_projects: set[str] = set()

    #: A list with the name for cross-project cookies, default for
    #: wikimedia centralAuth extensions.
    cross_projects_cookies = ['centralauth_Session',
                              'centralauth_Token',
                              'centralauth_User']
    cross_projects_cookie_username = 'centralauth_User'

    #: A list with the name in the cross-language flag permissions.
    cross_allowed: list[str] = []

    disambcatname: dict[str, str] = {}
    """A dict with the name of the category containing disambiguation
    pages for the various languages. Only one category per language, and
    without the namespace, so add things like:

        'en': "Disambiguation"
    """

    interwiki_attop: list[str] = []
    """attop is a list of languages that prefer to have the interwiki
    links at the top of the page.
    """

    interwiki_on_one_line: list[str] = []
    """on_one_line is a list of languages that want the interwiki links
    one-after-another on a single line
    """

    #: String used as separator between interwiki links and the text.
    interwiki_text_separator = '\n\n'

    # Similar for category
    category_attop: list[str] = []
    """attop is a list of categories that prefer to have the category
    links at the top of the page.
    """

    category_on_one_line: list[str] = []
    """on_one_line is a list of languages that want the category links
    one-after-another on a single line.
    """

    #: String used as separator between category links and the text
    category_text_separator = '\n\n'

    categories_last: list[str] = []
    """When both at the bottom should categories come after
    interwikilinks?

    TODO: :phab:`T86284` Needed on Wikia sites, as it uses the
    CategorySelect extension which puts categories last on all sites.
    TO BE DEPRECATED!
    """

    interwiki_putfirst: dict[str, str] = {}
    """Which languages have a special order for putting interlanguage
    links, and what order is it? If a language is not in
    interwiki_putfirst, alphabetical order on language code is used. For
    languages that are in interwiki_putfirst, interwiki_putfirst is
    checked first, and languages are put in the order given there. All
    other languages are put after those, in code-alphabetical order.
    """

    interwiki_forward: str | None = None
    """Some families, e. g. commons and meta, are not multilingual and
    forward interlanguage links to another family (wikipedia). These
    families can set this variable to the name of the target family.
    """

    #: Some languages belong to a group where the possibility is high
    #: that equivalent articles have identical titles among the group.
    language_groups = {
        # languages using the Arabic script
        'arab': [
            'ar', 'ary', 'arz', 'azb', 'ckb', 'fa', 'glk', 'ks', 'lrc',
            'mzn', 'ps', 'sd', 'ur',
            # languages using multiple scripts, including Arabic
            'ha', 'kk', 'ku', 'pnb', 'ug'
        ],
        # languages that use Chinese symbols
        'chinese': [
            'wuu', 'zh', 'zh-classical', 'zh-yue', 'gan', 'ii',
            # languages using multiple/mixed scripts, including Chinese
            'ja', 'za'
        ],
        # languages that use the Cyrillic alphabet
        'cyril': [
            'ab', 'av', 'ba', 'be', 'be-tarask', 'bg', 'bxr', 'ce', 'cu',
            'cv', 'kbd', 'koi', 'kv', 'ky', 'mk', 'lbe', 'mdf', 'mn', 'mo',
            'myv', 'mhr', 'mrj', 'os', 'ru', 'rue', 'sah', 'tg', 'tk',
            'udm', 'uk', 'xal',
            # languages using multiple scripts, including Cyrillic
            'ha', 'kk', 'sh', 'sr', 'tt'
        ],
        # languages that use a Greek script
        'grec': [
            'el', 'grc', 'pnt'
            # languages using multiple scripts, including Greek
        ],
        # languages that use the Latin alphabet
        'latin': [
            'aa', 'ace', 'af', 'ak', 'als', 'an', 'ang', 'ast', 'ay', 'bar',
            'bat-smg', 'bcl', 'bi', 'bm', 'br', 'bs', 'ca', 'cbk-zam', 'cdo',
            'ceb', 'ch', 'cho', 'chy', 'co', 'crh', 'cs', 'csb', 'cy', 'da',
            'de', 'diq', 'dsb', 'ee', 'eml', 'en', 'eo', 'es', 'et', 'eu',
            'ext', 'ff', 'fi', 'fiu-vro', 'fj', 'fo', 'fr', 'frp', 'frr',
            'fur', 'fy', 'ga', 'gag', 'gd', 'gl', 'gn', 'gv', 'hak', 'haw',
            'hif', 'ho', 'hr', 'hsb', 'ht', 'hu', 'hz', 'ia', 'id', 'ie', 'ig',
            'ik', 'ilo', 'io', 'is', 'it', 'jbo', 'jv', 'kaa', 'kab', 'kg',
            'ki', 'kj', 'kl', 'kr', 'ksh', 'kw', 'la', 'lad', 'lb', 'lg', 'li',
            'lij', 'lmo', 'ln', 'lt', 'ltg', 'lv', 'map-bms', 'mg', 'mh', 'mi',
            'ms', 'mt', 'mus', 'mwl', 'na', 'nah', 'nap', 'nds', 'nds-nl',
            'ng', 'nl', 'nn', 'no', 'nov', 'nrm', 'nv', 'ny', 'oc', 'om',
            'pag', 'pam', 'pap', 'pcd', 'pdc', 'pfl', 'pih', 'pl', 'pms', 'pt',
            'qu', 'rm', 'rn', 'ro', 'roa-rup', 'roa-tara', 'rw', 'sc', 'scn',
            'sco', 'se', 'sg', 'simple', 'sk', 'sl', 'sm', 'sn', 'so', 'sq',
            'srn', 'ss', 'st', 'stq', 'su', 'sv', 'sw', 'szl', 'tet', 'tl',
            'tn', 'to', 'tpi', 'tr', 'ts', 'tum', 'tw', 'ty', 'uz', 've',
            'vec', 'vi', 'vls', 'vo', 'wa', 'war', 'wo', 'xh', 'yo', 'zea',
            'zh-min-nan', 'zu',
            # languages using multiple scripts, including Latin
            'az', 'chr', 'ckb', 'ha', 'iu', 'kk', 'ku', 'rmy', 'sh', 'sr',
            'tt', 'ug', 'za'
        ],
        # Scandinavian languages
        'scand': [
            'da', 'fo', 'is', 'nb', 'nn', 'no', 'sv'
        ],
    }

    ldapDomain = ()
    """LDAP domain if your wiki uses LDAP authentication.

    .. seealso:: https://www.mediawiki.org/wiki/Extension:LDAPAuthentication2
    """

    crossnamespace: CrossnamespaceType = collections.defaultdict(dict)
    """Allows crossnamespace interwiki linking.

    Lists the possible crossnamespaces combinations; keys are
    originating namespace; values are dicts where keys are the
    originating langcode, or ``_default`` and  values are dicts where
    keys are the languages that can be linked to from the lang+ns, or
    ``_default``; values are a list of namespace numbers.

    **Examples:**

    Allowing linking *to* ``pt`` 102 namespace from any other lang 0
    namespace is:

    .. code-block:: Python

       crossnamespace[0] = {
           '_default': { 'pt': [102]}
       }

    While allowing linking *from* ``pt`` 102 namespace to any other
    lang 0 namespace is

    .. code-block:: Python

       crossnamespace[102] = {
           'pt': { '_default': [0]}
       }

    """

    shared_urlshortner_wiki: tuple[str, str] | None = None
    """Some wiki farms have UrlShortener extension enabled only on
    the main site. This value can specify this last one with
    ``(lang, family)`` tuple.
    """

    title_delimiter_and_aliases = ' _'
    """Titles usually are delimited by a space and the alias is replaced
    to this delimiter; e.g. "Main page" is the title with spaces as
    delimiters but "Main_page" also works. Other families may have
    different settings.

    .. note:: The first character is used as delimiter, the others are
       aliases.

    .. warning:: This attribute is used within ``re.sub()`` method. Use
       escape sequence if necessary

    .. versionadded:: 7.0
    """

    _families: dict[str, Family] = {}

    @staticmethod
    def load(fam: str | None = None):
        """Import the named family.

        :param fam: family name (if omitted, uses the configured default)
        :return: a Family instance configured for the named family.
        :raises pywikibot.exceptions.UnknownFamilyError: family not known
        """
        if fam is None:
            fam = config.family

        if fam in Family._families:
            return Family._families[fam]

        if fam not in config.family_files:
            raise UnknownFamilyError(f'Family {fam} does not exist')

        family_file = config.family_files[fam]

        if family_file.startswith(('http://', 'https://')):
            myfamily = AutoFamily(fam, family_file)
            Family._families[fam] = myfamily
            return Family._families[fam]

        try:
            # Ignore warnings due to dots in family names.
            # TODO: use more specific filter, so that family classes can use
            #     RuntimeWarning's while loading.
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                sys.path.append(dirname(family_file))
                mod = import_module(splitext(basename(family_file))[0])
        except ImportError:
            raise UnknownFamilyError(f'Family {fam} does not exist')
        cls = mod.Family.instance
        if cls.name != fam:
            warnings.warn(f'Family name {cls.name} does not match family '
                          f'module name {fam}',
                          FamilyMaintenanceWarning,
                          stacklevel=2)
        # Family 'name' and the 'langs' codes must be ascii letters and digits,
        # and codes must be lower-case due to the Site loading algorithm;
        # codes can accept also underscore/dash.
        if not all(x in NAME_CHARACTERS for x in cls.name):
            warnings.warn(
                f'Name of family {cls.name} must be ASCII letters and digits'
                ' [a-zA-Z0-9]',
                FamilyMaintenanceWarning,
                stacklevel=2,
            )
        for code in cls.langs:
            if not all(x in CODE_CHARACTERS for x in code):
                warnings.warn(
                    f'Family {cls.name} code {code} must be ASCII lowercase'
                    ' letters and digits [a-z0-9] or underscore/dash [_-]',
                    FamilyMaintenanceWarning,
                    stacklevel=2,
                )
        Family._families[fam] = cls
        return cls

    def category_redirects(self, code, fallback: str = '_default'):
        """Return list of category redirect templates."""
        if not hasattr(self, '_catredirtemplates') \
           or code not in self._catredirtemplates:
            self._get_cr_templates(code, fallback)
        return self._catredirtemplates[code]

    def _get_cr_templates(self, code, fallback) -> None:
        """Build list of category redirect templates."""
        if not hasattr(self, '_catredirtemplates'):
            self._catredirtemplates = {}
        if code in self.category_redirect_templates:
            cr_template_tuple = self.category_redirect_templates[code]
        elif fallback and fallback in self.category_redirect_templates:
            cr_template_tuple = self.category_redirect_templates[fallback]
        else:
            self._catredirtemplates[code] = []
            return
        cr_set = set()
        site = pywikibot.Site(code, self)
        tpl_ns = site.namespaces.TEMPLATE
        for cr_template in cr_template_tuple:
            cr_page = pywikibot.Page(site, cr_template, ns=tpl_ns)
            # retrieve all redirects to primary template from API,
            # add any that are not already on the list
            for t in cr_page.backlinks(filter_redirects=True,
                                       namespaces=tpl_ns):
                newtitle = t.title(with_ns=False)
                if newtitle not in cr_template_tuple:
                    cr_set.add(newtitle)
        self._catredirtemplates[code] = list(cr_template_tuple) + list(cr_set)

    def get_edit_restricted_templates(self, code):
        """Return tuple of edit restricted templates.

        .. versionadded:: 3.0
        """
        return self.edit_restricted_templates.get(code, ())

    def get_archived_page_templates(self, code):
        """Return tuple of archived page templates.

        .. versionadded:: 3.0
        """
        return self.archived_page_templates.get(code, ())

    def disambig(self, code, fallback: str | None = '_default') -> list[str]:
        """Return list of disambiguation templates.

        :raises KeyError: unknown title for disambig template
        """
        if code in self.disambiguationTemplates:
            return self.disambiguationTemplates[code]

        if fallback:
            return self.disambiguationTemplates[fallback]

        raise KeyError(
            f'ERROR: title for disambig template in language {code} unknown')

    def protocol(self, code: str) -> str:
        """The protocol to use to connect to the site.

        May be overridden to return 'http'. Other protocols are not
        supported.

        .. versionchanged:: 8.2
           ``https`` is returned instead of ``http``.

        :param code: language code
        :return: protocol that this family uses
        """
        return 'https'

    def verify_SSL_certificate(self, code: str) -> bool:
        """Return whether a HTTPS certificate should be verified.

        .. versionadded:: 5.3
           renamed from ignore_certificate_error

        :param code: language code
        :return: flag to verify the SSL certificate;
                 set it to False to allow access if certificate has an error.
        """
        return True

    def hostname(self, code):
        """The hostname to use for standard http connections."""
        return self.langs[code]

    def ssl_hostname(self, code):
        """The hostname to use for SSL connections."""
        return self.hostname(code)

    def scriptpath(self, code: str) -> str:
        """The prefix used to locate scripts on this wiki.

        This is the value displayed when you enter {{SCRIPTPATH}} on a
        wiki page (often displayed at [[Help:Variables]] if the wiki has
        copied the master help page correctly).

        The default value is the one used on Wikimedia Foundation wikis,
        but needs to be overridden in the family file for any wiki that
        uses a different value.

        :param code: Site code
        :raises KeyError: code is not recognised
        :return: URL path without ending '/'
        """
        return '/w'

    def ssl_pathprefix(self, code) -> str:
        """The path prefix for secure HTTP access."""
        # Override this ONLY if the wiki family requires a path prefix
        return ''

    def _hostname(self, code, protocol=None):
        """Return the protocol and hostname."""
        if protocol is None:
            protocol = self.protocol(code)
        if protocol == 'https':
            host = self.ssl_hostname(code)
        else:
            host = self.hostname(code)
        return protocol, host

    def base_url(self, code: str, uri: str, protocol=None) -> str:
        """Prefix uri with port and hostname.

        :param code: The site code
        :param uri: The absolute path after the hostname
        :param protocol: The protocol which is used. If None it'll determine
            the protocol from the code.
        :return: The full URL ending with uri
        """
        protocol, host = self._hostname(code, protocol)
        if protocol == 'https':
            uri = self.ssl_pathprefix(code) + uri
        return urlparse.urljoin(f'{protocol}://{host}', uri)

    def path(self, code) -> str:
        """Return path to index.php."""
        return f'{self.scriptpath(code)}/index.php'

    def querypath(self, code) -> str:
        """Return path to query.php."""
        return f'{self.scriptpath(code)}/query.php'

    def apipath(self, code) -> str:
        """Return path to api.php."""
        return f'{self.scriptpath(code)}/api.php'

    def eventstreams_host(self, code):
        """Hostname for EventStreams.

        .. versionadded:: 3.0
        """
        raise NotImplementedError('This family does not support EventStreams')

    def eventstreams_path(self, code):
        """Return path for EventStreams.

        .. versionadded:: 3.0
        """
        raise NotImplementedError('This family does not support EventStreams')

    def get_address(self, code, title) -> str:
        """Return the path to title using index.php with redirects disabled."""
        return f'{self.path(code)}?{title=!s}&redirect=no'

    def interface(self, code: str) -> str:
        """Return interface to use for code."""
        if code in self.interwiki_removals:
            if code in self.codes:
                warnings.warn(f'Interwiki removal {code} is in {self} codes',
                              FamilyMaintenanceWarning, stacklevel=2)
            if code in self.closed_wikis:
                return 'ClosedSite'
            if code in self.removed_wikis:
                return 'RemovedSite'

        return config.site_interface

    def from_url(self, url: str) -> str | None:
        """Return whether this family matches the given url.

        It is first checking if a domain of this family is in the domain
        of the URL. If that is the case it's checking all codes and
        verifies that a path generated via :attr:`APISite.articlepath
        <pywikibot.site.APISite.articlepath>` and :attr:`Family.path`
        matches the path of the URL together with the hostname for that
        code.

        It is using :attr:`Family.domains` to first check if a domain
        applies and then iterates over :attr:`Family.codes` to actually
        determine which code applies.

        .. versionchanged:: 10.0
           *url* parameter does not have to contain a api/query/script
           path

        :param url: the URL which may contain a ``$1``. If it's missing
            it is assumed to be at the end.
        :return: The language code of the URL. None if that URL is not
            from his family.
        :raises RuntimeError: When there are multiple languages in this
            family which would work with the given URL.
        """
        parsed = urlparse.urlparse(url)
        if parsed.scheme not in {'http', 'https', ''}:
            return None

        path = parsed.path
        if parsed.query:
            path += '?' + parsed.query

        # Discard $1 and everything after it
        path, *_ = path.partition('$1')

        for domain in self.domains:
            if domain in parsed.netloc:
                break
        else:
            return None

        matched_sites = set()
        for code in chain(self.codes,
                          getattr(self, 'test_codes', ()),
                          getattr(self, 'closed_wikis', ()),
                          ):
            if self._hostname(code)[1] == parsed.netloc:
                # Use the code and family instead of the url
                # This is only creating a Site instance if domain matches
                site = pywikibot.Site(code, self.name)
                pywikibot.log(f'Found candidate {site}')

                if not path:
                    return site.code

                for iw_url in site._interwiki_urls():
                    iw_url, *_ = iw_url.partition('{}')
                    if path.startswith(iw_url):
                        matched_sites.add(site)
                        break

        if len(matched_sites) == 1:
            return matched_sites.pop().code

        if not matched_sites:
            return None

        raise RuntimeError(
            'Found multiple matches for URL "{}": {}'
            .format(url, ', '.join(str(s) for s in matched_sites)))

    @deprecated('config.maximum_GET_length', since='8.0.0')
    def maximum_GET_length(self, code):
        """Return the maximum URL length for GET instead of POST.

        .. deprecated:: 8.0
           Use :ref:`config.maximum_GET_length<Account Settings>` instead.
        """
        return config.maximum_GET_length

    def dbName(self, code) -> str:
        """Return the name of the MySQL database."""
        return f'{code}{self.name}'

    def encoding(self, code) -> str:
        """Return the encoding for a specific language wiki."""
        return 'utf-8'

    def encodings(self, code):
        """Return list of historical encodings for a specific language wiki."""
        return (self.encoding(code), )

    def __eq__(self, other):
        """Compare self with other.

        If other is not a Family() object, try to create one.
        """
        if not isinstance(other, Family):
            other = self.load(other)

        return self is other

    def __ne__(self, other):
        try:
            return not self.__eq__(other)
        except UnknownFamilyError:
            return False

    def __hash__(self):
        return hash(self.name)

    def __str__(self) -> str:
        assert isinstance(self.name, str)
        return self.name

    def __repr__(self) -> str:
        return f'Family("{self.name}")'

    def shared_image_repository(self, code):
        """Return the shared image repository, if any."""
        return (None, None)

    def isPublic(self, code) -> bool:
        """Check the wiki require logging in before viewing it."""
        return True

    def post_get_convert(self, site, getText):
        """Do a conversion on the retrieved text from the Wiki.

        For example a :wiki:`X-conversion in Esperanto
        <Esperanto_orthography#X-system>`.
        """
        return getText

    def pre_put_convert(self, site, putText):
        """Do a conversion on the text to insert on the Wiki.

        For example a :wiki:`X-conversion in Esperanto
        <Esperanto_orthography#X-system>`.
        """
        return putText

    @property
    def obsolete(self) -> types.MappingProxyType[str, str | None]:
        """Old codes that are not part of the family.

        Interwiki replacements override removals for the same code.

        :return: mapping of old codes to new codes (or None)
        """
        data = dict.fromkeys(self.interwiki_removals)
        data.update(self.interwiki_replacements)
        return types.MappingProxyType(data)

    @classproperty
    def domains(cls) -> set[str]:
        """Get list of unique domain names included in this family.

        These domains may also exist in another family.
        """
        return set(cls.langs.values())

    @classproperty
    def codes(cls) -> set[str]:
        """Get list of codes used by this family."""
        return set(cls.langs.keys())

    @classproperty
    def interwiki_replacements(cls) -> Mapping[str, str]:
        """Return an interwiki code replacement mapping.

        Which language codes no longer exist and by which language code
        should they be replaced. If for example the language with code
        xx: now should get code yy:, add {'xx':'yy'} to
        :attr:`code_aliases`.

        .. versionchanged:: 8.2
           changed from dict to invariant mapping.
        """
        return types.MappingProxyType(cls.code_aliases)

    @classproperty
    def interwiki_removals(cls) -> frozenset[str]:
        """Return a list of interwiki codes to be removed from wiki pages.

        Codes that should be removed, usually because the site has been
        taken down.

        .. versionchanged:: 8.2
           changed from list to invariant frozenset.
        """
        return frozenset(cls.removed_wikis + cls.closed_wikis)


class SingleSiteFamily(Family):

    """Single site family."""

    def __new__(cls):
        """Initializer."""
        if not hasattr(cls, 'code'):
            cls.code = cls.name

        assert cls.domain

        cls.langs = {cls.code: cls.domain}

        return super().__new__(cls)

    @classproperty
    def domains(cls):
        """Return the full domain name of the site."""
        return (cls.domain, )

    def hostname(self, code):
        """Return the domain as the hostname."""
        return self.domain


class SubdomainFamily(Family):

    """Multi site wikis that are subdomains of the same top level domain."""

    def __new__(cls):
        """Initializer."""
        assert cls.domain
        return super().__new__(cls)

    @classproperty
    def langs(cls) -> dict[str, str]:
        """Property listing family languages."""
        codes = sorted(cls.codes)

        if hasattr(cls, 'test_codes'):
            codes += cls.test_codes

        codes += cls.closed_wikis

        # shortcut this classproperty
        cls.langs = {code: f'{code}.{cls.domain}' for code in codes}
        cls.langs.update({alias: f'{code}.{cls.domain}'
                          for alias, code in cls.code_aliases.items()})

        return cls.langs

    @classproperty
    def domains(cls):
        """Return the domain name of the sites in this family."""
        return [cls.domain]


class FandomFamily(Family):

    """Common features of Fandom families.

    .. versionadded:: 3.0
       renamed from WikiaFamily
    """

    @classproperty
    def langs(cls):
        """Property listing family languages."""
        codes = sorted(cls.codes)

        if hasattr(cls, 'code_aliases'):
            codes += cls.code_aliases

        return {code: cls.domain for code in codes}

    def scriptpath(self, code):
        """Return the script path for this family."""
        return '' if code == 'en' else ('/' + code)


class WikimediaFamily(Family):

    """Class for all wikimedia families.

    .. versionchanged:: 8.0
       :attr:`knows_codes` attribute was added.
    """

    multi_language_content_families = [
        'wikibooks',
        'wikinews',
        'wikipedia',
        'wikiquote',
        'wikisource',
        'wikiversity',
        'wikivoyage',
        'wiktionary',
    ]

    wikimedia_org_content_families = [
        'commons', 'incubator', 'species',
    ]

    wikimedia_org_meta_families = [
        'meta',
        'outreach',
        'strategy',
        'wikimediachapter',
        'wikimania',
    ]

    wikimedia_org_other_families = [
        'wikitech',
    ]

    other_content_families = [
        'lingualibre',
        'mediawiki',
        'wikidata',
        'wikifunctions',
    ]

    content_families = set(
        multi_language_content_families
        + wikimedia_org_content_families
        + other_content_families
    )

    wikimedia_org_families = set(
        wikimedia_org_content_families
        + wikimedia_org_meta_families
        + wikimedia_org_other_families
    )

    # CentralAuth cross available projects.
    cross_projects = set(
        multi_language_content_families
        + wikimedia_org_content_families
        + wikimedia_org_meta_families
        + other_content_families
    )

    # Known Wikimedia site codes
    known_codes = [
        'aa', 'ab', 'ace', 'ady', 'af', 'ak', 'als', 'alt', 'am', 'ami', 'an',
        'ang', 'ar', 'arc', 'ary', 'arz', 'as', 'ast', 'atj', 'av', 'avk',
        'awa', 'ay', 'az', 'azb', 'ba', 'ban', 'bar', 'bat-smg', 'bcl', 'be',
        'be-tarask', 'bg', 'bh', 'bi', 'bjn', 'blk', 'bm', 'bn', 'bo', 'bpy',
        'br', 'bs', 'bug', 'bxr', 'ca', 'cbk-zam', 'cdo', 'ce', 'ceb', 'ch',
        'cho', 'chr', 'chy', 'ckb', 'co', 'cr', 'crh', 'cs', 'csb', 'cu', 'cv',
        'cy', 'da', 'dag', 'de', 'din', 'diq', 'dk', 'dsb', 'dty', 'dv', 'dz',
        'ee', 'el', 'eml', 'en', 'eo', 'es', 'et', 'eu', 'ext', 'fa', 'ff',
        'fi', 'fiu-vro', 'fj', 'fo', 'fr', 'frp', 'frr', 'fur', 'fy', 'ga',
        'gag', 'gan', 'gcr', 'gd', 'gl', 'glk', 'gn', 'gom', 'gor', 'got',
        'gu', 'guw', 'gv', 'ha', 'hak', 'haw', 'he', 'hi', 'hif', 'ho', 'hr',
        'hsb', 'ht', 'hu', 'hy', 'hyw', 'hz', 'ia', 'id', 'ie', 'ig', 'ii',
        'ik', 'ilo', 'inh', 'io', 'is', 'it', 'iu', 'ja', 'jam', 'jbo', 'jv',
        'ka', 'kaa', 'kab', 'kbd', 'kbp', 'kcg', 'kg', 'ki', 'kj', 'kk', 'kl',
        'km', 'kn', 'ko', 'koi', 'kr', 'krc', 'ks', 'ksh', 'ku', 'kv', 'kw',
        'ky', 'la', 'lad', 'lb', 'lbe', 'lez', 'lfn', 'lg', 'li', 'lij', 'lld',
        'lmo', 'ln', 'lo', 'lrc', 'lt', 'ltg', 'lv', 'mad', 'mai', 'map-bms',
        'mdf', 'mg', 'mh', 'mhr', 'mi', 'min', 'mk', 'ml', 'mn', 'mni', 'mnw',
        'mo', 'mr', 'mrj', 'ms', 'mt', 'mus', 'mwl', 'my', 'myv', 'mzn', 'na',
        'nah', 'nan', 'nap', 'nb', 'nds', 'nds-nl', 'ne', 'new', 'ng', 'nia',
        'nl', 'nn', 'no', 'nov', 'nqo', 'nrm', 'nso', 'nv', 'ny', 'oc', 'olo',
        'om', 'or', 'os', 'pa', 'pag', 'pam', 'pap', 'pcd', 'pcm', 'pdc',
        'pfl', 'pi', 'pih', 'pl', 'pms', 'pnb', 'pnt', 'ps', 'pt', 'pwn', 'qu',
        'rm', 'rmy', 'rn', 'ro', 'roa-rup', 'roa-tara', 'ru', 'rue', 'rw',
        'sa', 'sah', 'sat', 'sc', 'scn', 'sco', 'sd', 'se', 'sg', 'sh', 'shi',
        'shn', 'si', 'simple', 'sk', 'skr', 'sl', 'sm', 'smn', 'sn', 'so',
        'sq', 'sr', 'srn', 'ss', 'st', 'stq', 'su', 'sv', 'sw', 'szl', 'szy',
        'ta', 'tay', 'tcy', 'te', 'tet', 'tg', 'th', 'ti', 'tk', 'tl', 'tn',
        'to', 'tpi', 'tr', 'trv', 'ts', 'tt', 'tum', 'tw', 'ty', 'tyv', 'udm',
        'ug', 'uk', 'ur', 'uz', 've', 'vec', 'vep', 'vi', 'vls', 'vo', 'wa',
        'war', 'wo', 'wuu', 'xal', 'xh', 'xmf', 'yi', 'yo', 'za', 'zea', 'zh',
        'zh-classical', 'zh-cn', 'zh-min-nan', 'zh-tw', 'zh-yue', 'zu',
    ]

    # Code mappings which are only an alias, and there is no 'old' wiki.
    # For all except 'nl_nds', subdomains do exist as a redirect, but that
    # should not be relied upon.
    code_aliases = {
        # Country aliases, see T87002
        'dk': 'da',
        'jp': 'ja',

        # Language aliases, see T86924
        'nb': 'no',

        # Closed wiki redirection aliases
        'mo': 'ro',

        # Incomplete language code change, see T86915
        'minnan': 'zh-min-nan',
        'nan': 'zh-min-nan',

        'zh-tw': 'zh',
        'zh-cn': 'zh',

        # Miss-spelling
        'nds_nl': 'nds-nl',

        # Renamed, see T11823
        'be-x-old': 'be-tarask',
    }

    # WikimediaFamily uses Wikibase for the category name containing
    # disambiguation pages for the various languages. We need the
    # Wikibase code and item number:
    disambcatname = {'wikidata': 'Q1982926'}

    # UrlShortener extension is only usable on metawiki, and this wiki can
    # process links to all WM domains.
    shared_urlshortner_wiki = ('meta', 'meta')

    @classproperty
    def domain(cls):
        """Domain property."""
        if cls.name in (cls.multi_language_content_families
                        + cls.other_content_families):
            return cls.name + '.org'
        if cls.name in cls.wikimedia_org_families:
            return 'wikimedia.org'

        raise NotImplementedError(
            f"Family {cls.name} needs to define property 'domain'")

    def shared_image_repository(self, code):
        """Return Wikimedia Commons as the shared image repository."""
        return ('commons', 'commons')

    def eventstreams_host(self, code) -> str:
        """Return 'https://stream.wikimedia.org' as the stream hostname."""
        return 'https://stream.wikimedia.org'

    def eventstreams_path(self, code) -> str:
        """Return path for EventStreams."""
        return '/v2/stream'

    @property
    def languages_by_size(self) -> list[str]:
        """Language codes of the largest wikis.

        They should be roughly sorted by size.

        .. versionchanged:: 9.0
           Sorting order is retrieved via :mod:`wikistats` for each call.

        :raises NotImplementedError: Family is not member of
            :attr:`multi_language_content_families`
        """
        if self.name not in self.multi_language_content_families:
            raise NotImplementedError(
                f'languages_by_size is not implemented for {self.name} family')

        exceptions = {
            'wikiversity': ['beta']
        }

        ws = wikistats.WikiStats()
        table = ws.languages_by_size(self.name)
        assert type(self.obsolete).__name__ == 'mappingproxy', (
            f'obsolete attribute is of type {type(self.obsolete).__name__} but'
            ' mappingproxy was expected'
        )

        lbs = [
            code for code in table
            if not (code in self.obsolete
                    or code in exceptions.get(self.name, []))
        ]

        # add codes missing by wikistats
        missing = set(self.codes) - set(lbs)
        return lbs + list(missing)


class WikimediaOrgFamily(SingleSiteFamily, WikimediaFamily):

    """Single site family for sites hosted at ``*.wikimedia.org``."""

    @classproperty
    def domain(cls) -> str:
        """Return the parents domain with a subdomain prefix."""
        return f'{cls.name}.wikimedia.org'


class WikibaseFamily(Family):

    """A base class for a Wikibase Family.

    .. versionadded:: 8.2
    """

    def interface(self, code) -> str:
        """Return 'DataSite' for Wikibase family."""
        return 'DataSite'

    def entity_sources(self, code: str) -> dict[str, tuple[str, str]]:
        """Provide repository site information for entity types.

        The result must be structured as follows:

            {<entity type>: (<family code>, <family name>)}

        for example:

            {'property': ('test', 'wikidata')}

        If an empty dict is returned, all entity types are found in the
        current ``DataSite``.

        The result is used by :meth:`DataSite.get_repo_for_entity_type
        <pywikibot.site._datasite.DataSite.get_repo_for_entity_type>`
        """
        return {}


class DefaultWikibaseFamily(WikibaseFamily):

    """A base class for a Wikimedia Wikibase Family.

    This class holds defaults for :meth:`calendarmodel`,
    :meth:`default_globe` and :meth:`globes` to prevent code duplication.

    .. warning:: Possibly you have to adjust the repository site in
       :meth:`WikibaseFamily.entity_sources` to get the valid entity.

    .. versionadded:: 8.2
    """

    def calendarmodel(self, code) -> str:
        """Default calendar model for WbTime datatype."""
        return 'http://www.wikidata.org/entity/Q1985727'

    def default_globe(self, code) -> str:
        """Default globe for Coordinate datatype."""
        return 'earth'

    def globes(self, code):
        """Supported globes for Coordinate datatype."""
        return {
            'ariel': 'http://www.wikidata.org/entity/Q3343',
            'bennu': 'http://www.wikidata.org/entity/Q11558',
            'callisto': 'http://www.wikidata.org/entity/Q3134',
            'ceres': 'http://www.wikidata.org/entity/Q596',
            'deimos': 'http://www.wikidata.org/entity/Q7548',
            'dione': 'http://www.wikidata.org/entity/Q15040',
            'earth': 'http://www.wikidata.org/entity/Q2',
            'enceladus': 'http://www.wikidata.org/entity/Q3303',
            'eros': 'http://www.wikidata.org/entity/Q16711',
            'europa': 'http://www.wikidata.org/entity/Q3143',
            'ganymede': 'http://www.wikidata.org/entity/Q3169',
            'gaspra': 'http://www.wikidata.org/entity/Q158244',
            'hyperion': 'http://www.wikidata.org/entity/Q15037',
            'iapetus': 'http://www.wikidata.org/entity/Q17958',
            'io': 'http://www.wikidata.org/entity/Q3123',
            'jupiter': 'http://www.wikidata.org/entity/Q319',
            'lutetia': 'http://www.wikidata.org/entity/Q107556',
            'mars': 'http://www.wikidata.org/entity/Q111',
            'mercury': 'http://www.wikidata.org/entity/Q308',
            'mimas': 'http://www.wikidata.org/entity/Q15034',
            'miranda': 'http://www.wikidata.org/entity/Q3352',
            'moon': 'http://www.wikidata.org/entity/Q405',
            'oberon': 'http://www.wikidata.org/entity/Q3332',
            'phobos': 'http://www.wikidata.org/entity/Q7547',
            'phoebe': 'http://www.wikidata.org/entity/Q17975',
            'pluto': 'http://www.wikidata.org/entity/Q339',
            'rhea': 'http://www.wikidata.org/entity/Q15050',
            'ryugu': 'http://www.wikidata.org/entity/Q1385178',
            'steins': 'http://www.wikidata.org/entity/Q150249',
            'tethys': 'http://www.wikidata.org/entity/Q15047',
            'titan': 'http://www.wikidata.org/entity/Q2565',
            'titania': 'http://www.wikidata.org/entity/Q3322',
            'triton': 'http://www.wikidata.org/entity/Q3359',
            'umbriel': 'http://www.wikidata.org/entity/Q3338',
            'venus': 'http://www.wikidata.org/entity/Q313',
            'vesta': 'http://www.wikidata.org/entity/Q3030',
        }


def AutoFamily(name: str, url: str) -> SingleSiteFamily:
    """Family that automatically loads the site configuration.

    :param name: Name for the family
    :param url: API endpoint URL of the wiki
    :return: Generated family class
    """
    url = urlparse.urlparse(url)
    domain = url.netloc

    def protocol(self, code):
        """Return the protocol of the URL."""
        return self.url.scheme

    def scriptpath(self, code):
        """Extract the script path from the URL."""
        if self.url.path.endswith('/api.php'):
            return removesuffix(self.url.path, '/api.php')

        # AutoFamily refers to the variable set below, not the function
        # but the reference must be given here
        return super(AutoFamily, self).scriptpath(code)

    AutoFamily = type('AutoFamily', (SingleSiteFamily,), locals())
    return AutoFamily()
