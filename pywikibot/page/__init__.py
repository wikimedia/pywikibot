"""
Objects representing various types of MediaWiki, including Wikibase, pages.

This module also includes objects:

* Property: a type of semantic data.
* Claim: an instance of a semantic assertion.
* Revision: a single change to a wiki page.
* FileInfo: a structure holding imageinfo of latest rev. of FilePage
* Link: an internal or interwiki link in wikitext.

"""
#
# (C) Pywikibot team, 2008-2021
#
# Distributed under the terms of the MIT license.
#
import json as jsonlib
import logging
import os.path
import re
import unicodedata
from collections import Counter, OrderedDict, defaultdict
from contextlib import suppress
from html.entities import name2codepoint
from http import HTTPStatus
from itertools import chain
from typing import Any, Optional, Union
from urllib.parse import quote_from_bytes
from warnings import warn

import pywikibot
from pywikibot import config, i18n, textlib
from pywikibot.backports import Dict, Iterable, List, Tuple
from pywikibot.comms import http
from pywikibot.exceptions import (
    APIError,
    AutoblockUserError,
    EntityTypeUnknownError,
    Error,
    InterwikiRedirectPageError,
    InvalidPageError,
    InvalidTitleError,
    IsNotRedirectPageError,
    IsRedirectPageError,
    NoMoveTargetError,
    NoPageError,
    NotEmailableError,
    NoUsernameError,
    NoWikibaseEntityError,
    OtherPageSaveError,
    PageSaveRelatedError,
    SectionError,
    SiteDefinitionError,
    UnknownExtensionError,
    UserRightsError,
    WikiBaseError,
)
from pywikibot.family import Family
from pywikibot.page._collections import (
    AliasesDict,
    ClaimCollection,
    LanguageDict,
    SiteLinkCollection,
)
from pywikibot.page._decorators import allow_asynchronous
from pywikibot.page._revision import Revision
from pywikibot.site import DataSite, Namespace
from pywikibot.tools import (
    ComparableMixin,
    compute_file_hash,
    deprecate_arg,
    deprecated,
    deprecated_args,
    first_upper,
    is_ip_address,
    issue_deprecation_warning,
    ModuleDeprecationWrapper,
    redirect_func,
    remove_last_args,
)


PROTOCOL_REGEX = r'\Ahttps?://'

__all__ = (
    'BasePage',
    'Page',
    'FilePage',
    'Category',
    'User',
    'WikibasePage',
    'ItemPage',
    'Property',
    'PropertyPage',
    'Claim',
    'Revision',
    'FileInfo',
    'BaseLink',
    'Link',
    'SiteLink',
    'SiteLinkCollection',
    'html2unicode',
    'UnicodeToAsciiHtml',
    'unicode2html',
    'url2unicode',
)

logger = logging.getLogger('pywiki.wiki.page')


# Note: Link objects (defined later on) represent a wiki-page's title, while
# Page objects (defined here) represent the page itself, including its
# contents.

