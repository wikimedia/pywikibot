"""Objects representing a base object for a MediaWiki page."""
#
# (C) Pywikibot team, 2008-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import itertools
import re
from collections import Counter
from contextlib import suppress
from itertools import islice
from textwrap import shorten, wrap
from typing import TYPE_CHECKING
from urllib.parse import quote_from_bytes
from warnings import warn

import pywikibot
from pywikibot import Timestamp, config, date, i18n, textlib, tools
from pywikibot.backports import Generator, Iterable, NoneType
from pywikibot.cosmetic_changes import CANCEL, CosmeticChangesToolkit
from pywikibot.exceptions import (
    Error,
    InvalidPageError,
    IsNotRedirectPageError,
    IsRedirectPageError,
    NoMoveTargetError,
    NoPageError,
    NoUsernameError,
    OtherPageSaveError,
    PageSaveRelatedError,
    SectionError,
)
from pywikibot.page._decorators import allow_asynchronous
from pywikibot.page._links import BaseLink, Link
from pywikibot.site import Namespace, NamespaceArgType
from pywikibot.tools import (
    ComparableMixin,
    cached,
    deprecate_positionals,
    deprecated,
    deprecated_args,
    first_upper,
)


if TYPE_CHECKING:
    from typing_extensions import Literal

    from pywikibot.page import Revision


PROTOCOL_REGEX = r'\Ahttps?://'

__all__ = ['BasePage']


