"""Page filter generators provided by the pagegenerators module."""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import calendar
import codecs
import io
import re
import sys
from collections import abc
from functools import partial
from http import HTTPStatus
from typing import Any, Optional, Union
from urllib.parse import urlparse

from requests.exceptions import ReadTimeout

import pywikibot
from pywikibot import config, date, xmlreader
from pywikibot.backports import (
    Callable,
    Dict,
    Iterable,
    Iterator,
    List,
    Sequence,
    Tuple,
)
from pywikibot.comms import http
from pywikibot.exceptions import APIError, ServerError
from pywikibot.tools import deprecated
from pywikibot.tools.collections import GeneratorWrapper
from pywikibot.tools.itertools import filter_unique, itergroup


OPT_SITE_TYPE = Optional['pywikibot.site.BaseSite']
OPT_TIMESTAMP_TYPE = Optional['pywikibot.Timestamp']
NAMESPACE_OR_INT_TYPE = Union[int, 'pywikibot.site.Namespace']
NAMESPACE_OR_STR_TYPE = Union[str, 'pywikibot.site.Namespace']


# This is the function that will be used to de-duplicate page iterators.
_filter_unique_pages = partial(
    filter_unique, key=lambda page: '{}:{}:{}'.format(*page._cmpkey()))


def AllpagesPageGenerator(
    start: str = '!',
    namespace: int = 0,
    includeredirects: Union[str, bool] = True,
    site: OPT_SITE_TYPE = None,
    total: Optional[int] = None, content: bool = False
) -> Iterable['pywikibot.page.Page']:
    """Iterate Page objects for all titles in a single namespace.

    If includeredirects is False, redirects are not included. If
    includeredirects equals the string 'only', only redirects are added.

    :param total: Maximum number of pages to retrieve in total
    :param content: If True, load current version of each page (default False)
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()

    filterredir: Optional[bool] = None
    if not includeredirects:
        filterredir = False
    elif includeredirects == 'only':
        filterredir = True

    return site.allpages(start=start, namespace=namespace,
                         filterredir=filterredir, total=total, content=content)


def PrefixingPageGenerator(prefix: str,
                           namespace: NAMESPACE_OR_INT_TYPE = None,
                           includeredirects: Union[None, bool, str] = True,
                           site: OPT_SITE_TYPE = None,
                           total: Optional[int] = None,
                           content: bool = False
                           ) -> Iterable['pywikibot.page.Page']:
    """
    Prefixed Page generator.

    :param prefix: The prefix of the pages.
    :param namespace: Namespace to retrieve pages from
    :param includeredirects: If includeredirects is None, False or an empty
        string, redirects will not be found. If includeredirects equals the
        string 'only', only redirects will be found. Otherwise redirects will
        be included.
    :param site: Site for generator results.
    :param total: Maximum number of pages to retrieve in total
    :param content: If True, load current version of each page (default False)
    :return: a generator that yields Page objects
    """
    if site is None:
        site = pywikibot.Site()

    prefixlink = pywikibot.Link(prefix, site)
    if namespace is None:
        namespace = prefixlink.namespace
    title = prefixlink.title

    filterredir: Optional[bool] = None
    if not includeredirects:
        filterredir = False
    elif includeredirects == 'only':
        filterredir = True

    return site.allpages(prefix=title, namespace=namespace,
                         filterredir=filterredir, total=total, content=content)


def LogeventsPageGenerator(logtype: Optional[str] = None,
                           user: Optional[str] = None,
                           site: OPT_SITE_TYPE = None,
                           namespace: Optional[int] = None,
                           total: Optional[int] = None,
                           start: OPT_TIMESTAMP_TYPE = None,
                           end: OPT_TIMESTAMP_TYPE = None,
                           reverse: bool = False
                           ) -> Iterator['pywikibot.page.Page']:
    """
    Generate Pages for specified modes of logevents.

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
            pywikibot.warning('LogeventsPageGenerator: '
                              'failed to load page for {!r}; skipping'
                              .format(entry.data))
            pywikibot.error(e)


