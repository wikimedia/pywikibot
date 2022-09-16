"""Objects representing various types of MediaWiki pages.

This module includes objects:

- BasePage: Base object for a MediaWiki page
- Page: A MediaWiki page
- Category: A page in the Category: namespace

Various Wikibase pages are defined in ``page._wikibase.py``,
various pages for Proofread Extensions are defined in
``pywikibot.proofreadpage``.

.. note:: `Link` objects represent a wiki-page's title, while
   :class:`pywikibot.Page` objects (defined here) represent the page
   itself, including its contents.
"""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import itertools
import re
from collections import Counter, defaultdict
from contextlib import suppress
from itertools import islice
from textwrap import shorten, wrap
from typing import Optional, Union
from urllib.parse import quote_from_bytes
from warnings import warn

import pywikibot
from pywikibot import Timestamp, config, date, i18n, textlib
from pywikibot.backports import Generator, Iterable, Iterator, List
from pywikibot.cosmetic_changes import CANCEL, CosmeticChangesToolkit
from pywikibot.exceptions import (
    Error,
    InterwikiRedirectPageError,
    InvalidPageError,
    IsNotRedirectPageError,
    IsRedirectPageError,
    NoMoveTargetError,
    NoPageError,
    NoUsernameError,
    OtherPageSaveError,
    PageSaveRelatedError,
    SectionError,
    UnknownExtensionError,
)
from pywikibot.page._decorators import allow_asynchronous
from pywikibot.page._links import BaseLink, Link
from pywikibot.page._toolforge import WikiBlameMixin
from pywikibot.site import Namespace, NamespaceArgType
from pywikibot.tools import (
    ComparableMixin,
    cached,
    first_upper,
    issue_deprecation_warning,
    remove_last_args,
)


PROTOCOL_REGEX = r'\Ahttps?://'