class BasePage(ComparableMixin):

    """
    BasePage: Base object for a MediaWiki page.

    This object only implements internally methods that do not require
    reading from or writing to the wiki. All other methods are delegated
    to the Site object.

    Will be subclassed by Page, WikibasePage, and FlowPage.
    """

    _cache_attrs = (
        '_text', '_pageid', '_catinfo', '_templates', '_protection',
        '_contentmodel', '_langlinks', '_isredir', '_coords',
        '_preloadedtext', '_timestamp', '_applicable_protections',
        '_flowinfo', '_quality', '_pageprops', '_revid', '_quality_text',
        '_pageimage', '_item', '_lintinfo',
    )

    def __init__(self, source, title='', ns=0):
        """
        Instantiate a Page object.

        Three calling formats are supported:

          - If the first argument is a Page, create a copy of that object.
            This can be used to convert an existing Page into a subclass
            object, such as Category or FilePage. (If the title is also
            given as the second argument, creates a copy with that title;
            this is used when pages are moved.)
          - If the first argument is a Site, create a Page on that Site
            using the second argument as the title (may include a section),
            and the third as the namespace number. The namespace number is
            mandatory, even if the title includes the namespace prefix. This
            is the preferred syntax when using an already-normalized title
            obtained from api.php or a database dump. WARNING: may produce
            invalid objects if page title isn't in normal form!
          - If the first argument is a BaseLink, create a Page from that link.
            This is the preferred syntax when using a title scraped from
            wikitext, URLs, or another non-normalized source.

        :param source: the source of the page
        :type source: pywikibot.page.BaseLink (or subclass),
            pywikibot.page.Page (or subclass), or pywikibot.page.Site
        :param title: normalized title of the page; required if source is a
            Site, ignored otherwise
        :type title: str
        :param ns: namespace number; required if source is a Site, ignored
            otherwise
        :type ns: int
        """
        if title is None:
            raise ValueError('Title cannot be None.')

        if isinstance(source, pywikibot.site.BaseSite):
            self._link = Link(title, source=source, default_namespace=ns)
            self._revisions = {}
        elif isinstance(source, Page):
            # copy all of source's attributes to this object
            # without overwriting non-None values
            self.__dict__.update((k, v) for k, v in source.__dict__.items()
                                 if k not in self.__dict__
                                 or self.__dict__[k] is None)
            if title:
                # overwrite title
                self._link = Link(title, source=source.site,
                                  default_namespace=ns)
        elif isinstance(source, BaseLink):
            self._link = source
            self._revisions = {}
        else:
            raise Error(
                "Invalid argument type '{}' in Page initializer: {}"
                .format(type(source), source))

    @property
    def site(self):
        """Return the Site object for the wiki on which this Page resides.

        :rtype: pywikibot.Site
        """
        return self._link.site

    def version(self):
        """
        Return MediaWiki version number of the page site.

        This is needed to use @need_version() decorator for methods of
        Page objects.
        """
        return self.site.version()

    @property
    def image_repository(self):
        """Return the Site object for the image repository."""
        return self.site.image_repository()

    @property
    def data_repository(self):
        """Return the Site object for the data repository."""
        return self.site.data_repository()

    def namespace(self):
        """
        Return the namespace of the page.

        :return: namespace of the page
        :rtype: pywikibot.Namespace
        """
        return self._link.namespace

    @property
    def content_model(self):
        """
        Return the content model for this page.

        If it cannot be reliably determined via the API,
        None is returned.
        """
        if not hasattr(self, '_contentmodel'):
            self.site.loadpageinfo(self)
        return self._contentmodel

    @property
    def depth(self):
        """Return the depth/subpage level of the page."""
        if not hasattr(self, '_depth'):
            # Check if the namespace allows subpages
            if self.namespace().subpages:
                self._depth = self.title().count('/')
            else:
                # Does not allow subpages, which means depth is always 0
                self._depth = 0

        return self._depth

    @property
    def pageid(self) -> int:
        """
        Return pageid of the page.

        :return: pageid or 0 if page does not exist
        """
        if not hasattr(self, '_pageid'):
            self.site.loadpageinfo(self)
        return self._pageid

    @deprecated_args(
        savetitle='as_url', withNamespace='with_ns',
        withSection='with_section', forceInterwiki='force_interwiki',
        asUrl='as_url', asLink='as_link', allowInterwiki='allow_interwiki')
    def title(self, *, underscore=False, with_ns=True,
              with_section=True, as_url=False, as_link=False,
              allow_interwiki=True, force_interwiki=False, textlink=False,
              as_filename=False, insite=None, without_brackets=False) -> str:
        """
        Return the title of this Page, as a string.

        :param underscore: (not used with as_link) if true, replace all ' '
            characters with '_'
        :param with_ns: if false, omit the namespace prefix. If this
            option is false and used together with as_link return a labeled
            link like [[link|label]]
        :param with_section: if false, omit the section
        :param as_url: (not used with as_link) if true, quote title as if in an
            URL
        :param as_link: if true, return the title in the form of a wikilink
        :param allow_interwiki: (only used if as_link is true) if true, format
            the link as an interwiki link if necessary
        :param force_interwiki: (only used if as_link is true) if true, always
            format the link as an interwiki link
        :param textlink: (only used if as_link is true) if true, place a ':'
            before Category: and Image: links
        :param as_filename: (not used with as_link) if true, replace any
            characters that are unsafe in filenames
        :param insite: (only used if as_link is true) a site object where the
            title is to be shown. Default is the current family/lang given by
            -family and -lang or -site option i.e. config.family and
            config.mylang
        :param without_brackets: (cannot be used with as_link) if true, remove
            the last pair of brackets(usually removes disambiguation brackets).
        """
        title = self._link.canonical_title()
        label = self._link.title
        if with_section and self.section():
            section = '#' + self.section()
        else:
            section = ''
        if as_link:
            if insite:
                target_code = insite.code
                target_family = insite.family.name
            else:
                target_code = config.mylang
                target_family = config.family
            if force_interwiki \
               or (allow_interwiki
                   and (self.site.family.name != target_family
                        or self.site.code != target_code)):
                if self.site.family.name not in (
                        target_family, self.site.code):
                    title = '{site.family.name}:{site.code}:{title}'.format(
                        site=self.site, title=title)
                else:
                    # use this form for sites like commons, where the
                    # code is the same as the family name
                    title = '{}:{}'.format(self.site.code, title)
            elif textlink and (self.is_filepage() or self.is_categorypage()):
                title = ':{}'.format(title)
            elif self.namespace() == 0 and not section:
                with_ns = True
            if with_ns:
                return '[[{}{}]]'.format(title, section)
            return '[[{}{}|{}]]'.format(title, section, label)
        if not with_ns and self.namespace() != 0:
            title = label + section
        else:
            title += section
        if without_brackets:
            brackets_re = r'\s+\([^()]+?\)$'
            title = re.sub(brackets_re, '', title)
        if underscore or as_url:
            title = title.replace(' ', '_')
        if as_url:
            encoded_title = title.encode(self.site.encoding())
            title = quote_from_bytes(encoded_title, safe='')
        if as_filename:
            # Replace characters that are not possible in file names on some
            # systems, but still are valid in MediaWiki titles:
            # Unix: /
            # MediaWiki: /:\
            # Windows: /:\"?*
            # Spaces are possible on most systems, but are bad for URLs.
            for forbidden in ':*?/\\" ':
                title = title.replace(forbidden, '_')
        return title

    @remove_last_args(('decode', 'underscore'))
    def section(self) -> Optional[str]:
        """
        Return the name of the section this Page refers to.

        The section is the part of the title following a '#' character, if
        any. If no section is present, return None.
        """
        try:
            section = self._link.section
        except AttributeError:
            section = None
        return section

    def __str__(self) -> str:
        """Return a string representation."""
        return self.title(as_link=True, force_interwiki=True)

    def __repr__(self) -> str:
        """Return a more complete string representation."""
        return '{}({!r})'.format(self.__class__.__name__, self.title())

    def _cmpkey(self):
        """
        Key for comparison of Page objects.

        Page objects are "equal" if and only if they are on the same site
        and have the same normalized title, including section if any.

        Page objects are sortable by site, namespace then title.
        """
        return (self.site, self.namespace(), self.title())

    def __hash__(self):
        """
        A stable identifier to be used as a key in hash-tables.

        This relies on the fact that the string
        representation of an instance cannot change after the construction.
        """
        return hash(self._cmpkey())

    def full_url(self):
        """Return the full URL."""
        return self.site.base_url(self.site.article_path
                                  + self.title(as_url=True))

    def autoFormat(self):
        """
        Return :py:obj:`date.getAutoFormat` dictName and value, if any.

        Value can be a year, date, etc., and dictName is 'YearBC',
        'Year_December', or another dictionary name. Please note that two
        entries may have exactly the same autoFormat, but be in two
        different namespaces, as some sites have categories with the
        same names. Regular titles return (None, None).
        """
        if not hasattr(self, '_autoFormat'):
            from pywikibot import date
            self._autoFormat = date.getAutoFormat(
                self.site.lang,
                self.title(with_ns=False)
            )
        return self._autoFormat

    def isAutoTitle(self):
        """Return True if title of this Page is in the autoFormat dict."""
        return self.autoFormat()[0] is not None

    @remove_last_args(['sysop'])
    def get(self, force: bool = False, get_redirect: bool = False) -> str:
        """Return the wiki-text of the page.

        This will retrieve the page from the server if it has not been
        retrieved yet, or if force is True. This can raise the following
        exceptions that should be caught by the calling code:

        :exception pywikibot.exceptions.NoPageError: The page does not exist
        :exception pywikibot.exceptions.IsRedirectPageError: The page is a
            redirect. The argument of the exception is the title of the page
            it redirects to.
        :exception pywikibot.exceptions.SectionError: The section does not
            exist on a page with a # link

        :param force:           reload all page attributes, including errors.
        :param get_redirect:    return the redirect text, do not follow the
                                redirect, do not raise an exception.
        """
        if force:
            del self.latest_revision_id
            if hasattr(self, '_bot_may_edit'):
                del self._bot_may_edit
        try:
            self._getInternals()
        except IsRedirectPageError:
            if not get_redirect:
                raise

        return self.latest_revision.text

    def _latest_cached_revision(self):
        """Get the latest revision if cached and has text, otherwise None."""
        if (hasattr(self, '_revid') and self._revid in self._revisions
                and self._revisions[self._revid].text is not None):
            return self._revisions[self._revid]
        return None

    def _getInternals(self):
        """
        Helper function for get().

        Stores latest revision in self if it doesn't contain it, doesn't think.
        * Raises exceptions from previous runs.
        * Stores new exceptions in _getexception and raises them.
        """
        # Raise exceptions from previous runs
        if hasattr(self, '_getexception'):
            raise self._getexception

        # If not already stored, fetch revision
        if self._latest_cached_revision() is None:
            try:
                self.site.loadrevisions(self, content=True)
            except (NoPageError, SectionError) as e:
                self._getexception = e
                raise

        # self._isredir is set by loadrevisions
        if self._isredir:
            self._getexception = IsRedirectPageError(self)
            raise self._getexception

    @remove_last_args(['sysop'])
    def getOldVersion(self, oldid,
                      force: bool = False, get_redirect: bool = False) -> str:
        """
        Return text of an old revision of this page; same options as get().

        :param oldid: The revid of the revision desired.
        """
        if force or oldid not in self._revisions \
                or self._revisions[oldid].text is None:
            self.site.loadrevisions(self,
                                    content=True,
                                    revids=oldid)
        # TODO: what about redirects, errors?
        return self._revisions[oldid].text

    def permalink(self, oldid=None, percent_encoded: bool = True,
                  with_protocol: bool = False) -> str:
        """Return the permalink URL of an old revision of this page.

        :param oldid: The revid of the revision desired.
        :param percent_encoded: if false, the link will be provided
            without title uncoded.
        :param with_protocol: if true, http or https prefixes will be
            included before the double slash.
        """
        if percent_encoded:
            title = self.title(as_url=True)
        else:
            title = self.title(as_url=False).replace(' ', '_')
        return '{}//{}{}/index.php?title={}&oldid={}'.format(
            self.site.protocol() + ':' if with_protocol else '',
            self.site.hostname(),
            self.site.scriptpath(),
            title,
            oldid if oldid is not None else self.latest_revision_id)

    @property
    def latest_revision_id(self):
        """Return the current revision id for this page."""
        if not hasattr(self, '_revid'):
            self.revisions()
        return self._revid

    @latest_revision_id.deleter
    def latest_revision_id(self):
        """
        Remove the latest revision id set for this Page.

        All internal cached values specifically for the latest revision
        of this page are cleared.

        The following cached values are not cleared:
        - text property
        - page properties, and page coordinates
        - lastNonBotUser
        - isDisambig and isCategoryRedirect status
        - langlinks, templates and deleted revisions
        """
        # When forcing, we retry the page no matter what:
        # * Old exceptions do not apply any more
        # * Deleting _revid to force reload
        # * Deleting _redirtarget, that info is now obsolete.
        for attr in ['_redirtarget', '_getexception', '_revid']:
            if hasattr(self, attr):
                delattr(self, attr)

    @latest_revision_id.setter
    def latest_revision_id(self, value):
        """Set the latest revision for this Page."""
        del self.latest_revision_id
        self._revid = value

    @property
    def latest_revision(self):
        """Return the current revision for this page."""
        rev = self._latest_cached_revision()
        if rev is not None:
            return rev

        with suppress(StopIteration):
            return next(self.revisions(content=True, total=1))
        raise InvalidPageError(self)

    @property
    def text(self) -> str:
        """
        Return the current (edited) wikitext, loading it if necessary.

        :return: text of the page
        """
        if getattr(self, '_text', None) is not None:
            return self._text

        try:
            return self.get(get_redirect=True)
        except NoPageError:
            # TODO: what other exceptions might be returned?
            return ''

    @text.setter
    def text(self, value: Optional[str]):
        """Update the current (edited) wikitext.

        :param value: New value or None
        """
        try:
            self.botMayEdit()  # T262136, T267770
        except Exception as e:
            # dry tests aren't able to make an API call
            # but are rejected by an Exception; ignore it then.
            if not str(e).startswith('DryRequest rejecting request:'):
                raise

        del self.text
        self._text = None if value is None else str(value)

    @text.deleter
    def text(self):
        """Delete the current (edited) wikitext."""
        if hasattr(self, '_text'):
            del self._text
        if hasattr(self, '_expanded_text'):
            del self._expanded_text
        if hasattr(self, '_raw_extracted_templates'):
            del self._raw_extracted_templates

    def preloadText(self) -> str:
        """
        The text returned by EditFormPreloadText.

        See API module "info".

        Application: on Wikisource wikis, text can be preloaded even if
        a page does not exist, if an Index page is present.
        """
        self.site.loadpageinfo(self, preload=True)
        return self._preloadedtext

    def _get_parsed_page(self):
        """Retrieve parsed text (via action=parse) and cache it."""
        # Get (cached) parsed text.
        if not hasattr(self, '_parsed_text'):
            self._parsed_text = self.site.get_parsed_page(self)
        return self._parsed_text

    def properties(self, force=False) -> dict:
        """
        Return the properties of the page.

        :param force: force updating from the live site
        """
        if not hasattr(self, '_pageprops') or force:
            self._pageprops = {}  # page may not have pageprops (see T56868)
            self.site.loadpageprops(self)
        return self._pageprops

    def defaultsort(self, force=False) -> Optional[str]:
        """
        Extract value of the {{DEFAULTSORT:}} magic word from the page.

        :param force: force updating from the live site
        """
        return self.properties(force=force).get('defaultsort')

    @deprecate_arg('refresh', 'force')
    def expand_text(self, force=False, includecomments=False) -> str:
        """Return the page text with all templates and parser words expanded.

        :param force: force updating from the live site
        :param includecomments: Also strip comments if includecomments
            parameter is not True.
        """
        if not hasattr(self, '_expanded_text') or (
                self._expanded_text is None) or force:
            if not self.text:
                self._expanded_text = ''
                return ''

            self._expanded_text = self.site.expand_text(
                self.text,
                title=self.title(with_section=False),
                includecomments=includecomments)
        return self._expanded_text

    def userName(self) -> str:
        """Return name or IP address of last user to edit page."""
        return self.latest_revision.user

    def isIpEdit(self) -> bool:
        """Return True if last editor was unregistered."""
        return self.latest_revision.anon

    def lastNonBotUser(self) -> str:
        """
        Return name or IP address of last human/non-bot user to edit page.

        Determine the most recent human editor out of the last revisions.
        If it was not able to retrieve a human user, returns None.

        If the edit was done by a bot which is no longer flagged as 'bot',
        i.e. which is not returned by Site.botusers(), it will be returned
        as a non-bot edit.
        """
        if hasattr(self, '_lastNonBotUser'):
            return self._lastNonBotUser

        self._lastNonBotUser = None
        for entry in self.revisions():
            if entry.user and (not self.site.isBot(entry.user)):
                self._lastNonBotUser = entry.user
                break

        return self._lastNonBotUser

    @remove_last_args(('datetime', ))
    def editTime(self):
        """Return timestamp of last revision to page.

        :rtype: pywikibot.Timestamp
        """
        return self.latest_revision.timestamp

    def exists(self) -> bool:
        """Return True if page exists on the wiki, even if it's a redirect.

        If the title includes a section, return False if this section isn't
        found.
        """
        with suppress(AttributeError):
            return self.pageid > 0
        raise InvalidPageError(self)

    @property
    def oldest_revision(self):
        """
        Return the first revision of this page.

        :rtype: :py:obj:`Revision`
        """
        return next(self.revisions(reverse=True, total=1))

    def isRedirectPage(self):
        """Return True if this is a redirect, False if not or not existing."""
        return self.site.page_isredirect(self)

    def isStaticRedirect(self, force: bool = False) -> bool:
        """
        Determine whether the page is a static redirect.

        A static redirect must be a valid redirect, and contain the magic
        word __STATICREDIRECT__.

        :param force: Bypass local caching
        """
        if self.isRedirectPage():
            static_keys = self.site.getmagicwords('staticredirect')
            text = self.get(get_redirect=True, force=force)
            if static_keys:
                for key in static_keys:
                    if key in text:
                        return True
        return False

    def isCategoryRedirect(self) -> bool:
        """Return True if this is a category redirect page, False otherwise."""
        if not self.is_categorypage():
            return False
        if not hasattr(self, '_catredirect'):
            self._catredirect = False
            catredirs = self.site.category_redirects()
            for template, args in self.templatesWithParams():
                if template.title(with_ns=False) in catredirs:
                    if args:
                        # Get target (first template argument)
                        target_title = args[0].strip()
                        p = pywikibot.Page(
                            self.site, target_title, Namespace.CATEGORY)
                        try:
                            p.title()
                        except pywikibot.exceptions.InvalidTitleError:
                            target_title = self.site.expand_text(
                                text=target_title,
                                title=self.title(),
                            )
                            p = pywikibot.Page(self.site, target_title,
                                               Namespace.CATEGORY)
                        if p.namespace() == Namespace.CATEGORY:
                            self._catredirect = p.title()
                        else:
                            pywikibot.warning(
                                'Category redirect target {} on {} is not a '
                                'category'.format(p.title(as_link=True),
                                                  self.title(as_link=True)))
                    else:
                        pywikibot.warning(
                            'No target found for category redirect on '
                            + self.title(as_link=True))
                    break
        return bool(self._catredirect)

    def getCategoryRedirectTarget(self):
        """
        If this is a category redirect, return the target category title.

        :rtype: pywikibot.page.Category
        """
        if self.isCategoryRedirect():
            return Category(Link(self._catredirect, self.site))
        raise IsNotRedirectPageError(self)

    def isTalkPage(self):
        """Return True if this page is in any talk namespace."""
        ns = self.namespace()
        return ns >= 0 and ns % 2 == 1

    def toggleTalkPage(self):
        """
        Return other member of the article-talk page pair for this Page.

        If self is a talk page, returns the associated content page;
        otherwise, returns the associated talk page. The returned page need
        not actually exist on the wiki.

        :return: Page or None if self is a special page.
        :rtype: typing.Optional[pywikibot.Page]
        """
        ns = self.namespace()
        if ns < 0:  # Special page
            return None

        title = self.title(with_ns=False)
        new_ns = ns + (1, -1)[self.isTalkPage()]
        return Page(self.site,
                    '{}:{}'.format(self.site.namespace(new_ns), title))

    def is_categorypage(self):
        """Return True if the page is a Category, False otherwise."""
        return self.namespace() == 14

    def is_filepage(self):
        """Return True if this is a file description page, False otherwise."""
        return self.namespace() == 6

    @remove_last_args(['get_Index'])
    def isDisambig(self) -> bool:
        """
        Return True if this is a disambiguation page, False otherwise.

        By default, it uses the Disambiguator extension's result. The
        identification relies on the presence of the __DISAMBIG__ magic word
        which may also be transcluded.

        If the Disambiguator extension isn't activated for the given site,
        the identification relies on the presence of specific templates.
        First load a list of template names from the Family file;
        if the value in the Family file is None or no entry was made, look for
        the list on [[MediaWiki:Disambiguationspage]]. If this page does not
        exist, take the MediaWiki message. 'Template:Disambig' is always
        assumed to be default, and will be appended regardless of its
        existence.
        """
        if self.site.has_extension('Disambiguator'):
            # If the Disambiguator extension is loaded, use it
            return 'disambiguation' in self.properties()

        if not hasattr(self.site, '_disambigtemplates'):
            try:
                default = set(self.site.family.disambig('_default'))
            except KeyError:
                default = {'Disambig'}
            try:
                distl = self.site.family.disambig(self.site.code,
                                                  fallback=False)
            except KeyError:
                distl = None
            if distl is None:
                disambigpages = Page(self.site,
                                     'MediaWiki:Disambiguationspage')
                if disambigpages.exists():
                    disambigs = {link.title(with_ns=False)
                                 for link in disambigpages.linkedPages()
                                 if link.namespace() == 10}
                elif self.site.has_mediawiki_message('disambiguationspage'):
                    message = self.site.mediawiki_message(
                        'disambiguationspage').split(':', 1)[1]
                    # add the default template(s) for default mw message
                    # only
                    disambigs = {first_upper(message)} | default
                else:
                    disambigs = default
                self.site._disambigtemplates = disambigs
            else:
                # Normalize template capitalization
                self.site._disambigtemplates = {first_upper(t) for t in distl}
        templates = {tl.title(with_ns=False) for tl in self.templates()}
        disambigs = set()
        # always use cached disambig templates
        disambigs.update(self.site._disambigtemplates)
        # see if any template on this page is in the set of disambigs
        disambig_in_page = disambigs.intersection(templates)
        return self.namespace() != 10 and bool(disambig_in_page)

    @deprecated_args(withTemplateInclusion='with_template_inclusion',
                     onlyTemplateInclusion='only_template_inclusion',
                     redirectsOnly='filter_redirects')
    def getReferences(self,
                      follow_redirects: bool = True,
                      with_template_inclusion: bool = True,
                      only_template_inclusion: bool = False,
                      filter_redirects: bool = False,
                      namespaces=None,
                      total: Optional[int] = None,
                      content: bool = False):
        """
        Return an iterator all pages that refer to or embed the page.

        If you need a full list of referring pages, use
        ``pages = list(s.getReferences())``

        :param follow_redirects: if True, also iterate pages that link to a
            redirect pointing to the page.
        :param with_template_inclusion: if True, also iterate pages where self
            is used as a template.
        :param only_template_inclusion: if True, only iterate pages where self
            is used as a template.
        :param filter_redirects: if True, only iterate redirects to self.
        :param namespaces: only iterate pages in these namespaces
        :param total: iterate no more than this number of pages in total
        :param content: if True, retrieve the content of the current version
            of each referring page (default False)
        :rtype: typing.Iterable[pywikibot.Page]
        """
        # N.B.: this method intentionally overlaps with backlinks() and
        # embeddedin(). Depending on the interface, it may be more efficient
        # to implement those methods in the site interface and then combine
        # the results for this method, or to implement this method and then
        # split up the results for the others.
        return self.site.pagereferences(
            self,
            follow_redirects=follow_redirects,
            filter_redirects=filter_redirects,
            with_template_inclusion=with_template_inclusion,
            only_template_inclusion=only_template_inclusion,
            namespaces=namespaces,
            total=total,
            content=content
        )

    @deprecated_args(followRedirects='follow_redirects',
                     filterRedirects='filter_redirects')
    def backlinks(self,
                  follow_redirects: bool = True,
                  filter_redirects: Optional[bool] = None,
                  namespaces=None,
                  total: Optional[int] = None,
                  content: bool = False):
        """
        Return an iterator for pages that link to this page.

        :param follow_redirects: if True, also iterate pages that link to a
            redirect pointing to the page.
        :param filter_redirects: if True, only iterate redirects; if False,
            omit redirects; if None, do not filter
        :param namespaces: only iterate pages in these namespaces
        :param total: iterate no more than this number of pages in total
        :param content: if True, retrieve the content of the current version
            of each referring page (default False)
        """
        return self.site.pagebacklinks(
            self,
            follow_redirects=follow_redirects,
            filter_redirects=filter_redirects,
            namespaces=namespaces,
            total=total,
            content=content
        )

    def embeddedin(self,
                   filter_redirects: Optional[bool] = None,
                   namespaces=None,
                   total: Optional[int] = None,
                   content: bool = False):
        """
        Return an iterator for pages that embed this page as a template.

        :param filter_redirects: if True, only iterate redirects; if False,
            omit redirects; if None, do not filter
        :param namespaces: only iterate pages in these namespaces
        :param total: iterate no more than this number of pages in total
        :param content: if True, retrieve the content of the current version
            of each embedding page (default False)
        """
        return self.site.page_embeddedin(
            self,
            filter_redirects=filter_redirects,
            namespaces=namespaces,
            total=total,
            content=content
        )

    def protection(self) -> dict:
        """Return a dictionary reflecting page protections."""
        return self.site.page_restrictions(self)

    def applicable_protections(self) -> set:
        """
        Return the protection types allowed for that page.

        If the page doesn't exist it only returns "create". Otherwise it
        returns all protection types provided by the site, except "create".
        It also removes "upload" if that page is not in the File namespace.

        It is possible, that it returns an empty set, but only if original
        protection types were removed.

        :return: set of str
        """
        # New API since commit 32083235eb332c419df2063cf966b3400be7ee8a
        if self.site.mw_version >= '1.25wmf14':
            self.site.loadpageinfo(self)
            return self._applicable_protections

        p_types = set(self.site.protection_types())
        if not self.exists():
            return {'create'} if 'create' in p_types else set()
        p_types.remove('create')  # no existing page allows that
        if not self.is_filepage():  # only file pages allow upload
            p_types.remove('upload')
        return p_types

    def has_permission(self, action: str = 'edit') -> bool:
        """Determine whether the page can be modified.

        Return True if the bot has the permission of needed restriction level
        for the given action type.

        :param action: a valid restriction type like 'edit', 'move'
        :raises ValueError: invalid action parameter
        """
        return self.site.page_can_be_edited(self, action)

    @deprecated("Page.has_permission('edit')", since='20200208')
    def canBeEdited(self):  # pragma: no cover
        """DEPRECATED. Determine whether the page may be edited."""
        return self.has_permission()

    def botMayEdit(self) -> bool:
        """
        Determine whether the active bot is allowed to edit the page.

        This will be True if the page doesn't contain {{bots}} or {{nobots}}
        or any other template from edit_restricted_templates list
        in x_family.py file, or it contains them and the active bot is allowed
        to edit this page. (This method is only useful on those sites that
        recognize the bot-exclusion protocol; on other sites, it will always
        return True.)

        The framework enforces this restriction by default. It is possible
        to override this by setting ignore_bot_templates=True in
        user-config.py, or using page.put(force=True).
        """
        if not hasattr(self, '_bot_may_edit'):
            self._bot_may_edit = self._check_bot_may_edit()
        return self._bot_may_edit

    def _check_bot_may_edit(self, module: Optional[str] = None) -> bool:
        """A botMayEdit helper method.

        @param module: The module name to be restricted. Defaults to
            pywikibot.calledModuleName().
        """
        if not hasattr(self, 'templatesWithParams'):
            return True

        if config.ignore_bot_templates:  # Check the "master ignore switch"
            return True

        username = self.site.username()
        try:
            templates = self.templatesWithParams()
        except (NoPageError, IsRedirectPageError, SectionError):
            return True

        # go through all templates and look for any restriction
        restrictions = set(self.site.get_edit_restricted_templates())

        if module is None:
            module = pywikibot.calledModuleName()

        # also add archive templates for non-archive bots
        if module != 'archivebot':
            restrictions.update(self.site.get_archived_page_templates())

        # multiple bots/nobots templates are allowed
        for template, params in templates:
            title = template.title(with_ns=False)

            if title in restrictions:
                return False

            if title not in ('Bots', 'Nobots'):
                continue

            try:
                key, sep, value = params[0].partition('=')
            except IndexError:
                key, sep, value = '', '', ''
                names = set()
            else:
                if not sep:
                    key, value = value, key
                key = key.strip()
                names = {name.strip() for name in value.split(',')}

            if len(params) > 1:
                pywikibot.warning(
                    '{{%s|%s}} has more than 1 parameter; taking the first.'
                    % (title.lower(), '|'.join(params)))

            if title == 'Nobots':
                if not params:
                    return False

                if key:
                    pywikibot.error(
                        '%s parameter for {{nobots}} is not allowed. '
                        'Edit declined' % key)
                    return False

                if 'all' in names or module in names or username in names:
                    return False

            if title == 'Bots':
                if value and not key:
                    pywikibot.warning(
                        '{{bots|%s}} is not valid. Ignoring.' % value)
                    continue

                if key and not value:
                    pywikibot.warning(
                        '{{bots|%s=}} is not valid. Ignoring.' % key)
                    continue

                if key == 'allow':
                    if not ('all' in names or username in names):
                        return False

                elif key == 'deny':
                    if 'all' in names or username in names:
                        return False

                elif key == 'allowscript':
                    if not ('all' in names or module in names):
                        return False

                elif key == 'denyscript':
                    if 'all' in names or module in names:
                        return False

                elif key:  # ignore unrecognized keys with a warning
                    pywikibot.warning(
                        '{{bots|%s}} is not valid. Ignoring.' % params[0])

        # no restricting template found
        return True

    @deprecate_arg('async', 'asynchronous')  # T106230
    @deprecated_args(comment='summary')
    def save(self,
             summary: Optional[str] = None,
             watch: Union[str, bool, None] = None,
             minor: bool = True,
             botflag: Optional[bool] = None,
             force: bool = False,
             asynchronous: bool = False,
             callback=None, apply_cosmetic_changes=None,
             quiet: bool = False, **kwargs):
        """
        Save the current contents of page's text to the wiki.

        :param summary: The edit summary for the modification (optional, but
            most wikis strongly encourage its use)
        :param watch: Specify how the watchlist is affected by this edit, set
            to one of "watch", "unwatch", "preferences", "nochange":
            * watch: add the page to the watchlist
            * unwatch: remove the page from the watchlist
            * preferences: use the preference settings (Default)
            * nochange: don't change the watchlist
            If None (default), follow bot account's default settings

            For backward compatibility watch parameter may also be boolean:
            if True, add or if False, remove this Page to/from bot
            user's watchlist.
        :type watch: str, bool (deprecated) or None
        :param minor: if True, mark this edit as minor
        :param botflag: if True, mark this edit as made by a bot (default:
            True if user has bot status, False if not)
        :param force: if True, ignore botMayEdit() setting
        :param asynchronous: if True, launch a separate thread to save
            asynchronously
        :param callback: a callable object that will be called after the
            page put operation. This object must take two arguments: (1) a
            Page object, and (2) an exception instance, which will be None
            if the page was saved successfully. The callback is intended for
            use by bots that need to keep track of which saves were
            successful.
        :param apply_cosmetic_changes: Overwrites the cosmetic_changes
            configuration value to this value unless it's None.
        :type apply_cosmetic_changes: bool or None
        :param quiet: enable/disable successful save operation message;
            defaults to False.
            In asynchronous mode, if True, it is up to the calling bot to
            manage the output e.g. via callback.
        """
        if not summary:
            summary = config.default_edit_summary
        if watch is True:
            watch = 'watch'
        elif watch is False:
            watch = 'unwatch'
        if not force and not self.botMayEdit():
            raise OtherPageSaveError(
                self, 'Editing restricted by {{bots}}, {{nobots}} '
                "or site's equivalent of {{in use}} template")
        self._save(summary=summary, watch=watch, minor=minor, botflag=botflag,
                   asynchronous=asynchronous, callback=callback,
                   cc=apply_cosmetic_changes, quiet=quiet, **kwargs)

    @allow_asynchronous
    def _save(self, summary=None, watch=None, minor=True, botflag=None,
              cc=None, quiet=False, **kwargs):
        """Helper function for save()."""
        link = self.title(as_link=True)
        if cc or (cc is None and config.cosmetic_changes):
            summary = self._cosmetic_changes_hook(summary)

        done = self.site.editpage(self, summary=summary, minor=minor,
                                  watch=watch, bot=botflag, **kwargs)
        if not done:
            if not quiet:
                pywikibot.warning('Page {} not saved'.format(link))
            raise PageSaveRelatedError(self)
        if not quiet:
            pywikibot.output('Page {} saved'.format(link))

    def _cosmetic_changes_hook(self, summary: str) -> str:
        """The cosmetic changes hook.

        :param summary: The current edit summary.
        :return: Modified edit summary if cosmetic changes has been done,
            else the old edit summary.
        """
        if self.isTalkPage() or self.content_model != 'wikitext' or \
           pywikibot.calledModuleName() in config.cosmetic_changes_deny_script:
            return summary

        # check if cosmetic_changes is enabled for this page
        family = self.site.family.name
        if config.cosmetic_changes_mylang_only:
            cc = ((family == config.family and self.site.lang == config.mylang)
                  or self.site.lang in config.cosmetic_changes_enable.get(
                      family, []))
        else:
            cc = True
        cc = cc and self.site.lang not in config.cosmetic_changes_disable.get(
            family, [])
        cc = cc and self._check_bot_may_edit('cosmetic_changes')
        if not cc:
            return summary

        old = self.text
        pywikibot.log('Cosmetic changes for {}-{} enabled.'
                      .format(family, self.site.lang))
        # cc depends on page directly and via several other imports
        from pywikibot.cosmetic_changes import (
            CANCEL,
            CosmeticChangesToolkit,
        )
        cc_toolkit = CosmeticChangesToolkit(self, ignore=CANCEL.MATCH)
        self.text = cc_toolkit.change(old)

        if summary and old.strip().replace(
                '\r\n', '\n') != self.text.strip().replace('\r\n', '\n'):
            summary += i18n.twtranslate(self.site, 'cosmetic_changes-append',
                                        fallback_prompt='; cosmetic changes')
        return summary

    @deprecate_arg('async', 'asynchronous')  # T106230
    @deprecated_args(comment='summary', watchArticle='watch',
                     minorEdit='minor')
    def put(self, newtext, summary=None, watch=None, minor=True, botflag=None,
            force=False, asynchronous=False, callback=None, **kwargs):
        """
        Save the page with the contents of the first argument as the text.

        This method is maintained primarily for backwards-compatibility.
        For new code, using Page.save() is preferred. See save() method
        docs for all parameters not listed here.

        :param newtext: The complete text of the revised page.
        :type newtext: str
        """
        self.text = newtext
        self.save(summary=summary, watch=watch, minor=minor, botflag=botflag,
                  force=force, asynchronous=asynchronous, callback=callback,
                  **kwargs)

    @deprecated('put(asynchronous=True) or save(asynchronous=True)',
                since='20180501')
    @deprecated_args(comment='summary', watchArticle='watch',
                     minorEdit='minor')
    def put_async(self, newtext, summary=None, watch=None, minor=True,
                  botflag=None, force=False, callback=None,
                  **kwargs):  # pragma: no cover
        """
        Put page on queue to be saved to wiki asynchronously.

        Asynchronous version of put (takes the same arguments), which places
        pages on a queue to be saved by a daemon thread. All arguments are
        the same as for .put(). This version is maintained solely for
        backwards-compatibility.
        """
        self.put(newtext, summary=summary, watch=watch,
                 minor=minor, botflag=botflag, force=force,
                 asynchronous=True, callback=callback, **kwargs)

    def watch(self, unwatch: bool = False) -> bool:
        """
        Add or remove this page to/from bot account's watchlist.

        :param unwatch: True to unwatch, False (default) to watch.
        :return: True if successful, False otherwise.
        """
        return self.site.watch(self, unwatch)

    def clear_cache(self):
        """Clear the cached attributes of the page."""
        self._revisions = {}
        for attr in self._cache_attrs:
            with suppress(AttributeError):
                delattr(self, attr)

    def purge(self, **kwargs) -> bool:
        """
        Purge the server's cache for this page.

        :keyword redirects: Automatically resolve redirects.
        :type redirects: bool
        :keyword converttitles: Convert titles to other variants if necessary.
            Only works if the wiki's content language supports variant
            conversion.
        :type converttitles: bool
        :keyword forcelinkupdate: Update the links tables.
        :type forcelinkupdate: bool
        :keyword forcerecursivelinkupdate: Update the links table, and update
            the links tables for any page that uses this page as a template.
        :type forcerecursivelinkupdate: bool
        """
        self.clear_cache()
        return self.site.purgepages([self], **kwargs)

    def touch(self, callback=None, botflag=False, **kwargs):
        """
        Make a touch edit for this page.

        See save() method docs for all parameters.
        The following parameters will be overridden by this method:
        - summary, watch, minor, force, asynchronous

        Parameter botflag is False by default.

        minor and botflag parameters are set to False which prevents hiding
        the edit when it becomes a real edit due to a bug.

        :note: This discards content saved to self.text.
        """
        if self.exists():
            # ensure always get the page text and not to change it.
            del self.text
            summary = i18n.twtranslate(self.site, 'pywikibot-touch',
                                       fallback_prompt='Pywikibot touch edit')
            self.save(summary=summary, watch='nochange',
                      minor=False, botflag=botflag, force=True,
                      asynchronous=False, callback=callback,
                      apply_cosmetic_changes=False, nocreate=True, **kwargs)
        else:
            raise NoPageError(self)

    def linkedPages(self, namespaces=None,
                    total: Optional[int] = None,
                    content: bool = False):
        """
        Iterate Pages that this Page links to.

        Only returns pages from "normal" internal links. Image and category
        links are omitted unless prefixed with ":". Embedded templates are
        omitted (but links within them are returned). All interwiki and
        external links are omitted.

        :param namespaces: only iterate links in these namespaces
        :param namespaces: int, or list of ints
        :param total: iterate no more than this number of pages in total
        :param content: if True, retrieve the content of the current version
            of each linked page (default False)
        :return: a generator that yields Page objects.
        :rtype: generator
        """
        return self.site.pagelinks(self, namespaces=namespaces,
                                   total=total, content=content)

    def interwiki(self, expand=True):
        """
        Iterate interwiki links in the page text, excluding language links.

        :param expand: if True (default), include interwiki links found in
            templates transcluded onto this page; if False, only iterate
            interwiki links found in this page's own wikitext
        :type expand: bool

        :return: a generator that yields Link objects
        :rtype: generator
        """
        # This function does not exist in the API, so it has to be
        # implemented by screen-scraping
        if expand:
            text = self.expand_text()
        else:
            text = self.text
        for linkmatch in pywikibot.link_regex.finditer(
                textlib.removeDisabledParts(text)):
            linktitle = linkmatch.group('title')
            link = Link(linktitle, self.site)
            # only yield links that are to a different site and that
            # are not language links
            try:
                if link.site != self.site:
                    if linktitle.lstrip().startswith(':'):
                        # initial ":" indicates not a language link
                        yield link
                    elif link.site.family != self.site.family:
                        # link to a different family is not a language link
                        yield link
            except Error:
                # ignore any links with invalid contents
                continue

    def langlinks(self, include_obsolete=False) -> list:
        """
        Return a list of all inter-language Links on this page.

        :param include_obsolete: if true, return even Link objects whose site
                                 is obsolete
        :type include_obsolete: bool

        :return: list of Link objects.
        """
        # Note: We preload a list of *all* langlinks, including links to
        # obsolete sites, and store that in self._langlinks. We then filter
        # this list if the method was called with include_obsolete=False
        # (which is the default)
        if not hasattr(self, '_langlinks'):
            self._langlinks = list(self.iterlanglinks(include_obsolete=True))

        if include_obsolete:
            return self._langlinks
        return [i for i in self._langlinks if not i.site.obsolete]

    def iterlanglinks(self,
                      total: Optional[int] = None,
                      include_obsolete: bool = False):
        """Iterate all inter-language links on this page.

        :param total: iterate no more than this number of pages in total
        :param include_obsolete: if true, yield even Link object whose site
                                 is obsolete
        :return: a generator that yields Link objects.
        :rtype: generator
        """
        if hasattr(self, '_langlinks'):
            return iter(self.langlinks(include_obsolete=include_obsolete))
        # XXX We might want to fill _langlinks when the Site
        # method is called. If we do this, we'll have to think
        # about what will happen if the generator is not completely
        # iterated upon.
        return self.site.pagelanglinks(self, total=total,
                                       include_obsolete=include_obsolete)

    def data_item(self):
        """
        Convenience function to get the Wikibase item of a page.

        :rtype: pywikibot.page.ItemPage
        """
        return ItemPage.fromPage(self)

    def templates(self, content: bool = False):
        """
        Return a list of Page objects for templates used on this Page.

        Template parameters are ignored. This method only returns embedded
        templates, not template pages that happen to be referenced through
        a normal link.

        :param content: if True, retrieve the content of the current version
            of each template (default False)
        :param content: bool
        """
        # Data might have been preloaded
        if not hasattr(self, '_templates'):
            self._templates = list(self.itertemplates(content=content))

        return self._templates

    def itertemplates(self,
                      total: Optional[int] = None,
                      content: bool = False):
        """
        Iterate Page objects for templates used on this Page.

        Template parameters are ignored. This method only returns embedded
        templates, not template pages that happen to be referenced through
        a normal link.

        :param total: iterate no more than this number of pages in total
        :param content: if True, retrieve the content of the current version
            of each template (default False)
        :param content: bool
        """
        if hasattr(self, '_templates'):
            return iter(self._templates)
        return self.site.pagetemplates(self, total=total, content=content)

    def imagelinks(self, total: Optional[int] = None, content: bool = False):
        """
        Iterate FilePage objects for images displayed on this Page.

        :param total: iterate no more than this number of pages in total
        :param content: if True, retrieve the content of the current version
            of each image description page (default False)
        :return: a generator that yields FilePage objects.
        """
        return self.site.pageimages(self, total=total, content=content)

    @deprecated_args(withSortKey='with_sort_key')
    def categories(self,
                   with_sort_key: bool = False,
                   total: Optional[int] = None,
                   content: bool = False):
        """
        Iterate categories that the article is in.

        :param with_sort_key: if True, include the sort key in each Category.
        :param total: iterate no more than this number of pages in total
        :param content: if True, retrieve the content of the current version
            of each category description page (default False)
        :return: a generator that yields Category objects.
        :rtype: generator
        """
        # FIXME: bug T75561: with_sort_key is ignored by Site.pagecategories
        if with_sort_key:
            raise NotImplementedError('with_sort_key is not implemented')

        return self.site.pagecategories(self, total=total, content=content)

    def extlinks(self, total: Optional[int] = None):
        """
        Iterate all external URLs (not interwiki links) from this page.

        :param total: iterate no more than this number of pages in total
        :return: a generator that yields str objects containing URLs.
        :rtype: generator
        """
        return self.site.page_extlinks(self, total=total)

    def coordinates(self, primary_only=False):
        """
        Return a list of Coordinate objects for points on the page.

        Uses the MediaWiki extension GeoData.

        :param primary_only: Only return the coordinate indicated to be primary
        :return: A list of Coordinate objects or a single Coordinate if
            primary_only is True
        :rtype: list of Coordinate or Coordinate or None
        """
        if not hasattr(self, '_coords'):
            self._coords = []
            self.site.loadcoordinfo(self)
        if primary_only:
            for coord in self._coords:
                if coord.primary:
                    return coord
            return None
        return list(self._coords)

    def page_image(self):
        """
        Return the most appropriate image on the page.

        Uses the MediaWiki extension PageImages.

        :return: A FilePage object
        :rtype: pywikibot.page.FilePage
        """
        if not hasattr(self, '_pageimage'):
            self._pageimage = None
            self.site.loadpageimage(self)

        return self._pageimage

    def getRedirectTarget(self):
        """
        Return a Page object for the target this Page redirects to.

        If this page is not a redirect page, will raise an
        IsNotRedirectPageError. This method also can raise a NoPageError.

        :rtype: pywikibot.Page
        """
        return self.site.getredirtarget(self)

    def moved_target(self):
        """
        Return a Page object for the target this Page was moved to.

        If this page was not moved, it will raise a NoMoveTargetError.
        This method also works if the source was already deleted.

        :rtype: pywikibot.page.Page
        :raises pywikibot.exceptions.NoMoveTargetError: page was not moved
        """
        gen = iter(self.site.logevents(logtype='move', page=self, total=1))
        try:
            lastmove = next(gen)
        except StopIteration:
            raise NoMoveTargetError(self)
        else:
            return lastmove.target_page

    @deprecated_args(getText='content', reverseOrder='reverse')
    def revisions(self,
                  reverse: bool = False,
                  total: Optional[int] = None,
                  content: bool = False,
                  starttime=None, endtime=None):
        """Generator which loads the version history as Revision instances."""
        # TODO: Only request uncached revisions
        self.site.loadrevisions(self, content=content, rvdir=reverse,
                                starttime=starttime, endtime=endtime,
                                total=total)
        return (self._revisions[rev] for rev in
                sorted(self._revisions, reverse=not reverse)[:total])

    @deprecated_args(reverseOrder='reverse')
    def getVersionHistoryTable(self,
                               reverse: bool = False,
                               total: Optional[int] = None):
        """Return the version history as a wiki table."""
        result = '{| class="wikitable"\n'
        result += '! oldid || date/time || username || edit summary\n'
        for entry in self.revisions(reverse=reverse, total=total):
            result += '|----\n'
            result += ('| {r.revid} || {r.timestamp} || {r.user} || '
                       '<nowiki>{r.comment}</nowiki>\n'.format(r=entry))
        result += '|}\n'
        return result

    def contributors(self,
                     total: Optional[int] = None,
                     starttime=None, endtime=None):
        """
        Compile contributors of this page with edit counts.

        :param total: iterate no more than this number of revisions in total
        :param starttime: retrieve revisions starting at this Timestamp
        :param endtime: retrieve revisions ending at this Timestamp

        :return: number of edits for each username
        :rtype: :py:obj:`collections.Counter`
        """
        return Counter(rev.user for rev in
                       self.revisions(total=total,
                                      starttime=starttime, endtime=endtime))

    def revision_count(self, contributors=None) -> int:
        """Determine number of edits from contributors.

        :param contributors: contributor usernames
        :type contributors: iterable of str or pywikibot.User,
            a single pywikibot.User, a str or None
        :return: number of edits for all provided usernames
        """
        cnt = self.contributors()

        if not contributors:
            return sum(cnt.values())

        if isinstance(contributors, User):
            contributors = contributors.username

        if isinstance(contributors, str):
            return cnt[contributors]

        return sum(cnt[user.username] if isinstance(user, User) else cnt[user]
                   for user in contributors)

    def merge_history(self, dest, timestamp=None, reason=None):
        """
        Merge revisions from this page into another page.

        See :py:obj:`APISite.merge_history` for details.

        :param dest: Destination page to which revisions will be merged
        :type dest: pywikibot.Page
        :param timestamp: Revisions from this page dating up to this timestamp
            will be merged into the destination page (if not given or False,
            all revisions will be merged)
        :type timestamp: pywikibot.Timestamp
        :param reason: Optional reason for the history merge
        :type reason: str
        """
        self.site.merge_history(self, dest, timestamp, reason)

    @deprecated_args(deleteAndMove='noredirect', movetalkpage='movetalk')
    @remove_last_args(['safe'])
    def move(self,
             newtitle: str,
             reason: Optional[str] = None,
             movetalk: bool = True,
             noredirect: bool = False):
        """
        Move this page to a new title.

        :param newtitle: The new page title.
        :param reason: The edit summary for the move.
        :param movetalk: If true, move this page's talk page (if it exists)
        :param noredirect: if move succeeds, delete the old page
            (usually requires sysop privileges, depending on wiki settings)
        """
        if reason is None:
            pywikibot.output('Moving {} to [[{}]].'
                             .format(self.title(as_link=True), newtitle))
            reason = pywikibot.input('Please enter a reason for the move:')
        return self.site.movepage(self, newtitle, reason,
                                  movetalk=movetalk,
                                  noredirect=noredirect)

    @deprecate_arg('quit', 'automatic_quit')
    def delete(self,
               reason: Optional[str] = None,
               prompt: bool = True,
               mark: bool = False,
               automatic_quit: bool = False):
        """
        Delete the page from the wiki. Requires administrator status.

        :param reason: The edit summary for the deletion, or rationale
            for deletion if requesting. If None, ask for it.
        :param prompt: If true, prompt user for confirmation before deleting.
        :param mark: If true, and user does not have sysop rights, place a
            speedy-deletion request on the page instead. If false, non-sysops
            will be asked before marking pages for deletion.
        :param automatic_quit: show also the quit option, when asking
            for confirmation.
        """
        if reason is None:
            pywikibot.output('Deleting {}.'.format(self.title(as_link=True)))
            reason = pywikibot.input('Please enter a reason for the deletion:')

        # If user has 'delete' right, delete the page
        if self.site.has_right('delete'):
            answer = 'y'
            if prompt and not hasattr(self.site, '_noDeletePrompt'):
                answer = pywikibot.input_choice(
                    'Do you want to delete {}?'.format(self.title(
                        as_link=True, force_interwiki=True)),
                    [('Yes', 'y'), ('No', 'n'), ('All', 'a')],
                    'n', automatic_quit=automatic_quit)
                if answer == 'a':
                    answer = 'y'
                    self.site._noDeletePrompt = True
            if answer == 'y':
                self.site.delete(self, reason)
            return

        # Otherwise mark it for deletion
        if mark or hasattr(self.site, '_noMarkDeletePrompt'):
            answer = 'y'
        else:
            answer = pywikibot.input_choice(
                "Can't delete {}; do you want to mark it for deletion instead?"
                .format(self),
                [('Yes', 'y'), ('No', 'n'), ('All', 'a')],
                'n', automatic_quit=False)
            if answer == 'a':
                answer = 'y'
                self.site._noMarkDeletePrompt = True
        if answer == 'y':
            template = '{{delete|1=%s}}\n' % reason
            # We can't add templates in a wikidata item, so let's use its
            # talk page
            if isinstance(self, pywikibot.ItemPage):
                target = self.toggleTalkPage()
            else:
                target = self
            target.text = template + target.text
            target.save(summary=reason)

    def has_deleted_revisions(self) -> bool:
        """Return True if the page has deleted revisions.

        *New in version 4.2.*
        """
        if not hasattr(self, '_has_deleted_revisions'):
            gen = self.site.deletedrevs(self, total=1, prop=['ids'])
            self._has_deleted_revisions = bool(list(gen))
        return self._has_deleted_revisions

    def loadDeletedRevisions(self, total: Optional[int] = None, **kwargs):
        """
        Retrieve deleted revisions for this Page.

        Stores all revisions' timestamps, dates, editors and comments in
        self._deletedRevs attribute.

        :return: iterator of timestamps (which can be used to retrieve
            revisions later on).
        :rtype: generator
        """
        if not hasattr(self, '_deletedRevs'):
            self._deletedRevs = {}
        for item in self.site.deletedrevs(self, total=total, **kwargs):
            for rev in item.get('revisions', []):
                self._deletedRevs[rev['timestamp']] = rev
                yield rev['timestamp']

    @deprecated_args(retrieveText='content')
    def getDeletedRevision(self, timestamp, content=False, **kwargs) -> List:
        """
        Return a particular deleted revision by timestamp.

        :return: a list of [date, editor, comment, text, restoration
            marker]. text will be None, unless content is True (or has
            been retrieved earlier). If timestamp is not found, returns
            empty list.
        """
        if hasattr(self, '_deletedRevs'):
            if timestamp in self._deletedRevs and (
                    not content
                    or 'content' in self._deletedRevs[timestamp]):
                return self._deletedRevs[timestamp]

        for item in self.site.deletedrevs(self, start=timestamp,
                                          content=content, total=1, **kwargs):
            # should only be one item with one revision
            if item['title'] == self.title():
                if 'revisions' in item:
                    return item['revisions'][0]
        return []

    def markDeletedRevision(self, timestamp, undelete=True):
        """
        Mark the revision identified by timestamp for undeletion.

        :param undelete: if False, mark the revision to remain deleted.
        :type undelete: bool
        """
        if not hasattr(self, '_deletedRevs'):
            self.loadDeletedRevisions()
        if timestamp not in self._deletedRevs:
            raise ValueError(
                'Timestamp {} is not a deleted revision'
                .format(timestamp))
        self._deletedRevs[timestamp]['marked'] = undelete

    @deprecated_args(comment='reason')
    def undelete(self, reason: Optional[str] = None):
        """
        Undelete revisions based on the markers set by previous calls.

        If no calls have been made since loadDeletedRevisions(), everything
        will be restored.

        Simplest case::

            Page(...).undelete('This will restore all revisions')

        More complex::

            pg = Page(...)
            revs = pg.loadDeletedRevisions()
            for rev in revs:
                if ... #decide whether to undelete a revision
                    pg.markDeletedRevision(rev) #mark for undeletion
            pg.undelete('This will restore only selected revisions.')

        :param reason: Reason for the action.
        """
        if hasattr(self, '_deletedRevs'):
            undelete_revs = [ts for ts, rev in self._deletedRevs.items()
                             if 'marked' in rev and rev['marked']]
        else:
            undelete_revs = []
        if reason is None:
            warn('Not passing a reason for undelete() is deprecated.',
                 DeprecationWarning)
            pywikibot.output('Undeleting {}.'.format(self.title(as_link=True)))
            reason = pywikibot.input(
                'Please enter a reason for the undeletion:')
        self.site.undelete(self, reason, revision=undelete_revs)

    def protect(self,
                reason: Optional[str] = None,
                protections: Optional[dict] = None,
                **kwargs):
        """
        Protect or unprotect a wiki page. Requires administrator status.

        Valid protection levels are '' (equivalent to 'none'),
        'autoconfirmed', 'sysop' and 'all'. 'all' means 'everyone is allowed',
        i.e. that protection type will be unprotected.

        In order to unprotect a type of permission, the protection level shall
        be either set to 'all' or '' or skipped in the protections dictionary.

        Expiry of protections can be set via kwargs, see Site.protect() for
        details. By default there is no expiry for the protection types.

        :param protections: A dict mapping type of protection to protection
            level of that type. Allowed protection types for a page can be
            retrieved by Page.self.applicable_protections()
            Defaults to protections is None, which means unprotect all
            protection types.
            Example: {'move': 'sysop', 'edit': 'autoconfirmed'}

        :param reason: Reason for the action, default is None and will set an
            empty string.
        """
        protections = protections or {}  # protections is converted to {}
        reason = reason or ''  # None is converted to ''

        self.site.protect(self, protections, reason, **kwargs)

    @deprecated_args(
        comment='summary', oldCat='old_cat', newCat='new_cat',
        sortKey='sort_key', inPlace='in_place')
    def change_category(
        self, old_cat, new_cat, summary=None, sort_key=None, in_place=True,
        include=None
    ) -> bool:
        """
        Remove page from oldCat and add it to newCat.

        :param old_cat: category to be removed
        :type old_cat: pywikibot.page.Category
        :param new_cat: category to be added, if any
        :type new_cat: pywikibot.page.Category or None

        :param summary: string to use as an edit summary

        :param sort_key: sortKey to use for the added category.
            Unused if newCat is None, or if inPlace=True
            If sortKey=True, the sortKey used for oldCat will be used.

        :param in_place: if True, change categories in place rather than
                      rearranging them.

        :param include: list of tags not to be disabled by default in relevant
            textlib functions, where CategoryLinks can be searched.
        :type include: list

        :return: True if page was saved changed, otherwise False.
        """
        # get list of Category objects the article is in and remove possible
        # duplicates
        cats = []
        for cat in textlib.getCategoryLinks(self.text, site=self.site,
                                            include=include or []):
            if cat not in cats:
                cats.append(cat)

        if not self.has_permission():
            pywikibot.output("Can't edit {}, skipping it..."
                             .format(self.title(as_link=True)))
            return False

        if old_cat not in cats:
            if self.namespace() != 10:
                pywikibot.error('{} is not in category {}!'
                                .format(self.title(as_link=True),
                                        old_cat.title()))
            else:
                pywikibot.output('{} is not in category {}, skipping...'
                                 .format(self.title(as_link=True),
                                         old_cat.title()))
            return False

        # This prevents the bot from adding new_cat if it is already present.
        if new_cat in cats:
            new_cat = None

        oldtext = self.text
        if in_place or self.namespace() == 10:
            newtext = textlib.replaceCategoryInPlace(oldtext, old_cat, new_cat,
                                                     site=self.site)
        else:
            old_cat_pos = cats.index(old_cat)
            if new_cat:
                if sort_key is True:
                    # Fetch sort_key from old_cat in current page.
                    sort_key = cats[old_cat_pos].sortKey
                cats[old_cat_pos] = Category(self.site, new_cat.title(),
                                             sort_key=sort_key)
            else:
                cats.pop(old_cat_pos)

            try:
                newtext = textlib.replaceCategoryLinks(oldtext, cats)
            except ValueError:
                # Make sure that the only way replaceCategoryLinks() can return
                # a ValueError is in the case of interwiki links to self.
                pywikibot.output('Skipping {} because of interwiki link to '
                                 'self'.format(self.title()))
                return False

        if oldtext != newtext:
            try:
                self.put(newtext, summary)
                return True
            except PageSaveRelatedError as error:
                pywikibot.output('Page {} not saved: {}'
                                 .format(self.title(as_link=True), error))
            except NoUsernameError:
                pywikibot.output('Page {} not saved; sysop privileges '
                                 'required.'.format(self.title(as_link=True)))
        return False

    def is_flow_page(self) -> bool:
        """Whether a page is a Flow page."""
        return self.content_model == 'flow-board'

    def create_short_link(self,
                          permalink: bool = False,
                          with_protocol: bool = True) -> str:
        """
        Return a shortened link that points to that page.

        If shared_urlshortner_wiki is defined in family config, it'll use
        that site to create the link instead of the current wiki.

        :param permalink: If true, the link will point to the actual revision
            of the page.
        :param with_protocol: If true, and if it's not already included,
            the link will have http(s) protocol prepended. On Wikimedia wikis
            the protocol is already present.
        :return: The reduced link.
        """
        wiki = self.site
        if self.site.family.shared_urlshortner_wiki:
            wiki = pywikibot.Site(*self.site.family.shared_urlshortner_wiki)

        url = self.permalink() if permalink else self.full_url()

        link = wiki.create_short_link(url)
        if re.match(PROTOCOL_REGEX, link):
            if not with_protocol:
                return re.sub(PROTOCOL_REGEX, '', link)
        elif with_protocol:
            return '{}://{}'.format(wiki.protocol(), link)
        return link


