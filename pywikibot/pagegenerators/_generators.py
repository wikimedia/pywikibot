"""Page filter generators provided by the pagegenerators module."""
#
# (C) Pywikibot team, 2008-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import calendar
import codecs
import io
import re
import sys
import typing
from collections import abc
from functools import partial
from http import HTTPStatus
from typing import TYPE_CHECKING, Any
from urllib.parse import urlparse

from requests.exceptions import ReadTimeout

import pywikibot
from pywikibot import config, date, xmlreader
from pywikibot.backports import (
    Callable,
    Generator,
    Iterable,
    Iterator,
    Sequence,
    batched,
)
from pywikibot.comms import http
from pywikibot.exceptions import APIError, ServerError
from pywikibot.site import Namespace
from pywikibot.tools import issue_deprecation_warning
from pywikibot.tools.collections import GeneratorWrapper
from pywikibot.tools.itertools import filter_unique


if TYPE_CHECKING:
    from pywikibot.site import BaseSite, NamespaceArgType
    from pywikibot.site._namespace import SingleNamespaceType
    from pywikibot.time import Timestamp

# This is the function that will be used to de-duplicate page iterators.
_filter_unique_pages = partial(
    filter_unique, key=lambda page: '{}:{}:{}'.format(*page._cmpkey()))


def AllpagesPageGenerator(
    start: str = '!',
    namespace: SingleNamespaceType = 0,
    includeredirects: typing.Literal['only'] | bool = True,
    site: BaseSite | None = None,
    total: int | None = None,
    content: bool = False,
    *,
    filterredir: bool | None = None,
) -> Iterable[pywikibot.page.Page]:
    """Iterate Page objects for all titles in a single namespace.

    .. deprecated:: 10.0
       The *includeredirects* parameter; use *filterredir* instead.
    .. seealso:: :meth:`APISite.allpages()
       <pywikibot.site._generators.GeneratorsMixin.allpages>`

    :param start: if provided, only generate pages >= this title
        lexically
    :param namespace: Namespace to retrieve pages from
    :param includeredirects: If False, redirects are not included. If
        equals the string 'only', only redirects are added. Otherwise
        redirects will be included. This parameter is deprecated; use
        *filterredir* instead.
    :param site: Site for generator results.
    :param total: Maximum number of pages to retrieve in total
    :param content: If True, load current version of each page (default
        False)
    :param filterredir: if True, only yield redirects; if False (and
        not None), only yield non-redirects (default: yield both).
    :return: a generator that yields Page objects
    :raises ValueError: *filterredir* as well as *includeredirects*
        parameters were given. Use *filterredir* only.
    """
    if site is None:
        site = pywikibot.Site()

    if filterredir is not None and includeredirects is not True:
        raise ValueError(
            f'filterredir parameter ({filterredir}) is used together with '
            f'outdated includeredirects parameter ({includeredirects}).'
        )

    # backward compatibility
    if includeredirects is not True:
        if not includeredirects:
            filterredir = False
        elif includeredirects == 'only':
            filterredir = True

        issue_deprecation_warning(
            'includeredirects parameter ({includeredirects})',
            f'filterredir={filterredir}',
            since='10.0.0'
        )

    return site.allpages(start=start, namespace=namespace,
                         filterredir=filterredir, total=total, content=content)


def PrefixingPageGenerator(
    prefix: str,
    namespace: SingleNamespaceType | None = None,
    includeredirects: typing.Literal['only'] | bool = True,
    site: BaseSite | None = None,
    total: int | None = None,
    content: bool = False,
    *,
    filterredir: bool | None = None,
) -> Iterable[pywikibot.page.Page]:
    """Prefixed Page generator.

    .. deprecated:: 10.0
       The *includeredirects* parameter; use *filterredir* instead.

    :param prefix: The prefix of the pages.
    :param namespace: Namespace to retrieve pages from
    :param includeredirects: If False, redirects are not included. If
        equals the string 'only', only redirects are added. Otherwise
        redirects will be included. This parameter is deprecated; use
        *filterredir* instead.
    :param site: Site for generator results.
    :param total: Maximum number of pages to retrieve in total
    :param content: If True, load current version of each page (default
        False)
    :param filterredir: if True, only yield redirects; if False (and
        not None), only yield non-redirects (default: yield both).
    :return: a generator that yields Page objects
    :raises ValueError: *filterredir* as well as *includeredirects*
        parameters were given. Use *filterredir* only.
    """
    if site is None:
        site = pywikibot.Site()

    prefixlink = pywikibot.Link(prefix, site)
    if namespace is None:
        namespace = prefixlink.namespace
    title = prefixlink.title

    if filterredir is not None and includeredirects is not True:
        raise ValueError(
            f'filterredir parameter ({filterredir}) is used together with '
            f'outdated includeredirects parameter ({includeredirects}).'
        )

    # backward compatibility
    if includeredirects is not True:
        if not includeredirects:
            filterredir = False
        elif includeredirects == 'only':
            filterredir = True

        issue_deprecation_warning(
            'includeredirects parameter ({includeredirects})',
            f'filterredir={filterredir}',
            since='10.0.0'
        )

    return site.allpages(prefix=title, namespace=namespace,
                         filterredir=filterredir, total=total, content=content)


