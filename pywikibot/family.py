"""Objects representing MediaWiki families."""
#
# (C) Pywikibot team, 2004-2022
#
# Distributed under the terms of the MIT license.
#
import collections
import logging
import re
import string
import sys
import types
import urllib.parse as urlparse
import warnings
from importlib import import_module
from itertools import chain
from os.path import basename, dirname, splitext
from typing import Optional

import pywikibot
from pywikibot import config
from pywikibot.backports import Dict, List, Set, Tuple  # skipcq: PY-W2000
from pywikibot.exceptions import FamilyMaintenanceWarning, UnknownFamilyError
from pywikibot.tools import classproperty, deprecated, remove_last_args


logger = logging.getLogger('pywiki.wiki.family')

# Legal characters for Family.name and Family.langs keys
NAME_CHARACTERS = string.ascii_letters + string.digits
# nds_nl code alias requires "_"n
# dash must be the last char to be reused as regex
CODE_CHARACTERS = string.ascii_lowercase + string.digits + '_-'


class Family:

    """Parent singleton class for all wiki families."""

    def __new__(cls):
        """Allocator."""
        # any Family class defined in this file are abstract
        if cls in globals().values():
            raise TypeError(
                'Abstract Family class {} cannot be instantiated; '
                'subclass it instead'.format(cls.__name__))

        # Override classproperty
        cls.instance = super().__new__(cls)
        cls.__new__ = lambda cls: cls.instance  # shortcut

        # don't use hasattr() here. consider only the class itself
        if '__init__' in cls.__dict__:
            # Initializer deprecated. Families should be immutable and any
            # instance / class modification should go to allocator (__new__).
            cls.__init__ = deprecated(cls.__init__)

            # Invoke initializer immediately and make initializer no-op.
            # This is to avoid repeated initializer invocation on repeated
            # invocations of the metaclass's __call__.
            cls.instance.__init__()
            cls.__init__ = lambda self: None  # no-op

        return cls.instance

    @classproperty
    def instance(cls):
        """Get the singleton instance."""
        # This is a placeholder to invoke allocator before it's allocated.
        # Allocator will override this classproperty.
        return cls()

    name = None

    langs = {}  # type: Dict[str, str]

    # For interwiki sorting order see
    # https://meta.wikimedia.org/wiki/Interwiki_sorting_order

    # The sorting order by language name from meta
    # MediaWiki:Interwiki_config-sorting_order-native-languagename
    alphabetic = [
        'ace', 'kbd', 'ady', 'af', 'ak', 'als', 'alt', 'am', 'smn', 'ang',
        'ab', 'ar', 'an', 'arc', 'roa-rup', 'frp', 'as', 'ast', 'atj', 'awa',
        'gn', 'av', 'ay', 'az', 'ban', 'bm', 'bn', 'bjn', 'zh-min-nan', 'nan',
        'map-bms', 'ba', 'be', 'be-tarask', 'mnw', 'bh', 'bcl', 'bi', 'bg',
        'bar', 'blk', 'bo', 'bs', 'br', 'bxr', 'ca', 'cv', 'ceb', 'cs', 'ch',
        'cbk-zam', 'ny', 'sn', 'tum', 'cho', 'co', 'cy', 'dag', 'da', 'dk',
        'ary', 'pdc', 'de', 'dv', 'nv', 'dsb', 'dty', 'dz', 'mh', 'et', 'el',
        'eml', 'en', 'myv', 'es', 'eo', 'ext', 'eu', 'ee', 'fa', 'hif', 'fo',
        'fr', 'fy', 'ff', 'fur', 'ga', 'gv', 'gag', 'gd', 'gl', 'gan', 'ki',
        'glk', 'guw', 'gu', 'gor', 'got', 'hak', 'xal', 'ko', 'ha', 'haw',
        'hy', 'hi', 'ho', 'hsb', 'hr', 'hyw', 'io', 'ig', 'ilo', 'inh', 'bpy',
        'id', 'ia', 'ie', 'iu', 'ik', 'os', 'xh', 'zu', 'is', 'it', 'he', 'jv',
        'kbp', 'kl', 'kn', 'kr', 'pam', 'krc', 'ka', 'ks', 'csb', 'kk', 'kw',
        'rw', 'rn', 'sw', 'kv', 'kg', 'gom', 'avk', 'ht', 'gcr', 'ku', 'kj',
        'ky', 'mrj', 'lld', 'lad', 'lbe', 'lo', 'ltg', 'la', 'lv', 'lb', 'lez',
        'lfn', 'lt', 'lij', 'li', 'ln', 'olo', 'jbo', 'lg', 'lmo', 'lrc',
        'mad', 'hu', 'mai', 'mk', 'mg', 'ml', 'mt', 'mi', 'mr', 'xmf', 'arz',
        'mzn', 'mni', 'ms', 'min', 'cdo', 'mwl', 'mdf', 'mo', 'mn', 'mus',
        'my', 'nah', 'na', 'fj', 'nl', 'nds-nl', 'cr', 'ne', 'new', 'nia',
        'ja', 'nqo', 'nap', 'ce', 'frr', 'pih', 'no', 'nb', 'nn', 'nrm', 'nov',
        'ii', 'oc', 'mhr', 'or', 'om', 'ng', 'hz', 'uz', 'pa', 'pi', 'pfl',
        'pag', 'ami', 'pnb', 'pap', 'ps', 'jam', 'koi', 'km', 'pcd', 'pcm',
        'pms', 'pwn', 'tpi', 'nds', 'pl', 'pnt', 'pt', 'aa', 'kaa', 'crh',
        'ty', 'ksh', 'ro', 'rmy', 'rm', 'qu', 'rue', 'ru', 'sah', 'szy', 'se',
        'sm', 'sa', 'sg', 'sat', 'skr', 'sc', 'sco', 'trv', 'stq', 'st', 'nso',
        'tn', 'sq', 'scn', 'si', 'simple', 'sd', 'ss', 'sk', 'sl', 'cu', 'szl',
        'so', 'ckb', 'srn', 'sr', 'sh', 'su', 'fi', 'sv', 'shi', 'tl', 'shn',
        'ta', 'kab', 'roa-tara', 'tt', 'tay', 'te', 'tet', 'th', 'ti', 'tg',
        'to', 'chr', 'chy', 've', 'tcy', 'tr', 'azb', 'tk', 'tw', 'kcg', 'tyv',
        'din', 'udm', 'bug', 'uk', 'ur', 'ug', 'za', 'vec', 'vep', 'vi', 'vo',
        'fiu-vro', 'wa', 'zh-classical', 'vls', 'war', 'wo', 'wuu', 'ts', 'yi',
        'yo', 'zh-yue', 'diq', 'zea', 'bat-smg', 'zh', 'zh-tw', 'zh-cn',
    ]

    # The revised sorting order by first word from meta
    # MediaWiki:Interwiki_config-sorting_order-native-languagename-firstword
    alphabetic_revised = [
        'ace', 'ady', 'kbd', 'af', 'ak', 'als', 'alt', 'kcg', 'am', 'smn',
        'ang', 'ab', 'ar', 'an', 'arc', 'roa-rup', 'frp', 'as', 'ast', 'atj',
        'awa', 'gn', 'av', 'ay', 'az', 'bjn', 'id', 'ms', 'ban', 'bm', 'bn',
        'zh-min-nan', 'nan', 'map-bms', 'jv', 'su', 'ba', 'min', 'be',
        'be-tarask', 'mnw', 'mad', 'bh', 'bcl', 'bi', 'bar', 'blk', 'bo', 'bs',
        'br', 'bug', 'bg', 'bxr', 'ca', 'ceb', 'cv', 'cs', 'ch', 'cbk-zam',
        'ny', 'sn', 'tum', 'cho', 'co', 'cy', 'dag', 'da', 'dk', 'ary', 'pdc',
        'de', 'dv', 'nv', 'dsb', 'na', 'dty', 'dz', 'mh', 'et', 'el', 'eml',
        'en', 'myv', 'es', 'eo', 'ext', 'eu', 'ee', 'fa', 'hif', 'fo', 'fr',
        'fy', 'ff', 'fur', 'ga', 'gv', 'sm', 'gag', 'gd', 'gl', 'gan', 'ki',
        'glk', 'guw', 'gu', 'got', 'hak', 'xal', 'ko', 'ha', 'haw', 'hy', 'hi',
        'ho', 'hsb', 'hr', 'hyw', 'io', 'ig', 'ilo', 'inh', 'bpy', 'ia', 'ie',
        'iu', 'ik', 'os', 'xh', 'zu', 'is', 'it', 'he', 'kl', 'kn', 'kr',
        'pam', 'ka', 'ks', 'csb', 'kk', 'kw', 'rw', 'ky', 'rn', 'mrj', 'sw',
        'kv', 'kg', 'gom', 'avk', 'gor', 'ht', 'gcr', 'ku', 'shn', 'kj', 'lld',
        'lad', 'lbe', 'lez', 'lfn', 'lo', 'la', 'ltg', 'lv', 'to', 'lb', 'lt',
        'lij', 'li', 'ln', 'nia', 'olo', 'jbo', 'lg', 'lmo', 'lrc', 'hu',
        'mai', 'mk', 'mg', 'ml', 'krc', 'mt', 'mi', 'mr', 'xmf', 'arz', 'mzn',
        'mni', 'cdo', 'mwl', 'koi', 'mdf', 'mo', 'mn', 'mus', 'my', 'nah',
        'fj', 'nl', 'nds-nl', 'cr', 'ne', 'new', 'ja', 'nqo', 'nap', 'ce',
        'frr', 'pih', 'no', 'nb', 'nn', 'nrm', 'nov', 'ii', 'oc', 'mhr', 'or',
        'om', 'ng', 'hz', 'uz', 'pa', 'pi', 'pfl', 'pag', 'ami', 'pnb', 'pap',
        'ps', 'jam', 'km', 'pcd', 'pcm', 'pms', 'pwn', 'nds', 'pl', 'pnt',
        'pt', 'aa', 'kaa', 'crh', 'ty', 'ksh', 'ro', 'rmy', 'rm', 'qu', 'ru',
        'rue', 'sah', 'szy', 'se', 'sa', 'sg', 'sat', 'skr', 'sc', 'sco',
        'trv', 'stq', 'st', 'nso', 'tn', 'sq', 'scn', 'si', 'simple', 'sd',
        'ss', 'sk', 'sl', 'cu', 'szl', 'so', 'ckb', 'srn', 'sr', 'sh', 'fi',
        'sv', 'shi', 'tl', 'ta', 'kab', 'kbp', 'roa-tara', 'tt', 'tay', 'te',
        'tet', 'th', 'vi', 'ti', 'tg', 'tpi', 'chr', 'chy', 've', 'tcy', 'tr',
        'azb', 'tk', 'tw', 'tyv', 'din', 'udm', 'uk', 'ur', 'ug', 'za', 'vec',
        'vep', 'vo', 'fiu-vro', 'wa', 'zh-classical', 'vls', 'war', 'wo',
        'wuu', 'ts', 'yi', 'yo', 'zh-yue', 'diq', 'zea', 'bat-smg', 'zh',
        'zh-tw', 'zh-cn',
    ]

    # Order for fy: alphabetical by code, but y counts as i
    fyinterwiki = alphabetic[:]
    fyinterwiki.remove('nb')
    fyinterwiki.sort(key=lambda x:
                     x.replace('y', 'i') + x.count('y') * '!')

    # A list of category redirect template names in different languages
    category_redirect_templates = {
        '_default': []
    }

    # A list of languages that use hard (not soft) category redirects
    use_hard_category_redirects = []

    # A list of disambiguation template names in different languages
    disambiguationTemplates = {
        '_default': []
    }

    # A dict of tuples for different sites with names of templates
    # that indicate an edit should be avoided
    edit_restricted_templates = {}  # type: Dict[str, Tuple[str, ...]]

    # A dict of tuples for different sites with names of archive
    # templates that indicate an edit of non-archive bots
    # should be avoided
    archived_page_templates = {}  # type: Dict[str, Tuple[str, ...]]

    # A list of projects that share cross-project sessions.
    cross_projects = []

    # A list with the name for cross-project cookies.
    # default for wikimedia centralAuth extensions.
    cross_projects_cookies = ['centralauth_Session',
                              'centralauth_Token',
                              'centralauth_User']
    cross_projects_cookie_username = 'centralauth_User'

    # A list with the name in the cross-language flag permissions
    cross_allowed = []  # type: List[str]

    # A dict with the name of the category containing disambiguation
    # pages for the various languages. Only one category per language,
    # and without the namespace, so add things like:
    # 'en': "Disambiguation"
    disambcatname = {}  # type: Dict[str, str]

    # attop is a list of languages that prefer to have the interwiki
    # links at the top of the page.
    interwiki_attop = []  # type: List[str]
    # on_one_line is a list of languages that want the interwiki links
    # one-after-another on a single line
    interwiki_on_one_line = []  # type: List[str]
    # String used as separator between interwiki links and the text
    interwiki_text_separator = '\n\n'

    # Similar for category
    category_attop = []  # type: List[str]
    # on_one_line is a list of languages that want the category links
    # one-after-another on a single line
    category_on_one_line = []  # type: List[str]
    # String used as separator between category links and the text
    category_text_separator = '\n\n'
    # When both at the bottom should categories come after interwikilinks?
    # TODO: T86284 Needed on Wikia sites, as it uses the CategorySelect
    # extension which puts categories last on all sites. TO BE DEPRECATED!
    categories_last = []  # type: List[str]

    # Which languages have a special order for putting interlanguage
    # links, and what order is it? If a language is not in
    # interwiki_putfirst, alphabetical order on language code is used.
    # For languages that are in interwiki_putfirst, interwiki_putfirst
    # is checked first, and languages are put in the order given there.
    # All other languages are put after those, in code-alphabetical
    # order.
    interwiki_putfirst = {}

    # Some families, e. g. commons and meta, are not multilingual and
    # forward interlanguage links to another family (wikipedia).
    # These families can set this variable to the name of the target
    # family.
    interwiki_forward = None

    # Which language codes no longer exist and by which language code
    # should they be replaced. If for example the language with code xx:
    # now should get code yy:, add {'xx':'yy'} to obsolete.
    interwiki_replacements = {}  # type: Dict[str, str]

    # Codes that should be removed, usually because the site has been
    # taken down.
    interwiki_removals = []  # type: List[str]

    # Language codes of the largest wikis. They should be roughly sorted
    # by size.
    languages_by_size = []  # type: List[str]

    # Some languages belong to a group where the possibility is high that
    # equivalent articles have identical titles among the group.
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

    # LDAP domain if your wiki uses LDAP authentication,
    # https://www.mediawiki.org/wiki/Extension:LDAPAuthentication2
    ldapDomain = ()

    # Allows crossnamespace interwiki linking.
    # Lists the possible crossnamespaces combinations
    # keys are originating NS
    # values are dicts where:
    #   keys are the originating langcode, or _default
    #   values are dicts where:
    #     keys are the languages that can be linked to from the lang+ns, or
    #     '_default'; values are a list of namespace numbers
    crossnamespace = collections.defaultdict(dict)
    ##
    # Examples :
    #
    # Allowing linking to pt' 102 NS from any other lang' 0 NS is
    #
    #   crossnamespace[0] = {
    #       '_default': { 'pt': [102]}
    #   }
    #
    # While allowing linking from pt' 102 NS to any other lang' = NS is
    #
    #   crossnamespace[102] = {
    #       'pt': { '_default': [0]}
    #   }

    # Some wiki farms have UrlShortener extension enabled only on the main
    # site. This value can specify this last one with (lang, family) tuple.
    shared_urlshortner_wiki = None  # type: Optional[Tuple[str, str]]

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

    _families = {}

    @staticmethod
    def load(fam: Optional[str] = None):
        """Import the named family.

        :param fam: family name (if omitted, uses the configured default)
        :return: a Family instance configured for the named family.
        :raises pywikibot.exceptions.UnknownFamilyError: family not known
        """
        if fam is None:
            fam = config.family

        if fam in Family._families:
            return Family._families[fam]

        if fam in config.family_files:
            family_file = config.family_files[fam]

            if family_file.startswith(('http://', 'https://')):
                myfamily = AutoFamily(fam, family_file)
                Family._families[fam] = myfamily
                return Family._families[fam]
        else:
            raise UnknownFamilyError('Family {} does not exist'.format(fam))

        try:
            # Ignore warnings due to dots in family names.
            # TODO: use more specific filter, so that family classes can use
            #     RuntimeWarning's while loading.
            with warnings.catch_warnings():
                warnings.simplefilter('ignore', RuntimeWarning)
                sys.path.append(dirname(family_file))
                mod = import_module(splitext(basename(family_file))[0])
        except ImportError:
            raise UnknownFamilyError('Family {} does not exist'.format(fam))
        cls = mod.Family.instance
        if cls.name != fam:
            warnings.warn('Family name {} does not match family module name {}'
                          .format(cls.name, fam), FamilyMaintenanceWarning)
        # Family 'name' and the 'langs' codes must be ascii letters and digits,
        # and codes must be lower-case due to the Site loading algorithm;
        # codes can accept also underscore/dash.
        if not all(x in NAME_CHARACTERS for x in cls.name):
            warnings.warn('Name of family {} must be ASCII letters '
                          'and digits [a-zA-Z0-9]'
                          .format(cls.name), FamilyMaintenanceWarning)
        for code in cls.langs.keys():
            if not all(x in CODE_CHARACTERS for x in code):
                warnings.warn('Family {} code {} must be ASCII lowercase '
                              'letters and digits [a-z0-9] or '
                              'underscore/dash [_-]'
                              .format(cls.name, code),
                              FamilyMaintenanceWarning)
        Family._families[fam] = cls
        return cls

    @deprecated('APISite.linktrail()', since='7.3.0')
    @remove_last_args(['fallback'])
    def linktrail(self, code: str) -> str:
        """Return regex for trailing chars displayed as part of a link.

        Returns a string, not a compiled regular expression object.

        .. deprecated:: 7.3
        """
        site = pywikibot.Site(code, 'wikipedia')
        return site.linktrail()

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

    def disambig(self, code, fallback: str = '_default'):
        """Return list of disambiguation templates."""
        if code in self.disambiguationTemplates:
            return self.disambiguationTemplates[code]

        if fallback:
            return self.disambiguationTemplates[fallback]

        raise KeyError(
            'ERROR: title for disambig template in language {} unknown'
            .format(code))

    # Methods
    def protocol(self, code: str) -> str:
        """
        The protocol to use to connect to the site.

        May be overridden to return 'https'. Other protocols are not supported.

        :param code: language code
        :return: protocol that this family uses
        """
        return 'http'

    def verify_SSL_certificate(self, code: str) -> bool:
        """
        Return whether a HTTPS certificate should be verified.

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
        """
        Prefix uri with port and hostname.

        :param code: The site code
        :param uri: The absolute path after the hostname
        :param protocol: The protocol which is used. If None it'll determine
            the protocol from the code.
        :return: The full URL ending with uri
        """
        protocol, host = self._hostname(code, protocol)
        if protocol == 'https':
            uri = self.ssl_pathprefix(code) + uri
        return urlparse.urljoin('{}://{}'.format(protocol, host), uri)

    def path(self, code) -> str:
        """Return path to index.php."""
        return '{}/index.php'.format(self.scriptpath(code))

    def querypath(self, code) -> str:
        """Return path to query.php."""
        return '{}/query.php'.format(self.scriptpath(code))

    def apipath(self, code) -> str:
        """Return path to api.php."""
        return '{}/api.php'.format(self.scriptpath(code))

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
        return '{}?title={}&redirect=no'.format(self.path(code), title)

    def interface(self, code) -> str:
        """Return interface to use for code."""
        if code in self.interwiki_removals:
            if code in self.codes:
                pywikibot.warn('Interwiki removal {} is in {} codes'
                               .format(code, self))
            if code in self.closed_wikis:
                return 'ClosedSite'
            if code in self.removed_wikis:
                return 'RemovedSite'

        return config.site_interface

    def from_url(self, url: str) -> Optional[str]:
        """Return whether this family matches the given url.

        It is first checking if a domain of this family is in the domain of
        the URL. If that is the case it's checking all codes and verifies that
        a path generated via
        :py:obj:`APISite.articlepath<pywikibot.site.APISite.articlepath>` and
        :py:obj:`Family.path` matches the path of the URL together with
        the hostname for that code.

        It is using :py:obj:`Family.domains` to first check if a domain
        applies and then iterates over :py:obj:`Family.codes` to actually
        determine which code applies.

        :param url: the URL which may contain a ``$1``. If it's missing it is
            assumed to be at the end.
        :return: The language code of the url. None if that url is not from
            this family.
        :raises RuntimeError: When there are multiple languages in this family
            which would work with the given URL.
        """
        parsed = urlparse.urlparse(url)
        if not re.match('(https?)?$', parsed.scheme):
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
                pywikibot.log('Found candidate {}'.format(site))

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

    def maximum_GET_length(self, code):
        """Return the maximum URL length for GET instead of POST."""
        return config.maximum_GET_length

    def dbName(self, code) -> str:
        """Return the name of the MySQL database."""
        return '{}{}'.format(code, self.name)

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
        return self.name

    def __repr__(self) -> str:
        return 'Family("{}")'.format(self.name)

    def shared_image_repository(self, code):
        """Return the shared image repository, if any."""
        return (None, None)

    def isPublic(self, code) -> bool:
        """Check the wiki require logging in before viewing it."""
        return True

    def post_get_convert(self, site, getText):
        """
        Do a conversion on the retrieved text from the Wiki.

        For example a X-conversion in Esperanto
        https://en.wikipedia.org/wiki/Esperanto_orthography#X-system.
        """
        return getText

    def pre_put_convert(self, site, putText):
        """
        Do a conversion on the text to insert on the Wiki.

        For example a X-conversion in Esperanto
        https://en.wikipedia.org/wiki/Esperanto_orthography#X-system.
        """
        return putText

    @property
    def obsolete(self) -> Dict[str, Optional[str]]:
        """
        Old codes that are not part of the family.

        Interwiki replacements override removals for the same code.

        :return: mapping of old codes to new codes (or None)
        """
        data = {code: None for code in self.interwiki_removals}
        data.update(self.interwiki_replacements)
        return types.MappingProxyType(data)

    @obsolete.setter
    def obsolete(self, data) -> None:
        """Split obsolete dict into constituent parts."""
        self.interwiki_removals[:] = [old for (old, new) in data.items()
                                      if new is None]
        self.interwiki_replacements.clear()
        self.interwiki_replacements.update((old, new)
                                           for (old, new) in data.items()
                                           if new is not None)

    @classproperty
    def domains(cls) -> Set[str]:
        """
        Get list of unique domain names included in this family.

        These domains may also exist in another family.
        """
        return set(cls.langs.values())

    @classproperty
    def codes(cls):
        """
        Get list of codes used by this family.

        :rtype: set of str
        """
        return set(cls.langs.keys())


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
    def langs(cls):
        """Property listing family languages."""
        codes = cls.codes[:]

        if hasattr(cls, 'test_codes'):
            codes += cls.test_codes
        if hasattr(cls, 'closed_wikis'):
            codes += cls.closed_wikis

        # shortcut this classproperty
        cls.langs = {code: '{}.{}'.format(code, cls.domain)
                     for code in codes}

        if hasattr(cls, 'code_aliases'):
            cls.langs.update({alias: '{}.{}'.format(code, cls.domain)
                              for alias, code in cls.code_aliases.items()})

        return cls.langs

    @classproperty
    def codes(cls):
        """Property listing family codes."""
        if cls.languages_by_size:
            return cls.languages_by_size
        raise NotImplementedError(
            'Family {} needs property "languages_by_size" or "codes"'
            .format(cls.name))

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
        codes = cls.codes

        if hasattr(cls, 'code_aliases'):
            codes += tuple(cls.code_aliases.keys())

        return {code: cls.domain for code in codes}

    def protocol(self, code) -> str:
        """Return 'https' as the protocol."""
        return 'https'

    def scriptpath(self, code):
        """Return the script path for this family."""
        return '' if code == 'en' else ('/' + code)


class WikimediaFamily(Family):

    """Class for all wikimedia families."""

    multi_language_content_families = [
        'wikipedia', 'wiktionary',
        'wikisource', 'wikibooks',
        'wikinews', 'wikiquote',
        'wikiversity', 'wikivoyage',
    ]

    wikimedia_org_content_families = [
        'commons', 'incubator', 'species',
    ]

    wikimedia_org_meta_families = [
        'meta', 'outreach', 'strategy',
        'wikimediachapter', 'wikimania',
    ]

    wikimedia_org_other_families = [
        'wikitech',
    ]

    other_content_families = [
        'wikidata',
        'mediawiki',
        'lingualibre',
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

    # Not open for edits; stewards can still edit.
    closed_wikis = []  # type: List[str]
    # Completely removed
    removed_wikis = []  # type: List[str]

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
            "Family {} needs to define property 'domain'".format(cls.name))

    @classproperty
    def interwiki_removals(cls):
        """Return a list of interwiki codes to be removed from wiki pages."""
        return frozenset(cls.removed_wikis + cls.closed_wikis)

    @classproperty
    def interwiki_replacements(cls):
        """Return an interwiki code replacement mapping."""
        return types.MappingProxyType(cls.code_aliases)

    def shared_image_repository(self, code):
        """Return Wikimedia Commons as the shared image repository."""
        return ('commons', 'commons')

    def protocol(self, code) -> str:
        """Return 'https' as the protocol."""
        return 'https'

    def eventstreams_host(self, code) -> str:
        """Return 'https://stream.wikimedia.org' as the stream hostname."""
        return 'https://stream.wikimedia.org'

    def eventstreams_path(self, code) -> str:
        """Return path for EventStreams."""
        return '/v2/stream'


class WikimediaOrgFamily(SingleSiteFamily, WikimediaFamily):

    """Single site family for sites hosted at ``*.wikimedia.org``."""

    @classproperty
    def domain(cls) -> str:
        """Return the parents domain with a subdomain prefix."""
        return '{}.wikimedia.org'.format(cls.name)


def AutoFamily(name: str, url: str) -> SingleSiteFamily:
    """
    Family that automatically loads the site configuration.

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
            return self.url.path[0:-8]

        # AutoFamily refers to the variable set below, not the function
        # but the reference must be given here
        return super(AutoFamily, self).scriptpath(code)

    AutoFamily = type('AutoFamily', (SingleSiteFamily,), locals())
    return AutoFamily()