class Page(BasePage):

    """Page: A MediaWiki page."""

    @deprecated_args(defaultNamespace='ns')
    def __init__(self, source, title: str = '', ns=0):
        """Instantiate a Page object."""
        if isinstance(source, pywikibot.site.BaseSite):
            if not title:
                raise ValueError('Title must be specified and not empty '
                                 'if source is a Site.')
        super().__init__(source, title, ns)

    @property
    def raw_extracted_templates(self):
        """
        Extract templates using :py:obj:`textlib.extract_templates_and_params`.

        Disabled parts and whitespace are stripped, except for
        whitespace in anonymous positional arguments.

        This value is cached.

        :rtype: list of (str, OrderedDict)
        """
        if not hasattr(self, '_raw_extracted_templates'):
            templates = textlib.extract_templates_and_params(
                self.text, True, True)
            self._raw_extracted_templates = templates

        return self._raw_extracted_templates

    def templatesWithParams(self):
        """
        Return templates used on this Page.

        The templates are extracted by
        :py:obj:`textlib.extract_templates_and_params`, with positional
        arguments placed first in order, and each named argument
        appearing as 'name=value'.

        All parameter keys and values for each template are stripped of
        whitespace.

        :return: a list of tuples with one tuple for each template invocation
            in the page, with the template Page as the first entry and a list
            of parameters as the second entry.
        :rtype: list of (pywikibot.page.Page, list)
        """
        # WARNING: may not return all templates used in particularly
        # intricate cases such as template substitution
        titles = {t.title() for t in self.templates()}
        templates = self.raw_extracted_templates
        # backwards-compatibility: convert the dict returned as the second
        # element into a list in the format used by old scripts
        result = []
        for template in templates:
            try:
                link = pywikibot.Link(template[0], self.site,
                                      default_namespace=10)
                if link.canonical_title() not in titles:
                    continue
            except Error:
                # this is a parser function or magic word, not template name
                # the template name might also contain invalid parts
                continue
            args = template[1]
            intkeys = {}
            named = {}
            positional = []
            for key in sorted(args):
                try:
                    intkeys[int(key)] = args[key]
                except ValueError:
                    named[key] = args[key]
            for i in range(1, len(intkeys) + 1):
                # only those args with consecutive integer keys can be
                # treated as positional; an integer could also be used
                # (out of order) as the key for a named argument
                # example: {{tmp|one|two|5=five|three}}
                if i in intkeys:
                    positional.append(intkeys[i])
                else:
                    for k in intkeys:
                        if k < 1 or k >= i:
                            named[str(k)] = intkeys[k]
                    break
            for item in named.items():
                positional.append('{}={}'.format(*item))
            result.append((pywikibot.Page(link, self.site), positional))
        return result

    def set_redirect_target(self, target_page, create=False, force=False,
                            keep_section=False, save=True, **kwargs):
        """
        Change the page's text to point to the redirect page.

        :param target_page: target of the redirect, this argument is required.
        :type target_page: pywikibot.Page or string
        :param create: if true, it creates the redirect even if the page
            doesn't exist.
        :type create: bool
        :param force: if true, it set the redirect target even the page
            doesn't exist or it's not redirect.
        :type force: bool
        :param keep_section: if the old redirect links to a section
            and the new one doesn't it uses the old redirect's section.
        :type keep_section: bool
        :param save: if true, it saves the page immediately.
        :type save: bool
        :param kwargs: Arguments which are used for saving the page directly
            afterwards, like 'summary' for edit summary.
        """
        if isinstance(target_page, str):
            target_page = pywikibot.Page(self.site, target_page)
        elif self.site != target_page.site:
            raise InterwikiRedirectPageError(self, target_page)
        if not self.exists() and not (create or force):
            raise NoPageError(self)
        if self.exists() and not self.isRedirectPage() and not force:
            raise IsNotRedirectPageError(self)
        redirect_regex = self.site.redirect_regex
        if self.exists():
            old_text = self.get(get_redirect=True)
        else:
            old_text = ''
        result = redirect_regex.search(old_text)
        if result:
            oldlink = result.group(1)
            if (keep_section and '#' in oldlink
                    and target_page.section() is None):
                sectionlink = oldlink[oldlink.index('#'):]
                target_page = pywikibot.Page(
                    self.site,
                    target_page.title() + sectionlink
                )
            prefix = self.text[:result.start()]
            suffix = self.text[result.end():]
        else:
            prefix = ''
            suffix = ''

        target_link = target_page.title(as_link=True, textlink=True,
                                        allow_interwiki=False)
        target_link = '#{} {}'.format(self.site.redirect(), target_link)
        self.text = prefix + target_link + suffix
        if save:
            self.save(**kwargs)

    def get_best_claim(self, prop: str):
        """
        Return the first best Claim for this page.

        Return the first 'preferred' ranked Claim specified by Wikibase
        property or the first 'normal' one otherwise.

        *New in version 3.0.*

        :param prop: property id, "P###"
        :return: Claim object given by Wikibase property number
            for this page object.
        :rtype: pywikibot.Claim or None

        :raises UnknownExtensionError: site has no Wikibase extension
        """
        def find_best_claim(claims):
            """Find the first best ranked claim."""
            index = None
            for i, claim in enumerate(claims):
                if claim.rank == 'preferred':
                    return claim
                if index is None and claim.rank == 'normal':
                    index = i
            if index is None:
                index = 0
            return claims[index]

        if not self.site.has_data_repository:
            raise UnknownExtensionError(
                'Wikibase is not implemented for {}.'.format(self.site))

        def get_item_page(func, *args):
            try:
                item_p = func(*args)
                item_p.get()
                return item_p
            except NoPageError:
                return None
            except IsRedirectPageError:
                return get_item_page(item_p.getRedirectTarget)

        item_page = get_item_page(pywikibot.ItemPage.fromPage, self)
        if item_page and prop in item_page.claims:
            return find_best_claim(item_page.claims[prop])
        return None