def LogeventsPageGenerator(logtype: str | None = None,
                           user: str | None = None,
                           site: BaseSite | None = None,
                           namespace: SingleNamespaceType | None = None,
                           total: int | None = None,
                           start: Timestamp | None = None,
                           end: Timestamp | None = None,
                           reverse: bool = False
                           ) -> Generator[pywikibot.page.Page, None, None]:
    """Generate Pages for specified modes of logevents.

    :param logtype: Mode of logs to retrieve
    :param user: User of logs retrieved
    :param site: Site for generator results
    :param namespace: Namespace to retrieve logs from
    :param total: Maximum number of pages to retrieve in total
    :param start: Timestamp to start listing from
    :param end: Timestamp to end listing at
    :param reverse: if True, start with oldest changes (default: newest)
    """
    if site is None:
        site = pywikibot.Site()
    for entry in site.logevents(total=total, logtype=logtype, user=user,
                                namespace=namespace, start=start, end=end,
                                reverse=reverse):
        try:
            yield entry.page()
        except KeyError as e:
            pywikibot.warning('LogeventsPageGenerator: failed to load page '
                              f'for {entry.data!r}; skipping')
            pywikibot.error(e)


def NewpagesPageGenerator(site: BaseSite | None = None,
                          namespaces: NamespaceArgType = (0, ),
                          total: int | None = None
                          ) -> Generator[pywikibot.page.Page, None, None]:
    """Iterate Page objects for all new titles in a single namespace.

    :param site: Site for generator results.
    :param namespaces: namespace to retrieve pages from
    :param total: Maximum number of pages to retrieve in total
    """
    # API does not (yet) have a newpages function, so this tries to duplicate
    # it by filtering the recentchanges output
    # defaults to namespace 0 because that's how Special:Newpages defaults
    if site is None:
        site = pywikibot.Site()
    return (page for page, _ in site.newpages(namespaces=namespaces,
                                              total=total, returndict=True))


def RecentChangesPageGenerator(
    site: BaseSite | None = None,
    _filter_unique: None | (Callable[[Iterable[pywikibot.Page]],
                            Iterable[pywikibot.Page]]) = None,
    **kwargs: Any
) -> Generator[pywikibot.Page, None, None]:
    """Generate recent changes pages, including duplicates.

    For keyword parameters refer :meth:`APISite.recentchanges()
    <pywikibot.site._generators.GeneratorsMixin.recentchanges>`.

    .. versionchanged:: 8.2
       The YieldType depends on namespace. It can be
       :class:`pywikibot.Page<pywikibot.page.Page>`,
       :class:`pywikibot.User<pywikibot.page.User>`,
       :class:`pywikibot.FilePage<pywikibot.page.FilePage>` or
       :class:`pywikibot.Category<pywikibot.page.Category>`.
    .. versionchanged:: 9.4
       Ignore :class:`pywikibot.FilePage<pywikibot.page.FilePage>` if it
       raises a :exc:`ValueError` during upcast e.g. due to an invalid
       file extension.

    :param site: Site for generator results.
    """
    def upcast(gen):
        """Upcast pywikibot.Page type."""
        for rc in gen:
            # The title in a log entry may have been suppressed
            if rc['type'] == 'log' and 'title' not in rc:
                continue

            ns = rc['ns']
            if ns == Namespace.USER:
                pageclass: type[pywikibot.Page] = pywikibot.User
            elif ns == Namespace.FILE:
                pageclass = pywikibot.FilePage
            elif ns == Namespace.CATEGORY:
                pageclass = pywikibot.Category
            else:
                pageclass = pywikibot.Page
            try:
                yield pageclass(site, rc['title'])
            except ValueError:
                if pageclass != pywikibot.FilePage:
                    raise

                pywikibot.exception()

    if site is None:
        site = pywikibot.Site()

    gen = site.recentchanges(**kwargs)
    gen.request['rcprop'] = 'title'
    gen = upcast(gen)

    if _filter_unique:
        gen = _filter_unique(gen)
    return gen


