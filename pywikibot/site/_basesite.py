"""Objects with site methods independent of the communication interface."""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import functools
import re
import threading
from typing import Optional
from warnings import warn

import pywikibot
from pywikibot.backports import Pattern
from pywikibot.exceptions import (
    Error,
    FamilyMaintenanceWarning,
    NoPageError,
    PageInUseError,
    UnknownSiteError,
)
from pywikibot.site._namespace import Namespace, NamespacesDict
from pywikibot.throttle import Throttle
from pywikibot.tools import (
    cached,
    ComparableMixin,
    SelfCallString,
    first_upper,
    normalize_username,
)


class BaseSite(ComparableMixin):

    """Site methods that are independent of the communication interface."""

    def __init__(self, code: str, fam=None, user=None) -> None:
        """
        Initializer.

        :param code: the site's language code
        :type code: str
        :param fam: wiki family name (optional)
        :type fam: str or pywikibot.family.Family
        :param user: bot user name (optional)
        :type user: str
        """
        if code.lower() != code:
            # Note the Site function in __init__ also emits a UserWarning
            # for this condition, showing the callers file and line no.
            pywikibot.log('BaseSite: code "{}" converted to lowercase'
                          .format(code))
            code = code.lower()
        if not all(x in pywikibot.family.CODE_CHARACTERS for x in code):
            pywikibot.log('BaseSite: code "{}" contains invalid characters'
                          .format(code))
        self.__code = code
        if isinstance(fam, str) or fam is None:
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
                pywikibot.log('Site {} instantiated and marked "obsolete" '
                              'to prevent access'.format(self))
        elif self.__code not in self.languages():
            if self.__family.name in self.__family.langs \
               and len(self.__family.langs) == 1:
                self.__code = self.__family.name
                if self.__family == pywikibot.config.family \
                   and code == pywikibot.config.mylang:
                    pywikibot.config.mylang = self.__code
                    warn('Global configuration variable "mylang" changed to '
                         '"{}" while instantiating site {}'
                         .format(self.__code, self), UserWarning)
            else:
                error_msg = ("Language '{}' does not exist in family {}"
                             .format(self.__code, self.__family.name))
                raise UnknownSiteError(error_msg)

        self._username = normalize_username(user)

        self.use_hard_category_redirects = (
            self.code in self.family.use_hard_category_redirects)

        # following are for use with lock_page and unlock_page methods
        self._pagemutex = threading.Condition()
        self._locked_pages = set()

    @property
    @cached
    def throttle(self):
        """Return this Site's throttle. Initialize a new one if needed."""
        return Throttle(self)

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
    @cached
    def doc_subpage(self) -> tuple:
        """Return the documentation subpage for this Site."""
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
                    warn('Site {} has no language defined in '
                         'doc_subpages dict in {}_family.py file'
                         .format(self, self.family.name),
                         FamilyMaintenanceWarning, 2)
        # doc_subpages not defined in x_family.py file
        except AttributeError:
            doc = ()  # default
            warn('Site {} has no doc_subpages dict in {}_family.py file'
                 .format(self, self.family.name),
                 FamilyMaintenanceWarning, 2)

        return doc

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

    def __setstate__(self, attrs) -> None:
        """Restore things removed in __getstate__."""
        self.__dict__.update(attrs)
        self._pagemutex = threading.Condition()

    def user(self) -> Optional[str]:
        """Return the currently-logged in bot username, or None."""
        if self.logged_in():
            return self.username()
        return None

    def username(self) -> Optional[str]:
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
            raise AttributeError("{} instance has no attribute '{}'"
                                 .format(self.__class__.__name__, attr))

    def __str__(self) -> str:
        """Return string representing this Site's name and code."""
        return self.family.name + ':' + self.code

    @property
    def sitename(self):
        """String representing this Site's name and code."""
        return SelfCallString(self.__str__())

    def __repr__(self) -> str:
        """Return internal representation."""
        return '{}("{}", "{}")'.format(
            self.__class__.__name__, self.code, self.family)

    def __hash__(self):
        """Return hash value of instance."""
        return hash(repr(self))

    def languages(self):
        """Return list of all valid language codes for this site's Family."""
        return list(self.family.langs.keys())

    def validLanguageLinks(self):  # noqa: N802
        """Return list of language codes to be used in interwiki links."""
        return [lang for lang in self.languages()
                if self.namespaces.lookup_normalized_name(lang) is None]

    def _interwiki_urls(self, only_article_suffixes: bool = False):
        base_path = self.path()
        if not only_article_suffixes:
            yield base_path + '{}'
        yield base_path + '/{}'
        yield base_path + '?title={}'
        yield self.articlepath

    def _build_namespaces(self):
        """Create default namespaces."""
        return Namespace.builtin_namespaces()

    @property
    @cached
    def namespaces(self):
        """Return dict of valid namespaces on this wiki."""
        return NamespacesDict(self._build_namespaces())

    def ns_normalize(self, value):
        """
        Return canonical local form of namespace name.

        :param value: A namespace name
        :type value: str

        """
        index = self.namespaces.lookup_name(value)
        return self.namespace(index)

    def redirect(self):
        """Return list of localized redirect tags for the site."""
        return ['REDIRECT']

    def pagenamecodes(self):
        """Return list of localized PAGENAME tags for the site."""
        return ['PAGENAME']

    def pagename2codes(self):
        """Return list of localized PAGENAMEE tags for the site."""
        return ['PAGENAMEE']

    def lock_page(self, page, block: bool = True):
        """
        Lock page for writing. Must be called before writing any page.

        We don't want different threads trying to write to the same page
        at the same time, even to different sections.

        :param page: the page to be locked
        :type page: pywikibot.Page
        :param block: if true, wait until the page is available to be locked;
            otherwise, raise an exception if page can't be locked

        """
        title = page.title(with_section=False)
        with self._pagemutex:
            while title in self._locked_pages:
                if not block:
                    raise PageInUseError(title)
                self._pagemutex.wait()
            self._locked_pages.add(title)

    def unlock_page(self, page) -> None:
        """
        Unlock page. Call as soon as a write operation has completed.

        :param page: the page to be locked
        :type page: pywikibot.Page

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

            dp = pywikibot.ItemPage(repo, item)
            try:
                name = dp.getSitelink(self)
            except NoPageError:
                raise Error(
                    'No disambiguation category name found in {repo} '
                    'for {site}'.format(repo=repo_name, site=self))

        else:  # fallback for non WM sites
            try:
                name = '{}:{}'.format(Namespace.CATEGORY,
                                      self.family.disambcatname[self.code])
            except KeyError:
                raise Error(
                    'No disambiguation category name found in '
                    '{site.family.name}_family for {site}'.format(site=self))

        return pywikibot.Category(pywikibot.Link(name, self))

    def isInterwikiLink(self, text):  # noqa: N802
        """Return True if text is in the form of an interwiki link.

        If a link object constructed using "text" as the link text parses as
        belonging to a different site, this method returns True.

        """
        linkfam, linkcode = pywikibot.Link(text, self).parse_site()
        return linkfam != self.family.name or linkcode != self.code

    def redirectRegex(  # noqa: N802
        self,
        pattern: Optional[str] = None
    ) -> Pattern[str]:
        """Return a compiled regular expression matching on redirect pages.

        Group 1 in the regex match object will be the target title.

        """
        if pattern is None:
            pattern = 'REDIRECT'
        # A redirect starts with hash (#), followed by a keyword, then
        # arbitrary stuff, then a wikilink. The wikilink may contain
        # a label, although this is not useful.
        return re.compile(r'\s*#{pattern}\s*:?\s*\[\[(.+?)(?:\|.*?)?\]\]'
                          .format(pattern=pattern), re.IGNORECASE | re.DOTALL)

    def sametitle(self, title1: str, title2: str) -> bool:
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
            return ns, name

        # Replace alias characters like underscores with title
        # delimiters like spaces and multiple combinations of them with
        # only one delimiter
        sep = self.family.title_delimiter_and_aliases[0]
        pattern = re.compile('[{}]+'
                             .format(self.family.title_delimiter_and_aliases))
        title1 = pattern.sub(sep, title1)
        title2 = pattern.sub(sep, title2)
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

    # site-specific formatting preferences

    def category_on_one_line(self):
        # TODO: is this even needed? No family in the framework uses it.
        """Return True if this site wants all category links on one line."""
        return self.code in self.family.category_on_one_line

    def interwiki_putfirst(self):
        """Return list of language codes for ordering of interwiki links."""
        return self.family.interwiki_putfirst.get(self.code, None)

    def getSite(self, code):  # noqa: N802
        """Return Site object for language 'code' in this Family."""
        return pywikibot.Site(code=code, fam=self.family, user=self.user())