class FilePage(Page):

    """
    A subclass of Page representing a file description page.

    Supports the same interface as Page, with some added methods.
    """

    def __init__(self, source, title: str = ''):
        """Initializer."""
        self._file_revisions = {}  # dictionary to cache File history.
        super().__init__(source, title, 6)
        if self.namespace() != 6:
            raise ValueError("'{}' is not in the file namespace!"
                             .format(self.title()))

    def _load_file_revisions(self, imageinfo):
        for file_rev in imageinfo:
            # filemissing in API response indicates most fields are missing
            # see https://gerrit.wikimedia.org/r/c/mediawiki/core/+/533482/
            if 'filemissing' in file_rev:
                pywikibot.warning("File '{}' contains missing revisions"
                                  .format(self.title()))
                continue
            file_revision = FileInfo(file_rev)
            self._file_revisions[file_revision.timestamp] = file_revision

    @property
    def latest_file_info(self):
        """
        Retrieve and store information of latest Image rev. of FilePage.

        At the same time, the whole history of Image is fetched and cached in
        self._file_revisions

        :return: instance of FileInfo()
        """
        if not self._file_revisions:
            self.site.loadimageinfo(self, history=True)
        latest_ts = max(self._file_revisions)
        return self._file_revisions[latest_ts]

    @property
    def oldest_file_info(self):
        """
        Retrieve and store information of oldest Image rev. of FilePage.

        At the same time, the whole history of Image is fetched and cached in
        self._file_revisions

        :return: instance of FileInfo()
        """
        if not self._file_revisions:
            self.site.loadimageinfo(self, history=True)
        oldest_ts = min(self._file_revisions)
        return self._file_revisions[oldest_ts]

    def get_file_history(self) -> dict:
        """
        Return the file's version history.

        :return: dictionary with:
            key: timestamp of the entry
            value: instance of FileInfo()
        """
        if not self._file_revisions:
            self.site.loadimageinfo(self, history=True)
        return self._file_revisions

    def getImagePageHtml(self) -> str:
        """Download the file page, and return the HTML, as a string.

        Caches the HTML code, so that if you run this method twice on the
        same FilePage object, the page will only be downloaded once.
        """
        if not hasattr(self, '_imagePageHtml'):
            path = '{}/index.php?title={}'.format(self.site.scriptpath(),
                                                  self.title(as_url=True))
            self._imagePageHtml = http.request(self.site, path).text
        return self._imagePageHtml

    def get_file_url(self, url_width=None, url_height=None,
                     url_param=None) -> str:
        """
        Return the url or the thumburl of the file described on this page.

        Fetch the information if not available.

        Once retrieved, thumburl information will also be accessible as
        latest_file_info attributes, named as in [1]:
        - url, thumburl, thumbwidth and thumbheight

        Parameters correspond to iiprops in:
        [1] https://www.mediawiki.org/wiki/API:Imageinfo

        Parameters validation and error handling left to the API call.

        :param url_width: see iiurlwidth in [1]
        :param url_height: see iiurlheigth in [1]
        :param url_param: see iiurlparam in [1]
        :return: latest file url or thumburl
        """
        # Plain url is requested.
        if url_width is None and url_height is None and url_param is None:
            return self.latest_file_info.url

        # Thumburl is requested.
        self.site.loadimageinfo(self, history=not self._file_revisions,
                                url_width=url_width, url_height=url_height,
                                url_param=url_param)
        return self.latest_file_info.thumburl

    @deprecated('file_is_shared', since='20200618')
    def fileIsShared(self) -> bool:  # pragma: no cover
        """DEPRECATED. Check if the image is stored on Wikimedia Commons."""
        return self.file_is_shared()

    def file_is_shared(self) -> bool:
        """Check if the file is stored on any known shared repository."""
        # as of now, the only known repositories are commons and wikitravel
        # TODO: put the URLs to family file
        if not self.site.has_image_repository:
            return False

        if 'wikitravel_shared' in self.site.shared_image_repository():
            return self.latest_file_info.url.startswith(
                'https://wikitravel.org/upload/shared/')
        # default to commons
        return self.latest_file_info.url.startswith(
            'https://upload.wikimedia.org/wikipedia/commons/')

    def getFileVersionHistoryTable(self):
        """Return the version history in the form of a wiki table."""
        lines = []
        for info in self.get_file_history().values():
            dimension = '{width}×{height} px ({size} bytes)'.format(
                **info.__dict__)
            lines.append('| {timestamp} || {user} || {dimension} |'
                         '| <nowiki>{comment}</nowiki>'
                         .format(dimension=dimension, **info.__dict__))
        return ('{| class="wikitable"\n'
                '! {{int:filehist-datetime}} || {{int:filehist-user}} |'
                '| {{int:filehist-dimensions}} || {{int:filehist-comment}}\n'
                '|-\n%s\n|}\n' % '\n|-\n'.join(lines))

    def usingPages(self, total: Optional[int] = None, content: bool = False):
        """Yield Pages on which the file is displayed.

        :param total: iterate no more than this number of pages in total
        :param content: if True, load the current content of each iterated page
            (default False)
        """
        return self.site.imageusage(self, total=total, content=content)

    def upload(self, source: str, **kwargs) -> bool:
        """
        Upload this file to the wiki.

        keyword arguments are from site.upload() method.

        :param source: Path or URL to the file to be uploaded.

        :keyword comment: Edit summary; if this is not provided, then
            filepage.text will be used. An empty summary is not permitted.
            This may also serve as the initial page text (see below).
        :keyword text: Initial page text; if this is not set, then
            filepage.text will be used, or comment.
        :keyword watch: If true, add filepage to the bot user's watchlist
        :keyword ignore_warnings: It may be a static boolean, a callable
            returning a boolean or an iterable. The callable gets a list of
            UploadError instances and the iterable should contain the warning
            codes for which an equivalent callable would return True if all
            UploadError codes are in thet list. If the result is False it'll
            not continue uploading the file and otherwise disable any warning
            and reattempt to upload the file. NOTE: If report_success is True
            or None it'll raise an UploadError exception if the static
            boolean is False.
        :type ignore_warnings: bool or callable or iterable of str
        :keyword chunk_size: The chunk size in bytesfor chunked uploading (see
            https://www.mediawiki.org/wiki/API:Upload#Chunked_uploading). It
            will only upload in chunks, if the chunk size is positive but lower
            than the file size.
        :type chunk_size: int
        :keyword _file_key: Reuses an already uploaded file using the filekey.
            If None (default) it will upload the file.
        :type _file_key: str or None
        :keyword _offset: When file_key is not None this can be an integer to
            continue a previously canceled chunked upload. If False it treats
            that as a finished upload. If True it requests the stash info from
            the server to determine the offset. By default starts at 0.
        :type _offset: int or bool
        :keyword _verify_stash: Requests the SHA1 and file size uploaded and
            compares it to the local file. Also verifies that _offset is
            matching the file size if the _offset is an int. If _offset is
            False if verifies that the file size match with the local file. If
            None it'll verifies the stash when a file key and offset is given.
        :type _verify_stash: bool or None
        :keyword report_success: If the upload was successful it'll print a
            success message and if ignore_warnings is set to False it'll
            raise an UploadError if a warning occurred. If it's
            None (default) it'll be True if ignore_warnings is a bool and False
            otherwise. If it's True or None ignore_warnings must be a bool.
        :return: It returns True if the upload was successful and False
            otherwise.
        """
        filename = url = None
        if '://' in source:
            url = source
        else:
            filename = source
        return self.site.upload(self, source_filename=filename, source_url=url,
                                **kwargs)

    def download(self, filename=None, chunk_size=100 * 1024, revision=None):
        """
        Download to filename file of FilePage.

        :param filename: filename where to save file:
            None: self.title(as_filename=True, with_ns=False)
            will be used
            str: provided filename will be used.
        :type filename: None or str
        :param chunk_size: the size of each chunk to be received and
            written to file.
        :type chunk_size: int
        :param revision: file revision to download:
            None: self.latest_file_info will be used
            FileInfo: provided revision will be used.
        :type revision: None or FileInfo
        :return: True if download is successful, False otherwise.
        :raise IOError: if filename cannot be written for any reason.
        """
        if filename is None:
            filename = self.title(as_filename=True, with_ns=False)

        filename = os.path.expanduser(filename)

        if revision is None:
            revision = self.latest_file_info

        req = http.fetch(revision.url, stream=True)
        if req.status_code == HTTPStatus.OK:
            try:
                with open(filename, 'wb') as f:
                    for chunk in req.iter_content(chunk_size):
                        f.write(chunk)
            except IOError as e:
                raise e

            sha1 = compute_file_hash(filename)
            return sha1 == revision.sha1
        pywikibot.warning(
            'Unsuccessfull request ({}): {}'
            .format(req.status_code, req.url))
        return False

    def globalusage(self, total=None):
        """
        Iterate all global usage for this page.

        :param total: iterate no more than this number of pages in total
        :return: a generator that yields Pages also on sites different from
            self.site.
        :rtype: generator
        """
        return self.site.globalusage(self, total=total)

    def data_item(self):
        """
        Convenience function to get the associated Wikibase item of the file.

        If WikibaseMediaInfo extension is available (e.g. on Commons),
        the method returns the associated mediainfo entity. Otherwise,
        it falls back to behavior of BasePage.data_item.

        *New in version 6.5.*

        :rtype: pywikibot.page.WikibaseEntity
        """
        if self.site.has_extension('WikibaseMediaInfo'):
            if not hasattr(self, '_item'):
                self._item = MediaInfo(self.site)
                self._item._file = self
            return self._item

        return super().data_item()