def UnconnectedPageGenerator(
    site: BaseSite | None = None,
    total: int | None = None
) -> Iterable[pywikibot.page.Page]:
    """Iterate Page objects for all unconnected pages to a Wikibase repository.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    if not site.data_repository():
        raise ValueError('The given site does not have Wikibase repository.')
    return site.unconnected_pages(total=total)


def FileLinksGenerator(
    referredFilePage: pywikibot.page.FilePage,  # noqa: N803
    total: int | None = None,
    content: bool = False
) -> Iterable[pywikibot.page.Page]:
    """Yield Pages on which referredFilePage file is displayed."""
    return referredFilePage.using_pages(total=total, content=content)


def ImagesPageGenerator(
    pageWithImages: pywikibot.page.Page,  # noqa: N803
    total: int | None = None,
    content: bool = False
) -> Iterable[pywikibot.page.Page]:
    """Yield FilePages displayed on pageWithImages."""
    return pageWithImages.imagelinks(total=total, content=content)


def InterwikiPageGenerator(page: pywikibot.page.Page
                           ) -> Generator[pywikibot.page.Page, None, None]:
    """Iterate over all interwiki (non-language) links on a page."""
    return (pywikibot.Page(link) for link in page.interwiki())


def LanguageLinksPageGenerator(page: pywikibot.page.Page,
                               total: int | None = None
                               ) -> Generator[pywikibot.page.Page, None, None]:
    """Iterate over all interwiki language links on a page."""
    return (pywikibot.Page(link) for link in page.iterlanglinks(total=total))


def CategorizedPageGenerator(category: pywikibot.page.Category,
                             recurse: int | bool = False,
                             start: str | None = None,
                             total: int | None = None,
                             content: bool = False,
                             namespaces: NamespaceArgType = None,
                             ) -> Generator[pywikibot.page.Page, None, None]:
    """Yield all pages in a specific category.

    :param recurse: if not False or 0, also iterate articles in
        subcategories. If an int, limit recursion to this number of
        levels. (Example: recurse=1 will iterate articles in first-level
        subcats, but no deeper.)
    :param start: if provided, only generate pages >= this title
        lexically
    :param total: iterate no more than this number of pages in
        total (at all levels)
    :param content: if True, retrieve the content of the current version
        of each page (default False)
    """
    yield from category.articles(
        content=content,
        namespaces=namespaces,
        recurse=recurse,
        startprefix=start,
        total=total,
    )


def SubCategoriesPageGenerator(category: pywikibot.page.Category,
                               recurse: int | bool = False,
                               start: str | None = None,
                               total: int | None = None,
                               content: bool = False,
                               ) -> Generator[pywikibot.page.Page, None, None]:
    """Yield all subcategories in a specific category.

    :param recurse: if not False or 0, also iterate articles in
        subcategories. If an int, limit recursion to this number of
        levels. (Example: recurse=1 will iterate articles in first-level
        subcats, but no deeper.)
    :param start: if provided, only generate pages >= this title
        lexically
    :param total: iterate no more than this number of pages in
        total (at all levels)
    :param content: if True, retrieve the content of the current version
        of each page (default False)
    """
    # TODO: page generator could be modified to use cmstartsortkey ...
    for s in category.subcategories(recurse=recurse,
                                    total=total, content=content):
        if start is None or s.title(with_ns=False) >= start:
            yield s


def LinkedPageGenerator(
    linkingPage: pywikibot.page.Page,  # noqa: N803
    total: int | None = None,
    content: bool = False
) -> Iterable[pywikibot.page.BasePage]:
    """Yield all pages linked from a specific page.

    See :py:obj:`page.BasePage.linkedPages` for details.

    :param linkingPage: the page that links to the pages we want
    :param total: the total number of pages to iterate
    :param content: if True, retrieve the current content of each linked page
    :return: a generator that yields Page objects of pages linked to
        linkingPage
    """
    return linkingPage.linkedPages(total=total, content=content)


def _yield_titles(f: codecs.StreamReaderWriter | io.StringIO,
                  site: pywikibot.site.BaseSite
                  ) -> Generator[pywikibot.page.Page, None, None]:
    """Yield page titles from a text stream.

    :param f: text stream object
    :param site: Site for generator results.
    :return: a generator that yields Page objects of pages with titles in text
        stream
    """
    linkmatch = None
    for linkmatch in pywikibot.link_regex.finditer(f.read()):
        # If the link is in interwiki format, the Page object may reside
        # on a different Site than the default.
        # This makes it possible to work on different wikis using a single
        # text file, but also could be dangerous because you might
        # inadvertently change pages on another wiki!
        yield pywikibot.Page(pywikibot.Link(linkmatch['title'], site))

    if linkmatch is not None:
        return

    f.seek(0)
    for title in f:
        title = title.strip()
        if '|' in title:
            title = title[:title.index('|')]
        if title:
            yield pywikibot.Page(site, title)


def TextIOPageGenerator(source: str | None = None,
                        site: BaseSite | None = None,
                        ) -> Generator[pywikibot.page.Page, None, None]:
    """Iterate pages from a list in a text file or on a webpage.

    The text source must contain page links between double-square-brackets or,
    alternatively, separated by newlines. The generator will yield each
    corresponding Page object.

    :param source: the file path or URL that should be read. If no name is
                     given, the generator prompts the user.
    :param site: Site for generator results.
    """
    if source is None:
        source = pywikibot.input('Please enter the filename / URL:')
    if site is None:
        site = pywikibot.Site()
    # If source cannot be parsed as an HTTP URL, treat as local file
    if not urlparse(source).netloc:
        with codecs.open(source, 'r', config.textfile_encoding) as local_file:
            yield from _yield_titles(local_file, site)
    # Else, fetch page (page should return text in same format as that expected
    # in filename, i.e. pages separated by newlines or pages enclosed in double
    # brackets
    else:
        with io.StringIO(http.fetch(source).text) as f:
            yield from _yield_titles(f, site)


def PagesFromTitlesGenerator(iterable: Iterable[str],
                             site: BaseSite | None = None
                             ) -> Generator[pywikibot.page.Page, None, None]:
    """Generate pages from the titles (strings) yielded by iterable.

    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    for title in iterable:
        if not isinstance(title, str):
            break
        yield pywikibot.Page(pywikibot.Link(title, site))