class BasePage(ComparableMixin):

    """BasePage: Base object for a MediaWiki page.

    This object only implements internally methods that do not require
    reading from or writing to the wiki. All other methods are delegated
    to the Site object.

    Will be subclassed by :class:`pywikibot.Page` and
    :class:`pywikibot.page.WikibasePage`.
    """

    _cache_attrs = (
        '_applicable_protections', '_catinfo', '_contentmodel', '_coords',
        '_imageforpage', '_isredir', '_item', '_langlinks', '_lintinfo',
        '_pageid', '_pageimage', '_pageprops', '_preloadedtext', '_protection',
        '_quality', '_quality_text', '_revid', '_templates', '_text',
        '_timestamp',
    )

    def __init__(self, source, title: str = '', ns=0) -> None:
        """Instantiate a Page object.

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

        self._link: BaseLink
        if isinstance(source, pywikibot.site.BaseSite):
            self._link = Link(title, source=source, default_namespace=ns)
            self._revisions = {}
        elif isinstance(source, BasePage):
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
            raise Error(f"Invalid argument type '{type(source)}' in Page "
                        f'initializer: {source}')

    @property
    def site(self):
        """Return the Site object for the wiki on which this Page resides.

        :rtype: pywikibot.Site
        """
        return self._link.site

    def version(self):
        """Return MediaWiki version number of the page site.

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
        """Return the namespace of the page.

        :return: namespace of the page
        """
        return self._link.namespace

    @property
    def content_model(self):
        """Return the content model for this page.

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
        """Return pageid of the page.

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
        """Return the title of this Page, as a string.

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
                    title = f'{self.site.family.name}:{self.site.code}:{title}'
                else:
                    # use this form for sites like commons, where the
                    # code is the same as the family name
                    title = f'{self.site.code}:{title}'
            elif textlink and (self.is_filepage() or self.is_categorypage()):
                title = f':{title}'
            elif self.namespace() == Namespace.MAIN and not section:
                with_ns = True
            if with_ns:
                return f'[[{title}{section}]]'
            return f'[[{title}{section}|{label}]]'
        if not with_ns and self.namespace() != Namespace.MAIN:
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
            title = tools.as_filename(title)
        return title

    def section(self) -> str | None:
        """Return the name of the section this Page refers to.

        The section is the part of the title following a ``#`` character,
        if any. If no section is present, return None.
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
        return f'{self.__class__.__name__}({self.title()!r})'

    def _cmpkey(self):
        """Key for comparison of Page objects.

        Page objects are "equal" if and only if they are on the same site
        and have the same normalized title, including section if any.

        Page objects are sortable by site, namespace then title.
        """
        return (self.site, self.namespace(), self.title())

    def __hash__(self):
        """A stable identifier to be used as a key in hash-tables.

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
        """Return :py:obj:`date.getAutoFormat` dictName and value, if any.

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
        retrieved yet, or if force is True. Exceptions should be caught
        by the calling code.

        **Example:**

        >>> import pywikibot
        >>> site = pywikibot.Site('mediawiki')
        >>> page = pywikibot.Page(site, 'Pywikibot')
        >>> page.get(get_redirect=True)
        '#REDIRECT[[Manual:Pywikibot]]'
        >>> page.get()
        Traceback (most recent call last):
         ...
        pywikibot.exceptions.IsRedirectPageError: ... is a redirect page.

        .. versionchanged:: 9.2
           :exc:`exceptions.SectionError` is raised if the
           :meth:`section` does not exists
        .. seealso:: :attr:`text` property

        :param force: reload all page attributes, including errors.
        :param get_redirect: return the redirect text, do not follow the
            redirect, do not raise an exception.
        :raises NoPageError: The page does not exist.
        :raises IsRedirectPageError: The page is a redirect.
        :raises SectionError: The section does not exist on a page with
            a # link.
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

        text = self.latest_revision.text

        # check for valid section in title
        page_section = self.section()
        if page_section:
            content = textlib.extract_sections(text, self.site)
            headings = {section.heading for section in content.sections}
            if page_section not in headings:
                raise SectionError(f'{page_section!r} is not a valid section '
                                   f'of {self.title(with_section=False)}')

        return text

    def has_content(self) -> bool:
        """Page has been loaded.

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
        """Helper function for get().

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

    def get_revision(
        self, oldid: int, *, force: bool = False, content: bool = False
    ) -> pywikibot.page.Revision:
        """Return an old revision of this page.

        .. versionadded:: 9.6
        .. seealso:: :meth:`getOldVersion`


        :param oldid: The revid of the revision desired.
        :param content: if True, retrieve the content of the revision
            (default False)
        """
        if force or oldid not in self._revisions \
           or (content and self._revisions[oldid].text is None):
            self.site.loadrevisions(self, content=content, revids=oldid)
        return self._revisions[oldid]

    def getOldVersion(self, oldid, force: bool = False) -> str:
        """Return text of an old revision of this page.

        .. versionchanged:: 10.0
           The unused parameter *get_redirect* was removed.
        .. seealso:: :meth:`get_revision`

        :param oldid: The revid of the revision desired.
        """
        return self.get_revision(oldid, content=True, force=force).text

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
        """Remove the latest revision id set for this Page.

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
    def latest_revision(self) -> pywikibot.page.Revision:
        """Return the current revision for this page.

        **Example:**

        >>> site = pywikibot.Site()
        >>> page = pywikibot.Page(site, 'Main Page')
        ... # get the latest timestamp of that page
        >>> edit_time = page.latest_revision.timestamp
        >>> type(edit_time)
        <class 'pywikibot.time.Timestamp'>

        .. seealso:: :attr:`oldest_revision`
        """
        rev = self._latest_cached_revision()
        if rev is not None:
            return rev

        with suppress(StopIteration):
            return next(self.revisions(content=True, total=1))
        raise InvalidPageError(self)

    @property
    def text(self) -> str:
        """Return the current (edited) wikitext, loading it if necessary.

        This property should be preferred over :meth:`get`. If the page
        does not exist, an empty string will be returned. For a redirect
        it returns the redirect page content and does not raise an
        :exc:`exceptions.IsRedirectPageError` exception.

        **Example:**

        >>> import pywikibot
        >>> site = pywikibot.Site('mediawiki')
        >>> page = pywikibot.Page(site, 'Pywikibot')
        >>> page.text
        '#REDIRECT[[Manual:Pywikibot]]'
        >>> page.text = 'PWB Framework'
        >>> page.text
        'PWB Framework'
        >>> page.text = None  # reload from wiki
        >>> page.text
        '#REDIRECT[[Manual:Pywikibot]]'
        >>> del page.text  # other way to reload from wiki

        To save the modified text :meth:`save` is one possible method.

        :return: text of the page
        """
        if hasattr(self, '_text') and self._text is not None:
            return self._text

        try:
            return self.get(get_redirect=True)
        except NoPageError:
            # TODO: what other exceptions might be returned?
            return ''

    @text.setter
    def text(self, value: str | None) -> None:
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
        """The text returned by EditFormPreloadText.

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
                lines: int | None = None,
                chars: int | None = None,
                sentences: int | None = None,
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
            `sentences` parameter.
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
                    "'sentences' parameter")

            extract = self.text[:]
            if intro:
                pos = extract.find('\n=')
                if pos:
                    extract = extract[:pos]
            if chars:
                extract = shorten(extract, chars, break_long_words=False,
                                  placeholder='…')
        else:
            raise ValueError('variant parameter must be "plain", "html" or '
                             f'"wiki", not "{variant}"')

        if not lines:
            return extract

        text_lines = []
        for i, text in enumerate(extract.splitlines(), start=1):
            text_lines += wrap(text, width=79) or ['']
            if i >= lines:
                break

        return '\n'.join(text_lines[:min(lines, len(text_lines))])

    def properties(self, force: bool = False) -> dict:
        """Return the properties of the page.

        :param force: force updating from the live site
        """
        if not hasattr(self, '_pageprops') or force:
            self._pageprops = {}  # page may not have pageprops (see T56868)
            self.site.loadpageprops(self)
        return self._pageprops

    def defaultsort(self, force: bool = False) -> str | None:
        """Extract value of the {{DEFAULTSORT:}} magic word from the page.

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

    @deprecated('latest_revision.user', since='9.3.0')
    def userName(self) -> str:
        """Return name or IP address of last user to edit page.

        .. deprecated:: 9.3
           Use :attr:`latest_revision.user<latest_revision>`
           instead.
        """
        return self.latest_revision.user  # type: ignore[attr-defined]

    @deprecated('latest_revision.anon', since='9.3.0')
    def isIpEdit(self) -> bool:
        """Return True if last editor was unregistered.

        .. deprecated:: 9.3
           Use :attr:`latest_revision.anon<latest_revision>`
           instead.
        """
        return self.latest_revision.anon  # type: ignore[attr-defined]

    @cached
    def lastNonBotUser(self) -> str | None:
        """Return name or IP address of last human/non-bot user to edit page.

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

    @deprecated('latest_revision.timestamp', since='8.0.0')
    def editTime(self) -> pywikibot.Timestamp:
        """Return timestamp of last revision to page.

        .. deprecated:: 8.0
           Use :attr:`latest_revision.timestamp<latest_revision>`
           instead.
        """
        return self.latest_revision.timestamp  # type: ignore[attr-defined]

    def exists(self) -> bool:
        """Return True if page exists on the wiki, even if it's a redirect.

        If the title includes a section, return False if this section isn't
        found.
        """
        with suppress(AttributeError):
            return self.pageid > 0
        raise InvalidPageError(self)

    @property
    def oldest_revision(self) -> pywikibot.page.Revision:
        """Return the first revision of this page.

        **Example:**

        >>> site = pywikibot.Site()
        >>> page = pywikibot.Page(site, 'Main Page')
        ... # get the creation timestamp of that page
        >>> creation_time = page.oldest_revision.timestamp
        >>> type(creation_time)
        <class 'pywikibot.time.Timestamp'>

        .. seealso:: :attr:`latest_revision`
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
            self._catredirect: str | Literal[False] = False
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
                            f'Category redirect target {p.title(as_link=True)}'
                            f' on {self.title(as_link=True)} is not a category'
                        )
                else:
                    pywikibot.warning(
                        'No target found for category redirect on '
                        + self.title(as_link=True))
                break

        return bool(self._catredirect)

    def getCategoryRedirectTarget(self) -> pywikibot.Category:
        """If this is a category redirect, return the target category title."""
        if self.isCategoryRedirect():
            return pywikibot.Category(Link(self._catredirect, self.site))
        raise IsNotRedirectPageError(self)

    def isTalkPage(self):
        """Return True if this page is in any talk namespace."""
        ns = self.namespace()
        return ns >= 0 and ns % 2 == 1

    def toggleTalkPage(self) -> pywikibot.Page | None:
        """Return other member of the article-talk page pair for this Page.

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
        return pywikibot.Page(self.site,
                              f'{self.site.namespace(new_ns)}:{title}')

    def is_categorypage(self):
        """Return True if the page is a Category, False otherwise."""
        return self.namespace() == Namespace.CATEGORY

    def is_filepage(self):
        """Return True if this is a file description page, False otherwise."""
        return self.namespace() == Namespace.FILE

    def isDisambig(self) -> bool:
        """Return True if this is a disambiguation page, False otherwise.

        By default, it uses the Disambiguator extension's result. The
        identification relies on the presence of the ``__DISAMBIG__``
        magic word which may also be transcluded.

        If the Disambiguator extension isn't activated for the given
        site, the identification relies on the presence of specific
        templates. First load a list of template names from the
        :class:`Family<family.Family>` file via :meth:`BaseSite.disambig()
        <pywikibot.site._basesite.BaseSite.disambig>`; if the value in
        the Family file not found, look for the list on
        ``[[MediaWiki:Disambiguationspage]]``. If this page does not
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
                distl = self.site.disambig(fallback=False)
            except KeyError:
                distl = None

            if distl:
                # Normalize template capitalization
                self.site._disambigtemplates = {first_upper(t) for t in distl}
            else:
                # look for the list on [[MediaWiki:Disambiguationspage]]
                disambigpages = pywikibot.Page(self.site,
                                               'MediaWiki:Disambiguationspage')
                if disambigpages.exists():
                    disambigs = {link.title(with_ns=False)
                                 for link in disambigpages.linkedPages()
                                 if link.namespace() == Namespace.TEMPLATE}
                elif self.site.has_mediawiki_message('disambiguationspage'):
                    # take the MediaWiki message
                    message = self.site.mediawiki_message(
                        'disambiguationspage').split(':', 1)[1]
                    # add the default template(s) for default mw message
                    # only
                    disambigs = {first_upper(message)} | default
                else:
                    disambigs = default
                self.site._disambigtemplates = disambigs

        templates = {tl.title(with_ns=False)
                     for tl in self.templates(namespaces=Namespace.TEMPLATE)}
        disambigs = set()
        # always use cached disambig templates
        disambigs.update(self.site._disambigtemplates)
        # see if any template on this page is in the set of disambigs
        disambig_in_page = disambigs.intersection(templates)
        return (self.namespace() != Namespace.TEMPLATE
                and bool(disambig_in_page))

    def getReferences(self,
                      follow_redirects: bool = True,
                      with_template_inclusion: bool = True,
                      only_template_inclusion: bool = False,
                      filter_redirects: bool = False,
                      namespaces=None,
                      total: int | None = None,
                      content: bool = False) -> Iterable[pywikibot.Page]:
        """Return an iterator all pages that refer to or embed the page.

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
                  filter_redirects: bool | None = None,
                  namespaces=None,
                  total: int | None = None,
                  content: bool = False) -> Iterable[pywikibot.Page]:
        """Return an iterator for pages that link to this page.

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
                   filter_redirects: bool | None = None,
                   namespaces=None,
                   total: int | None = None,
                   content: bool = False) -> Iterable[pywikibot.Page]:
        """Return an iterator for pages that embed this page as a template.

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
        filter_fragments: bool | None = None,
        namespaces: NamespaceArgType = None,
        total: int | None = None,
        content: bool = False
    ) -> Iterable[pywikibot.Page]:
        """Return an iterable of redirects to this page.

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

    def protection(self) -> dict[str, tuple[str, str]]:
        """Return a dictionary reflecting page protections.

        **Example:**

        >>> site = pywikibot.Site('wikipedia:test')
        >>> page = pywikibot.Page(site, 'Main Page')
        >>> page.protection()
        {'edit': ('sysop', 'infinity'), 'move': ('sysop', 'infinity')}

        .. seealso::
           - :meth:`Site.page_restrictions()
             <pywikibot.site._apisite.APISite.page_restrictions>`
           - :meth:`applicable_protections`
           - :meth:`protect`
        """
        return self.site.page_restrictions(self)

    def applicable_protections(self) -> set[str]:
        """Return the protection types allowed for that page.

        **Example:**

        >>> site = pywikibot.Site('wikipedia:test')
        >>> page = pywikibot.Page(site, 'Main Page')
        >>> sorted(page.applicable_protections())
        ['edit', 'move']

        .. seealso::
           - :meth:`protect`
           - :meth:`protection`
        """
        self.site.loadpageinfo(self)
        return self._applicable_protections

    def has_permission(self, action: str = 'edit') -> bool:
        """Determine whether the page can be modified.

        Return True if the bot has the permission of needed restriction level
        for the given action type:

        >>> site = pywikibot.Site('test')
        >>> page = pywikibot.Page(site, 'Main Page')
        >>> page.has_permission()
        False
        >>> page.has_permission('move')
        False
        >>> page.has_permission('invalid')
        Traceback (most recent call last):
        ...
        ValueError: APISite.page_can_be_edited(): Invalid value "invalid" ...

        .. seealso:: :meth:`APISite.page_can_be_edited()
           <pywikibot.site._apisite.APISite.page_can_be_edited>`


        :param action: a valid restriction type like 'edit', 'move';
            default is ``edit``.
        :raises ValueError: invalid action parameter
        """
        return self.site.page_can_be_edited(self, action)

    def botMayEdit(self) -> bool:
        """Determine whether the active bot is allowed to edit the page.

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

    def _check_bot_may_edit(self, module: str | None = None) -> bool:
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

    @deprecated_args(botflag='bot')  # since 9.3.0
    def save(self,
             summary: str | None = None,
             watch: str | None = None,
             minor: bool = True,
             bot: bool = True,
             force: bool = False,
             asynchronous: bool = False,
             callback=None,
             apply_cosmetic_changes: bool | None = None,
             quiet: bool = False,
             **kwargs):
        """Save the current contents of page's text to the wiki.

        .. versionchanged:: 7.0
           boolean *watch* parameter is deprecated
        .. versionchanged:: 9.3
           *botflag* parameter was renamed to *bot*.
        .. versionchanged:: 9.4
           edits cannot be marked as bot edits if the bot account has no
           ``bot`` right. Therefore a ``None`` argument for *bot*
           parameter was dropped.
        .. versionchanged:: 10.0
           boolean *watch* parameter is desupported

        .. hint:: Setting up :manpage:`OAuth` or :manpage:`BotPassword
           <BotPasswords>` login, you have to grant
           ``High-volume (bot) access`` to get ``bot`` right even if the
           account is member of the bots group granted by bureaucrats.
           Otherwise edits cannot be marked with both flag and *bot*
           argument will be ignored.

        .. seealso:: :meth:`APISite.editpage
           <pywikibot.site._apisite.APISite.editpage>`

        :param summary: The edit summary for the modification (optional,
            but most wikis strongly encourage its use)
        :param watch: Specify how the watchlist is affected by this edit,
            set to one of ``watch``, ``unwatch``, ``preferences``,
            ``nochange``:

            * watch --- add the page to the watchlist
            * unwatch --- remove the page from the watchlist
            * preferences --- use the preference settings (Default)
            * nochange --- don't change the watchlist

            If None (default), follow bot account's default settings
        :param minor: if True, mark this edit as minor
        :param bot: if True, mark this edit as made by a bot if user has
            ``bot`` right (default), if False do not mark it as bot edit.
        :param force: if True, ignore botMayEdit() setting
        :param asynchronous: if True, launch a separate thread to save
            asynchronously
        :param callback: a callable object that will be called after the
            page put operation. This object must take two arguments: (1)
            a Page object, and (2) an exception instance, which will be
            None if the page was saved successfully. The callback is
            intended for use by bots that need to keep track of which
            saves were successful.
        :param apply_cosmetic_changes: Overwrites the cosmetic_changes
            configuration value to this value unless it's None.
        :param quiet: enable/disable successful save operation message;
            defaults to False. In asynchronous mode, if True, it is up
            to the calling bot to manage the output e.g. via callback.
        :raises TypeError: watch parameter must be a string literal or
            None
        :raises OtherPageSaveError: Editing restricted by a template.
        """
        if not summary:
            summary = config.default_edit_summary

        if not isinstance(watch, (str, NoneType)):
            raise TypeError(
                f'watch parameter must be a string literal, not {watch}')
        if not force and not self.botMayEdit():
            raise OtherPageSaveError(
                self, 'Editing restricted by {{bots}}, {{nobots}} '
                "or site's equivalent of {{in use}} template"
            )

        self._save(summary=summary, watch=watch, minor=minor, bot=bot,
                   asynchronous=asynchronous, callback=callback,
                   cc=apply_cosmetic_changes, quiet=quiet, **kwargs)

    @allow_asynchronous
    def _save(self, summary=None, cc=None, quiet: bool = False, **kwargs):
        """Helper function for save()."""
        link = self.title(as_link=True)
        if cc or (cc is None and config.cosmetic_changes):
            summary = self._cosmetic_changes_hook(summary)

        done = self.site.editpage(self, summary=summary, **kwargs)
        if not done:
            if not quiet:
                pywikibot.warning(f'Page {link} not saved')
            raise PageSaveRelatedError(self)

        if not self.pageid:
            self.site.loadpageinfo(self)

        if not quiet:
            pywikibot.info(f'Page {link} saved')

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
        pywikibot.log(
            f'Cosmetic changes for {family}-{self.site.lang} enabled.')
        # cc depends on page directly and via several other imports
        cc_toolkit = CosmeticChangesToolkit(self, ignore=CANCEL.MATCH)
        self.text = cc_toolkit.change(old)

        if summary and old.strip().replace(
                '\r\n', '\n') != self.text.strip().replace('\r\n', '\n'):
            summary += i18n.twtranslate(self.site,
                                        'pywikibot-cosmetic-changes')
        return summary

    @deprecated_args(botflag='bot')  # since 9.3.0
    def put(self, newtext: str,
            summary: str | None = None,
            watch: str | None = None,
            minor: bool = True,
            bot: bool = True,
            force: bool = False,
            asynchronous: bool = False,
            callback=None,
            show_diff: bool = False,
            **kwargs) -> None:
        """Save the page with the contents of the first argument as the text.

        This method is maintained primarily for backwards-compatibility.
        For new code, using :meth:`save` is preferred; also ee that
        method docs for all parameters not listed here.

        .. versionadded:: 7.0
           The `show_diff` parameter
        .. versionchanged:: 9.3
           *botflag* parameter was renamed to *bot*.
        .. versionchanged:: 9.4
           edits cannot be marked as bot edits if the bot account has no
           ``bot`` right. Therefore a ``None`` argument for *bot*
           parameter was dropped.

        .. seealso:: :meth:`save`

        :param newtext: The complete text of the revised page.
        :param show_diff: show changes between oldtext and newtext
            (default: False)
        """
        if show_diff:
            pywikibot.showDiff(self.text, newtext)
        self.text = newtext
        self.save(summary=summary, watch=watch, minor=minor, bot=bot,
                  force=force, asynchronous=asynchronous, callback=callback,
                  **kwargs)

    def watch(self, unwatch: bool = False) -> bool:
        """Add or remove this page to/from bot account's watchlist.

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
        """Purge the server's cache for this page.

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

    @deprecated_args(botflag='bot')  # since 9.3.0
    def touch(self, callback=None, bot: bool = False, **kwargs):
        """Make a touch edit for this page.

        See Meth:`save` method docs for all parameters. The following
        parameters will be overridden by this method: *summary*, *watch*,
        *minor*, *force*, *asynchronous*

        Parameter *bot* is False by default.

        *minor* and *bot* parameters are set to ``False`` which prevents
        hiding the edit when it becomes a real edit due to a bug.

        .. note:: This discards content saved to self.text.

        .. versionchanged:: 9.2
           *botflag* parameter was renamed to *bot*.
        """
        if not self.exists():
            raise NoPageError(self)

        # ensure always get the page text and not to change it.
        del self.text
        summary = i18n.twtranslate(self.site, 'pywikibot-touch')
        self.save(summary=summary, watch='nochange', minor=False, bot=bot,
                  force=True, asynchronous=False, callback=callback,
                  apply_cosmetic_changes=False, nocreate=True, **kwargs)

    def linkedPages(
        self,
        **kwargs
    ) -> Generator[pywikibot.page.BasePage, None, None]:
        """Iterate Pages that this Page links to.

        Only returns pages from "normal" internal links. Embedded
        templates are omitted but links within them are returned. All
        interwiki and external links are omitted.

        For the parameters refer
        :py:mod:`APISite.pagelinks<pywikibot.site.APISite.pagelinks>`

        .. versionadded:: 7.0
           the `follow_redirects` keyword argument.
        .. versionremoved:: 10.0
           the positional arguments.

        .. seealso::
           - :meth:`Site.pagelinks
             <pywikibot.site._generators.GeneratorsMixin.pagelinks>`
           - :api:`Links`

        :keyword namespaces: Only iterate pages in these namespaces
            (default: all)
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :keyword bool follow_redirects: if True, yields the target of
            any redirects, rather than the redirect page
        :keyword int total: iterate no more than this number of pages in
            total
        :keyword bool content: if True, load the current content of each
            page
        """
        return self.site.pagelinks(self, **kwargs)

    def interwiki(
        self,
        expand: bool = True,
    ) -> Generator[pywikibot.page.Link, None, None]:
        """Yield interwiki links in the page text, excluding language links.

        :param expand: if True (default), include interwiki links found in
            templates transcluded onto this page; if False, only iterate
            interwiki links found in this page's own wikitext
        :return: a generator that yields Link objects
        """
        # This function does not exist in the API, so it has to be
        # implemented by screen-scraping
        text = self.expand_text() if expand else self.text
        for linkmatch in pywikibot.link_regex.finditer(
                textlib.removeDisabledParts(text)):
            linktitle = linkmatch['title']
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

    def langlinks(
        self,
        include_obsolete: bool = False,
    ) -> list[pywikibot.Link]:
        """Return a list of all inter-language Links on this page.

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

    def iterlanglinks(
        self,
        total: int | None = None,
        include_obsolete: bool = False,
    ) -> Iterable[pywikibot.Link]:
        """Iterate all inter-language links on this page.

        :param total: iterate no more than this number of pages in total
        :param include_obsolete: if true, yield even Link object whose site
                                 is obsolete
        :return: a generator that yields Link objects.
        """
        if hasattr(self, '_langlinks'):
            return iter(self.langlinks(include_obsolete=include_obsolete))
        # FIXME: We might want to fill _langlinks when the Site
        # method is called. If we do this, we'll have to think
        # about what will happen if the generator is not completely
        # iterated upon.
        return self.site.pagelanglinks(self, total=total,
                                       include_obsolete=include_obsolete)

    def data_item(self) -> pywikibot.page.ItemPage:
        """Convenience function to get the Wikibase item of a page."""
        return pywikibot.ItemPage.fromPage(self)

    @deprecate_positionals(since='9.2')
    def templates(self,
                  *,
                  content: bool = False,
                  namespaces: NamespaceArgType = None) -> list[pywikibot.Page]:
        """Return a list of Page objects for templates used on this Page.

        This method returns a list of pages which are embedded as
        templates even they are not in the TEMPLATE: namespace. This
        method caches the result. If *namespaces* is used, all pages are
        retrieved and cached but the result is filtered.

        .. versionchanged:: 2.0
           a list of :class:`pywikibot.Page` is returned instead of a
           list of template titles. The given pages may have namespaces
           different from TEMPLATE namespace. *get_redirect* parameter
           was removed.
        .. versionchanged:: 9.2
           *namespaces* parameter was added; all parameters must be given
           as keyword arguments.

        .. seealso::
           - :meth:`itertemplates`

        :param content: if True, retrieve the content of the current version
            of each template (default False)
        :param namespaces: Only iterate pages in these namespaces
        """
        # Data might have been preloaded
        # Delete cache if content is needed and elements have no content
        if (hasattr(self, '_templates')
                and content
                and not all(t.has_content() for t in self._templates)):
            del self._templates

        # retrieve all pages in _templates and filter namespaces later
        if not hasattr(self, '_templates'):
            self._templates = set(self.itertemplates(content=content))

        if namespaces is not None:
            ns = self.site.namespaces.resolve(namespaces)
            return [t for t in self._templates if t.namespace() in ns]

        return list(self._templates)

    @deprecate_positionals(since='9.2')
    def itertemplates(
        self,
        total: int | None = None,
        *,
        content: bool = False,
        namespaces: NamespaceArgType = None
    ) -> Iterable[pywikibot.Page]:
        """Iterate Page objects for templates used on this Page.

        This method yield pages embedded as templates even they are not
        in the TEMPLATE: namespace. The retrieved pages are not cached
        but they can be yielded from the cache of a previous
        :meth:`templates` call.

        .. versionadded:: 2.0
        .. versionchanged:: 9.2
           *namespaces* parameter was added; all parameters except
           *total* must be given as keyword arguments.

        .. seealso::
           - :meth:`site.APISite.pagetemplates()
             <pywikibot.site._generators.GeneratorsMixin.pagetemplates>`
           - :meth:`templates`
           - :meth:`getReferences`

        :param total: iterate no more than this number of pages in total
        :param content: if True, retrieve the content of the current version
            of each template (default False)
        :param namespaces: Only iterate pages in these namespaces
        """
        if hasattr(self, '_templates'):
            return itertools.islice(self.templates(
                content=content, namespaces=namespaces), total)

        return self.site.pagetemplates(
            self, content=content, namespaces=namespaces, total=total)

    def imagelinks(
        self,
        total: int | None = None,
        content: bool = False,
    ) -> Iterable[pywikibot.FilePage]:
        """Iterate FilePage objects for images displayed on this Page.

        :param total: iterate no more than this number of pages in total
        :param content: if True, retrieve the content of the current version
            of each image description page (default False)
        :return: a generator that yields FilePage objects.
        """
        return self.site.pageimages(self, total=total, content=content)

    def categories(
        self,
        with_sort_key: bool = False,
        total: int | None = None,
        content: bool = False,
    ) -> Iterable[pywikibot.Page]:
        """Iterate categories that the article is in.

        .. versionchanged:: 2.0
           *with_sort_key* parameter is not supported and a
           NotImplementedError is raised if set.
        .. versionchanged:: 9.6
           *with_sort_key* parameter is supported.
        .. seealso:: :meth:`Site.pagecategories()
           <pywikibot.site._generators.GeneratorsMixin.pagecategories>`
        .. note:: This method also yields categories which are
           transcluded.

        :param with_sort_key: if True, include the sort key in
            each Category.
        :param total: iterate no more than this number of pages in total
        :param content: if True, retrieve the content of the current
            version of each category description page (default False)
        :return: a generator that yields Category objects.
        """
        # Data might have been preloaded
        # Delete cache if content is needed and elements have no content
        if hasattr(self, '_categories'):
            if (content
                    and not all(c.has_content() for c in self._categories)):
                del self._categories
            else:
                return itertools.islice(self._categories, total)

        return self.site.pagecategories(self, with_sort_key=with_sort_key,
                                        total=total, content=content)

    def extlinks(self, total: int | None = None) -> Iterable[str]:
        """Iterate all external URLs (not interwiki links) from this page.

        :param total: iterate no more than this number of pages in total
        :return: a generator that yields str objects containing URLs.
        """
        return self.site.page_extlinks(self, total=total)

    def coordinates(self, primary_only: bool = False):
        """Return a list of Coordinate objects for points on the page.

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
        """Return the most appropriate image on the page.

        Uses the MediaWiki extension PageImages.

        :return: A FilePage object
        :rtype: pywikibot.page.FilePage
        """
        if not hasattr(self, '_pageimage'):
            self._pageimage = None
            self.site.loadpageimage(self)

        return self._pageimage

    def getRedirectTarget(self, *,
                          ignore_section: bool = True) -> pywikibot.Page:
        """Return a Page object for the target this Page redirects to.

        .. versionadded:: 9.3
           *ignore_section* parameter

        .. seealso::
           * :meth:`Site.getredirtarget()
             <pywikibot.site._apisite.APISite.getredirtarget>`
           * :meth:`moved_target`

        :param ignore_section: do not include section to the target even
            the link has one

        :raises CircularRedirectError: page is a circular redirect
        :raises InterwikiRedirectPageError: the redirect target is on
            another site
        :raises IsNotRedirectPageError: page is not a redirect
        :raises RuntimeError: no redirects found
        :raises SectionError: the section is not found on target page
            and *ignore_section* is not set
        """
        return self.site.getredirtarget(self, ignore_section=ignore_section)

    def moved_target(self) -> pywikibot.page.Page:
        """Return a Page object for the target this Page was moved to.

        If this page was not moved, it will raise a NoMoveTargetError.
        This method also works if the source was already deleted.

        .. seealso:: :meth:`getRedirectTarget`

        :raises NoMoveTargetError: page was not moved
        """
        gen = iter(self.site.logevents(logtype='move', page=self, total=1))
        try:
            lastmove = next(gen)
        except StopIteration:
            raise NoMoveTargetError(self)

        return lastmove.target_page

    def revisions(self,
                  reverse: bool = False,
                  total: int | None = None,
                  content: bool = False,
                  starttime=None, endtime=None):
        """Generator which loads the version history as Revision instances."""
        # TODO: Only request uncached revisions
        self.site.loadrevisions(self, content=content, rvdir=reverse,
                                starttime=starttime, endtime=endtime,
                                total=total)

        revs: Iterable[Revision] = self._revisions.values()

        if starttime or endtime:
            t_min, t_max = Timestamp.min, Timestamp.max

            if reverse:
                t0 = Timestamp.set_timestamp(starttime) if starttime else t_min
                t1 = Timestamp.set_timestamp(endtime) if endtime else t_max
            else:
                t0 = Timestamp.set_timestamp(endtime) if endtime else t_min
                t1 = Timestamp.set_timestamp(starttime) if starttime else t_max

            revs = [rev for rev in revs if t0 <= rev.timestamp <= t1]  # type: ignore[attr-defined]  # noqa: E501

        revs = sorted(revs, reverse=not reverse, key=lambda rev: rev.timestamp)  # type: ignore[attr-defined]  # noqa: E501

        return islice(revs, total)

    def getVersionHistoryTable(self,
                               reverse: bool = False,
                               total: int | None = None):
        """Return the version history as a wiki table."""
        result = '{| class="wikitable"\n'
        result += '! oldid || date/time || username || edit summary\n'
        for entry in self.revisions(reverse=reverse, total=total):
            result += '|----\n'
            result += (f'| {entry.revid} || {entry.timestamp} || {entry.user} '
                       f'|| <nowiki>{entry.comment}</nowiki>\n')
        result += '|}\n'
        return result

    def contributors(self,
                     total: int | None = None,
                     starttime=None, endtime=None):
        """Compile contributors of this page with edit counts.

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

    def merge_history(self,
                      dest: BasePage,
                      timestamp: pywikibot.Timestamp | None = None,
                      reason: str | None = None) -> None:
        """Merge revisions from this page into another page.

        .. seealso:: :meth:`APISite.merge_history()
           <pywikibot.site._apisite.APISite.merge_history>` for details.

        :param dest: Destination page to which revisions will be merged
        :param timestamp: Revisions from this page dating up to this timestamp
            will be merged into the destination page (if not given or False,
            all revisions will be merged)
        :param reason: Optional reason for the history merge
        """
        self.site.merge_history(self, dest, timestamp, reason)

    def move(self,
             newtitle: str,
             reason: str | None = None,
             movetalk: bool = True,
             noredirect: bool = False,
             movesubpages: bool = True) -> pywikibot.page.Page:
        """Move this page to a new title.

        .. versionchanged:: 7.2
           The *movesubpages* parameter was added

        :param newtitle: The new page title.
        :param reason: The edit summary for the move.
        :param movetalk: If true, move this page's talk page (if it exists)
        :param noredirect: if move succeeds, delete the old page
            (usually requires sysop privileges, depending on wiki settings)
        :param movesubpages: Rename subpages, if applicable.
        """
        if reason is None:
            pywikibot.info(f'Moving {self} to [[{newtitle}]].')
            reason = pywikibot.input('Please enter a reason for the move:')
        return self.site.movepage(self, newtitle, reason,
                                  movetalk=movetalk,
                                  noredirect=noredirect,
                                  movesubpages=movesubpages)

    def delete(
        self,
        reason: str | None = None,
        prompt: bool = True,
        mark: bool = False,
        automatic_quit: bool = False,
        *,
        deletetalk: bool = False
    ) -> int:
        """Delete the page from the wiki. Requires administrator status.

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
            pywikibot.info(f'Deleting {self.title(as_link=True)}.')
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
                f"Can't delete {self};"
                ' do you want to mark it for deletion instead?',
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
                trgt = self.toggleTalkPage()
                assert trgt is not None
                target: BasePage = trgt
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

    def loadDeletedRevisions(self, total: int | None = None, **kwargs):
        """Retrieve deleted revisions for this Page.

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
    ) -> list:
        """Return a particular deleted revision by timestamp.

        .. seealso:: :meth:`APISite.deletedrevs()
           <pywikibot.site._generators.GeneratorsMixin.deletedrevs>`

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
        """Mark the revision identified by timestamp for undeletion.

        .. seealso::
           - :meth:`undelete`
           - :meth:`loadDeletedRevisions`

        :param undelete: if False, mark the revision to remain deleted.
        """
        if not hasattr(self, '_deletedRevs'):
            self.loadDeletedRevisions()
        if timestamp not in self._deletedRevs:
            raise ValueError(
                f'Timestamp {timestamp} is not a deleted revision')
        self._deletedRevs[timestamp]['marked'] = undelete

    def undelete(self, reason: str | None = None) -> None:
        """Undelete revisions based on the markers set by previous calls.

        If no calls have been made since :meth:`loadDeletedRevisions`,
        everything will be restored.

        Simplest case:

        .. code-block:: python

            Page(...).undelete('This will restore all revisions')

        More complex:

        .. code-block:: Python

            page = Page(...)
            revs = page.loadDeletedRevisions()
            for rev in revs:
                if ...  # decide whether to undelete a revision
                    page.markDeletedRevision(rev)  # mark for undeletion
            page.undelete('This will restore only selected revisions.')

        .. seealso::
           - :meth:`loadDeletedRevisions`
           - :meth:`markDeletedRevision`
           - :meth:`site.APISite.undelete
             <pywikibot.site._apisite.APISite.undelete>`

        :param reason: Reason for the action.
        """
        if hasattr(self, '_deletedRevs'):
            undelete_revs = [ts for ts, rev in self._deletedRevs.items()
                             if rev.get('marked')]
        else:
            undelete_revs = []
        if reason is None:
            warn('Not passing a reason for undelete() is deprecated.',
                 DeprecationWarning)
            pywikibot.info(f'Undeleting {self.title(as_link=True)}.')
            reason = pywikibot.input(
                'Please enter a reason for the undeletion:')
        self.site.undelete(self, reason, revisions=undelete_revs)

    def protect(self,
                reason: str | None = None,
                protections: dict[str, str | None] | None = None,
                **kwargs) -> None:
        """Protect or unprotect a wiki page. Requires  *protect* right.

        Valid protection levels are ``''`` (equivalent to ``None``),
        ``'autoconfirmed'``, ``'sysop'`` and ``'all'``. ``'all'`` means
        everyone is allowed, i.e. that protection type will be
        unprotected.

        In order to unprotect a type of permission, the protection level
        shall be either set to ``'all'`` or ``''`` or skipped in the
        protections dictionary.

        Expiry of protections can be set via *kwargs*, see
        :meth:`Site.protect()<pywikibot.site._apisite.APISite.protect>`
        for details. By default there is no expiry for the protection
        types.

        .. seealso::
           - :meth:`Site.protect()
             <pywikibot.site._apisite.APISite.protect>`
           - :meth:`applicable_protections`

        :param protections: A dict mapping type of protection to
            protection level of that type. Allowed protection types for
            a page can be retrieved by :meth:`applicable_protections`.
            Defaults to protections is None, which means unprotect all
            protection types.

            Example: :code:`{'move': 'sysop', 'edit': 'autoconfirmed'}`

        :param reason: Reason for the action, default is None and will
            set an empty string.
        """
        protections = protections or {}  # protections is converted to {}
        reason = reason or ''  # None is converted to ''

        self.site.protect(self, protections, reason, **kwargs)

    def change_category(self, old_cat, new_cat,
                        summary: str | None = None,
                        sort_key=None,
                        in_place: bool = True,
                        include: list[str] | None = None,
                        show_diff: bool = False) -> bool:
        """Remove page from oldCat and add it to newCat.

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
            pywikibot.info(f"Can't edit {self}, skipping it...")
            return False

        if old_cat not in cats:
            pywikibot.info(
                f'{self} is not in category {old_cat.title()}, skipping...'
            )
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
                cats[old_cat_pos] = pywikibot.Category(self.site,
                                                       new_cat.title(),
                                                       sort_key=sort_key)
            else:
                cats.pop(old_cat_pos)

            try:
                newtext = textlib.replaceCategoryLinks(oldtext, cats)
            except ValueError:
                # Make sure that the only way replaceCategoryLinks() can return
                # a ValueError is in the case of interwiki links to self.
                pywikibot.info(
                    f'Skipping {self} because of interwiki link to self')
                return False

        if oldtext != newtext:
            try:
                self.put(newtext, summary, show_diff=show_diff)
            except PageSaveRelatedError as error:
                pywikibot.info(f'Page {self} not saved: {error}')
            except NoUsernameError:
                pywikibot.info(
                    f'Page {self} not saved; sysop privileges required.')
            else:
                return True

        return False

    def is_flow_page(self) -> bool:
        """Whether a page is a Flow page.

        .. attention::
           Structured Discussion/Flow support was deprecated in 9.4 and
           removed in Pywikibot 10. This method is kept to detect
           unsupported content.
        """
        return self.content_model == 'flow-board'

    def create_short_link(self,
                          permalink: bool = False,
                          with_protocol: bool = True) -> str:
        """Return a shortened link that points to that page.

        If shared_urlshortner_wiki is defined in family config, it'll
        use that site to create the link instead of the current wiki.

        :param permalink: If true, the link will point to the actual
            revision of the page.
        :param with_protocol: If true, and if it's not already included,
            the link will have http(s) protocol prepended. On Wikimedia
            wikis the protocol is already present.
        :return: The reduced link.
        :raises APIError: urlshortener-ratelimit exceeded
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
            return f'{wiki.protocol()}://{link}'
        return link