class Category(Page):

    """A page in the Category: namespace."""

    @deprecated_args(sortKey='sort_key')
    def __init__(self, source, title: str = '', sort_key=None):
        """
        Initializer.

        All parameters are the same as for Page() Initializer.
        """
        self.sortKey = sort_key
        super().__init__(source, title, ns=14)
        if self.namespace() != 14:
            raise ValueError("'{}' is not in the category namespace!"
                             .format(self.title()))

    @deprecated_args(sortKey='sort_key')
    def aslink(self, sort_key: Optional[str] = None) -> str:
        """
        Return a link to place a page in this Category.

        Use this only to generate a "true" category link, not for interwikis
        or text links to category pages.

        :param sort_key: The sort key for the article to be placed in this
            Category; if omitted, default sort key is used.
        """
        key = sort_key or self.sortKey
        if key is not None:
            title_with_sort_key = self.title(with_section=False) + '|' + key
        else:
            title_with_sort_key = self.title(with_section=False)
        return '[[{}]]'.format(title_with_sort_key)

    def subcategories(self,
                      recurse: Union[int, bool] = False,
                      total: Optional[int] = None,
                      content: bool = False):
        """
        Iterate all subcategories of the current category.

        :param recurse: if not False or 0, also iterate subcategories of
            subcategories. If an int, limit recursion to this number of
            levels. (Example: recurse=1 will iterate direct subcats and
            first-level sub-sub-cats, but no deeper.)
        :param total: iterate no more than this number of
            subcategories in total (at all levels)
        :param content: if True, retrieve the content of the current version
            of each category description page (default False)
        """
        if not isinstance(recurse, bool) and recurse:
            recurse = recurse - 1
        if not hasattr(self, '_subcats'):
            self._subcats = []
            for member in self.site.categorymembers(
                    self, member_type='subcat', total=total, content=content):
                subcat = Category(member)
                self._subcats.append(subcat)
                yield subcat
                if total is not None:
                    total -= 1
                    if total == 0:
                        return
                if recurse:
                    for item in subcat.subcategories(
                            recurse, total=total, content=content):
                        yield item
                        if total is not None:
                            total -= 1
                            if total == 0:
                                return
        else:
            for subcat in self._subcats:
                yield subcat
                if total is not None:
                    total -= 1
                    if total == 0:
                        return
                if recurse:
                    for item in subcat.subcategories(
                            recurse, total=total, content=content):
                        yield item
                        if total is not None:
                            total -= 1
                            if total == 0:
                                return

    @deprecated_args(startFrom='startprefix', startsort=True, endsort=True)
    def articles(self,
                 recurse: Union[int, bool] = False,
                 total: Optional[int] = None,
                 content: bool = False,
                 namespaces: Union[int, List[int]] = None,
                 sortby: Optional[str] = None,
                 reverse: bool = False,
                 starttime=None, endtime=None,
                 startprefix: Optional[str] = None,
                 endprefix: Optional[str] = None):
        """
        Yield all articles in the current category.

        By default, yields all *pages* in the category that are not
        subcategories!

        :param recurse: if not False or 0, also iterate articles in
            subcategories. If an int, limit recursion to this number of
            levels. (Example: recurse=1 will iterate articles in first-level
            subcats, but no deeper.)
        :param total: iterate no more than this number of pages in
            total (at all levels)
        :param namespaces: only yield pages in the specified namespaces
        :param content: if True, retrieve the content of the current version
            of each page (default False)
        :param sortby: determines the order in which results are generated,
            valid values are "sortkey" (default, results ordered by category
            sort key) or "timestamp" (results ordered by time page was
            added to the category). This applies recursively.
        :param reverse: if True, generate results in reverse order
            (default False)
        :param starttime: if provided, only generate pages added after this
            time; not valid unless sortby="timestamp"
        :type starttime: pywikibot.Timestamp
        :param endtime: if provided, only generate pages added before this
            time; not valid unless sortby="timestamp"
        :type endtime: pywikibot.Timestamp
        :param startprefix: if provided, only generate pages >= this title
            lexically; not valid if sortby="timestamp"
        :param endprefix: if provided, only generate pages < this title
            lexically; not valid if sortby="timestamp"
        :rtype: typing.Iterable[pywikibot.Page]
        """
        seen = set()
        for member in self.site.categorymembers(self,
                                                namespaces=namespaces,
                                                total=total,
                                                content=content,
                                                sortby=sortby,
                                                reverse=reverse,
                                                starttime=starttime,
                                                endtime=endtime,
                                                startprefix=startprefix,
                                                endprefix=endprefix,
                                                member_type=['page', 'file']):
            if recurse:
                seen.add(hash(member))
            yield member
            if total is not None:
                total -= 1
                if total == 0:
                    return

        if recurse:
            if not isinstance(recurse, bool) and recurse:
                recurse -= 1
            for subcat in self.subcategories():
                for article in subcat.articles(recurse=recurse,
                                               total=total,
                                               content=content,
                                               namespaces=namespaces,
                                               sortby=sortby,
                                               reverse=reverse,
                                               starttime=starttime,
                                               endtime=endtime,
                                               startprefix=startprefix,
                                               endprefix=endprefix):
                    hash_value = hash(article)
                    if hash_value in seen:
                        continue
                    seen.add(hash_value)
                    yield article
                    if total is not None:
                        total -= 1
                        if total == 0:
                            return

    def members(self, recurse: bool = False,
                namespaces=None,
                total: Optional[int] = None,
                content=False):
        """Yield all category contents (subcats, pages, and files).

        :rtype: typing.Iterable[pywikibot.Page]
        """
        for member in self.site.categorymembers(
                self, namespaces=namespaces, total=total, content=content):
            yield member
            if total is not None:
                total -= 1
                if total == 0:
                    return
        if recurse:
            if not isinstance(recurse, bool) and recurse:
                recurse = recurse - 1
            for subcat in self.subcategories():
                for article in subcat.members(
                        recurse, namespaces, total=total, content=content):
                    yield article
                    if total is not None:
                        total -= 1
                        if total == 0:
                            return

    def isEmptyCategory(self) -> bool:
        """Return True if category has no members (including subcategories)."""
        ci = self.categoryinfo
        return sum(ci[k] for k in ['files', 'pages', 'subcats']) == 0

    def isHiddenCategory(self) -> bool:
        """Return True if the category is hidden."""
        return 'hiddencat' in self.properties()

    @property
    def categoryinfo(self) -> dict:
        """
        Return a dict containing information about the category.

        The dict contains values for:

        Numbers of pages, subcategories, files, and total contents.
        """
        return self.site.categoryinfo(self)

    def newest_pages(self, total=None):
        """
        Return pages in a category ordered by the creation date.

        If two or more pages are created at the same time, the pages are
        returned in the order they were added to the category. The most
        recently added page is returned first.

        It only allows to return the pages ordered from newest to oldest, as it
        is impossible to determine the oldest page in a category without
        checking all pages. But it is possible to check the category in order
        with the newly added first and it yields all pages which were created
        after the currently checked page was added (and thus there is no page
        created after any of the cached but added before the currently
        checked).

        :param total: The total number of pages queried.
        :type total: int
        :return: A page generator of all pages in a category ordered by the
            creation date. From newest to oldest. Note: It currently only
            returns Page instances and not a subclass of it if possible. This
            might change so don't expect to only get Page instances.
        :rtype: generator
        """
        def check_cache(latest):
            """Return the cached pages in order and not more than total."""
            cached = []
            for timestamp in sorted((ts for ts in cache if ts > latest),
                                    reverse=True):
                # The complete list can be removed, it'll either yield all of
                # them, or only a portion but will skip the rest anyway
                cached += cache.pop(timestamp)[:None if total is None else
                                               total - len(cached)]
                if total and len(cached) >= total:
                    break  # already got enough
            assert total is None or len(cached) <= total, \
                'Number of caches is more than total number requested'
            return cached

        # all pages which have been checked but where created before the
        # current page was added, at some point they will be created after
        # the current page was added. It saves all pages via the creation
        # timestamp. Be prepared for multiple pages.
        cache = defaultdict(list)
        # TODO: Make site.categorymembers is usable as it returns pages
        # There is no total defined, as it's not known how many pages need to
        # be checked before the total amount of new pages was found. In worst
        # case all pages of a category need to be checked.
        for member in pywikibot.data.api.QueryGenerator(
            site=self.site, parameters={
                'list': 'categorymembers', 'cmsort': 'timestamp',
                'cmdir': 'older', 'cmprop': 'timestamp|title',
                'cmtitle': self.title()}):
            # TODO: Upcast to suitable class
            page = pywikibot.Page(self.site, member['title'])
            assert page.namespace() == member['ns'], \
                'Namespace of the page is not consistent'
            cached = check_cache(pywikibot.Timestamp.fromISOformat(
                member['timestamp']))
            yield from cached
            if total is not None:
                total -= len(cached)
                if total <= 0:
                    break
            cache[page.oldest_revision.timestamp] += [page]
        else:
            # clear cache
            assert total is None or total > 0, \
                'As many items as given in total already returned'
            yield from check_cache(pywikibot.Timestamp.min)


class User(Page):

    """
    A class that represents a Wiki user.

    This class also represents the Wiki page User:<username>
    """

    @deprecated_args(site='source', name='title')
    def __init__(self, source, title=''):
        """
        Initializer for a User object.

        All parameters are the same as for Page() Initializer.
        """
        self._isAutoblock = True
        if title.startswith('#'):
            title = title[1:]
        elif ':#' in title:
            title = title.replace(':#', ':')
        else:
            self._isAutoblock = False
        super().__init__(source, title, ns=2)
        if self.namespace() != 2:
            raise ValueError("'{}' is not in the user namespace!"
                             .format(self.title()))
        if self._isAutoblock:
            # This user is probably being queried for purpose of lifting
            # an autoblock.
            pywikibot.output(
                'This is an autoblock ID, you can only use to unblock it.')

    @property
    def username(self) -> str:
        """
        The username.

        Convenience method that returns the title of the page with
        namespace prefix omitted, which is the username.
        """
        if self._isAutoblock:
            return '#' + self.title(with_ns=False)
        return self.title(with_ns=False)

    def isRegistered(self, force: bool = False) -> bool:
        """
        Determine if the user is registered on the site.

        It is possible to have a page named User:xyz and not have
        a corresponding user with username xyz.

        The page does not need to exist for this method to return
        True.

        :param force: if True, forces reloading the data from API
        """
        # T135828: the registration timestamp may be None but the key exists
        return (not self.isAnonymous()
                and 'registration' in self.getprops(force))

    def isAnonymous(self) -> bool:
        """Determine if the user is editing as an IP address."""
        return is_ip_address(self.username)

    def getprops(self, force: bool = False) -> dict:
        """
        Return a properties about the user.

        :param force: if True, forces reloading the data from API
        """
        if force and hasattr(self, '_userprops'):
            del self._userprops
        if not hasattr(self, '_userprops'):
            self._userprops = list(self.site.users([self.username, ]))[0]
            if self.isAnonymous():
                r = list(self.site.blocks(users=self.username))
                if r:
                    self._userprops['blockedby'] = r[0]['by']
                    self._userprops['blockreason'] = r[0]['reason']
        return self._userprops

    def registration(self, force=False):
        """
        Fetch registration date for this user.

        :param force: if True, forces reloading the data from API
        :type force: bool

        :rtype: pywikibot.Timestamp or None
        """
        if not self.isAnonymous():
            reg = self.getprops(force).get('registration')
            if reg:
                return pywikibot.Timestamp.fromISOformat(reg)
        return None

    def editCount(self, force: bool = False) -> int:
        """
        Return edit count for a registered user.

        Always returns 0 for 'anonymous' users.

        :param force: if True, forces reloading the data from API
        """
        return self.getprops(force).get('editcount', 0)

    def isBlocked(self, force: bool = False) -> bool:
        """
        Determine whether the user is currently blocked.

        :param force: if True, forces reloading the data from API
        """
        return 'blockedby' in self.getprops(force)

    def isEmailable(self, force: bool = False) -> bool:
        """
        Determine whether emails may be send to this user through MediaWiki.

        :param force: if True, forces reloading the data from API
        """
        return not self.isAnonymous() and 'emailable' in self.getprops(force)

    def groups(self, force: bool = False) -> list:
        """
        Return a list of groups to which this user belongs.

        The list of groups may be empty.

        :param force: if True, forces reloading the data from API
        :return: groups property
        """
        return self.getprops(force).get('groups', [])

    def gender(self, force: bool = False) -> str:
        """Return the gender of the user.

        :param force: if True, forces reloading the data from API
        :return: return 'male', 'female', or 'unknown'
        """
        if self.isAnonymous():
            return 'unknown'
        return self.getprops(force).get('gender', 'unknown')

    def rights(self, force: bool = False) -> list:
        """Return user rights.

        :param force: if True, forces reloading the data from API
        :return: return user rights
        """
        return self.getprops(force).get('rights', [])

    def getUserPage(self, subpage=''):
        """
        Return a Page object relative to this user's main page.

        :param subpage: subpage part to be appended to the main
                            page title (optional)
        :type subpage: str
        :return: Page object of user page or user subpage
        :rtype: pywikibot.Page
        """
        if self._isAutoblock:
            # This user is probably being queried for purpose of lifting
            # an autoblock, so has no user pages per se.
            raise AutoblockUserError(
                'This is an autoblock ID, you can only use to unblock it.')
        if subpage:
            subpage = '/' + subpage
        return Page(Link(self.title() + subpage, self.site))

    def getUserTalkPage(self, subpage=''):
        """
        Return a Page object relative to this user's main talk page.

        :param subpage: subpage part to be appended to the main
                            talk page title (optional)
        :type subpage: str
        :return: Page object of user talk page or user talk subpage
        :rtype: pywikibot.Page
        """
        if self._isAutoblock:
            # This user is probably being queried for purpose of lifting
            # an autoblock, so has no user talk pages per se.
            raise AutoblockUserError(
                'This is an autoblock ID, you can only use to unblock it.')
        if subpage:
            subpage = '/' + subpage
        return Page(Link(self.username + subpage,
                         self.site, default_namespace=3))

    def send_email(self, subject: str, text: str, ccme: bool = False) -> bool:
        """
        Send an email to this user via MediaWiki's email interface.

        :param subject: the subject header of the mail
        :param text: mail body
        :param ccme: if True, sends a copy of this email to the bot
        :raises NotEmailableError: the user of this User is not emailable
        :raises UserRightsError: logged in user does not have 'sendemail' right
        :return: operation successful indicator
        """
        if not self.isEmailable():
            raise NotEmailableError(self)

        if not self.site.has_right('sendemail'):
            raise UserRightsError("You don't have permission to send mail")

        params = {
            'action': 'emailuser',
            'target': self.username,
            'token': self.site.tokens['email'],
            'subject': subject,
            'text': text,
        }
        if ccme:
            params['ccme'] = 1
        mailrequest = self.site._simple_request(**params)
        maildata = mailrequest.submit()

        if 'emailuser' in maildata:
            if maildata['emailuser']['result'] == 'Success':
                return True
        return False

    def block(self, *args, **kwargs):
        """
        Block user.

        Refer :py:obj:`APISite.blockuser` method for parameters.

        :return: None
        """
        try:
            self.site.blockuser(self, *args, **kwargs)
        except APIError as err:
            if err.code == 'invalidrange':
                raise ValueError('{} is not a valid IP range.'
                                 .format(self.username))

            raise err

    def unblock(self, reason: Optional[str] = None):
        """
        Remove the block for the user.

        :param reason: Reason for the unblock.
        """
        self.site.unblockuser(self, reason)

    def logevents(self, **kwargs):
        """Yield user activities.

        :keyword logtype: only iterate entries of this type
            (see mediawiki api documentation for available types)
        :type logtype: str
        :keyword page: only iterate entries affecting this page
        :type page: Page or str
        :keyword namespace: namespace to retrieve logevents from
        :type namespace: int or Namespace
        :keyword start: only iterate entries from and after this Timestamp
        :type start: Timestamp or ISO date string
        :keyword end: only iterate entries up to and through this Timestamp
        :type end: Timestamp or ISO date string
        :keyword reverse: if True, iterate oldest entries first
            (default: newest)
        :type reverse: bool
        :keyword tag: only iterate entries tagged with this tag
        :type tag: str
        :keyword total: maximum number of events to iterate
        :type total: int
        :rtype: iterable
        """
        return self.site.logevents(user=self.username, **kwargs)

    @property
    def last_event(self):
        """Return last user activity.

        :return: last user log entry
        :rtype: LogEntry or None
        """
        return next(iter(self.logevents(total=1)), None)

    @deprecated_args(limit='total', namespace='namespaces')
    def contributions(self, total: int = 500, **kwargs) -> tuple:
        """
        Yield tuples describing this user edits.

        Each tuple is composed of a pywikibot.Page object,
        the revision id (int), the edit timestamp (as a pywikibot.Timestamp
        object), and the comment (str).
        Pages returned are not guaranteed to be unique.

        :param total: limit result to this number of pages
        :keyword start: Iterate contributions starting at this Timestamp
        :keyword end: Iterate contributions ending at this Timestamp
        :keyword reverse: Iterate oldest contributions first (default: newest)
        :keyword namespaces: only iterate pages in these namespaces
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :keyword showMinor: if True, iterate only minor edits; if False and
            not None, iterate only non-minor edits (default: iterate both)
        :keyword top_only: if True, iterate only edits which are the latest
            revision (default: False)
        :return: tuple of pywikibot.Page, revid, pywikibot.Timestamp, comment
        """
        for contrib in self.site.usercontribs(
                user=self.username, total=total, **kwargs):
            ts = pywikibot.Timestamp.fromISOformat(contrib['timestamp'])
            yield (Page(self.site, contrib['title'], contrib['ns']),
                   contrib['revid'],
                   ts,
                   contrib.get('comment'))

    @property
    def first_edit(self):
        """Return first user contribution.

        :return: first user contribution entry
        :return: tuple of pywikibot.Page, revid, pywikibot.Timestamp, comment
        :rtype: tuple or None
        """
        return next(self.contributions(reverse=True, total=1), None)

    @property
    def last_edit(self):
        """Return last user contribution.

        :return: last user contribution entry
        :return: tuple of pywikibot.Page, revid, pywikibot.Timestamp, comment
        :rtype: tuple or None
        """
        return next(self.contributions(total=1), None)

    def deleted_contributions(
        self, *, total: int = 500, **kwargs
    ) -> Iterable[Tuple[Page, Revision]]:
        """Yield tuples describing this user's deleted edits.

        *New in version 5.5.*

        :param total: Limit results to this number of pages
        :keyword start: Iterate contributions starting at this Timestamp
        :keyword end: Iterate contributions ending at this Timestamp
        :keyword reverse: Iterate oldest contributions first (default: newest)
        :keyword namespaces: Only iterate pages in these namespaces
        """
        for data in self.site.alldeletedrevisions(user=self.username,
                                                  total=total, **kwargs):
            page = Page(self.site, data['title'], data['ns'])
            for contrib in data['revisions']:
                yield page, Revision(**contrib)

    @deprecate_arg('number', 'total')
    def uploadedImages(self, total=10):
        """
        Yield tuples describing files uploaded by this user.

        Each tuple is composed of a pywikibot.Page, the timestamp (str in
        ISO8601 format), comment (str) and a bool for pageid > 0.
        Pages returned are not guaranteed to be unique.

        :param total: limit result to this number of pages
        :type total: int
        """
        if not self.isRegistered():
            return
        for item in self.logevents(logtype='upload', total=total):
            yield (item.page(),
                   str(item.timestamp()),
                   item.comment(),
                   item.pageid() > 0)

    @property
    def is_thankable(self) -> bool:
        """
        Determine if the user has thanks notifications enabled.

        NOTE: This doesn't accurately determine if thanks is enabled for user.
              Privacy of thanks preferences is under discussion, please see
              https://phabricator.wikimedia.org/T57401#2216861, and
              https://phabricator.wikimedia.org/T120753#1863894
        """
        return self.isRegistered() and 'bot' not in self.groups()