def PagesFromPageidGenerator(
    pageids: Iterable[str],
    site: BaseSite | None = None
) -> Iterable[pywikibot.page.Page]:
    """Return a page generator from pageids.

    Pages are iterated in the same order than in the underlying pageids.
    Pageids are filtered and only one page is returned in case of
    duplicate pageid.

    :param pageids: an iterable that returns pageids, or a comma-separated
                    string of pageids (e.g. '945097,1483753,956608')
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()

    return site.load_pages_from_pageids(pageids)


def UserContributionsGenerator(username: str,
                               namespaces: NamespaceArgType = None,
                               site: BaseSite | None = None,
                               total: int | None = None,
                               _filter_unique: None | (Callable[
                                   [Iterable[pywikibot.page.Page]],
                                   Iterable[pywikibot.page.Page]]) =
                               _filter_unique_pages
                               ) -> Iterable[pywikibot.page.Page]:
    """Yield unique pages edited by user:username.

    :param total: Maximum number of pages to retrieve in total
    :param namespaces: list of namespace numbers to fetch contribs from
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()

    user = pywikibot.User(site, username)
    if not (user.isAnonymous() or user.isRegistered()):
        pywikibot.warning(
            f'User "{user.username}" does not exist on site "{site}".')

    gen = (contrib[0] for contrib in user.contributions(
        namespaces=namespaces, total=total))
    if _filter_unique:
        return _filter_unique(gen)
    return gen


def NewimagesPageGenerator(total: int | None = None,
                           site: BaseSite | None = None
                           ) -> Generator[pywikibot.page.Page, None, None]:
    """New file generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return (entry.page()
            for entry in site.logevents(logtype='upload', total=total))


def WikibaseItemGenerator(gen: Iterable[pywikibot.page.Page]
                          ) -> Generator[pywikibot.page.ItemPage, None, None]:
    """A wrapper generator used to yield Wikibase items of another generator.

    :param gen: Generator to wrap.
    :return: Wrapped generator
    """
    for page in gen:
        if isinstance(page, pywikibot.ItemPage):
            yield page
        elif page.site.data_repository() == page.site:
            # These are already items, as they have a DataSite in page.site.
            # However generator is yielding Page, so convert to ItemPage.
            # FIXME: If we've already fetched content, we should retain it
            yield pywikibot.ItemPage(page.site, page.title())
        else:
            yield pywikibot.ItemPage.fromPage(page)


def AncientPagesPageGenerator(
    total: int = 100,
    site: BaseSite | None = None
) -> Generator[pywikibot.page.Page, None, None]:
    """Ancient page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return (page for page, _ in site.ancientpages(total=total))


def UnusedFilesGenerator(
    total: int | None = None,
    site: BaseSite | None = None
) -> Iterable[pywikibot.page.FilePage]:
    """Unused files generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.unusedfiles(total=total)


def WithoutInterwikiPageGenerator(
    total: int | None = None,
    site: BaseSite | None = None
) -> Iterable[pywikibot.page.Page]:
    """Page lacking interwikis generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.withoutinterwiki(total=total)


def UnCategorizedCategoryGenerator(
    total: int | None = 100,
    site: BaseSite | None = None
) -> Iterable[pywikibot.Category]:
    """Uncategorized category generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.uncategorizedcategories(total=total)


def UnCategorizedImageGenerator(
    total: int = 100,
    site: BaseSite | None = None
) -> Iterable[pywikibot.page.FilePage]:
    """Uncategorized file generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.uncategorizedimages(total=total)


def UnCategorizedPageGenerator(
    total: int = 100,
    site: BaseSite | None = None
) -> Iterable[pywikibot.page.Page]:
    """Uncategorized page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.uncategorizedpages(total=total)


def UnCategorizedTemplateGenerator(
    total: int = 100,
    site: BaseSite | None = None
) -> Iterable[pywikibot.page.Page]:
    """Uncategorized template generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.uncategorizedtemplates(total=total)


def LonelyPagesPageGenerator(
    total: int | None = None,
    site: BaseSite | None = None
) -> Iterable[pywikibot.page.Page]:
    """Lonely page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.lonelypages(total=total)


def UnwatchedPagesPageGenerator(
    total: int | None = None,
    site: BaseSite | None = None
) -> Iterable[pywikibot.page.Page]:
    """Unwatched page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.unwatchedpages(total=total)


def page_with_property_generator(
    name: str,
    total: int | None = None,
    site: BaseSite | None = None
) -> Iterable[pywikibot.page.Page]:
    """Special:PagesWithProperty page generator.

    :param name: Property name of pages to be retrieved
    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.pages_with_property(name, total=total)


def WantedPagesPageGenerator(
    total: int = 100,
    site: BaseSite | None = None
) -> Iterable[pywikibot.page.Page]:
    """Wanted page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.wantedpages(total=total)


def DeadendPagesPageGenerator(
    total: int = 100,
    site: BaseSite | None = None
) -> Iterable[pywikibot.page.Page]:
    """Dead-end page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.deadendpages(total=total)


def LongPagesPageGenerator(total: int = 100,
                           site: BaseSite | None = None
                           ) -> Generator[pywikibot.page.Page, None, None]:
    """Long page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return (page for page, _ in site.longpages(total=total))