__all__ = (
    'BasePage',
    'Category',
    'Page',
)


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

    def __init__(self, source, title: str = '', ns=0) -> None:
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

    def namespace(self) -> Namespace:
        """
        Return the namespace of the page.

        :return: namespace of the page
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
    @cached
    def depth(self) -> int:
        """Return the depth/subpage level of the page.

        Check if the namespace allows subpages.
        Not allowed subpages means depth is always 0.
        """
        return self.title().count('/') if self.namespace().subpages else 0

    @property
    def pageid(self) -> int:
        """
        Return pageid of the page.

        :return: pageid or 0 if page does not exist
        """
        if not hasattr(self, '_pageid'):
            self.site.loadpageinfo(self)
        return self._pageid

    def title(
        self,
        *,
        underscore: bool = False,
        with_ns: bool = True,
        with_section: bool = True,
        as_url: bool = False,
        as_link: bool = False,
        allow_interwiki: bool = True,
        force_interwiki: bool = False,
        textlink: bool = False,
        as_filename: bool = False,
        insite=None,
        without_brackets: bool = False
    ) -> str:
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
        return self.site.base_url(
            self.site.articlepath.format(self.title(as_url=True)))

    @cached
    def autoFormat(self):
        """
        Return :py:obj:`date.getAutoFormat` dictName and value, if any.

        Value can be a year, date, etc., and dictName is 'YearBC',
        'Year_December', or another dictionary name. Please note that two
        entries may have exactly the same autoFormat, but be in two
        different namespaces, as some sites have categories with the
        same names. Regular titles return (None, None).
        """
        return date.getAutoFormat(self.site.lang, self.title(with_ns=False))

    def isAutoTitle(self):
        """Return True if title of this Page is in the autoFormat dict."""
        return self.autoFormat()[0] is not None

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

    def has_content(self) -> bool:
        """
        Page has been loaded.

        Not existing pages are considered loaded.

        .. versionadded:: 7.6
        """
        return not self.exists() or self._latest_cached_revision() is not None

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

    @remove_last_args(['get_redirect'])
    def getOldVersion(self, oldid, force: bool = False) -> str:
        """Return text of an old revision of this page.

        :param oldid: The revid of the revision desired.
        """
        if force or oldid not in self._revisions \
                or self._revisions[oldid].text is None:
            self.site.loadrevisions(self, content=True, revids=oldid)
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
    def latest_revision_id(self) -> None:
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
    def latest_revision_id(self, value) -> None:
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
    def text(self) -> None:
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

    def get_parsed_page(self, force: bool = False) -> str:
        """Retrieve parsed text (via action=parse) and cache it.

        .. versionchanged:: 7.1
           `force` parameter was added;
           `_get_parsed_page` becomes a public method

        :param force: force updating from the live site

        .. seealso::
           :meth:`APISite.get_parsed_page()
           <pywikibot.site._apisite.APISite.get_parsed_page>`
        """
        if not hasattr(self, '_parsed_text') or force:
            self._parsed_text = self.site.get_parsed_page(self)
        return self._parsed_text

    def extract(self, variant: str = 'plain', *,
                lines: Optional[int] = None,
                chars: Optional[int] = None,
                sentences: Optional[int] = None,
                intro: bool = True) -> str:
        """Retrieve an extract of this page.

        .. versionadded:: 7.1

        :param variant: The variant of extract, either 'plain' for plain
            text, 'html' for limited HTML (both excludes templates and
            any text formatting) or 'wiki' for bare wikitext which also
            includes any templates for example.
        :param lines: if not None, wrap the extract into lines with
            width of 79 chars and return a string with that given number
            of lines.
        :param chars: How many characters to return.  Actual text
            returned might be slightly longer.
        :param sentences: How many sentences to return
        :param intro: Return only content before the first section
        :raises NoPageError: given page does not exist
        :raises NotImplementedError: "wiki" variant does not support
            `sencence` parameter.
        :raises ValueError: `variant` parameter must be "plain", "html" or
            "wiki"

        .. seealso:: :meth:`APISite.extract()
           <pywikibot.site._extensions.TextExtractsMixin.extract>`.
        """
        if variant in ('plain', 'html'):
            extract = self.site.extract(self, chars=chars, sentences=sentences,
                                        intro=intro,
                                        plaintext=variant == 'plain')
        elif variant == 'wiki':
            if not self.exists():
                raise NoPageError(self)
            if sentences:
                raise NotImplementedError(
                    "'wiki' variant of extract method does not support "
                    "'sencence' parameter")

            extract = self.text[:]
            if intro:
                pos = extract.find('\n=')
                if pos:
                    extract = extract[:pos]
            if chars:
                extract = shorten(extract, chars, break_long_words=False,
                                  placeholder='…')
        else:
            raise ValueError(
                'variant parameter must be "plain", "html" or "wiki", not "{}"'
                .format(variant))

        if not lines:
            return extract

        text_lines = []
        for i, text in enumerate(extract.splitlines(), start=1):
            text_lines += wrap(text, width=79) or ['']
            if i >= lines:
                break

        return '\n'.join(text_lines[:min(lines, len(text_lines))])

    def properties(self, force: bool = False) -> dict:
        """
        Return the properties of the page.

        :param force: force updating from the live site
        """
        if not hasattr(self, '_pageprops') or force:
            self._pageprops = {}  # page may not have pageprops (see T56868)
            self.site.loadpageprops(self)
        return self._pageprops

    def defaultsort(self, force: bool = False) -> Optional[str]:
        """
        Extract value of the {{DEFAULTSORT:}} magic word from the page.

        :param force: force updating from the live site
        """
        return self.properties(force=force).get('defaultsort')

    def expand_text(
        self,
        force: bool = False,
        includecomments: bool = False
    ) -> str:
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

    @cached
    def lastNonBotUser(self) -> str:
        """
        Return name or IP address of last human/non-bot user to edit page.

        Determine the most recent human editor out of the last revisions.
        If it was not able to retrieve a human user, returns None.

        If the edit was done by a bot which is no longer flagged as 'bot',
        i.e. which is not returned by Site.botusers(), it will be returned
        as a non-bot edit.
        """
        for entry in self.revisions():
            if entry.user and (not self.site.isBot(entry.user)):
                return entry.user

        return None

    def editTime(self) -> pywikibot.Timestamp:
        """Return timestamp of last revision to page."""
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
        """Determine whether the page is a static redirect.

        A static redirect must be a valid redirect, and contain the magic
        word __STATICREDIRECT__.

        .. versionchanged:: 7.0
           __STATICREDIRECT__ can be transcluded

        :param force: Bypass local caching
        """
        return self.isRedirectPage() \
            and 'staticredirect' in self.properties(force=force)

    def isCategoryRedirect(self) -> bool:
        """Return True if this is a category redirect page, False otherwise."""
        if not self.is_categorypage():
            return False

        if not hasattr(self, '_catredirect'):
            self._catredirect = False
            catredirs = self.site.category_redirects()
            for template, args in self.templatesWithParams():
                if template.title(with_ns=False) not in catredirs:
                    continue

                if args:
                    # Get target (first template argument)
                    target_title = args[0].strip()
                    p = pywikibot.Page(
                        self.site, target_title, Namespace.CATEGORY)
                    try:
                        p.title()
                    except pywikibot.exceptions.InvalidTitleError:
                        target_title = self.site.expand_text(
                            text=target_title, title=self.title())
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

    def getCategoryRedirectTarget(self) -> 'Category':
        """If this is a category redirect, return the target category title."""
        if self.isCategoryRedirect():
            return Category(Link(self._catredirect, self.site))
        raise IsNotRedirectPageError(self)

    def isTalkPage(self):
        """Return True if this page is in any talk namespace."""
        ns = self.namespace()
        return ns >= 0 and ns % 2 == 1

    def toggleTalkPage(self) -> Optional['Page']:
        """
        Return other member of the article-talk page pair for this Page.

        If self is a talk page, returns the associated content page;
        otherwise, returns the associated talk page. The returned page need
        not actually exist on the wiki.

        :return: Page or None if self is a special page.
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

    def redirects(
        self,
        *,
        filter_fragments: Optional[bool] = None,
        namespaces: NamespaceArgType = None,
        total: Optional[int] = None,
        content: bool = False
    ) -> 'Iterable[pywikibot.Page]':
        """
        Return an iterable of redirects to this page.

        :param filter_fragments: If True, only return redirects with fragments.
            If False, only return redirects without fragments. If None, return
            both (no filtering).
        :param namespaces: only return redirects from these namespaces
        :param total: maximum number of redirects to retrieve in total
        :param content: load the current content of each redirect

        .. versionadded:: 7.0
        """
        return self.site.page_redirects(
            self,
            filter_fragments=filter_fragments,
            namespaces=namespaces,
            total=total,
            content=content,
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
        user cnfig file (user-config.py), or using page.put(force=True).
        """
        if not hasattr(self, '_bot_may_edit'):
            self._bot_may_edit = self._check_bot_may_edit()
        return self._bot_may_edit

    def _check_bot_may_edit(self, module: Optional[str] = None) -> bool:
        """A botMayEdit helper method.

        :param module: The module name to be restricted. Defaults to
            :func:`pywikibot.calledModuleName`.
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

    def save(self,
             summary: Optional[str] = None,
             watch: Optional[str] = None,
             minor: bool = True,
             botflag: Optional[bool] = None,
             force: bool = False,
             asynchronous: bool = False,
             callback=None,
             apply_cosmetic_changes: Optional[bool] = None,
             quiet: bool = False,
             **kwargs):
        """
        Save the current contents of page's text to the wiki.

        .. versionchanged:: 7.0
           boolean watch parameter is deprecated

        :param summary: The edit summary for the modification (optional, but
            most wikis strongly encourage its use)
        :param watch: Specify how the watchlist is affected by this edit, set
            to one of "watch", "unwatch", "preferences", "nochange":
            * watch: add the page to the watchlist
            * unwatch: remove the page from the watchlist
            * preferences: use the preference settings (Default)
            * nochange: don't change the watchlist
            If None (default), follow bot account's default settings
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
        :param quiet: enable/disable successful save operation message;
            defaults to False.
            In asynchronous mode, if True, it is up to the calling bot to
            manage the output e.g. via callback.
        """
        if not summary:
            summary = config.default_edit_summary

        if isinstance(watch, bool):  # pragma: no cover
            issue_deprecation_warning(
                'boolean watch parameter',
                '"watch", "unwatch", "preferences" or "nochange" value',
                since='7.0.0')
            watch = ('unwatch', 'watch')[watch]

        if not force and not self.botMayEdit():
            raise OtherPageSaveError(
                self, 'Editing restricted by {{bots}}, {{nobots}} '
                "or site's equivalent of {{in use}} template")
        self._save(summary=summary, watch=watch, minor=minor, botflag=botflag,
                   asynchronous=asynchronous, callback=callback,
                   cc=apply_cosmetic_changes, quiet=quiet, **kwargs)

    @allow_asynchronous
    def _save(self, summary=None, watch=None, minor: bool = True, botflag=None,
              cc=None, quiet: bool = False, **kwargs):
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
        cc_toolkit = CosmeticChangesToolkit(self, ignore=CANCEL.MATCH)
        self.text = cc_toolkit.change(old)

        # i18n package changed in Pywikibot 7.0.0
        old_i18n = i18n.twtranslate(self.site, 'cosmetic_changes-append',
                                    fallback_prompt='; cosmetic changes')
        if summary and old.strip().replace(
                '\r\n', '\n') != self.text.strip().replace('\r\n', '\n'):
            summary += i18n.twtranslate(self.site,
                                        'pywikibot-cosmetic-changes',
                                        fallback_prompt=old_i18n)
        return summary

    def put(self, newtext: str,
            summary: Optional[str] = None,
            watch: Optional[str] = None,
            minor: bool = True,
            botflag: Optional[bool] = None,
            force: bool = False,
            asynchronous: bool = False,
            callback=None,
            show_diff: bool = False,
            **kwargs) -> None:
        """
        Save the page with the contents of the first argument as the text.

        This method is maintained primarily for backwards-compatibility.
        For new code, using Page.save() is preferred. See save() method
        docs for all parameters not listed here.

        .. versionadded:: 7.0
           The `show_diff` parameter

        :param newtext: The complete text of the revised page.
        :param show_diff: show changes between oldtext and newtext
            (default: False)
        """
        if show_diff:
            pywikibot.showDiff(self.text, newtext)
        self.text = newtext
        self.save(summary=summary, watch=watch, minor=minor, botflag=botflag,
                  force=force, asynchronous=asynchronous, callback=callback,
                  **kwargs)

    def watch(self, unwatch: bool = False) -> bool:
        """
        Add or remove this page to/from bot account's watchlist.

        :param unwatch: True to unwatch, False (default) to watch.
        :return: True if successful, False otherwise.
        """
        return self.site.watch(self, unwatch)

    def clear_cache(self) -> None:
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

    def touch(self, callback=None, botflag: bool = False, **kwargs):
        """
        Make a touch edit for this page.

        See save() method docs for all parameters.
        The following parameters will be overridden by this method:
        - summary, watch, minor, force, asynchronous

        Parameter botflag is False by default.

        minor and botflag parameters are set to False which prevents hiding
        the edit when it becomes a real edit due to a bug.

        .. note:: This discards content saved to self.text.
        """
        if self.exists():
            # ensure always get the page text and not to change it.
            del self.text
            summary = i18n.twtranslate(self.site, 'pywikibot-touch')
            self.save(summary=summary, watch='nochange',
                      minor=False, botflag=botflag, force=True,
                      asynchronous=False, callback=callback,
                      apply_cosmetic_changes=False, nocreate=True, **kwargs)
        else:
            raise NoPageError(self)

    def linkedPages(
        self, *args, **kwargs
    ) -> Generator['pywikibot.Page', None, None]:
        """Iterate Pages that this Page links to.

        Only returns pages from "normal" internal links. Embedded
        templates are omitted but links within them are returned. All
        interwiki and external links are omitted.

        For the parameters refer
        :py:mod:`APISite.pagelinks<pywikibot.site.APISite.pagelinks>`

        .. versionadded:: 7.0
           the `follow_redirects` keyword argument
        .. deprecated:: 7.0
           the positional arguments

        .. seealso:: :api:`Links`

        :keyword namespaces: Only iterate pages in these namespaces
            (default: all)
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :keyword follow_redirects: if True, yields the target of any redirects,
            rather than the redirect page
        :keyword total: iterate no more than this number of pages in total
        :keyword content: if True, load the current content of each page
        """
        # Deprecate positional arguments and synchronize with Site.pagelinks
        keys = ('namespaces', 'total', 'content')
        for i, arg in enumerate(args):  # pragma: no cover
            key = keys[i]
            issue_deprecation_warning(
                'Positional argument {} ({})'.format(i + 1, arg),
                'keyword argument "{}={}"'.format(key, arg),
                since='7.0.0')
            if key in kwargs:
                pywikibot.warning('{!r} is given as keyword argument {!r} '
                                  'already; ignoring {!r}'
                                  .format(key, arg, kwargs[key]))
            else:
                kwargs[key] = arg

        return self.site.pagelinks(self, **kwargs)

    def interwiki(self, expand: bool = True):
        """
        Iterate interwiki links in the page text, excluding language links.

        :param expand: if True (default), include interwiki links found in
            templates transcluded onto this page; if False, only iterate
            interwiki links found in this page's own wikitext
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
                # initial ":" indicates not a language link
                # link to a different family is not a language link
                if link.site != self.site \
                   and (linktitle.lstrip().startswith(':')
                        or link.site.family != self.site.family):
                    yield link
            except Error:
                # ignore any links with invalid contents
                continue

    def langlinks(self, include_obsolete: bool = False) -> list:
        """
        Return a list of all inter-language Links on this page.

        :param include_obsolete: if true, return even Link objects whose site
                                 is obsolete
        :return: list of Link objects.
        """
        # Note: We preload a list of *all* langlinks, including links to
        # obsolete sites, and store that in self._langlinks. We then filter
        # this list if the method was called with include_obsolete=False
        # (which is the default)
        if not hasattr(self, '_langlinks'):
            self._langlinks = set(self.iterlanglinks(include_obsolete=True))

        if include_obsolete:
            return list(self._langlinks)
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
        return pywikibot.ItemPage.fromPage(self)

    def templates(self, content: bool = False) -> List['pywikibot.Page']:
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
        # Delete cache if content is needed and elements have no content
        if (hasattr(self, '_templates')
                and content
                and not all(t.has_content() for t in self._templates)):
            del self._templates

        if not hasattr(self, '_templates'):
            self._templates = set(self.itertemplates(content=content))

        return list(self._templates)

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
            return itertools.islice(self.templates(content=content), total)

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

    def categories(self,
                   with_sort_key: bool = False,
                   total: Optional[int] = None,
                   content: bool = False) -> Iterator['pywikibot.Page']:
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

        # Data might have been preloaded
        # Delete cache if content is needed and elements have no content
        if hasattr(self, '_categories'):
            if (content
                    and not all(c.has_content() for c in self._categories)):
                del self._categories
            else:
                return itertools.islice(self._categories, total)

        return self.site.pagecategories(self, total=total, content=content)

    def extlinks(self, total: Optional[int] = None):
        """
        Iterate all external URLs (not interwiki links) from this page.

        :param total: iterate no more than this number of pages in total
        :return: a generator that yields str objects containing URLs.
        :rtype: generator
        """
        return self.site.page_extlinks(self, total=total)

    def coordinates(self, primary_only: bool = False):
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

        revs = self._revisions.values()

        if starttime or endtime:
            t_min, t_max = Timestamp.min, Timestamp.max

            if reverse:
                t0 = Timestamp.set_timestamp(starttime) if starttime else t_min
                t1 = Timestamp.set_timestamp(endtime) if endtime else t_max
            else:
                t0 = Timestamp.set_timestamp(endtime) if endtime else t_min
                t1 = Timestamp.set_timestamp(starttime) if starttime else t_max

            revs = [rev for rev in revs if t0 <= rev.timestamp <= t1]

        revs = sorted(revs, reverse=not reverse, key=lambda rev: rev.timestamp)

        return islice(revs, total)

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

        if isinstance(contributors, pywikibot.User):
            contributors = contributors.username

        if isinstance(contributors, str):
            return cnt[contributors]

        return sum(cnt[user.username]
                   if isinstance(user, pywikibot.User) else cnt[user]
                   for user in contributors)

    def merge_history(self, dest, timestamp=None, reason=None) -> None:
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

    def move(self,
             newtitle: str,
             reason: Optional[str] = None,
             movetalk: bool = True,
             noredirect: bool = False,
             movesubpages: bool = True) -> None:
        """
        Move this page to a new title.

        .. versionchanged:: 7.2
           The `movesubpages` parameter was added

        :param newtitle: The new page title.
        :param reason: The edit summary for the move.
        :param movetalk: If true, move this page's talk page (if it exists)
        :param noredirect: if move succeeds, delete the old page
            (usually requires sysop privileges, depending on wiki settings)
        :param movesubpages: Rename subpages, if applicable.
        """
        if reason is None:
            pywikibot.output('Moving {} to [[{}]].'
                             .format(self.title(as_link=True), newtitle))
            reason = pywikibot.input('Please enter a reason for the move:')
        return self.site.movepage(self, newtitle, reason,
                                  movetalk=movetalk,
                                  noredirect=noredirect,
                                  movesubpages=movesubpages)

    def delete(
        self,
        reason: Optional[str] = None,
        prompt: bool = True,
        mark: bool = False,
        automatic_quit: bool = False,
        *,
        deletetalk: bool = False
    ) -> int:
        """
        Delete the page from the wiki. Requires administrator status.

        .. versionchanged:: 7.1
           keyword only parameter *deletetalk* was added.

        :param reason: The edit summary for the deletion, or rationale
            for deletion if requesting. If None, ask for it.
        :param deletetalk: Also delete the talk page, if it exists.
        :param prompt: If true, prompt user for confirmation before deleting.
        :param mark: If true, and user does not have sysop rights, place a
            speedy-deletion request on the page instead. If false, non-sysops
            will be asked before marking pages for deletion.
        :param automatic_quit: show also the quit option, when asking
            for confirmation.

        :return: the function returns an integer, with values as follows:
            value    meaning
            0        no action was done
            1        page was deleted
            -1       page was marked for deletion
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
                self.site.delete(self, reason, deletetalk=deletetalk)
                return 1
            return 0

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
            return -1
        return 0

    def has_deleted_revisions(self) -> bool:
        """Return True if the page has deleted revisions.

        .. versionadded:: 4.2
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

    def getDeletedRevision(
        self,
        timestamp,
        content: bool = False,
        **kwargs
    ) -> List:
        """
        Return a particular deleted revision by timestamp.

        :return: a list of [date, editor, comment, text, restoration
            marker]. text will be None, unless content is True (or has
            been retrieved earlier). If timestamp is not found, returns
            empty list.
        """
        if hasattr(self, '_deletedRevs') \
           and timestamp in self._deletedRevs \
           and (not content or 'content' in self._deletedRevs[timestamp]):
            return self._deletedRevs[timestamp]

        for item in self.site.deletedrevs(self, start=timestamp,
                                          content=content, total=1, **kwargs):
            # should only be one item with one revision
            if item['title'] == self.title() and 'revisions' in item:
                return item['revisions'][0]
        return []

    def markDeletedRevision(self, timestamp, undelete: bool = True):
        """
        Mark the revision identified by timestamp for undeletion.

        :param undelete: if False, mark the revision to remain deleted.
        """
        if not hasattr(self, '_deletedRevs'):
            self.loadDeletedRevisions()
        if timestamp not in self._deletedRevs:
            raise ValueError(
                'Timestamp {} is not a deleted revision'
                .format(timestamp))
        self._deletedRevs[timestamp]['marked'] = undelete

    def undelete(self, reason: Optional[str] = None) -> None:
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
                **kwargs) -> None:
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

    def change_category(self, old_cat, new_cat,
                        summary: Optional[str] = None,
                        sort_key=None,
                        in_place: bool = True,
                        include: Optional[List[str]] = None,
                        show_diff: bool = False) -> bool:
        """
        Remove page from oldCat and add it to newCat.

        .. versionadded:: 7.0
           The `show_diff` parameter

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
        :param show_diff: show changes between oldtext and newtext
            (default: False)

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
                self.put(newtext, summary, show_diff=show_diff)
            except PageSaveRelatedError as error:
                pywikibot.output('Page {} not saved: {}'
                                 .format(self.title(as_link=True), error))
            except NoUsernameError:
                pywikibot.output('Page {} not saved; sysop privileges '
                                 'required.'.format(self.title(as_link=True)))
            else:
                return True

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


class Page(BasePage, WikiBlameMixin):

    """Page: A MediaWiki page."""

    def __init__(self, source, title: str = '', ns=0) -> None:
        """Instantiate a Page object."""
        if isinstance(source, pywikibot.site.BaseSite) and not title:
            raise ValueError('Title must be specified and not empty '
                             'if source is a Site.')
        super().__init__(source, title, ns)

    @property
    @cached
    def raw_extracted_templates(self):
        """Extract templates and parameters.

        This method is using
        :func:`textlib.extract_templates_and_params`.
        Disabled parts and whitespace are stripped, except for
        whitespace in anonymous positional arguments.

        :rtype: list of (str, OrderedDict)
        """
        return textlib.extract_templates_and_params(self.text, True, True)

    def templatesWithParams(self):
        """Return templates used on this Page.

        The templates are extracted by :meth:`raw_extracted_templates`,
        with positional arguments placed first in order, and each named
        argument appearing as 'name=value'.

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
                    continue

                for k in intkeys:
                    if k < 1 or k >= i:
                        named[str(k)] = intkeys[k]
                break

            for item in named.items():
                positional.append('{}={}'.format(*item))
            result.append((pywikibot.Page(link, self.site), positional))
        return result

    def set_redirect_target(
        self,
        target_page,
        create: bool = False,
        force: bool = False,
        keep_section: bool = False,
        save: bool = True,
        **kwargs
    ):
        """
        Change the page's text to point to the redirect page.

        :param target_page: target of the redirect, this argument is required.
        :type target_page: pywikibot.Page or string
        :param create: if true, it creates the redirect even if the page
            doesn't exist.
        :param force: if true, it set the redirect target even the page
            doesn't exist or it's not redirect.
        :param keep_section: if the old redirect links to a section
            and the new one doesn't it uses the old redirect's section.
        :param save: if true, it saves the page immediately.
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

        .. versionadded:: 3.0

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


class Category(Page):

    """A page in the Category: namespace."""

    def __init__(self, source, title: str = '', sort_key=None) -> None:
        """
        Initializer.

        All parameters are the same as for Page() Initializer.
        """
        self.sortKey = sort_key
        super().__init__(source, title, ns=14)
        if self.namespace() != 14:
            raise ValueError("'{}' is not in the category namespace!"
                             .format(self.title()))

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

        def is_cache_valid(cache: dict, content: bool) -> bool:
            return cache['content'] or not content

        if not self.categoryinfo['subcats']:
            return

        if not isinstance(recurse, bool) and recurse:
            recurse = recurse - 1

        if (not hasattr(self, '_subcats')
                or not is_cache_valid(self._subcats, content)):
            cache = {'data': [], 'content': content}

            for subcat in self.site.categorymembers(
                    self, member_type='subcat', total=total, content=content):
                cache['data'].append(subcat)
                yield subcat
                if total is not None:
                    total -= 1
                    if total == 0:
                        return

                if recurse:
                    for item in subcat.subcategories(
                            recurse, total=total, content=content):
                        yield item
                        if total is None:
                            continue

                        total -= 1
                        if total == 0:
                            return
            else:
                # cache is valid only if all subcategories are fetched (T88217)
                self._subcats = cache
        else:
            for subcat in self._subcats['data']:
                yield subcat
                if total is not None:
                    total -= 1
                    if total == 0:
                        return

                if recurse:
                    for item in subcat.subcategories(
                            recurse, total=total, content=content):
                        yield item
                        if total is None:
                            continue

                        total -= 1
                        if total == 0:
                            return

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
                    if total is None:
                        continue

                    total -= 1
                    if total == 0:
                        return

    def members(self, recurse: bool = False,
                namespaces=None,
                total: Optional[int] = None,
                content: bool = False):
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
                    if total is None:
                        continue

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

    def newest_pages(
        self,
        total: Optional[int] = None
    ) -> Generator[Page, None, None]:
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
        :return: A page generator of all pages in a category ordered by the
            creation date. From newest to oldest.

            .. note:: It currently only returns Page instances and not a
               subclass of it if possible. This might change so don't
               expect to only get Page instances.
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