class WikibaseEntity:

    """
    The base interface for Wikibase entities.

    Each entity is identified by a data repository it belongs to
    and an identifier.

    :cvar DATA_ATTRIBUTES: dictionary which maps data attributes (eg. 'labels',
        'claims') to appropriate collection classes (eg. LanguageDict,
        ClaimsCollection)

    :cvar entity_type: entity type identifier
    :type entity_type: str

    :cvar title_pattern: regular expression which matches all possible
        entity ids for this entity type
    :type title_pattern: str
    """

    DATA_ATTRIBUTES = {}  # type: Dict[str, Any]

    def __init__(self, repo, id_=None):
        """
        Initializer.

        :param repo: Entity repository.
        :type repo: DataSite
        :param id_: Entity identifier.
        :type id_: str or None, -1 and None mean non-existing
        """
        self.repo = repo
        self.id = id_ if id_ is not None else '-1'
        if self.id != '-1' and not self.is_valid_id(self.id):
            raise InvalidTitleError(
                "'{}' is not a valid {} page title"
                .format(self.id, self.entity_type))

    def __repr__(self):
        if self.id != '-1':
            return 'pywikibot.page.{}({!r}, {!r})'.format(
                self.__class__.__name__, self.repo, self.id)
        return 'pywikibot.page.{}({!r})'.format(
            self.__class__.__name__, self.repo)

    @classmethod
    def is_valid_id(cls, entity_id: str) -> bool:
        """
        Whether the string can be a valid id of the entity type.

        :param entity_id: The ID to test.
        """
        if not hasattr(cls, 'title_pattern'):
            return True

        return bool(re.fullmatch(cls.title_pattern, entity_id))

    def __getattr__(self, name):
        if name in self.DATA_ATTRIBUTES:
            if self.getID() == '-1':
                for key, cls in self.DATA_ATTRIBUTES.items():
                    setattr(self, key, cls.new_empty(self.repo))
                return getattr(self, name)
            return self.get()[name]

        raise AttributeError("'{}' object has no attribute '{}'"
                             .format(self.__class__.__name__, name))

    def _defined_by(self, singular: bool = False) -> dict:
        """
        Internal function to provide the API parameters to identify the entity.

        An empty dict is returned if the entity has not been created yet.

        :param singular: Whether the parameter names should use the singular
                         form
        :return: API parameters
        """
        params = {}
        if self.id != '-1':
            if singular:
                params['id'] = self.id
            else:
                params['ids'] = self.id
        return params

    def getID(self, numeric=False):
        """
        Get the identifier of this entity.

        :param numeric: Strip the first letter and return an int
        :type numeric: bool
        """
        if numeric:
            return int(self.id[1:]) if self.id != '-1' else -1
        return self.id

    def get_data_for_new_entity(self) -> dict:
        """
        Return data required for creation of a new entity.

        Override it if you need.
        """
        return {}

    def toJSON(self, diffto: Optional[dict] = None) -> dict:
        """
        Create JSON suitable for Wikibase API.

        When diffto is provided, JSON representing differences
        to the provided data is created.

        :param diffto: JSON containing entity data
        """
        data = {}
        for key in self.DATA_ATTRIBUTES:
            attr = getattr(self, key, None)
            if attr is None:
                continue
            if diffto:
                value = attr.toJSON(diffto=diffto.get(key))
            else:
                value = attr.toJSON()
            if value:
                data[key] = value
        return data

    @classmethod
    def _normalizeData(cls, data: dict) -> dict:
        """
        Helper function to expand data into the Wikibase API structure.

        :param data: The dict to normalize
        :return: The dict with normalized data
        """
        norm_data = {}
        for key, attr in cls.DATA_ATTRIBUTES.items():
            if key in data:
                norm_data[key] = attr.normalizeData(data[key])
        return norm_data

    @property
    def latest_revision_id(self) -> Optional[int]:
        """
        Get the revision identifier for the most recent revision of the entity.

        :rtype: int or None if it cannot be determined
        :raise NoWikibaseEntityError: if the entity doesn't exist
        """
        if not hasattr(self, '_revid'):
            # fixme: unlike BasePage.latest_revision_id, this raises
            # exception when entity is redirect, cannot use get_redirect
            self.get()
        return self._revid

    @latest_revision_id.setter
    def latest_revision_id(self, value: Optional[int]) -> None:
        self._revid = value

    @latest_revision_id.deleter
    def latest_revision_id(self) -> None:
        if hasattr(self, '_revid'):
            del self._revid

    def exists(self) -> bool:
        """Determine if an entity exists in the data repository."""
        if not hasattr(self, '_content'):
            try:
                self.get()
                return True
            except NoWikibaseEntityError:
                return False
        return 'missing' not in self._content

    def get(self, force: bool = False) -> dict:
        """
        Fetch all entity data and cache it.

        :param force: override caching
        :raise NoWikibaseEntityError: if this entity doesn't exist
        :return: actual data which entity holds
        """
        if force or not hasattr(self, '_content'):
            identification = self._defined_by()
            if not identification:
                raise NoWikibaseEntityError(self)

            try:
                data = self.repo.loadcontent(identification)
            except APIError as err:
                if err.code == 'no-such-entity':
                    raise NoWikibaseEntityError(self)
                raise
            item_index, content = data.popitem()
            self.id = item_index
            self._content = content
        if 'missing' in self._content:
            raise NoWikibaseEntityError(self)

        self.latest_revision_id = self._content.get('lastrevid')

        data = {}

        # This initializes all data,
        for key, cls in self.DATA_ATTRIBUTES.items():
            value = cls.fromJSON(self._content.get(key, {}), self.repo)
            setattr(self, key, value)
            data[key] = value
        return data

    def editEntity(self, data=None, **kwargs):
        """
        Edit an entity using Wikibase wbeditentity API.

        :param data: Data to be saved
        :type data: dict, or None to save the current content of the entity.
        """
        if data is None:
            data = self.toJSON(diffto=getattr(self, '_content', None))
        else:
            data = self._normalizeData(data)

        baserevid = getattr(self, '_revid', None)

        updates = self.repo.editEntity(
            self, data, baserevid=baserevid, **kwargs)

        # the attribute may have been unset in ItemPage
        if getattr(self, 'id', '-1') == '-1':
            self.__init__(self.repo, updates['entity']['id'])

        # the response also contains some data under the 'entity' key
        # but it is NOT the actual content
        # see also [[d:Special:Diff/1356933963]]
        # TODO: there might be some circumstances under which
        # the content can be safely reused
        if hasattr(self, '_content'):
            del self._content
        self.latest_revision_id = updates['entity'].get('lastrevid')

    def concept_uri(self):
        """
        Return the full concept URI.

        :raise NoWikibaseEntityError: if this entity doesn't exist
        """
        entity_id = self.getID()
        if entity_id == '-1':
            raise NoWikibaseEntityError(self)
        return '{}{}'.format(self.repo.concept_base_uri, entity_id)


class MediaInfo(WikibaseEntity):

    """Interface for MediaInfo entities on Commons.

    *New in version 6.5.*
    """

    title_pattern = r'M[1-9]\d*'
    DATA_ATTRIBUTES = {
        'labels': LanguageDict,
        # TODO: 'statements': ClaimCollection,
    }

    @property
    def file(self) -> FilePage:
        """Get the file associated with the mediainfo."""
        if not hasattr(self, '_file'):
            if self.id == '-1':
                # if the above doesn't apply, this entity is in an invalid
                # state which needs to be raised as an exception, but also
                # logged in case an exception handler is catching
                # the generic Error
                pywikibot.error('{} is in invalid state'
                                .format(self.__class__.__name__))
                raise Error('{} is in invalid state'
                            .format(self.__class__.__name__))

            page_id = self.getID(numeric=True)
            result = list(self.repo.load_pages_from_pageids([page_id]))
            if not result:
                raise Error('There is no existing page with id "{}"'
                            .format(page_id))

            page = result.pop()
            if page.namespace() != page.site.namespaces.FILE:
                raise Error('Page with id "{}" is not a file'.format(page_id))

            self._file = FilePage(page)

        return self._file

    def get(self, force: bool = False) -> dict:
        if self.id == '-1':
            if force:
                if not self.file.exists():
                    exc = NoPageError(self.file)
                    raise NoWikibaseEntityError(self) from exc
                # get just the id for Wikibase API call
                self.id = 'M' + str(self.file.pageid)
            else:
                try:
                    data = self.file.latest_revision.slots['mediainfo']['*']
                except NoPageError as exc:
                    raise NoWikibaseEntityError(self) from exc

                self._content = jsonlib.loads(data)
                self.id = self._content['id']

        return super().get(force=force)

    def getID(self, numeric=False):
        """
        Get the entity identifier.

        :param numeric: Strip the first letter and return an int
        :type numeric: bool
        """
        if self.id == '-1':
            self.get()
        return super().getID(numeric=numeric)


class WikibasePage(BasePage, WikibaseEntity):

    """
    Mixin base class for Wikibase entities which are also pages (eg. items).

    There should be no need to instantiate this directly.
    """

    _cache_attrs = BasePage._cache_attrs + ('_content', )

    def __init__(self, site, title='', **kwargs):
        """
        Initializer.

        If title is provided, either ns or entity_type must also be provided,
        and will be checked against the title parsed using the Page
        initialisation logic.

        :param site: Wikibase data site
        :type site: pywikibot.site.DataSite
        :param title: normalized title of the page
        :type title: str
        :keyword ns: namespace
        :type ns: Namespace instance, or int
        :keyword entity_type: Wikibase entity type
        :type entity_type: str ('item' or 'property')

        :raises TypeError: incorrect use of parameters
        :raises ValueError: incorrect namespace
        :raises pywikibot.exceptions.Error: title parsing problems
        :raises NotImplementedError: the entity type is not supported
        """
        if not isinstance(site, pywikibot.site.DataSite):
            raise TypeError('site must be a pywikibot.site.DataSite object')
        if title and ('ns' not in kwargs and 'entity_type' not in kwargs):
            pywikibot.debug('{}.__init__: {} title {!r} specified without '
                            'ns or entity_type'
                            .format(self.__class__.__name__, site,
                                    title),
                            layer='wikibase')

        self._namespace = None

        if 'ns' in kwargs:
            if isinstance(kwargs['ns'], Namespace):
                self._namespace = kwargs.pop('ns')
                kwargs['ns'] = self._namespace.id
            else:
                # numerical namespace given
                ns = int(kwargs['ns'])
                if site.item_namespace.id == ns:
                    self._namespace = site.item_namespace
                elif site.property_namespace.id == ns:
                    self._namespace = site.property_namespace
                else:
                    raise ValueError('{!r}: Namespace "{}" is not valid'
                                     .format(site, int(ns)))

        if 'entity_type' in kwargs:
            entity_type = kwargs.pop('entity_type')
            try:
                entity_type_ns = site.get_namespace_for_entity_type(
                    entity_type)
            except EntityTypeUnknownError:
                raise ValueError('Wikibase entity type "{}" unknown'
                                 .format(entity_type))

            if self._namespace:
                if self._namespace != entity_type_ns:
                    raise ValueError('Namespace "{}" is not valid for Wikibase'
                                     ' entity type "{}"'
                                     .format(int(kwargs['ns']), entity_type))
            else:
                self._namespace = entity_type_ns
                kwargs['ns'] = self._namespace.id

        BasePage.__init__(self, site, title, **kwargs)

        # If a title was not provided,
        # avoid checks which may cause an exception.
        if not title:
            WikibaseEntity.__init__(self, site)
            return

        if self._namespace:
            if self._link.namespace != self._namespace.id:
                raise ValueError("'{}' is not in the namespace {}"
                                 .format(title, self._namespace.id))
        else:
            # Neither ns or entity_type was provided.
            # Use the _link to determine entity type.
            ns = self._link.namespace
            if self.site.item_namespace.id == ns:
                self._namespace = self.site.item_namespace
            elif self.site.property_namespace.id == ns:
                self._namespace = self.site.property_namespace
            else:
                raise ValueError('{!r}: Namespace "{!r}" is not valid'
                                 .format(self.site, ns))

        WikibaseEntity.__init__(
            self,
            # .site forces a parse of the Link title to determine site
            self.site,
            # Link.__init__, called from Page.__init__, has cleaned the title
            # stripping whitespace and uppercasing the first letter according
            # to the namespace case=first-letter.
            self._link.title)

    def namespace(self) -> int:
        """
        Return the number of the namespace of the entity.

        :return: Namespace id
        """
        return self._namespace.id

    def exists(self) -> bool:
        """Determine if an entity exists in the data repository."""
        if not hasattr(self, '_content'):
            try:
                self.get(get_redirect=True)
                return True
            except NoPageError:
                return False
        return 'missing' not in self._content

    def botMayEdit(self) -> bool:
        """
        Return whether bots may edit this page.

        Because there is currently no system to mark a page that it shouldn't
        be edited by bots on Wikibase pages it always returns True. The content
        of the page is not text but a dict, the original way (to search for a
        template) doesn't apply.

        :return: True
        """
        return True

    def get(self, force: bool = False, *args, **kwargs) -> dict:
        """
        Fetch all page data, and cache it.

        :param force: override caching
        :raise NotImplementedError: a value in args or kwargs
        :return: actual data which entity holds
        :note: dicts returned by this method are references to content
            of this entity and their modifying may indirectly cause
            unwanted change to the live content
        """
        if args or kwargs:
            raise NotImplementedError(
                '{}.get does not implement var args: {!r} and {!r}'.format(
                    self.__class__.__name__, args, kwargs))

        # todo: this variable is specific to ItemPage
        lazy_loading_id = not hasattr(self, 'id') and hasattr(self, '_site')
        try:
            data = WikibaseEntity.get(self, force=force)
        except NoWikibaseEntityError:
            if lazy_loading_id:
                p = Page(self._site, self._title)
                if not p.exists():
                    raise NoPageError(p)
                # todo: raise a nicer exception here (T87345)
            raise NoPageError(self)

        if 'pageid' in self._content:
            self._pageid = self._content['pageid']

        # xxx: this is ugly
        if 'claims' in data:
            self.claims.set_on_item(self)

        return data

    @property
    def latest_revision_id(self) -> int:
        """
        Get the revision identifier for the most recent revision of the entity.

        :rtype: int
        :raise pywikibot.exceptions.NoPageError: if the entity doesn't exist
        """
        if not hasattr(self, '_revid'):
            self.get()
        return self._revid

    @latest_revision_id.setter
    def latest_revision_id(self, value):
        self._revid = value

    @latest_revision_id.deleter
    def latest_revision_id(self):
        # fixme: this seems too destructive in comparison to the parent
        self.clear_cache()

    @allow_asynchronous
    def editEntity(self, data=None, **kwargs):
        """
        Edit an entity using Wikibase wbeditentity API.

        This function is wrapped around by:
         - editLabels
         - editDescriptions
         - editAliases
         - ItemPage.setSitelinks

        :param data: Data to be saved
        :type data: dict, or None to save the current content of the entity.
        :keyword asynchronous: if True, launch a separate thread to edit
            asynchronously
        :type asynchronous: bool
        :keyword callback: a callable object that will be called after the
            entity has been updated. It must take two arguments: (1) a
            WikibasePage object, and (2) an exception instance, which will be
            None if the page was saved successfully. This is intended for use
            by bots that need to keep track of which saves were successful.
        :type callback: callable
        """
        # kept for the decorator
        super().editEntity(data, **kwargs)

    def editLabels(self, labels, **kwargs):
        """
        Edit entity labels.

        Labels should be a dict, with the key
        as a language or a site object. The
        value should be the string to set it to.
        You can set it to '' to remove the label.
        """
        data = {'labels': labels}
        self.editEntity(data, **kwargs)

    def editDescriptions(self, descriptions, **kwargs):
        """
        Edit entity descriptions.

        Descriptions should be a dict, with the key
        as a language or a site object. The
        value should be the string to set it to.
        You can set it to '' to remove the description.
        """
        data = {'descriptions': descriptions}
        self.editEntity(data, **kwargs)

    def editAliases(self, aliases, **kwargs):
        """
        Edit entity aliases.

        Aliases should be a dict, with the key
        as a language or a site object. The
        value should be a list of strings.
        """
        data = {'aliases': aliases}
        self.editEntity(data, **kwargs)

    def set_redirect_target(self, target_page, create=False, force=False,
                            keep_section=False, save=True, **kwargs):
        """
        Set target of a redirect for a Wikibase page.

        Has not been implemented in the Wikibase API yet, except for ItemPage.
        """
        raise NotImplementedError

    @allow_asynchronous
    def addClaim(self, claim, bot=True, **kwargs):
        """
        Add a claim to the entity.

        :param claim: The claim to add
        :type claim: pywikibot.page.Claim
        :param bot: Whether to flag as bot (if possible)
        :type bot: bool
        :keyword asynchronous: if True, launch a separate thread to add claim
            asynchronously
        :type asynchronous: bool
        :keyword callback: a callable object that will be called after the
            claim has been added. It must take two arguments:
            (1) a WikibasePage object, and (2) an exception instance,
            which will be None if the entity was saved successfully. This is
            intended for use by bots that need to keep track of which saves
            were successful.
        :type callback: callable
        """
        if claim.on_item is not None:
            raise ValueError(
                'The provided Claim instance is already used in an entity')
        self.repo.addClaim(self, claim, bot=bot, **kwargs)
        claim.on_item = self

    def removeClaims(self, claims, **kwargs):
        """
        Remove the claims from the entity.

        :param claims: list of claims to be removed
        :type claims: list or pywikibot.Claim
        """
        # this check allows single claims to be removed by pushing them into a
        # list of length one.
        if isinstance(claims, pywikibot.Claim):
            claims = [claims]
        data = self.repo.removeClaims(claims, **kwargs)
        for claim in claims:
            claim.on_item.latest_revision_id = data['pageinfo']['lastrevid']
            claim.on_item = None
            claim.snak = None