def ShortPagesPageGenerator(total: int = 100,
                            site: BaseSite | None = None
                            ) -> Generator[pywikibot.page.Page, None, None]:
    """Short page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return (page for page, _ in site.shortpages(total=total))


def RandomPageGenerator(
    total: int | None = None,
    site: BaseSite | None = None,
    namespaces: NamespaceArgType = None
) -> Iterable[pywikibot.page.Page]:
    """Random page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.randompages(total=total, namespaces=namespaces)


def RandomRedirectPageGenerator(
    total: int | None = None,
    site: BaseSite | None = None,
    namespaces: NamespaceArgType = None,
) -> Iterable[pywikibot.page.Page]:
    """Random redirect generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.randompages(total=total, namespaces=namespaces,
                            redirects=True)


def LinksearchPageGenerator(
    url: str,
    namespaces: NamespaceArgType = None,
    total: int | None = None,
    site: BaseSite | None = None,
    protocol: str | None = None
) -> Iterable[pywikibot.page.Page]:
    """Yield all pages that link to a certain URL.

    :param url: The URL to search for (with or without the protocol
        prefix); this may include a '*' as a wildcard, only at the start
        of the hostname
    :param namespaces: list of namespace numbers to fetch contribs from
    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results
    :param protocol: Protocol to search for, likely http or https, http
        by default. Full list shown on Special:LinkSearch wikipage.
    """
    if site is None:
        site = pywikibot.Site()
    return site.exturlusage(url, namespaces=namespaces, protocol=protocol,
                            total=total, content=False)


def SearchPageGenerator(
    query: str,
    total: int | None = None,
    namespaces: NamespaceArgType = None,
    site: BaseSite | None = None,
    **kwargs
) -> Iterable[pywikibot.page.Page]:
    r"""Yield pages from the MediaWiki internal search engine.

    .. versionchanged:: 10.0
       Keyword arguments *content*, *sort* and *where* was added.

    .. seealso:: :meth:`site.search()
       <pywikibot.site._generators.GeneratorsMixin.search>`

    :param query: the text to search for
    :param total: Maximum number of pages to retrieve in total
    :param namespaces: search only in these namespaces (defaults to all)
    :param site: Site for generator results.
    :keyword str \| None where: Where to search; value must be one of the
        given literals or None (many wikis do not support all search
        types)
    :keyword bool content: if True, load the current content of each
        iterated page (default False)
    :keyword sort: Set the sort order of returned results. If None is
        given, 'none' is used. Default is sort by relevance.
    """
    if site is None:
        site = pywikibot.Site()
    return site.search(query, total=total, namespaces=namespaces, **kwargs)


def LiveRCPageGenerator(site: BaseSite | None = None,
                        total: int | None = None
                        ) -> Generator[pywikibot.page.Page, None, None]:
    """Yield pages from a socket.io RC stream.

    Generates pages based on the EventStreams Server-Sent-Event (SSE) recent
    changes stream.
    The Page objects will have an extra property ._rcinfo containing the
    literal rc data. This can be used to e.g. filter only new pages. See
    `pywikibot.comms.eventstreams.rc_listener` for details on the .rcinfo
    format.

    :param site: site to return recent changes for
    :param total: the maximum number of changes to return
    """
    if site is None:
        site = pywikibot.Site()

    from pywikibot.comms.eventstreams import site_rc_listener

    for entry in site_rc_listener(site, total=total):
        # The title in a log entry may have been suppressed
        if 'title' not in entry and entry['type'] == 'log':
            continue
        page = pywikibot.Page(site, entry['title'], entry['namespace'])
        page._rcinfo = entry  # type: ignore[attr-defined]
        yield page


# following classes just ported from version 1 without revision; not tested


class GoogleSearchPageGenerator(GeneratorWrapper):

    """Page generator using Google search results.

    To use this generator, you need to install the package 'google':

        :py:obj:`https://pypi.org/project/google`

    This package has been available since 2010, hosted on GitHub
    since 2012, and provided by PyPI since 2013.

    As there are concerns about Google's Terms of Service, this
    generator prints a warning for each query.

    .. versionchanged:: 7.6
       subclassed from :class:`tools.collections.GeneratorWrapper`
    """

    def __init__(self, query: str | None = None,
                 site: BaseSite | None = None) -> None:
        """Initializer.

        :param site: Site for generator results.
        """
        self.query = query or pywikibot.input('Please enter the search query:')
        if site is None:
            site = pywikibot.Site()
        self.site = site
        self._google_query = None

    @staticmethod
    def queryGoogle(query: str) -> Generator[str, None, None]:
        """Perform a query using python package 'google'.

        The terms of service as at June 2014 give two conditions that
        may apply to use of search:

            1. Don't access [Google Services] using a method other than
               the interface and the instructions that [they] provide.
            2. Don't remove, obscure, or alter any legal notices
               displayed in or along with [Google] Services.

        Both of those issues should be managed by the package 'google',
        however Pywikibot will at least ensure the user sees the TOS
        in order to comply with the second condition.
        """
        try:
            import google
        except ImportError:
            pywikibot.error('generator GoogleSearchPageGenerator '
                            "depends on package 'google'.\n"
                            'To install, please run: pip install google.')
            sys.exit(1)
        pywikibot.warning('Please read http://www.google.com/accounts/TOS')
        yield from google.search(query)

    @property
    def generator(self) -> Generator[pywikibot.page.Page, None, None]:
        """Yield results from :meth:`queryGoogle` query.

        Google contains links in the format:
        https://de.wikipedia.org/wiki/en:Foobar

        .. versionchanged:: 7.6
           changed from iterator method to generator property
        """
        # restrict query to local site
        local_query = f'{self.query} site:{self.site.hostname()}'
        base = f'http://{self.site.hostname()}{self.site.articlepath}'
        pattern = base.replace('{}', '(.+)')
        for url in self.queryGoogle(local_query):
            m = re.search(pattern, url)
            if m:
                page = pywikibot.Page(pywikibot.Link(m[1], self.site))
                if page.site == self.site:
                    yield page


def MySQLPageGenerator(query: str, site: BaseSite | None = None,
                       verbose: bool | None = None
                       ) -> Generator[pywikibot.page.Page, None, None]:
    """Yield a list of pages based on a MySQL query.

    The query should return two columns, page namespace and page title pairs
    from some table. An example query that yields all ns0 pages might look
    like::

        SELECT
         page_namespace,
         page_title
        FROM page
        WHERE page_namespace = 0;

    .. seealso:: :manpage:`MySQL`

    :param query: MySQL query to execute
    :param site: Site object
    :param verbose: if True, print query to be executed;
        if None, config.verbose_output will be used.
    :return: generator which yields pywikibot.Page
    """
    from pywikibot.data import mysql

    if site is None:
        site = pywikibot.Site()

    row_gen = mysql.mysql_query(query,
                                dbname=site.dbName(),
                                verbose=verbose)

    for row in row_gen:
        namespace_number, page_name = row
        page_name = page_name.decode(site.encoding())
        page = pywikibot.Page(site, page_name, ns=int(namespace_number))
        yield page


def SupersetPageGenerator(query: str,
                          site: BaseSite | None = None,
                          schema_name: str | None = None,
                          database_id: int | None = None
                          ) -> Iterator[pywikibot.page.Page]:
    """Generate pages that result from the given SPARQL query.

    Pages are generated using site in following order:

    1. site retrieved using page_wikidb column in SQL result
    2. site as parameter
    3. site retrieved using schema_name

    SQL columns used are

    - page_id
    - page_namespace + page_title
    - page_wikidb

    Example SQL queries

    .. code-block:: sql

        SELECT
            gil_wiki AS page_wikidb,
            gil_page AS page_id
        FROM globalimagelinks
        GROUP BY gil_wiki
        LIMIT 10

    OR

    .. code-block:: sql

        SELECT
            page_id
        FROM page
        LIMIT 10

    OR

    .. code-block:: sql

        SELECT
            page_namespace,
            page_title
        FROM page
        LIMIT 10

    .. versionadded:: 9.2

    :param query: the SQL query string.
    :param site: Site for generator results.
    :param schema_name: target superset schema name
    :param database_id: target superset database id
    """
    from pywikibot.data.superset import SupersetQuery

    # Do not pass site to superset if schema_name is defined.
    # The user may use schema_name to point to different
    # wikimedia db on purpose and use site for
    # generating result pages.

    superset_site = None if schema_name else site

    superset = SupersetQuery(site=superset_site,
                             schema_name=schema_name,
                             database_id=database_id)

    try:
        rows = superset.query(query)
    except Exception as e:
        pywikibot.error(f'Error executing query: {query}\n{e}')
        return

    sites = {}

    # If there is no site then retrieve it using schema_name
    if not site:
        if not schema_name:
            raise TypeError('Schema name or site must be provided.')

        wikidb = re.sub('_p$', '', schema_name)
        site = pywikibot.site.APISite.fromDBName(wikidb)

    for row in rows:
        # If page_wikidb column in SQL result then use it to retrieve site
        if 'page_wikidb' in row:
            # remove "_p" suffix
            wikidb = re.sub('_p$', '', row['page_wikidb'])

            # Caching sites
            if wikidb not in sites:
                try:
                    sites[wikidb] = pywikibot.site.APISite.fromDBName(wikidb)
                except ValueError:
                    msg = f'Cannot parse a site from {wikidb} for {row}.'
                    pywikibot.warning(msg)
                    continue
            site = sites[wikidb]

        # Generate page objects

        # Create page object from page_id
        if 'page_id' in row:
            page_ids = [row['page_id']]
            pages = site.load_pages_from_pageids(page_ids)
            for page in pages:
                yield page

        # Create page object from page_namespace + page_title
        elif 'page_title' in rows[0] and 'page_namespace' in rows[0]:
            page_namespace = int(row['page_namespace'])
            page_title = row['page_title']
            page = pywikibot.Page(site, page_title, ns=page_namespace)
            yield page

        else:
            raise ValueError('The SQL result is in wrong format.')


class XMLDumpPageGenerator(abc.Iterator):  # type: ignore[type-arg]

    """Xml iterator that yields Page objects.

    .. versionadded:: 7.2
       the `content` parameter

    :param filename: filename of XML dump
    :param start: skip entries below that value
    :param namespaces: namespace filter
    :param site: current site for the generator
    :param text_predicate: a callable with entry.text as parameter and boolean
        as result to indicate the generator should return the page or not
    :param content: If True, assign old page content to Page.text

    :ivar skipping: True if start parameter is given, else False
    :ivar parser: holds the xmlreader.XmlDump parse method
    """

    def __init__(
        self,
        filename: str,
        start: str | None = None,
        namespaces: NamespaceArgType = None,
        site: BaseSite | None = None,
        text_predicate: Callable[[str], bool] | None = None,
        content=False,
    ) -> None:
        """Initializer."""
        self.text_predicate = text_predicate
        self.content = content
        self.skipping = bool(start)

        self.start: str | None = None
        if start is not None and self.skipping:
            self.start = start.replace('_', ' ')

        self.site = site or pywikibot.Site()
        if not namespaces:
            self.namespaces = self.site.namespaces
        else:
            self.namespaces = self.site.namespaces.resolve(namespaces)
        dump = xmlreader.XmlDump(filename, on_error=pywikibot.error)
        self.parser = dump.parse()

    def __next__(self) -> pywikibot.page.Page:
        """Get next Page."""
        while True:
            entry = next(self.parser)
            if self.skipping:
                if entry.title < self.start:
                    continue
                self.skipping = False
            page = pywikibot.Page(self.site, entry.title)
            if page.namespace() not in self.namespaces:
                continue
            if not self.text_predicate or self.text_predicate(entry.text):
                if self.content:
                    page.text = entry.text
                return page


def YearPageGenerator(start: int = 1, end: int = 2050,
                      site: BaseSite | None = None
                      ) -> Generator[pywikibot.page.Page, None, None]:
    """Year page generator.

    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    pywikibot.info(f'Starting with year {start}')
    for i in range(start, end + 1):
        if i % 100 == 0:
            pywikibot.info(f'Preparing {i}...')
        # There is no year 0
        if i != 0:
            current_year = date.formatYear(site.lang, i)
            yield pywikibot.Page(pywikibot.Link(current_year, site))