def NewpagesPageGenerator(site: OPT_SITE_TYPE = None,
                          namespaces: Tuple[int] = (0, ),
                          total: Optional[int] = None
                          ) -> Iterator['pywikibot.page.Page']:
    """
    Iterate Page objects for all new titles in a single namespace.

    :param site: Site for generator results.
    :param namespace: namespace to retrieve pages from
    :param total: Maxmium number of pages to retrieve in total
    """
    # API does not (yet) have a newpages function, so this tries to duplicate
    # it by filtering the recentchanges output
    # defaults to namespace 0 because that's how Special:Newpages defaults
    if site is None:
        site = pywikibot.Site()
    return (page for page, _ in site.newpages(namespaces=namespaces,
                                              total=total, returndict=True))


def RecentChangesPageGenerator(site: OPT_SITE_TYPE = None,
                               _filter_unique: Optional[Callable[
                                   [Iterable['pywikibot.page.Page']],
                                   Iterable['pywikibot.page.Page']]] = None,
                               **kwargs: Any
                               ) -> Iterable['pywikibot.page.Page']:
    """
    Generate pages that are in the recent changes list, including duplicates.

    For parameters refer pywikibot.site.recentchanges

    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()

    gen = site.recentchanges(**kwargs)
    gen.request['rcprop'] = 'title'
    gen = (pywikibot.Page(site, rc['title'])
           for rc in gen if rc['type'] != 'log' or 'title' in rc)

    if _filter_unique:
        gen = _filter_unique(gen)
    return gen


def UnconnectedPageGenerator(
    site: OPT_SITE_TYPE = None,
    total: Optional[int] = None
) -> Iterable['pywikibot.page.Page']:
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
    referredFilePage: 'pywikibot.page.FilePage',  # noqa: N803
    total: Optional[int] = None,
    content: bool = False
) -> Iterable['pywikibot.page.Page']:
    """Yield Pages on which referredFilePage file is displayed."""
    return referredFilePage.using_pages(total=total, content=content)


def ImagesPageGenerator(
    pageWithImages: 'pywikibot.page.Page',  # noqa: N803
    total: Optional[int] = None,
    content: bool = False
) -> Iterable['pywikibot.page.Page']:
    """Yield FilePages displayed on pageWithImages."""
    return pageWithImages.imagelinks(total=total, content=content)


def InterwikiPageGenerator(page: 'pywikibot.page.Page'
                           ) -> Iterable['pywikibot.page.Page']:
    """Iterate over all interwiki (non-language) links on a page."""
    return (pywikibot.Page(link) for link in page.interwiki())


def LanguageLinksPageGenerator(page: 'pywikibot.page.Page',
                               total: Optional[int] = None
                               ) -> Iterable['pywikibot.page.Page']:
    """Iterate over all interwiki language links on a page."""
    return (pywikibot.Page(link) for link in page.iterlanglinks(total=total))


def CategorizedPageGenerator(category: pywikibot.page.Category,
                             recurse: Union[int, bool] = False,
                             start: Optional[str] = None,
                             total: Optional[int] = None,
                             content: bool = False,
                             namespaces: Optional[Sequence[int]] = None
                             ) -> Iterable['pywikibot.page.Page']:
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
    kwargs = {
        'content': content,
        'namespaces': namespaces,
        'recurse': recurse,
        'startprefix': start,
        'total': total,
    }
    yield from category.articles(**kwargs)


def SubCategoriesPageGenerator(category: 'pywikibot.page.Category',
                               recurse: Union[int, bool] = False,
                               start: Optional[str] = None,
                               total: Optional[int] = None,
                               content: bool = False
                               ) -> Iterable['pywikibot.page.Page']:
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
    linkingPage: 'pywikibot.page.Page',  # noqa: N803
    total: Optional[int] = None,
    content: bool = False
) -> Iterable['pywikibot.page.Page']:
    """Yield all pages linked from a specific page.

    See :py:obj:`page.BasePage.linkedPages` for details.

    :param linkingPage: the page that links to the pages we want
    :param total: the total number of pages to iterate
    :param content: if True, retrieve the current content of each linked page
    :return: a generator that yields Page objects of pages linked to
        linkingPage
    """
    return linkingPage.linkedPages(total=total, content=content)


def _yield_titles(f: Union[codecs.StreamReaderWriter, io.StringIO],
                  site: pywikibot.site.BaseSite
                  ) -> Iterable['pywikibot.page.Page']:
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


def TextIOPageGenerator(source: Optional[str] = None,
                        site: OPT_SITE_TYPE = None
                        ) -> Iterable['pywikibot.page.Page']:
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
                             site: OPT_SITE_TYPE = None
                             ) -> Iterable['pywikibot.page.Page']:
    """
    Generate pages from the titles (strings) yielded by iterable.

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
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
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
                               namespaces: Optional[List[int]] = None,
                               site: OPT_SITE_TYPE = None,
                               total: Optional[int] = None,
                               _filter_unique: Optional[Callable[
                                   [Iterable['pywikibot.page.Page']],
                                   Iterable['pywikibot.page.Page']]] =
                               _filter_unique_pages
                               ) -> Iterator['pywikibot.page.Page']:
    """Yield unique pages edited by user:username.

    :param total: Maximum number of pages to retrieve in total
    :param namespaces: list of namespace numbers to fetch contribs from
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()

    user = pywikibot.User(site, username)
    if not (user.isAnonymous() or user.isRegistered()):
        pywikibot.warning('User "{}" does not exist on site "{}".'
                          .format(user.username, site))

    gen = (contrib[0] for contrib in user.contributions(
        namespaces=namespaces, total=total))
    if _filter_unique:
        return _filter_unique(gen)
    return gen


def NewimagesPageGenerator(total: Optional[int] = None,
                           site: OPT_SITE_TYPE = None
                           ) -> Iterator['pywikibot.page.Page']:
    """
    New file generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return (entry.page()
            for entry in site.logevents(logtype='upload', total=total))