class ItemPage(WikibasePage):

    """
    Wikibase entity of type 'item'.

    A Wikibase item may be defined by either a 'Q' id (qid),
    or by a site & title.

    If an item is defined by site & title, once an item's qid has
    been looked up, the item is then defined by the qid.
    """

    _cache_attrs = WikibasePage._cache_attrs + (
        'labels', 'descriptions', 'aliases', 'claims', 'sitelinks')
    entity_type = 'item'
    title_pattern = r'Q[1-9]\d*'
    DATA_ATTRIBUTES = {
        'labels': LanguageDict,
        'descriptions': LanguageDict,
        'aliases': AliasesDict,
        'claims': ClaimCollection,
        'sitelinks': SiteLinkCollection,
    }

    def __init__(self, site, title=None, ns=None):
        """
        Initializer.

        :param site: data repository
        :type site: pywikibot.site.DataSite
        :param title: identifier of item, "Q###",
                      -1 or None for an empty item.
        :type title: str
        :type ns: namespace
        :type ns: Namespace instance, or int, or None
            for default item_namespace
        """
        if ns is None:
            ns = site.item_namespace
        # Special case for empty item.
        if title is None or title == '-1':
            super().__init__(site, '-1', ns=ns)
            assert self.id == '-1'
            return

        # we don't want empty titles
        if not title:
            raise InvalidTitleError("Item's title cannot be empty")

        super().__init__(site, title, ns=ns)

        assert self.id == self._link.title

    def _defined_by(self, singular: bool = False) -> dict:
        """
        Internal function to provide the API parameters to identify the item.

        The API parameters may be 'id' if the ItemPage has one,
        or 'site'&'title' if instantiated via ItemPage.fromPage with
        lazy_load enabled.

        Once an item's Q## is looked up, that will be used for all future
        requests.

        An empty dict is returned if the ItemPage is instantiated without
        either ID (internally it has id = '-1') or site&title.

        :param singular: Whether the parameter names should use the
            singular form
        :return: API parameters
        """
        params = {}
        if singular:
            id = 'id'
            site = 'site'
            title = 'title'
        else:
            id = 'ids'
            site = 'sites'
            title = 'titles'

        lazy_loading_id = not hasattr(self, 'id') and hasattr(self, '_site')

        # id overrides all
        if hasattr(self, 'id'):
            if self.id != '-1':
                params[id] = self.id
        elif lazy_loading_id:
            params[site] = self._site.dbName()
            params[title] = self._title
        else:
            # if none of the above applies, this item is in an invalid state
            # which needs to be raise as an exception, but also logged in case
            # an exception handler is catching the generic Error.
            pywikibot.error('{} is in invalid state'
                            .format(self.__class__.__name__))
            raise Error('{} is in invalid state'
                        .format(self.__class__.__name__))

        return params

    def title(self, **kwargs):
        """
        Return ID as title of the ItemPage.

        If the ItemPage was lazy-loaded via ItemPage.fromPage, this method
        will fetch the Wikibase item ID for the page, potentially raising
        NoPageError with the page on the linked wiki if it does not exist, or
        does not have a corresponding Wikibase item ID.

        This method also refreshes the title if the id property was set.
        i.e. item.id = 'Q60'

        All optional keyword parameters are passed to the superclass.
        """
        # If instantiated via ItemPage.fromPage using site and title,
        # _site and _title exist, and id does not exist.
        lazy_loading_id = not hasattr(self, 'id') and hasattr(self, '_site')

        if lazy_loading_id or self._link._text != self.id:
            # If the item is lazy loaded or has been modified,
            # _link._text is stale. Removing _link._title
            # forces Link to re-parse ._text into ._title.
            if hasattr(self._link, '_title'):
                del self._link._title
            self._link._text = self.getID()
            self._link.parse()
            # Remove the temporary values that are no longer needed after
            # the .getID() above has called .get(), which populated .id
            if hasattr(self, '_site'):
                del self._title
                del self._site

        return super().title(**kwargs)

    def getID(self, numeric=False, force=False):
        """
        Get the entity identifier.

        :param numeric: Strip the first letter and return an int
        :type numeric: bool
        :param force: Force an update of new data
        :type force: bool
        """
        if not hasattr(self, 'id') or force:
            self.get(force=force)
        return super().getID(numeric=numeric)

    @classmethod
    def fromPage(cls, page, lazy_load=False):
        """
        Get the ItemPage for a Page that links to it.

        :param page: Page to look for corresponding data item
        :type page: pywikibot.page.Page
        :param lazy_load: Do not raise NoPageError if either page or
            corresponding ItemPage does not exist.
        :type lazy_load: bool
        :rtype: pywikibot.page.ItemPage

        :raise pywikibot.exceptions.NoPageError: There is no corresponding
            ItemPage for the page
        :raise pywikibot.exceptions.WikiBaseError: The site of the page
            has no data repository.
        """
        if hasattr(page, '_item'):
            return page._item
        if not page.site.has_data_repository:
            raise WikiBaseError('{} has no data repository'
                                .format(page.site))
        if not lazy_load and not page.exists():
            raise NoPageError(page)

        repo = page.site.data_repository()
        if hasattr(page,
                   '_pageprops') and page.properties().get('wikibase_item'):
            # If we have already fetched the pageprops for something else,
            # we already have the id, so use it
            page._item = cls(repo, page.properties().get('wikibase_item'))
            return page._item
        i = cls(repo)
        # clear id, and temporarily store data needed to lazy loading the item
        del i.id
        i._site = page.site
        i._title = page.title(with_section=False)
        if not lazy_load and not i.exists():
            raise NoPageError(i)
        page._item = i
        return page._item

    @classmethod
    def from_entity_uri(cls, site, uri: str, lazy_load: bool = False):
        """
        Get the ItemPage from its entity uri.

        :param site: The Wikibase site for the item.
        :type site: pywikibot.site.DataSite
        :param uri: Entity uri for the Wikibase item.
        :param lazy_load: Do not raise NoPageError if ItemPage does not exist.
        :rtype: pywikibot.page.ItemPage

        :raise TypeError: Site is not a valid DataSite.
        :raise ValueError: Site does not match the base of the provided uri.
        :raise pywikibot.exceptions.NoPageError: Uri points to non-existent
            item.
        """
        if not isinstance(site, DataSite):
            raise TypeError('{} is not a data repository.'.format(site))

        base_uri, _, qid = uri.rpartition('/')
        if base_uri != site.concept_base_uri.rstrip('/'):
            raise ValueError(
                'The supplied data repository ({repo}) does not correspond to '
                'that of the item ({item})'.format(
                    repo=site.concept_base_uri.rstrip('/'),
                    item=base_uri))

        item = cls(site, qid)
        if not lazy_load and not item.exists():
            raise NoPageError(item)

        return item

    def get(self, force=False, get_redirect=False, *args, **kwargs) -> dict:
        """
        Fetch all item data, and cache it.

        :param force: override caching
        :type force: bool
        :param get_redirect: return the item content, do not follow the
                             redirect, do not raise an exception.
        :type get_redirect: bool
        :raise NotImplementedError: a value in args or kwargs
        :return: actual data which entity holds
        :note: dicts returned by this method are references to content of this
            entity and their modifying may indirectly cause unwanted change to
            the live content
        """
        data = super().get(force, *args, **kwargs)

        if self.isRedirectPage() and not get_redirect:
            raise IsRedirectPageError(self)

        return data

    def getRedirectTarget(self):
        """Return the redirect target for this page."""
        target = super().getRedirectTarget()
        cmodel = target.content_model
        if cmodel != 'wikibase-item':
            raise Error('{} has redirect target {} with content model {} '
                        'instead of wikibase-item'
                        .format(self, target, cmodel))
        return self.__class__(target.site, target.title(), target.namespace())

    def iterlinks(self, family=None):
        """
        Iterate through all the sitelinks.

        :param family: string/Family object which represents what family of
                       links to iterate
        :type family: str|pywikibot.family.Family
        :return: iterator of pywikibot.Page objects
        :rtype: iterator
        """
        if not hasattr(self, 'sitelinks'):
            self.get()
        if family is not None and not isinstance(family, Family):
            family = Family.load(family)
        for sl in self.sitelinks.values():
            if family is None or family == sl.site.family:
                pg = pywikibot.Page(sl)
                pg._item = self
                yield pg

    def getSitelink(self, site, force=False) -> str:
        """
        Return the title for the specific site.

        If the item doesn't have that language, raise NoPageError.

        :param site: Site to find the linked page of.
        :type site: pywikibot.Site or database name
        :param force: override caching
        """
        if force or not hasattr(self, '_content'):
            self.get(force=force)

        if site not in self.sitelinks:
            raise NoPageError(self)

        return self.sitelinks[site].canonical_title()

    def setSitelink(self, sitelink, **kwargs):
        """
        Set sitelinks. Calls setSitelinks().

        A sitelink can be a Page object, a BaseLink object
        or a {'site':dbname,'title':title} dictionary.
        """
        self.setSitelinks([sitelink], **kwargs)

    def removeSitelink(self, site, **kwargs):
        """
        Remove a sitelink.

        A site can either be a Site object, or it can be a dbName.
        """
        self.removeSitelinks([site], **kwargs)

    def removeSitelinks(self, sites, **kwargs):
        """
        Remove sitelinks.

        Sites should be a list, with values either
        being Site objects, or dbNames.
        """
        data = []
        for site in sites:
            site = SiteLinkCollection.getdbName(site)
            data.append({'site': site, 'title': ''})
        self.setSitelinks(data, **kwargs)

    def setSitelinks(self, sitelinks, **kwargs):
        """
        Set sitelinks.

        Sitelinks should be a list. Each item in the
        list can either be a Page object, a BaseLink object, or a dict
        with a value for 'site' and 'title'.
        """
        data = {'sitelinks': sitelinks}
        self.editEntity(data, **kwargs)

    def mergeInto(self, item, **kwargs):
        """
        Merge the item into another item.

        :param item: The item to merge into
        :type item: pywikibot.page.ItemPage
        """
        data = self.repo.mergeItems(from_item=self, to_item=item, **kwargs)
        if not data.get('success', 0):
            return
        self.latest_revision_id = data['from']['lastrevid']
        item.latest_revision_id = data['to']['lastrevid']
        if data.get('redirected', 0):
            self._isredir = True
            self._redirtarget = item

    def set_redirect_target(self, target_page, create=False, force=False,
                            keep_section=False, save=True, **kwargs):
        """
        Make the item redirect to another item.

        You need to define an extra argument to make this work, like save=True

        :param target_page: target of the redirect, this argument is required.
        :type target_page: pywikibot.page.ItemPage or string
        :param force: if true, it sets the redirect target even the page
            is not redirect.
        :type force: bool
        """
        if isinstance(target_page, str):
            target_page = pywikibot.ItemPage(self.repo, target_page)
        elif self.repo != target_page.repo:
            raise InterwikiRedirectPageError(self, target_page)
        if self.exists() and not self.isRedirectPage() and not force:
            raise IsNotRedirectPageError(self)
        if not save or keep_section or create:
            raise NotImplementedError
        data = self.repo.set_redirect_target(
            from_item=self, to_item=target_page,
            bot=kwargs.get('botflag', True))
        if data.get('success', 0):
            del self.latest_revision_id
            self._isredir = True
            self._redirtarget = target_page

    def isRedirectPage(self):
        """Return True if item is a redirect, False if not or not existing."""
        if hasattr(self, '_content') and not hasattr(self, '_isredir'):
            self._isredir = self.id != self._content.get('id', self.id)
            return self._isredir
        return super().isRedirectPage()


# alias for backwards compatibility
ItemPage.concept_url = redirect_func(
    ItemPage.concept_uri, old_name='concept_url', class_name='ItemPage',
    since='20170222')


class Property:

    """
    A Wikibase property.

    While every Wikibase property has a Page on the data repository,
    this object is for when the property is used as part of another concept
    where the property is not _the_ Page of the property.

    For example, a claim on an ItemPage has many property attributes, and so
    it subclasses this Property class, but a claim does not have Page like
    behaviour and semantics.
    """

    types = {'wikibase-item': ItemPage,
             # 'wikibase-property': PropertyPage, must be declared first
             'string': str,
             'commonsMedia': FilePage,
             'globe-coordinate': pywikibot.Coordinate,
             'url': str,
             'time': pywikibot.WbTime,
             'quantity': pywikibot.WbQuantity,
             'monolingualtext': pywikibot.WbMonolingualText,
             'math': str,
             'external-id': str,
             'geo-shape': pywikibot.WbGeoShape,
             'tabular-data': pywikibot.WbTabularData,
             'musical-notation': str,
             }

    # the value type where different from the type
    value_types = {'wikibase-item': 'wikibase-entityid',
                   'wikibase-property': 'wikibase-entityid',
                   'commonsMedia': 'string',
                   'url': 'string',
                   'globe-coordinate': 'globecoordinate',
                   'math': 'string',
                   'external-id': 'string',
                   'geo-shape': 'string',
                   'tabular-data': 'string',
                   'musical-notation': 'string',
                   }

    def __init__(self, site, id: str, datatype: Optional[str] = None):
        """
        Initializer.

        :param site: data repository
        :type site: pywikibot.site.DataSite
        :param id: id of the property
        :param datatype: datatype of the property;
            if not given, it will be queried via the API
        """
        self.repo = site
        self.id = id.upper()
        if datatype:
            self._type = datatype

    @property
    def type(self) -> str:
        """Return the type of this property."""
        if not hasattr(self, '_type'):
            self._type = self.repo.getPropertyType(self)
        return self._type

    def getID(self, numeric=False):
        """
        Get the identifier of this property.

        :param numeric: Strip the first letter and return an int
        :type numeric: bool
        """
        if numeric:
            return int(self.id[1:])
        return self.id


class PropertyPage(WikibasePage, Property):

    """
    A Wikibase entity in the property namespace.

    Should be created as::

        PropertyPage(DataSite, 'P21')

    or::

        PropertyPage(DataSite, datatype='url')
    """

    _cache_attrs = WikibasePage._cache_attrs + (
        '_type', 'labels', 'descriptions', 'aliases', 'claims')
    entity_type = 'property'
    title_pattern = r'P[1-9]\d*'
    DATA_ATTRIBUTES = {
        'labels': LanguageDict,
        'descriptions': LanguageDict,
        'aliases': AliasesDict,
        'claims': ClaimCollection,
    }

    def __init__(self, source, title=None, datatype=None):
        """
        Initializer.

        :param source: data repository property is on
        :type source: pywikibot.site.DataSite
        :param title: identifier of property, like "P##",
                      "-1" or None for an empty property.
        :type title: str
        :param datatype: Datatype for a new property.
        :type datatype: str
        """
        # Special case for new property.
        if title is None or title == '-1':
            if not datatype:
                raise TypeError('"datatype" is required for new property.')
            WikibasePage.__init__(self, source, '-1',
                                  ns=source.property_namespace)
            Property.__init__(self, source, '-1', datatype=datatype)
            assert self.id == '-1'
        else:
            if not title:
                raise InvalidTitleError(
                    "Property's title cannot be empty")

            WikibasePage.__init__(self, source, title,
                                  ns=source.property_namespace)
            Property.__init__(self, source, self.id)

    def get(self, force: bool = False, *args, **kwargs) -> dict:
        """
        Fetch the property entity, and cache it.

        :param force: override caching
        :raise NotImplementedError: a value in args or kwargs
        :return: actual data which entity holds
        :note: dicts returned by this method are references to content of this
            entity and their modifying may indirectly cause unwanted change to
            the live content
        """
        if args or kwargs:
            raise NotImplementedError(
                'PropertyPage.get only implements "force".')

        data = WikibasePage.get(self, force)
        if 'datatype' in self._content:
            self._type = self._content['datatype']
        data['datatype'] = self._type
        return data

    def newClaim(self, *args, **kwargs):
        """
        Helper function to create a new claim object for this property.

        :rtype: pywikibot.page.Claim
        """
        # todo: raise when self.id is -1
        return Claim(self.site, self.getID(), datatype=self.type,
                     *args, **kwargs)

    def getID(self, numeric=False):
        """
        Get the identifier of this property.

        :param numeric: Strip the first letter and return an int
        :type numeric: bool
        """
        # enforce this parent's implementation
        return WikibasePage.getID(self, numeric=numeric)

    def get_data_for_new_entity(self):
        """Return data required for creation of new property."""
        return {'datatype': self.type}


# Add PropertyPage to the class attribute "types" after its declaration.
Property.types['wikibase-property'] = PropertyPage