def DayPageGenerator(start_month: int = 1, end_month: int = 12,
                     site: BaseSite | None = None, year: int = 2000
                     ) -> Generator[pywikibot.page.Page, None, None]:
    """Day page generator.

    :param site: Site for generator results.
    :param year: considering leap year.
    """
    if site is None:
        site = pywikibot.Site()
    lang = site.lang
    first_page = pywikibot.Page(site, date.format_date(start_month, 1, lang))
    pywikibot.info(f'Starting with {first_page.title(as_link=True)}')
    for month in range(start_month, end_month + 1):
        for day in range(1, calendar.monthrange(year, month)[1] + 1):
            yield pywikibot.Page(
                pywikibot.Link(date.format_date(month, day, lang), site))


def WikidataPageFromItemGenerator(
    gen: Iterable[pywikibot.page.ItemPage],
    site: pywikibot.site.BaseSite,
) -> Generator[pywikibot.page.Page, None, None]:
    """Generate pages from site based on sitelinks of item pages.

    :param gen: generator of :py:obj:`pywikibot.ItemPage`
    :param site: Site for generator results.
    """
    repo = site.data_repository()
    for batch in batched(gen, 50):
        req = {'ids': [item.id for item in batch],
               'sitefilter': site.dbName(),
               'action': 'wbgetentities',
               'props': 'sitelinks'}

        wbrequest = repo.simple_request(**req)
        wbdata = wbrequest.submit()
        entities = (item for item in wbdata['entities'].values() if
                    'sitelinks' in item and site.dbName() in item['sitelinks'])
        sitelinks = (item['sitelinks'][site.dbName()]['title']
                     for item in entities)
        for sitelink in sitelinks:
            yield pywikibot.Page(site, sitelink)