def WikibaseItemGenerator(gen: Iterable['pywikibot.page.Page']
                          ) -> Iterator['pywikibot.page.ItemPage']:
    """
    A wrapper generator used to yield Wikibase items of another generator.

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
    site: OPT_SITE_TYPE = None
) -> Iterator['pywikibot.page.Page']:
    """
    Ancient page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return (page for page, _ in site.ancientpages(total=total))


def UnusedFilesGenerator(
    total: Optional[int] = None,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.FilePage']:
    """Unused files generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.unusedfiles(total=total)


def WithoutInterwikiPageGenerator(
    total: Optional[int] = None,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
    """Page lacking interwikis generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.withoutinterwiki(total=total)


def UnCategorizedCategoryGenerator(
    total: Optional[int] = 100,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.Category']:
    """Uncategorized category generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.uncategorizedcategories(total=total)


def UnCategorizedImageGenerator(
    total: int = 100,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.FilePage']:
    """Uncategorized file generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.uncategorizedimages(total=total)


def UnCategorizedPageGenerator(
    total: int = 100,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
    """Uncategorized page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.uncategorizedpages(total=total)


def UnCategorizedTemplateGenerator(
    total: int = 100,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
    """Uncategorized template generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.uncategorizedtemplates(total=total)


def LonelyPagesPageGenerator(
    total: Optional[int] = None,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
    """Lonely page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.lonelypages(total=total)


def UnwatchedPagesPageGenerator(
    total: Optional[int] = None,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
    """Unwatched page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.unwatchedpages(total=total)


def page_with_property_generator(
    name: str,
    total: Optional[int] = None,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
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
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
    """Wanted page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.wantedpages(total=total)


def DeadendPagesPageGenerator(
    total: int = 100,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
    """Dead-end page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.deadendpages(total=total)


def LongPagesPageGenerator(total: int = 100,
                           site: OPT_SITE_TYPE = None
                           ) -> Iterator['pywikibot.page.Page']:
    """
    Long page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return (page for page, _ in site.longpages(total=total))


def ShortPagesPageGenerator(total: int = 100,
                            site: OPT_SITE_TYPE = None
                            ) -> Iterator['pywikibot.page.Page']:
    """
    Short page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return (page for page, _ in site.shortpages(total=total))


def RandomPageGenerator(
    total: Optional[int] = None,
    site: OPT_SITE_TYPE = None,
    namespaces: Optional[Sequence[NAMESPACE_OR_STR_TYPE]] = None
) -> Iterable['pywikibot.page.Page']:
    """Random page generator.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.randompages(total=total, namespaces=namespaces)


def RandomRedirectPageGenerator(
    total: Optional[int] = None,
    site: OPT_SITE_TYPE = None,
    namespaces: Optional[
        Sequence[NAMESPACE_OR_STR_TYPE]] = None
) -> Iterable['pywikibot.page.Page']:
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
    namespaces: Optional[List[int]] = None,
    total: Optional[int] = None,
    site: OPT_SITE_TYPE = None,
    protocol: Optional[str] = None
) -> Iterable['pywikibot.page.Page']:
    """Yield all pages that link to a certain URL.

    :param url: The URL to search for (with ot without the protocol prefix);
            this may include a '*' as a wildcard, only at the start of the
            hostname
    :param namespaces: list of namespace numbers to fetch contribs from
    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results
    :param protocol: Protocol to search for, likely http or https, http by
        default. Full list shown on Special:LinkSearch wikipage
    """
    if site is None:
        site = pywikibot.Site()
    return site.exturlusage(url, namespaces=namespaces, protocol=protocol,
                            total=total, content=False)


def SearchPageGenerator(
    query: str,
    total: Optional[int] = None,
    namespaces: Optional[Sequence[NAMESPACE_OR_STR_TYPE]] = None,
    site: OPT_SITE_TYPE = None
) -> Iterable['pywikibot.page.Page']:
    """Yield pages from the MediaWiki internal search engine.

    :param total: Maximum number of pages to retrieve in total
    :param site: Site for generator results.
    """
    if site is None:
        site = pywikibot.Site()
    return site.search(query, total=total, namespaces=namespaces)


def LiveRCPageGenerator(site: OPT_SITE_TYPE = None,
                        total: Optional[int] = None
                        ) -> Iterator['pywikibot.page.Page']:
    """
    Yield pages from a socket.io RC stream.

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
        page._rcinfo = entry
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

    def __init__(self, query: Optional[str] = None,
                 site: OPT_SITE_TYPE = None) -> None:
        """
        Initializer.

        :param site: Site for generator results.
        """
        self.query = query or pywikibot.input('Please enter the search query:')
        if site is None:
            site = pywikibot.Site()
        self.site = site
        self._google_query = None

    @staticmethod
    def queryGoogle(query: str) -> Iterator[Any]:
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
    def generator(self) -> Iterator['pywikibot.page.Page']:
        """Yield results from :meth:`queryGoogle` query.

        Google contains links in the format:
        https://de.wikipedia.org/wiki/en:Foobar

        .. versionchanged:: 7.6
           changed from iterator method to generator property
        """
        # restrict query to local site
        local_query = f'{self.query} site:{self.site.hostname()}'
        base = 'http://{}{}'.format(self.site.hostname(),
                                    self.site.articlepath)
        pattern = base.replace('{}', '(.+)')
        for url in self.queryGoogle(local_query):
            m = re.search(pattern, url)
            if m:
                page = pywikibot.Page(pywikibot.Link(m[1], self.site))
                if page.site == self.site:
                    yield page


def MySQLPageGenerator(query: str, site: OPT_SITE_TYPE = None,
                       verbose: Optional[bool] = None
                       ) -> Iterator['pywikibot.page.Page']:
    """
    Yield a list of pages based on a MySQL query.

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

    def __init__(self, filename: str, start: Optional[str] = None,
                 namespaces: Union[
                     None, NAMESPACE_OR_STR_TYPE,
                     Sequence[NAMESPACE_OR_STR_TYPE]] = None,
                 site: OPT_SITE_TYPE = None,
                 text_predicate: Optional[Callable[[str], bool]] = None,
                 content=False) -> None:
        """Initializer."""
        self.text_predicate = text_predicate
        self.content = content
        self.skipping = bool(start)

        self.start: Optional[str] = None
        if start is not None and self.skipping:
            self.start = start.replace('_', ' ')

        self.site = site or pywikibot.Site()
        if not namespaces:
            self.namespaces = self.site.namespaces
        else:
            self.namespaces = self.site.namespaces.resolve(namespaces)
        dump = xmlreader.XmlDump(filename, on_error=pywikibot.error)
        self.parser = dump.parse()

    def __next__(self) -> 'pywikibot.page.Page':
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


@deprecated('XMLDumpPageGenerator with content=True parameter', since='7.2.0')
class XMLDumpOldPageGenerator(XMLDumpPageGenerator):

    """Xml iterator that yields Page objects with old text loaded.

    .. deprecated:: 7.2
       :class:`XMLDumpPageGenerator` with `content` parameter should be
       used instead
    """

    def __init__(self, *args, **kwargs):
        """Initializer."""
        super().__init__(*args, **kwargs, content=True)


def YearPageGenerator(start: int = 1, end: int = 2050,
                      site: OPT_SITE_TYPE = None
                      ) -> Iterator['pywikibot.page.Page']:
    """
    Year page generator.

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
                     site: OPT_SITE_TYPE = None, year: int = 2000
                     ) -> Iterator['pywikibot.page.Page']:
    """
    Day page generator.

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


def WikidataPageFromItemGenerator(gen: Iterable['pywikibot.page.ItemPage'],
                                  site: 'pywikibot.site.BaseSite'
                                  ) -> Iterator['pywikibot.page.Page']:
    """Generate pages from site based on sitelinks of item pages.

    :param gen: generator of :py:obj:`pywikibot.ItemPage`
    :param site: Site for generator results.
    """
    repo = site.data_repository()
    for sublist in itergroup(gen, 50):
        req = {'ids': [item.id for item in sublist],
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
                                site: OPT_SITE_TYPE = None,
                                item_name: str = 'item',
                                endpoint: Optional[str] = None,
                                entity_url: Optional[str] = None,
                                result_type: Any = set
                                ) -> Iterator['pywikibot.page.Page']:
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


def WikibaseSearchItemPageGenerator(text: str,
                                    language: Optional[str] = None,
                                    total: Optional[int] = None,
                                    site: OPT_SITE_TYPE = None
                                    ) -> Iterator['pywikibot.page.ItemPage']:
    """
    Generate pages that contain the provided text.

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

    def __init__(self, categories: Sequence[str],
                 subset_combination: bool = True,
                 namespaces: Optional[Sequence[NAMESPACE_OR_STR_TYPE]] = None,
                 site: OPT_SITE_TYPE = None,
                 extra_options: Optional[Dict[Any, Any]] = None) -> None:
        """
        Initializer.

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
                   namespaces: Optional[Sequence[NAMESPACE_OR_STR_TYPE]],
                   extra_options: Optional[Dict[Any, Any]]) -> Dict[str, Any]:
        """
        Get the querystring options to query PetScan.

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

    def query(self) -> Iterator[Dict[str, Any]]:
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
    def generator(self) -> Iterator['pywikibot.page.Page']:
        """Yield results from :meth:`query`.

        .. versionchanged:: 7.6
           changed from iterator method to generator property
        """
        for raw_page in self.query():
            page = pywikibot.Page(self.site, raw_page['title'],
                                  int(raw_page['namespace']))
            yield page