class Claim(Property):

    """
    A Claim on a Wikibase entity.

    Claims are standard claims as well as references and qualifiers.
    """

    TARGET_CONVERTER = {
        'wikibase-item': lambda value, site:
            ItemPage(site, 'Q' + str(value['numeric-id'])),
        'wikibase-property': lambda value, site:
            PropertyPage(site, 'P' + str(value['numeric-id'])),
        'commonsMedia': lambda value, site:
            FilePage(pywikibot.Site('commons', 'commons'), value),  # T90492
        'globe-coordinate': pywikibot.Coordinate.fromWikibase,
        'geo-shape': pywikibot.WbGeoShape.fromWikibase,
        'tabular-data': pywikibot.WbTabularData.fromWikibase,
        'time': pywikibot.WbTime.fromWikibase,
        'quantity': pywikibot.WbQuantity.fromWikibase,
        'monolingualtext': lambda value, site:
            pywikibot.WbMonolingualText.fromWikibase(value)
    }

    SNAK_TYPES = ('value', 'somevalue', 'novalue')

    @deprecated_args(isReference='is_reference', isQualifier='is_qualifier')
    def __init__(self, site, pid, snak=None, hash=None, is_reference=False,
                 is_qualifier=False, rank='normal', **kwargs):
        """
        Initializer.

        Defined by the "snak" value, supplemented by site + pid

        :param site: repository the claim is on
        :type site: pywikibot.site.DataSite
        :param pid: property id, with "P" prefix
        :param snak: snak identifier for claim
        :param hash: hash identifier for references
        :param is_reference: whether specified claim is a reference
        :param is_qualifier: whether specified claim is a qualifier
        :param rank: rank for claim
        """
        Property.__init__(self, site, pid, **kwargs)
        self.snak = snak
        self.hash = hash
        self.rank = rank
        self.isReference = is_reference
        self.isQualifier = is_qualifier
        if self.isQualifier and self.isReference:
            raise ValueError('Claim cannot be both a qualifier and reference.')
        self.sources = []
        self.qualifiers = OrderedDict()
        self.target = None
        self.snaktype = 'value'
        self._on_item = None  # The item it's on

    @property
    def on_item(self):
        """Return item this claim is attached to."""
        return self._on_item

    @on_item.setter
    def on_item(self, item):
        self._on_item = item
        for values in self.qualifiers.values():
            for qualifier in values:
                qualifier.on_item = item
        for source in self.sources:
            for values in source.values():
                for source in values:
                    source.on_item = item

    def __repr__(self):
        """Return the representation string."""
        return '{cls_name}.fromJSON({}, {})'.format(
            repr(self.repo), self.toJSON(), cls_name=type(self).__name__)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False

        return self.same_as(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    @staticmethod
    def _claim_mapping_same(this, other):
        if len(this) != len(other):
            return False
        my_values = list(chain.from_iterable(this.values()))
        other_values = list(chain.from_iterable(other.values()))
        if len(my_values) != len(other_values):
            return False
        for val in my_values:
            if val not in other_values:
                return False
        for val in other_values:
            if val not in my_values:
                return False
        return True

    def same_as(self, other, ignore_rank=True, ignore_quals=False,
                ignore_refs=True):
        """Check if two claims are same."""
        if ignore_rank:
            attributes = ['id', 'snaktype', 'target']
        else:
            attributes = ['id', 'snaktype', 'rank', 'target']
        for attr in attributes:
            if getattr(self, attr) != getattr(other, attr):
                return False

        if not ignore_quals:
            if not self._claim_mapping_same(self.qualifiers, other.qualifiers):
                return False

        if not ignore_refs:
            if len(self.sources) != len(other.sources):
                return False
            for source in self.sources:
                same = False
                for other_source in other.sources:
                    if self._claim_mapping_same(source, other_source):
                        same = True
                        break
                if not same:
                    return False

        return True

    def copy(self):
        """
        Create an independent copy of this object.

        :rtype: pywikibot.page.Claim
        """
        is_qualifier = self.isQualifier
        is_reference = self.isReference
        self.isQualifier = False
        self.isReference = False
        copy = self.fromJSON(self.repo, self.toJSON())
        for cl in (self, copy):
            cl.isQualifier = is_qualifier
            cl.isReference = is_reference
        copy.hash = None
        copy.snak = None
        return copy

    @classmethod
    def fromJSON(cls, site, data):
        """
        Create a claim object from JSON returned in the API call.

        :param data: JSON containing claim data
        :type data: dict

        :rtype: pywikibot.page.Claim
        """
        claim = cls(site, data['mainsnak']['property'],
                    datatype=data['mainsnak'].get('datatype', None))
        if 'id' in data:
            claim.snak = data['id']
        elif 'hash' in data:
            claim.hash = data['hash']
        claim.snaktype = data['mainsnak']['snaktype']
        if claim.getSnakType() == 'value':
            value = data['mainsnak']['datavalue']['value']
            # The default covers string, url types
            if claim.type in cls.types or claim.type == 'wikibase-property':
                claim.target = cls.TARGET_CONVERTER.get(
                    claim.type, lambda value, site: value)(value, site)
            else:
                pywikibot.warning(
                    '{} datatype is not supported yet.'.format(claim.type))
                claim.target = pywikibot.WbUnknown.fromWikibase(value)
        if 'rank' in data:  # References/Qualifiers don't have ranks
            claim.rank = data['rank']
        if 'references' in data:
            for source in data['references']:
                claim.sources.append(cls.referenceFromJSON(site, source))
        if 'qualifiers' in data:
            for prop in data['qualifiers-order']:
                claim.qualifiers[prop] = [
                    cls.qualifierFromJSON(site, qualifier)
                    for qualifier in data['qualifiers'][prop]]
        return claim

    @classmethod
    def referenceFromJSON(cls, site, data) -> dict:
        """
        Create a dict of claims from reference JSON returned in the API call.

        Reference objects are represented a bit differently, and require
        some more handling.
        """
        source = OrderedDict()

        # Before #84516 Wikibase did not implement snaks-order.
        # https://gerrit.wikimedia.org/r/c/84516/
        if 'snaks-order' in data:
            prop_list = data['snaks-order']
        else:
            prop_list = data['snaks'].keys()

        for prop in prop_list:
            for claimsnak in data['snaks'][prop]:
                claim = cls.fromJSON(site, {'mainsnak': claimsnak,
                                            'hash': data.get('hash')})
                claim.isReference = True
                if claim.getID() not in source:
                    source[claim.getID()] = []
                source[claim.getID()].append(claim)
        return source

    @classmethod
    def qualifierFromJSON(cls, site, data):
        """
        Create a Claim for a qualifier from JSON.

        Qualifier objects are represented a bit
        differently like references, but I'm not
        sure if this even requires it's own function.

        :rtype: pywikibot.page.Claim
        """
        claim = cls.fromJSON(site, {'mainsnak': data,
                                    'hash': data.get('hash')})
        claim.isQualifier = True
        return claim

    def toJSON(self) -> dict:
        """Create dict suitable for the MediaWiki API."""
        data = {
            'mainsnak': {
                'snaktype': self.snaktype,
                'property': self.getID()
            },
            'type': 'statement'
        }
        if hasattr(self, 'snak') and self.snak is not None:
            data['id'] = self.snak
        if hasattr(self, 'rank') and self.rank is not None:
            data['rank'] = self.rank
        if self.getSnakType() == 'value':
            data['mainsnak']['datatype'] = self.type
            data['mainsnak']['datavalue'] = self._formatDataValue()
        if self.isQualifier or self.isReference:
            data = data['mainsnak']
            if hasattr(self, 'hash') and self.hash is not None:
                data['hash'] = self.hash
        else:
            if self.qualifiers:
                data['qualifiers'] = {}
                data['qualifiers-order'] = list(self.qualifiers.keys())
                for prop, qualifiers in self.qualifiers.items():
                    for qualifier in qualifiers:
                        assert qualifier.isQualifier is True
                    data['qualifiers'][prop] = [
                        qualifier.toJSON() for qualifier in qualifiers]

            if self.sources:
                data['references'] = []
                for collection in self.sources:
                    reference = {
                        'snaks': {}, 'snaks-order': list(collection.keys())}
                    for prop, val in collection.items():
                        reference['snaks'][prop] = []
                        for source in val:
                            assert source.isReference is True
                            src_data = source.toJSON()
                            if 'hash' in src_data:
                                reference.setdefault('hash', src_data['hash'])
                                del src_data['hash']
                            reference['snaks'][prop].append(src_data)
                    data['references'].append(reference)
        return data

    def setTarget(self, value):
        """
        Set the target value in the local object.

        :param value: The new target value.
        :type value: object

        :exception ValueError: if value is not of the type
            required for the Claim type.
        """
        value_class = self.types[self.type]
        if not isinstance(value, value_class):
            raise ValueError('{} is not type {}.'
                             .format(value, value_class))
        self.target = value

    def changeTarget(self, value=None, snaktype='value', **kwargs):
        """
        Set the target value in the data repository.

        :param value: The new target value.
        :type value: object
        :param snaktype: The new snak type.
        :type snaktype: str ('value', 'somevalue', or 'novalue')
        """
        if value:
            self.setTarget(value)

        data = self.repo.changeClaimTarget(self, snaktype=snaktype,
                                           **kwargs)
        # TODO: Re-create the entire item from JSON, not just id
        self.snak = data['claim']['id']
        self.on_item.latest_revision_id = data['pageinfo']['lastrevid']

    def getTarget(self):
        """
        Return the target value of this Claim.

        None is returned if no target is set

        :return: object
        """
        return self.target

    def getSnakType(self) -> str:
        """
        Return the type of snak.

        :return: str ('value', 'somevalue' or 'novalue')
        """
        return self.snaktype

    def setSnakType(self, value):
        """
        Set the type of snak.

        :param value: Type of snak
        :type value: str ('value', 'somevalue', or 'novalue')
        """
        if value in self.SNAK_TYPES:
            self.snaktype = value
        else:
            raise ValueError(
                "snaktype must be 'value', 'somevalue', or 'novalue'.")

    def getRank(self):
        """Return the rank of the Claim."""
        return self.rank

    def setRank(self, rank):
        """Set the rank of the Claim."""
        self.rank = rank

    def changeRank(self, rank, **kwargs):
        """Change the rank of the Claim and save."""
        self.rank = rank
        return self.repo.save_claim(self, **kwargs)

    def changeSnakType(self, value=None, **kwargs):
        """
        Save the new snak value.

        TODO: Is this function really needed?
        """
        if value:
            self.setSnakType(value)
        self.changeTarget(snaktype=self.getSnakType(), **kwargs)

    def getSources(self) -> list:
        """Return a list of sources, each being a list of Claims."""
        return self.sources

    def addSource(self, claim, **kwargs):
        """
        Add the claim as a source.

        :param claim: the claim to add
        :type claim: pywikibot.Claim
        """
        self.addSources([claim], **kwargs)

    def addSources(self, claims, **kwargs):
        """
        Add the claims as one source.

        :param claims: the claims to add
        :type claims: list of pywikibot.Claim
        """
        for claim in claims:
            if claim.on_item is not None:
                raise ValueError(
                    'The provided Claim instance is already used in an entity')
        if self.on_item is not None:
            data = self.repo.editSource(self, claims, new=True, **kwargs)
            self.on_item.latest_revision_id = data['pageinfo']['lastrevid']
            for claim in claims:
                claim.hash = data['reference']['hash']
                claim.on_item = self.on_item
        source = defaultdict(list)
        for claim in claims:
            claim.isReference = True
            source[claim.getID()].append(claim)
        self.sources.append(source)

    def removeSource(self, source, **kwargs):
        """
        Remove the source. Call removeSources().

        :param source: the source to remove
        :type source: pywikibot.Claim
        """
        self.removeSources([source], **kwargs)

    def removeSources(self, sources, **kwargs):
        """
        Remove the sources.

        :param sources: the sources to remove
        :type sources: list of pywikibot.Claim
        """
        data = self.repo.removeSources(self, sources, **kwargs)
        self.on_item.latest_revision_id = data['pageinfo']['lastrevid']
        for source in sources:
            source_dict = defaultdict(list)
            source_dict[source.getID()].append(source)
            self.sources.remove(source_dict)

    def addQualifier(self, qualifier, **kwargs):
        """Add the given qualifier.

        :param qualifier: the qualifier to add
        :type qualifier: pywikibot.page.Claim
        """
        if qualifier.on_item is not None:
            raise ValueError(
                'The provided Claim instance is already used in an entity')
        if self.on_item is not None:
            data = self.repo.editQualifier(self, qualifier, **kwargs)
            self.on_item.latest_revision_id = data['pageinfo']['lastrevid']
            qualifier.on_item = self.on_item
        qualifier.isQualifier = True
        if qualifier.getID() in self.qualifiers:
            self.qualifiers[qualifier.getID()].append(qualifier)
        else:
            self.qualifiers[qualifier.getID()] = [qualifier]

    def removeQualifier(self, qualifier, **kwargs):
        """
        Remove the qualifier. Call removeQualifiers().

        :param qualifier: the qualifier to remove
        :type qualifier: pywikibot.page.Claim
        """
        self.removeQualifiers([qualifier], **kwargs)

    def removeQualifiers(self, qualifiers, **kwargs):
        """
        Remove the qualifiers.

        :param qualifiers: the qualifiers to remove
        :type qualifiers: list Claim
        """
        data = self.repo.remove_qualifiers(self, qualifiers, **kwargs)
        self.on_item.latest_revision_id = data['pageinfo']['lastrevid']
        for qualifier in qualifiers:
            self.qualifiers[qualifier.getID()].remove(qualifier)
            qualifier.on_item = None

    def target_equals(self, value) -> bool:
        """
        Check whether the Claim's target is equal to specified value.

        The function checks for:

        - WikibasePage ID equality
        - WbTime year equality
        - Coordinate equality, regarding precision
        - WbMonolingualText text equality
        - direct equality

        :param value: the value to compare with
        :return: true if the Claim's target is equal to the value provided,
            false otherwise
        """
        if (isinstance(self.target, WikibasePage)
                and isinstance(value, str)):
            return self.target.id == value

        if (isinstance(self.target, pywikibot.WbTime)
                and not isinstance(value, pywikibot.WbTime)):
            return self.target.year == int(value)

        if (isinstance(self.target, pywikibot.Coordinate)
                and isinstance(value, str)):
            coord_args = [float(x) for x in value.split(',')]
            if len(coord_args) >= 3:
                precision = coord_args[2]
            else:
                precision = 0.0001  # Default value (~10 m at equator)
            with suppress(TypeError):
                if self.target.precision is not None:
                    precision = max(precision, self.target.precision)

            return (abs(self.target.lat - coord_args[0]) <= precision
                    and abs(self.target.lon - coord_args[1]) <= precision)

        if (isinstance(self.target, pywikibot.WbMonolingualText)
                and isinstance(value, str)):
            return self.target.text == value

        return self.target == value

    def has_qualifier(self, qualifier_id: str, target) -> bool:
        """
        Check whether Claim contains specified qualifier.

        :param qualifier_id: id of the qualifier
        :param target: qualifier target to check presence of
        :return: true if the qualifier was found, false otherwise
        """
        if self.isQualifier or self.isReference:
            raise ValueError('Qualifiers and references cannot have '
                             'qualifiers.')

        for qualifier in self.qualifiers.get(qualifier_id, []):
            if qualifier.target_equals(target):
                return True
        return False

    def _formatValue(self) -> dict:
        """
        Format the target into the proper JSON value that Wikibase wants.

        :return: JSON value
        """
        if self.type in ('wikibase-item', 'wikibase-property'):
            value = {'entity-type': self.getTarget().entity_type,
                     'numeric-id': self.getTarget().getID(numeric=True)}
        elif self.type in ('string', 'url', 'math', 'external-id',
                           'musical-notation'):
            value = self.getTarget()
        elif self.type == 'commonsMedia':
            value = self.getTarget().title(with_ns=False)
        elif self.type in ('globe-coordinate', 'time',
                           'quantity', 'monolingualtext',
                           'geo-shape', 'tabular-data'):
            value = self.getTarget().toWikibase()
        else:  # WbUnknown
            pywikibot.warning(
                '{} datatype is not supported yet.'.format(self.type))
            value = self.getTarget().toWikibase()
        return value

    def _formatDataValue(self) -> dict:
        """
        Format the target into the proper JSON datavalue that Wikibase wants.

        :return: Wikibase API representation with type and value.
        """
        return {
            'value': self._formatValue(),
            'type': self.value_types.get(self.type, self.type)
        }


class FileInfo:

    """
    A structure holding imageinfo of latest rev. of FilePage.

    All keys of API imageinfo dictionary are mapped to FileInfo attributes.
    Attributes can be retrieved both as self['key'] or self.key.

    Following attributes will be returned:
        - timestamp, user, comment, url, size, sha1, mime, metadata
        - archivename (not for latest revision)

    See Site.loadimageinfo() for details.

    Note: timestamp will be casted to pywikibot.Timestamp.
    """

    def __init__(self, file_revision):
        """Initiate the class using the dict from L{APISite.loadimageinfo}."""
        self.__dict__.update(file_revision)
        self.timestamp = pywikibot.Timestamp.fromISOformat(self.timestamp)

    def __getitem__(self, key):
        """Give access to class values by key."""
        return getattr(self, key)

    def __repr__(self):
        """Return a more complete string representation."""
        return repr(self.__dict__)

    def __eq__(self, other):
        """Test if two File_info objects are equal."""
        return self.__dict__ == other.__dict__


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

    def __init__(self, title: str, namespace=None, site=None):
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

    def __repr__(self):
        """Return a more complete string representation."""
        assert isinstance(self._items, tuple)
        assert all(isinstance(item, (bytes, str)) for item in self._items)

        attrs = ('{0!r}'.format(getattr(self, attr)) for attr in self._items)
        return 'pywikibot.page.{}({})'.format(
            self.__class__.__name__, ', '.join(attrs))

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

        :raise pywikibot.exceptions.Error: no corresponding namespace is found
            in onsite
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
                # not found
                raise Error(
                    'No corresponding namespace found for namespace {} on {}.'
                    .format(self.namespace, onsite))

        if self.namespace != Namespace.MAIN:
            return '{}:{}'.format(name, self.title)
        return self.title

    def astext(self, onsite=None):
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
    def fromPage(cls, page):
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

    @deprecated_args(defaultNamespace='default_namespace')
    def __init__(self, text, source=None, default_namespace=0):
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
        source_is_page = isinstance(source, BasePage)

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
        t = re.sub(
            '[_ \xa0\u1680\u180E\u2000-\u200A\u2028\u2029\u202F\u205F\u3000]+',
            ' ', t)
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

        if self._site.namespaces[self._namespace].case == 'first-letter':
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
    def fromPage(cls, page, source=None):
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
    def langlinkUnsafe(cls, lang, title, source):
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

    *New in version 3.0.*
    """

    # Components used for __repr__
    _items = ('_sitekey', '_rawtitle', 'badges')

    def __init__(self, title, site=None, badges=None):
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
    def fromJSON(cls, data: dict, site=None):
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

    def toJSON(self) -> dict:
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
    ignore = (set(map(lambda x: _ILLEGAL_HTML_ENTITIES_MAPPING.get(x, x),
                      ignore)) | {129, 141, 157})

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


@deprecated_args(site='encodings')
@deprecated('pywikibot.tools.chars.url2string', since='6.2.0')
def url2unicode(title: str, encodings='utf-8') -> str:
    """
    DEPRECATED. Convert URL-encoded text to unicode using several encoding.

    Uses the first encoding that doesn't cause an error.

    :param title: URL-encoded character data to convert
    :param encodings: Encodings to attempt to use during conversion.
    :type encodings: str, list or Site

    :raise UnicodeError: Could not convert using any encoding.
    """
    if isinstance(encodings, pywikibot.site.BaseSite):
        # use all possible encodings from Site object
        encodings = encodings.encodings()
        issue_deprecation_warning(
            'Passing BaseSite object to encodings parameter',
            'BaseSite.endcodings()',
            depth=1,
            since='6.2.0'
        )

    return pywikibot.tools.chars.url2string(title, encodings)


wrapper = ModuleDeprecationWrapper(__name__)
wrapper.add_deprecated_attr(
    'UnicodeToAsciiHtml',
    replacement_name='pywikibot.tools.chars.string_to_ascii_html',
    since='6.2.0')
wrapper.add_deprecated_attr(
    'unicode2html',
    replacement_name='pywikibot.tools.chars.string2html',
    since='6.2.0')