def WikidataSPARQLPageGenerator(query: str,
                                site: BaseSite | None = None,
                                item_name: str = 'item',
                                endpoint: str | None = None,
                                entity_url: str | None = None,
                                result_type: Any = set
                                ) -> Iterator[pywikibot.page.Page]:
    """Generate pages that result from the given SPARQL query.

    :param query: the SPARQL query string.
    :param site: Site for generator results.
    :param item_name: name of the item in the SPARQL query
    :param endpoint: SPARQL endpoint URL
    :param entity_url: URL prefix for any entities returned in a query.
    :param result_type: type of the iterable in which
             SPARQL results are stored (default set)
    """
    from pywikibot.data import sparql

    if site is None:
        site = pywikibot.Site()
    repo = site.data_repository()
    dependencies = {'endpoint': endpoint, 'entity_url': entity_url}
    if not endpoint or not entity_url:
        dependencies['repo'] = repo
    query_object = sparql.SparqlQuery(**dependencies)  # type: ignore[arg-type]
    data = query_object.get_items(query,
                                  item_name=item_name,
                                  result_type=result_type)
    entities = (repo.get_entity_for_entity_id(entity) for entity in data)
    if isinstance(site, pywikibot.site.DataSite):
        return entities

    return WikidataPageFromItemGenerator(entities, site)


def WikibaseSearchItemPageGenerator(
    text: str,
    language: str | None = None,
    total: int | None = None,
    site: BaseSite | None = None,
) -> Generator[pywikibot.page.ItemPage, None, None]:
    """Generate pages that contain the provided text.

    :param text: Text to look for.
    :param language: Code of the language to search in. If not specified,
        value from pywikibot.config.data_lang is used.
    :param total: Maximum number of pages to retrieve in total, or None in
        case of no limit.
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    if language is None:
        language = site.lang
    repo = site.data_repository()

    data = repo.search_entities(text, language, total=total)
    return (pywikibot.ItemPage(repo, item['id']) for item in data)


class PetScanPageGenerator(GeneratorWrapper):

    """Queries PetScan to generate pages.

    .. seealso:: https://petscan.wmflabs.org/
    .. versionadded:: 3.0
    .. versionchanged:: 7.6
       subclassed from :class:`tools.collections.GeneratorWrapper`
    """

    def __init__(
        self,
        categories: Sequence[str],
        subset_combination: bool = True,
        namespaces: Iterable[int | pywikibot.site.Namespace] | None = None,
        site: BaseSite | None = None,
        extra_options: dict[Any, Any] | None = None
    ) -> None:
        """Initializer.

        :param categories: List of category names to retrieve pages from
        :param subset_combination: Combination mode.
            If True, returns the intersection of the results of the categories,
            else returns the union of the results of the categories
        :param namespaces: List of namespaces to search in
            (default is None, meaning all namespaces)
        :param site: Site to operate on
            (default is the default site from the user config)
        :param extra_options: Dictionary of extra options to use (optional)
        """
        if site is None:
            site = pywikibot.Site()

        self.site = site
        self.opts = self.buildQuery(categories, subset_combination,
                                    namespaces, extra_options)

    def buildQuery(self, categories: Sequence[str], subset_combination: bool,
                   namespaces: Iterable[int | pywikibot.site.Namespace] | None,
                   extra_options: dict[Any, Any] | None) -> dict[str, Any]:
        """Get the querystring options to query PetScan.

        :param categories: List of categories (as strings)
        :param subset_combination: Combination mode.
            If True, returns the intersection of the results of the categories,
            else returns the union of the results of the categories
        :param namespaces: List of namespaces to search in
        :param extra_options: Dictionary of extra options to use
        :return: Dictionary of querystring parameters to use in the query
        """
        extra_options = extra_options or {}

        query = {
            'language': self.site.code,
            'project': self.site.hostname().split('.')[-2],
            'combination': 'subset' if subset_combination else 'union',
            'categories': '\r\n'.join(categories),
            'format': 'json',
            'doit': ''
        }

        if namespaces:
            for namespace in namespaces:
                query[f'ns[{int(namespace)}]'] = 1

        query_final = query.copy()
        query_final.update(extra_options)

        return query_final

    def query(self) -> Generator[dict[str, Any], None, None]:
        """Query PetScan.

        .. versionchanged:: 7.4
           raises :class:`APIError` if query returns an error message.

        :raises ServerError: Either ReadTimeout or server status error
        :raises APIError: error response from petscan
        """
        url = 'https://petscan.wmflabs.org'

        try:
            req = http.fetch(url, params=self.opts)
        except ReadTimeout:
            raise ServerError(f'received ReadTimeout from {url}')

        server_err = HTTPStatus.INTERNAL_SERVER_ERROR
        if server_err <= req.status_code < server_err + 100:
            raise ServerError(
                f'received {req.status_code} status from {req.url}')

        data = req.json()
        if 'error' in data:
            raise APIError('Petscan', data['error'], **self.opts)

        raw_pages = data['*'][0]['a']['*']
        yield from raw_pages

    @property
    def generator(self) -> Generator[pywikibot.page.Page, None, None]:
        """Yield results from :meth:`query`.

        .. versionchanged:: 7.6
           changed from iterator method to generator property
        """
        for raw_page in self.query():
            yield pywikibot.Page(self.site, raw_page['title'],
                                 int(raw_page['namespace']))


class PagePilePageGenerator(GeneratorWrapper):

    """Queries PagePile to generate pages.

    .. seealso:: https://pagepile.toolforge.org/
    .. versionadded:: 9.0
    """

    def __init__(self, id: int):
        """Initializer.

        :param id: The PagePile id to query
        """
        self.opts = self.buildQuery(id)

    def buildQuery(self, id: int):
        """Get the querystring options to query PagePile.

        :param id: int
        :return: Dictionary of querystring parameters to use in the query
        """
        query = {
            'id': id,
            'action': 'get_data',
            'format': 'json',
            'doit': ''
        }

        return query

    def query(self) -> Generator[str, None, None]:
        """Query PagePile.

        :raises ServerError: Either ReadTimeout or server status error
        :raises APIError: error response from petscan
        """
        url = 'https://pagepile.toolforge.org/api.php'

        req = http.fetch(url, params=self.opts)

        data = req.json()
        if 'error' in data:
            raise APIError('PagePile', data['error'], **self.opts)

        self.site = pywikibot.site.APISite.fromDBName(data['wiki'])
        raw_pages = data['pages']
        yield from raw_pages

    @property
    def generator(self) -> Generator[pywikibot.page.Page, None, None]:
        """Yield results from :meth:`query`."""
        for raw_page in self.query():
            page = pywikibot.Page(self.site, raw_page)
            yield page
