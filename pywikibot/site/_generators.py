"""Objects representing API generators to MediaWiki site."""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import heapq
import itertools
import typing
from contextlib import suppress
from itertools import zip_longest
from typing import Any, Optional, Union
from warnings import warn

import pywikibot
from pywikibot.backports import Dict, Generator, Iterable, List  # skipcq
from pywikibot.data import api
from pywikibot.exceptions import (
    APIError,
    Error,
    InconsistentTitleError,
    InvalidTitleError,
    NoPageError,
    UserRightsError,
)
from pywikibot.site._decorators import need_right, need_version
from pywikibot.site._namespace import NamespaceArgType
from pywikibot.tools import is_ip_address, issue_deprecation_warning
from pywikibot.tools.itertools import filter_unique, itergroup


class GeneratorsMixin:

    """API generators mixin to MediaWiki site."""

    def load_pages_from_pageids(self, pageids):
        """
        Return a page generator from pageids.

        Pages are iterated in the same order than in the underlying pageids.

        Pageids are filtered and only one page is returned in case of
        duplicate pageids.

        :param pageids: an iterable that returns pageids (str or int),
            or a comma- or pipe-separated string of pageids
            (e.g. '945097,1483753, 956608' or '945097|483753|956608')
        """
        if not pageids:
            return
        if isinstance(pageids, str):
            pageids = pageids.replace('|', ',')
            pageids = pageids.split(',')
            pageids = [p.strip() for p in pageids]

        # Validate pageids.
        gen = (str(int(p)) for p in pageids if int(p) > 0)

        for sublist in itergroup(filter_unique(gen), self.maxlimit):
            # Store the order of the input data.
            priority_dict = dict(zip(sublist, range(len(sublist))))

            prio_queue = []
            next_prio = 0
            params = {'pageids': sublist, }
            rvgen = api.PropertyGenerator('info', site=self, parameters=params)

            for pagedata in rvgen:
                title = pagedata['title']
                pageid = str(pagedata['pageid'])
                page = pywikibot.Page(pywikibot.Link(title, source=self))
                api.update_page(page, pagedata)
                priority, page = heapq.heappushpop(prio_queue,
                                                   (priority_dict[pageid],
                                                    page))
                # Smallest priority matches expected one; yield early.
                if priority == next_prio:
                    yield page
                    next_prio += 1
                else:
                    # Push onto the heap.
                    heapq.heappush(prio_queue, (priority, page))

            # Extract data in the same order of the input data.
            while prio_queue:
                priority, page = heapq.heappop(prio_queue)
                yield page

    def preloadpages(
        self,
        pagelist,
        *,
        groupsize: int = 50,
        templates: bool = False,
        langlinks: bool = False,
        pageprops: bool = False,
        categories: bool = False,
        content: bool = True
    ):
        """Return a generator to a list of preloaded pages.

        Pages are iterated in the same order than in the underlying pagelist.
        In case of duplicates in a groupsize batch, return the first entry.

        .. versionchanged:: 7.6
           *content* parameter was added.
        .. versionchanged:: 7.7
           *categories* parameter was added.

        :param pagelist: an iterable that returns Page objects
        :param groupsize: how many Pages to query at a time
        :param templates: preload pages (typically templates) transcluded in
            the provided pages
        :param langlinks: preload all language links from the provided pages
            to other languages
        :param pageprops: preload various properties defined in page content
        :param categories: preload page categories
        :param content: preload page content
        """
        props = 'revisions|info|categoryinfo'
        if templates:
            props += '|templates'
        if langlinks:
            props += '|langlinks'
        if pageprops:
            props += '|pageprops'
        if categories:
            props += '|categories'

        for sublist in itergroup(pagelist, min(groupsize, self.maxlimit)):
            # Do not use p.pageid property as it will force page loading.
            pageids = [str(p._pageid) for p in sublist
                       if hasattr(p, '_pageid') and p._pageid > 0]
            cache = {}
            # In case of duplicates, return the first entry.
            for priority, page in enumerate(sublist):
                try:
                    cache.setdefault(page.title(with_section=False),
                                     (priority, page))
                except InvalidTitleError:
                    pywikibot.exception()

            prio_queue = []
            next_prio = 0
            rvgen = api.PropertyGenerator(props, site=self)
            rvgen.set_maximum_items(-1)  # suppress use of "rvlimit" parameter

            if len(pageids) == len(sublist) \
               and len(set(pageids)) <= self.maxlimit:
                # only use pageids if all pages have them
                rvgen.request['pageids'] = set(pageids)
            else:
                rvgen.request['titles'] = list(cache.keys())
            rvgen.request['rvprop'] = self._rvprops(content=content)
            pywikibot.output('Retrieving {} pages from {}.'
                             .format(len(cache), self))

            for pagedata in rvgen:
                pywikibot.debug('Preloading {}'.format(pagedata))
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
                                'preloadpages: Query returned unexpected '
                                "title '{}'".format(pagedata['title']))
                            continue

                except KeyError:
                    pywikibot.debug("No 'title' in {}".format(pagedata))
                    pywikibot.debug('pageids={}'.format(pageids))
                    pywikibot.debug('titles={}'.format(list(cache.keys())))
                    continue

                priority, page = cache[pagedata['title']]
                api.update_page(page, pagedata, rvgen.props)
                priority, page = heapq.heappushpop(prio_queue,
                                                   (priority, page))
                # Smallest priority matches expected one; yield.
                if priority == next_prio:
                    yield page
                    next_prio += 1
                else:
                    # Push back onto the heap.
                    heapq.heappush(prio_queue, (priority, page))

            # Empty the heap.
            while prio_queue:
                priority, page = heapq.heappop(prio_queue)
                yield page

    def pagebacklinks(self, page, *, follow_redirects: bool = False,
                      filter_redirects=None, namespaces=None, total=None,
                      content: bool = False):
        """Iterate all pages that link to the given page.

        .. seealso:: :api:`Backlinks`

        :param page: The Page to get links to.
        :param follow_redirects: Also return links to redirects pointing to
            the given page.
        :param filter_redirects: If True, only return redirects to the given
            page. If False, only return non-redirect links. If None, return
            both (no filtering).
        :param namespaces: If present, only return links from the namespaces
            in this list.
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :param total: Maximum number of pages to retrieve in total.
        :param content: if True, load the current content of each iterated page
            (default False)
        :rtype: typing.Iterable[pywikibot.Page]
        :raises KeyError: a namespace identifier was not resolved
        :raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        bltitle = page.title(with_section=False).encode(self.encoding())
        blargs = {'gbltitle': bltitle}
        if filter_redirects is not None:
            blargs['gblfilterredir'] = ('redirects' if filter_redirects
                                        else 'nonredirects')
        blgen = self._generator(api.PageGenerator, type_arg='backlinks',
                                namespaces=namespaces, total=total,
                                g_content=content, **blargs)
        if follow_redirects:
            # links identified by MediaWiki as redirects may not really be,
            # so we have to check each "redirect" page and see if it
            # really redirects to this page
            # see fixed MediaWiki bug T9304
            redirgen = self._generator(api.PageGenerator,
                                       type_arg='backlinks',
                                       gbltitle=bltitle,
                                       gblfilterredir='redirects')
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
                        redir, follow_redirects=True,
                        filter_redirects=filter_redirects,
                        namespaces=namespaces,
                        content=content
                    )
            return itertools.chain(*genlist.values())
        return blgen

    def page_embeddedin(self, page, *, filter_redirects=None, namespaces=None,
                        total=None, content: bool = False):
        """Iterate all pages that embedded the given page as a template.

        .. seealso:: :api:`Embeddedin`

        :param page: The Page to get inclusions for.
        :param filter_redirects: If True, only return redirects that embed
            the given page. If False, only return non-redirect links. If
            None, return both (no filtering).
        :param namespaces: If present, only return links from the namespaces
            in this list.
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :param content: if True, load the current content of each iterated page
            (default False)
        :rtype: typing.Iterable[pywikibot.Page]
        :raises KeyError: a namespace identifier was not resolved
        :raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        eiargs = {'geititle':
                  page.title(with_section=False).encode(self.encoding())}
        if filter_redirects is not None:
            eiargs['geifilterredir'] = ('redirects' if filter_redirects
                                        else 'nonredirects')
        return self._generator(api.PageGenerator, type_arg='embeddedin',
                               namespaces=namespaces, total=total,
                               g_content=content, **eiargs)

    @need_version('1.24')
    def page_redirects(
        self,
        page: 'pywikibot.Page',
        *,
        filter_fragments: Optional[bool] = None,
        namespaces: NamespaceArgType = None,
        total: Optional[int] = None,
        content: bool = False
    ) -> 'Iterable[pywikibot.Page]':
        """Iterale all redirects to the given page.

        .. seealso:: :api:`Redirects`

        .. versionadded:: 7.0

        :param page: The Page to get redirects for.
        :param filter_fragments: If True, only return redirects with fragments.
            If False, only return redirects without fragments. If None, return
            both (no filtering).
        :param namespaces: Only return redirects from the namespaces
        :param total: maximum number of redirects to retrieve in total
        :param content: load the current content of each redirect
        """
        rdargs = {
            'titles': page.title(with_section=False).encode(self.encoding()),
        }
        if filter_fragments is not None:
            rdargs['grdshow'] = ('' if filter_fragments else '!') + 'fragment'
        return self._generator(api.PageGenerator, type_arg='redirects',
                               namespaces=namespaces, total=total,
                               g_content=content, **rdargs)

    def pagereferences(
        self,
        page, *,
        follow_redirects: bool = False,
        filter_redirects=None,
        with_template_inclusion: bool = True,
        only_template_inclusion: bool = False,
        namespaces=None,
        total=None,
        content: bool = False
    ):
        """
        Convenience method combining pagebacklinks and page_embeddedin.

        :param namespaces: If present, only return links from the namespaces
            in this list.
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :rtype: typing.Iterable[pywikibot.Page]
        :raises KeyError: a namespace identifier was not resolved
        :raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if only_template_inclusion:
            return self.page_embeddedin(page,
                                        filter_redirects=filter_redirects,
                                        namespaces=namespaces, total=total,
                                        content=content)
        if not with_template_inclusion:
            return self.pagebacklinks(page, follow_redirects=follow_redirects,
                                      filter_redirects=filter_redirects,
                                      namespaces=namespaces, total=total,
                                      content=content)
        return itertools.islice(
            itertools.chain(
                self.pagebacklinks(
                    page, follow_redirects=follow_redirects,
                    filter_redirects=filter_redirects,
                    namespaces=namespaces, content=content),
                self.page_embeddedin(
                    page, filter_redirects=filter_redirects,
                    namespaces=namespaces, content=content)
            ), total)

    def pagelinks(
        self, page, *,
        namespaces=None,
        follow_redirects: bool = False,
        total: Optional[int] = None,
        content: bool = False
    ) -> Generator['pywikibot.Page', None, None]:
        """Iterate internal wikilinks contained (or transcluded) on page.

        .. seealso:: :api:`Links`

        :param namespaces: Only iterate pages in these namespaces
            (default: all)
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :param follow_redirects: if True, yields the target of any redirects,
            rather than the redirect page
        :param total: iterate no more than this number of pages in total
        :param content: if True, load the current content of each iterated page
        :raises KeyError: a namespace identifier was not resolved
        :raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        plargs = {}
        if hasattr(page, '_pageid'):
            plargs['pageids'] = str(page._pageid)
        else:
            pltitle = page.title(with_section=False).encode(self.encoding())
            plargs['titles'] = pltitle
        return self._generator(api.PageGenerator, type_arg='links',
                               namespaces=namespaces, total=total,
                               g_content=content, redirects=follow_redirects,
                               **plargs)

    # Sortkey doesn't work with generator
    def pagecategories(self, page, *, total=None, content: bool = False):
        """Iterate categories to which page belongs.

        .. seealso:: :api:`Categories`

        :param content: if True, load the current content of each iterated page
            (default False); note that this means the contents of the
            category description page, not the pages contained in the category
        """
        clargs = {}
        if hasattr(page, '_pageid'):
            clargs['pageids'] = str(page._pageid)
        else:
            clargs['titles'] = page.title(
                with_section=False).encode(self.encoding())
        return self._generator(api.PageGenerator,
                               type_arg='categories', total=total,
                               g_content=content, **clargs)

    def pageimages(self, page, *, total=None, content: bool = False):
        """Iterate images used (not just linked) on the page.

        .. seealso:: :api:`Images`

        :param content: if True, load the current content of each iterated page
            (default False); note that this means the content of the image
            description page, not the image itself

        """
        imtitle = page.title(with_section=False).encode(self.encoding())
        return self._generator(api.PageGenerator, type_arg='images',
                               titles=imtitle, total=total,
                               g_content=content)

    def pagetemplates(self, page, *, namespaces=None, total=None,
                      content: bool = False):
        """Iterate templates transcluded (not just linked) on the page.

        .. seealso:: :api:`Templates`

        :param namespaces: Only iterate pages in these namespaces
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :param content: if True, load the current content of each iterated page
            (default False)

        :raises KeyError: a namespace identifier was not resolved
        :raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        tltitle = page.title(with_section=False).encode(self.encoding())
        return self._generator(api.PageGenerator, type_arg='templates',
                               titles=tltitle, namespaces=namespaces,
                               total=total, g_content=content)

    def categorymembers(self, category, *,
                        namespaces=None,
                        sortby: Optional[str] = None,
                        reverse: bool = False,
                        starttime=None,
                        endtime=None,
                        total: Optional[int] = None,
                        content: bool = False,
                        member_type=None,
                        startprefix: Optional[str] = None,
                        endprefix: Optional[str] = None):
        """Iterate members of specified category.

        .. seealso:: :api:`Categorymembers`

        :param category: The Category to iterate.
        :param namespaces: If present, only return category members from
            these namespaces. To yield subcategories or files, use
            parameter member_type instead.
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :param sortby: determines the order in which results are generated,
            valid values are "sortkey" (default, results ordered by category
            sort key) or "timestamp" (results ordered by time page was
            added to the category)
        :param reverse: if True, generate results in reverse order
            (default False)
        :param starttime: if provided, only generate pages added after this
            time; not valid unless sortby="timestamp"
        :type starttime: time.Timestamp
        :param endtime: if provided, only generate pages added before this
            time; not valid unless sortby="timestamp"
        :param startprefix: if provided, only generate pages >= this title
            lexically; not valid if sortby="timestamp"
        :param endprefix: if provided, only generate pages < this title
            lexically; not valid if sortby="timestamp"
        :param content: if True, load the current content of each iterated page
            (default False)
        :param member_type: member type; if member_type includes 'page' and is
            used in conjunction with sortby="timestamp", the API may limit
            results to only pages in the first 50 namespaces.
        :type member_type: str or iterable of str;
            values: page, subcat, file
        :rtype: typing.Iterable[pywikibot.Page]
        :raises KeyError: a namespace identifier was not resolved
        :raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if category.namespace() != 14:
            raise Error('categorymembers: non-Category page {!r} specified'
                        .format(category))

        cmtitle = category.title(with_section=False).encode(self.encoding())
        cmargs = {
            'type_arg': 'categorymembers',
            'gcmtitle': cmtitle,
            'gcmprop': 'ids|title|sortkey'
        }

        if sortby in ['sortkey', 'timestamp']:
            cmargs['gcmsort'] = sortby
        elif sortby:
            raise ValueError('categorymembers: invalid sortby value {!r}'
                             .format(sortby))

        if starttime and endtime and starttime > endtime:
            raise ValueError(
                'categorymembers: starttime must be before endtime')
        if startprefix and endprefix and startprefix > endprefix:
            raise ValueError(
                'categorymembers: startprefix must be less than endprefix')

        if isinstance(member_type, str):
            member_type = {member_type}

        if member_type and sortby == 'timestamp':
            # Covert namespaces to a known type
            namespaces = set(self.namespaces.resolve(namespaces or []))

            if 'page' in member_type:
                excluded_namespaces = set()
                if 'file' not in member_type:
                    excluded_namespaces.add(6)
                if 'subcat' not in member_type:
                    excluded_namespaces.add(14)

                if namespaces:
                    if excluded_namespaces.intersection(namespaces):
                        raise ValueError(
                            'incompatible namespaces {!r} and member_type {!r}'
                            .format(namespaces, member_type))
                    # All excluded namespaces are not present in `namespaces`.
                else:
                    # If the number of namespaces is greater than permitted by
                    # the API, it will issue a warning and use the namespaces
                    # up until the limit, which will usually be sufficient.
                    # TODO: QueryGenerator should detect when the number of
                    # namespaces requested is higher than available, and split
                    # the request into several batches.
                    excluded_namespaces.update([-1, -2])
                    namespaces = set(self.namespaces) - excluded_namespaces
            else:
                if 'file' in member_type:
                    namespaces.add(6)
                if 'subcat' in member_type:
                    namespaces.add(14)

            member_type = None

        if member_type:
            cmargs['gcmtype'] = member_type

        if reverse:
            cmargs['gcmdir'] = 'desc'
            # API wants start/end params in opposite order if using descending
            # sort; we take care of this reversal for the user
            starttime, endtime = endtime, starttime
            startprefix, endprefix = endprefix, startprefix

        if starttime and sortby == 'timestamp':
            cmargs['gcmstart'] = starttime
        elif starttime:
            raise ValueError('categorymembers: '
                             "invalid combination of 'sortby' and 'starttime'")

        if endtime and sortby == 'timestamp':
            cmargs['gcmend'] = endtime
        elif endtime:
            raise ValueError('categorymembers: '
                             "invalid combination of 'sortby' and 'endtime'")

        if startprefix and sortby != 'timestamp':
            cmargs['gcmstartsortkeyprefix'] = startprefix
        elif startprefix:
            raise ValueError('categorymembers: invalid combination of '
                             "'sortby' and 'startprefix'")

        if endprefix and sortby != 'timestamp':
            cmargs['gcmendsortkeyprefix'] = endprefix
        elif endprefix:
            raise ValueError('categorymembers: '
                             "invalid combination of 'sortby' and 'endprefix'")

        return self._generator(api.PageGenerator, namespaces=namespaces,
                               total=total, g_content=content, **cmargs)

    def _rvprops(self, content: bool = False) -> List[str]:
        """Setup rvprop items for loadrevisions and preloadpages.

        :return: rvprop items
        """
        props = ['comment', 'contentmodel', 'flags', 'ids', 'parsedcomment',
                 'sha1', 'size', 'tags', 'timestamp', 'user', 'userid']
        if content:
            props.append('content')
        if self.mw_version >= '1.32':
            props.append('roles')
        return props

    def loadrevisions(
        self,
        page,
        *,
        content: bool = False,
        section=None,
        **kwargs
    ):
        """Retrieve revision information and store it in page object.

        By default, retrieves the last (current) revision of the page,
        unless any of the optional parameters revids, startid, endid,
        starttime, endtime, rvdir, user, excludeuser, or total are
        specified. Unless noted below, all parameters not specified
        default to False.

        If rvdir is False or not specified, startid must be greater than
        endid if both are specified; likewise, starttime must be greater
        than endtime. If rvdir is True, these relationships are reversed.

        .. seealso:: :api:`Revisions`

        :param page: retrieve revisions of this Page and hold the data.
        :type page: pywikibot.Page
        :param content: if True, retrieve the wiki-text of each revision;
            otherwise, only retrieve the revision metadata (default)
        :param section: if specified, retrieve only this section of the text
            (content must be True); section must be given by number (top of
            the article is section 0), not name
        :type section: int
        :keyword revids: retrieve only the specified revision ids (raise
            Exception if any of revids does not correspond to page)
        :type revids: an int, a str or a list of ints or strings
        :keyword startid: retrieve revisions starting with this revid
        :keyword endid: stop upon retrieving this revid
        :keyword starttime: retrieve revisions starting at this Timestamp
        :keyword endtime: stop upon reaching this Timestamp
        :keyword rvdir: if false, retrieve newest revisions first (default);
            if true, retrieve oldest first
        :keyword user: retrieve only revisions authored by this user
        :keyword excludeuser: retrieve all revisions not authored by this user
        :keyword total: number of revisions to retrieve
        :raises ValueError: invalid startid/endid or starttime/endtime values
        :raises pywikibot.exceptions.Error: revids belonging to a different
            page
        """
        latest = all(val is None for val in kwargs.values())

        revids = kwargs.get('revids')
        startid = kwargs.get('startid')
        starttime = kwargs.get('starttime')
        endid = kwargs.get('endid')
        endtime = kwargs.get('endtime')
        rvdir = kwargs.get('rvdir')
        user = kwargs.get('user')
        step = kwargs.get('step')

        # check for invalid argument combinations
        if (startid is not None or endid is not None) \
           and (starttime is not None or endtime is not None):
            raise ValueError(
                'loadrevisions: startid/endid combined with starttime/endtime')

        if starttime is not None and endtime is not None:
            if rvdir and starttime >= endtime:
                raise ValueError(
                    'loadrevisions: starttime > endtime with rvdir=True')

            if not rvdir and endtime >= starttime:
                raise ValueError(
                    'loadrevisions: endtime > starttime with rvdir=False')

        if startid is not None and endid is not None:
            if rvdir and startid >= endid:
                raise ValueError(
                    'loadrevisions: startid > endid with rvdir=True')
            if not rvdir and endid >= startid:
                raise ValueError(
                    'loadrevisions: endid > startid with rvdir=False')

        rvargs = {
            'type_arg': 'info|revisions',
            'rvprop': self._rvprops(content=content),
        }

        if content and section is not None:
            rvargs['rvsection'] = str(section)

        if revids is None:
            rvtitle = page.title(with_section=False).encode(self.encoding())
            rvargs['titles'] = rvtitle
        else:
            if isinstance(revids, (int, str)):
                ids = str(revids)
            else:
                ids = '|'.join(str(r) for r in revids)
            rvargs['revids'] = ids

        if rvdir:
            rvargs['rvdir'] = 'newer'
        elif rvdir is not None:
            rvargs['rvdir'] = 'older'

        if startid:
            rvargs['rvstartid'] = startid
        if endid:
            rvargs['rvendid'] = endid
        if starttime:
            rvargs['rvstart'] = starttime
        if endtime:
            rvargs['rvend'] = endtime

        if user:
            rvargs['rvuser'] = user
        else:
            rvargs['rvexcludeuser'] = kwargs.get('excludeuser')

        # assemble API request
        rvgen = self._generator(api.PropertyGenerator,
                                total=kwargs.get('total'), **rvargs)

        if step:
            rvgen.set_query_increment = step

        if latest or 'revids' in rvgen.request:
            rvgen.set_maximum_items(-1)  # suppress use of rvlimit parameter

        for pagedata in rvgen:
            if not self.sametitle(pagedata['title'],
                                  page.title(with_section=False)):
                raise InconsistentTitleError(page, pagedata['title'])
            if 'missing' in pagedata:
                raise NoPageError(page)
            api.update_page(page, pagedata, rvgen.props)

    def pagelanglinks(self, page, *,
                      total: Optional[int] = None,
                      include_obsolete: bool = False,
                      include_empty_titles: bool = False):
        """Iterate all interlanguage links on page, yielding Link objects.

        .. versionchanged:: 6.2:
           `include_empty_titles` parameter was added.

        .. seealso:: :api:`Langlinks`

        :param include_obsolete: if true, yield even Link objects whose
            site is obsolete
        :param include_empty_titles: if true, yield even Link objects whose
            title is empty but redirects to a site like [[en:]]
        """
        lltitle = page.title(with_section=False)
        llquery = self._generator(api.PropertyGenerator,
                                  type_arg='langlinks',
                                  titles=lltitle.encode(self.encoding()),
                                  total=total)
        for pageitem in llquery:
            if not self.sametitle(pageitem['title'], lltitle):
                raise InconsistentTitleError(page, pageitem['title'])
            if 'langlinks' not in pageitem:
                continue
            for linkdata in pageitem['langlinks']:
                link = pywikibot.Link.langlinkUnsafe(linkdata['lang'],
                                                     linkdata['*'],
                                                     source=self)
                if link.site.obsolete and not include_obsolete:
                    continue

                if link.title or include_empty_titles:
                    yield link

    def page_extlinks(self, page, *, total=None):
        """Iterate all external links on page, yielding URL strings.

        .. seealso:: :api:`Extlinks`
        """
        eltitle = page.title(with_section=False)
        elquery = self._generator(api.PropertyGenerator, type_arg='extlinks',
                                  titles=eltitle.encode(self.encoding()),
                                  total=total)
        for pageitem in elquery:
            if not self.sametitle(pageitem['title'], eltitle):
                raise InconsistentTitleError(page, pageitem['title'])
            if 'extlinks' not in pageitem:
                continue
            for linkdata in pageitem['extlinks']:
                yield linkdata['*']

    def allpages(
        self,
        start: str = '!',
        prefix: str = '',
        namespace=0,
        filterredir=None,
        filterlanglinks=None,
        minsize=None,
        maxsize=None,
        protect_type=None,
        protect_level=None,
        reverse: bool = False,
        total=None,
        content: bool = False
    ):
        """Iterate pages in a single namespace.

        .. seealso:: :api:`Allpages`

        :param start: Start at this title (page need not exist).
        :param prefix: Only yield pages starting with this string.
        :param namespace: Iterate pages from this (single) namespace
        :type namespace: int or Namespace.
        :param filterredir: if True, only yield redirects; if False (and not
            None), only yield non-redirects (default: yield both)
        :param filterlanglinks: if True, only yield pages with language links;
            if False (and not None), only yield pages without language links
            (default: yield both)
        :param minsize: if present, only yield pages at least this many
            bytes in size
        :param maxsize: if present, only yield pages at most this many bytes
            in size
        :param protect_type: only yield pages that have a protection of the
            specified type
        :type protect_type: str
        :param protect_level: only yield pages that have protection at this
            level; can only be used if protect_type is specified
        :param reverse: if True, iterate in reverse Unicode lexigraphic
            order (default: iterate in forward order)
        :param content: if True, load the current content of each iterated page
            (default False)
        :raises KeyError: the namespace identifier was not resolved
        :raises TypeError: the namespace identifier has an inappropriate
            type such as bool, or an iterable with more than one namespace
        """
        # backward compatibility test
        if filterredir not in (True, False, None):
            old = filterredir
            if not filterredir:
                filterredir = False
            elif filterredir == 'only':
                filterredir = True
            else:
                filterredir = None
            issue_deprecation_warning(
                'The value "{}" for "filterredir"'.format(old),
                '"{}"'.format(filterredir), since='7.0.0')

        apgen = self._generator(api.PageGenerator, type_arg='allpages',
                                namespaces=namespace,
                                gapfrom=start, total=total,
                                g_content=content)
        if prefix:
            apgen.request['gapprefix'] = prefix
        if filterredir is not None:
            apgen.request['gapfilterredir'] = ('redirects' if filterredir else
                                               'nonredirects')
        if filterlanglinks is not None:
            apgen.request['gapfilterlanglinks'] = ('withlanglinks'
                                                   if filterlanglinks else
                                                   'withoutlanglinks')
        if isinstance(minsize, int):
            apgen.request['gapminsize'] = str(minsize)
        if isinstance(maxsize, int):
            apgen.request['gapmaxsize'] = str(maxsize)
        if isinstance(protect_type, str):
            apgen.request['gapprtype'] = protect_type
            if isinstance(protect_level, str):
                apgen.request['gapprlevel'] = protect_level
        if reverse:
            apgen.request['gapdir'] = 'descending'
        return apgen

    def alllinks(
        self,
        start: str = '!',
        prefix: str = '',
        namespace=0,
        unique: bool = False,
        fromids: bool = False,
        total=None
    ):
        """Iterate all links to pages (which need not exist) in one namespace.

        Note that, in practice, links that were found on pages that have
        been deleted may not have been removed from the links table, so this
        method can return false positives.

        .. seealso:: :api:`Alllinks`

        :param start: Start at this title (page need not exist).
        :param prefix: Only yield pages starting with this string.
        :param namespace: Iterate pages from this (single) namespace
        :type namespace: int or Namespace
        :param unique: If True, only iterate each link title once (default:
            iterate once for each linking page)
        :param fromids: if True, include the pageid of the page containing
            each link (default: False) as the '_fromid' attribute of the Page;
            cannot be combined with unique
        :raises KeyError: the namespace identifier was not resolved
        :raises TypeError: the namespace identifier has an inappropriate
            type such as bool, or an iterable with more than one namespace
        """
        if unique and fromids:
            raise Error('alllinks: unique and fromids cannot both be True.')
        algen = self._generator(api.ListGenerator, type_arg='alllinks',
                                namespaces=namespace, alfrom=start,
                                total=total, alunique=unique)
        if prefix:
            algen.request['alprefix'] = prefix
        if fromids:
            algen.request['alprop'] = 'title|ids'
        for link in algen:
            p = pywikibot.Page(self, link['title'], link['ns'])
            if fromids:
                p._fromid = link['fromid']
            yield p

    def allcategories(self, start: str = '!', prefix: str = '', total=None,
                      reverse: bool = False, content: bool = False):
        """Iterate categories used (which need not have a Category page).

        Iterator yields Category objects. Note that, in practice, links that
        were found on pages that have been deleted may not have been removed
        from the database table, so this method can return false positives.

        .. seealso:: :api:`Allcategories`

        :param start: Start at this category title (category need not exist).
        :param prefix: Only yield categories starting with this string.
        :param reverse: if True, iterate in reverse Unicode lexigraphic
            order (default: iterate in forward order)
        :param content: if True, load the current content of each iterated page
            (default False); note that this means the contents of the category
            description page, not the pages that are members of the category
        """
        acgen = self._generator(api.PageGenerator,
                                type_arg='allcategories', gacfrom=start,
                                total=total, g_content=content)
        if prefix:
            acgen.request['gacprefix'] = prefix
        if reverse:
            acgen.request['gacdir'] = 'descending'
        return acgen

    def botusers(self, total=None):
        """Iterate bot users.

        Iterated values are dicts containing 'name', 'userid', 'editcount',
        'registration', and 'groups' keys. 'groups' will be present only if
        the user is a member of at least 1 group, and will be a list of
        str; all the other values are str and should always be present.
        """
        if not hasattr(self, '_bots'):
            self._bots = {}

        if not self._bots:
            for item in self.allusers(group='bot', total=total):
                self._bots.setdefault(item['name'], item)

        yield from self._bots.values()

    def allusers(
        self,
        start: str = '!',
        prefix: str = '',
        group=None,
        total=None
    ):
        """Iterate registered users, ordered by username.

        Iterated values are dicts containing 'name', 'editcount',
        'registration', and (sometimes) 'groups' keys. 'groups' will be
        present only if the user is a member of at least 1 group, and
        will be a list of str; all the other values are str and should
        always be present.

        .. seealso:: :api:`Allusers`

        :param start: start at this username (name need not exist)
        :param prefix: only iterate usernames starting with this substring
        :param group: only iterate users that are members of this group
        :type group: str
        """
        augen = self._generator(api.ListGenerator, type_arg='allusers',
                                auprop='editcount|groups|registration',
                                aufrom=start, total=total)
        if prefix:
            augen.request['auprefix'] = prefix
        if group:
            augen.request['augroup'] = group
        return augen

    def allimages(
        self,
        start: str = '!',
        prefix: str = '',
        minsize=None,
        maxsize=None,
        reverse: bool = False,
        sha1=None,
        sha1base36=None,
        total=None,
        content: bool = False
    ):
        """Iterate all images, ordered by image title.

        Yields FilePages, but these pages need not exist on the wiki.

        .. seealso:: :api:`Allimages`

        :param start: start at this title (name need not exist)
        :param prefix: only iterate titles starting with this substring
        :param minsize: only iterate images of at least this many bytes
        :param maxsize: only iterate images of no more than this many bytes
        :param reverse: if True, iterate in reverse lexigraphic order
        :param sha1: only iterate image (it is theoretically possible there
            could be more than one) with this sha1 hash
        :param sha1base36: same as sha1 but in base 36
        :param content: if True, load the current content of each iterated page
            (default False); note that this means the content of the image
            description page, not the image itself
        """
        aigen = self._generator(api.PageGenerator,
                                type_arg='allimages', gaifrom=start,
                                total=total, g_content=content)
        if prefix:
            aigen.request['gaiprefix'] = prefix
        if isinstance(minsize, int):
            aigen.request['gaiminsize'] = str(minsize)
        if isinstance(maxsize, int):
            aigen.request['gaimaxsize'] = str(maxsize)
        if reverse:
            aigen.request['gaidir'] = 'descending'
        if sha1:
            aigen.request['gaisha1'] = sha1
        if sha1base36:
            aigen.request['gaisha1base36'] = sha1base36
        return aigen

    def filearchive(
        self,
        start=None,
        end=None,
        reverse: bool = False,
        total=None,
        **kwargs
    ):
        """Iterate archived files.

        Yields dict of file archive informations.

        .. seealso:: :api:`filearchive`

        :param start: start at this title (name need not exist)
        :param end: end at this title (name need not exist)
        :param reverse: if True, iterate in reverse lexigraphic order
        :param total: maximum number of pages to retrieve in total
        :keyword prefix: only iterate titles starting with this substring
        :keyword sha1: only iterate image with this sha1 hash
        :keyword sha1base36: same as sha1 but in base 36
        :keyword prop: Image information to get. Default is timestamp
        """
        if start and end:
            self.assert_valid_iter_params(
                'filearchive', start, end, reverse, is_ts=False)
        fagen = self._generator(api.ListGenerator,
                                type_arg='filearchive',
                                fafrom=start,
                                fato=end,
                                total=total)
        for k, v in kwargs.items():
            fagen.request['fa' + k] = v
        if reverse:
            fagen.request['fadir'] = 'descending'
        return fagen

    def blocks(self, starttime=None, endtime=None, reverse: bool = False,
               blockids=None, users=None, iprange: Optional[str] = None,
               total: Optional[int] = None):
        """Iterate all current blocks, in order of creation.

        The iterator yields dicts containing keys corresponding to the
        block properties.

        .. seealso:: :api:`Blocks`

        .. note:: logevents only logs user blocks,
           while this method iterates all blocks
           including IP ranges.
        .. warning::
           ``iprange`` parameter cannot be used together with ``users``.

        :param starttime: start iterating at this Timestamp
        :type starttime: time.Timestamp
        :param endtime: stop iterating at this Timestamp
        :type endtime: time.Timestamp
        :param reverse: if True, iterate oldest blocks first (default: newest)
        :param blockids: only iterate blocks with these id numbers. Numbers
            must be separated by '|' if given by a str.
        :type blockids: str, tuple or list
        :param users: only iterate blocks affecting these usernames or IPs
        :type users: str, tuple or list
        :param iprange: a single IP or an IP range. Ranges broader than
            IPv4/16 or IPv6/19 are not accepted.
        :param total: total amount of block entries
        """
        if starttime and endtime:
            self.assert_valid_iter_params('blocks', starttime, endtime,
                                          reverse)
        bkgen = self._generator(api.ListGenerator, type_arg='blocks',
                                total=total)
        bkgen.request['bkprop'] = ['id', 'user', 'by', 'timestamp', 'expiry',
                                   'reason', 'range', 'flags', 'userid']
        if starttime:
            bkgen.request['bkstart'] = starttime
        if endtime:
            bkgen.request['bkend'] = endtime
        if reverse:
            bkgen.request['bkdir'] = 'newer'
        if blockids:
            bkgen.request['bkids'] = blockids
        if users:
            if isinstance(users, str):
                users = users.split('|')

            # actual IPv6 addresses (anonymous users) are uppercase, but they
            # have never a :: in the username (so those are registered users)
            users = [user.upper() if is_ip_address(user) and '::' not in user
                     else user for user in users]
            bkgen.request['bkusers'] = users
        elif iprange:
            bkgen.request['bkip'] = iprange
        return bkgen

    def exturlusage(self, url: Optional[str] = None,
                    protocol: Optional[str] = None, namespaces=None,
                    total: Optional[int] = None, content: bool = False):
        """Iterate Pages that contain links to the given URL.

        .. seealso:: :api:`Exturlusage`

        :param url: The URL to search for (with or without the protocol
            prefix); this may include a '*' as a wildcard, only at the start
            of the hostname
        :param namespaces: list of namespace numbers to fetch contribs from
        :type namespaces: list of int
        :param total: Maximum number of pages to retrieve in total
        :param protocol: Protocol to search for, likely http or https, http by
                default. Full list shown on Special:LinkSearch wikipage
        """
        if url is not None:
            found_protocol, _, url = url.rpartition('://')

            # If url is * we make it None in order to search for every page
            # with any URL.
            if url == '*':
                url = None

            if found_protocol:
                if protocol and protocol != found_protocol:
                    raise ValueError('Protocol was specified, but a different '
                                     'one was found in searched url')
                protocol = found_protocol

        if not protocol:
            protocol = 'http'

        return self._generator(api.PageGenerator, type_arg='exturlusage',
                               geuquery=url, geuprotocol=protocol,
                               namespaces=namespaces,
                               total=total, g_content=content)

    def imageusage(self, image: 'pywikibot.FilePage', *,
                   namespaces=None,
                   filterredir: Optional[bool] = None,
                   total: Optional[int] = None,
                   content: bool = False):
        """Iterate Pages that contain links to the given FilePage.

        .. seealso:: :api:`Imageusage`
        .. versionchanged:: 7.2
           all parameters except `image` are keyword only.

        :param image: the image to search for (FilePage need not exist on
            the wiki)
        :param namespaces: If present, only iterate pages in these namespaces
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :param filterredir: if True, only yield redirects; if False (and not
            None), only yield non-redirects (default: yield both)
        :param total: iterate no more than this number of pages in total
        :param content: if True, load the current content of each iterated page
            (default False)
        :raises KeyError: a namespace identifier was not resolved
        :raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        iuargs = {'giutitle': image.title(with_section=False)}
        if filterredir is not None:
            iuargs['giufilterredir'] = ('redirects' if filterredir else
                                        'nonredirects')
        return self._generator(api.PageGenerator, type_arg='imageusage',
                               namespaces=namespaces,
                               total=total, g_content=content, **iuargs)

    def logevents(self, logtype: Optional[str] = None,
                  user: Optional[str] = None, page=None,
                  namespace=None, start=None, end=None,
                  reverse: bool = False, tag: Optional[str] = None,
                  total: Optional[int] = None):
        """Iterate all log entries.

        .. seealso:: :api:`Logevents`

        .. note:: logevents with `logtype='block'` only logs user blocks
           whereas `site.blocks` iterates all blocks including IP ranges.

        :param logtype: only iterate entries of this type
            (see mediawiki api documentation for available types)
        :param user: only iterate entries that match this user name
        :param page: only iterate entries affecting this page
        :type page: pywikibot.Page or str
        :param namespace: namespace(s) to retrieve logevents from
        :type namespace: int or Namespace or an iterable of them

        .. note:: due to an API limitation,
           if namespace param contains multiple namespaces,
           log entries from all namespaces will be fetched from
           the API and will be filtered later during iteration.

        :param start: only iterate entries from and after this Timestamp
        :type start: time.Timestamp or ISO date string
        :param end: only iterate entries up to and through this Timestamp
        :type end: time.Timestamp or ISO date string
        :param reverse: if True, iterate oldest entries first (default: newest)
        :param tag: only iterate entries tagged with this tag
        :param total: maximum number of events to iterate
        :rtype: iterable

        :raises KeyError: the namespace identifier was not resolved
        :raises TypeError: the namespace identifier has an inappropriate
            type such as bool, or an iterable with more than one namespace
        """
        if start and end:
            self.assert_valid_iter_params('logevents', start, end, reverse)

        legen = self._generator(api.LogEntryListGenerator, type_arg=logtype,
                                total=total)
        if logtype is not None:
            legen.request['letype'] = logtype
        if user is not None:
            legen.request['leuser'] = user
        if page is not None:
            legen.request['letitle'] = page
        if start is not None:
            legen.request['lestart'] = start
        if end is not None:
            legen.request['leend'] = end
        if reverse:
            legen.request['ledir'] = 'newer'
        if namespace is not None:
            legen.set_namespace(namespace)
        if tag:
            legen.request['letag'] = tag

        return legen

    def recentchanges(self, *,
                      start=None,
                      end=None,
                      reverse: bool = False,
                      namespaces=None,
                      changetype: Optional[str] = None,
                      minor: Optional[bool] = None,
                      bot: Optional[bool] = None,
                      anon: Optional[bool] = None,
                      redirect: Optional[bool] = None,
                      patrolled: Optional[bool] = None,
                      top_only: bool = False,
                      total: Optional[int] = None,
                      user: Union[str, List[str], None] = None,
                      excludeuser: Union[str, List[str], None] = None,
                      tag: Optional[str] = None):
        """Iterate recent changes.

        .. seealso:: :api:`RecentChanges`

        :param start: Timestamp to start listing from
        :type start: pywikibot.Timestamp
        :param end: Timestamp to end listing at
        :type end: pywikibot.Timestamp
        :param reverse: if True, start with oldest changes (default: newest)
        :param namespaces: only iterate pages in these namespaces
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :param changetype: only iterate changes of this type ("edit" for
            edits to existing pages, "new" for new pages, "log" for log
            entries)
        :param minor: if True, only list minor edits; if False, only list
            non-minor edits; if None, list all
        :param bot: if True, only list bot edits; if False, only list
            non-bot edits; if None, list all
        :param anon: if True, only list anon edits; if False, only list
            non-anon edits; if None, list all
        :param redirect: if True, only list edits to redirect pages; if
            False, only list edits to non-redirect pages; if None, list all
        :param patrolled: if True, only list patrolled edits; if False,
            only list non-patrolled edits; if None, list all
        :param top_only: if True, only list changes that are the latest
            revision (default False)
        :param user: if not None, only list edits by this user or users
        :param excludeuser: if not None, exclude edits by this user or users
        :param tag: a recent changes tag
        :raises KeyError: a namespace identifier was not resolved
        :raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if start and end:
            self.assert_valid_iter_params('recentchanges', start, end, reverse)

        rcgen = self._generator(api.ListGenerator, type_arg='recentchanges',
                                rcprop='user|comment|timestamp|title|ids'
                                       '|sizes|redirect|loginfo|flags|tags',
                                namespaces=namespaces,
                                total=total, rctoponly=top_only)
        if start is not None:
            rcgen.request['rcstart'] = start
        if end is not None:
            rcgen.request['rcend'] = end
        if reverse:
            rcgen.request['rcdir'] = 'newer'
        if changetype:
            rcgen.request['rctype'] = changetype
        filters = {'minor': minor,
                   'bot': bot,
                   'anon': anon,
                   'redirect': redirect,
                   }
        if patrolled is not None and (
                self.has_right('patrol') or self.has_right('patrolmarks')):
            rcgen.request['rcprop'] += ['patrolled']
            filters['patrolled'] = patrolled
        rcgen.request['rcshow'] = api.OptionSet(self, 'recentchanges', 'show',
                                                filters)

        if user:
            rcgen.request['rcuser'] = user

        if excludeuser:
            rcgen.request['rcexcludeuser'] = excludeuser
        rcgen.request['rctag'] = tag
        return rcgen

    def search(self, searchstring: str, *,
               namespaces=None,
               where: Optional[str] = None,
               total: Optional[int] = None,
               content: bool = False):
        """Iterate Pages that contain the searchstring.

        Note that this may include non-existing Pages if the wiki's database
        table contains outdated entries.

        .. versionchanged:: 7.0
           Default of `where` parameter has been changed from 'text' to
           None. The behaviour depends on the installed search engine
           which is 'text' on CirrusSearch'.
           raises APIError instead of Error if searchstring is not set
           or what parameter is wrong.

        .. seealso:: :api:`Search`

        :param searchstring: the text to search for
        :param where: Where to search; value must be "text", "title",
            "nearmatch" or None (many wikis do not support all search types)
        :param namespaces: search only in these namespaces (defaults to all)
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :param content: if True, load the current content of each iterated page
            (default False)
        :raises KeyError: a namespace identifier was not resolved
        :raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        :raises APIError: The "gsrsearch" parameter must be set:
            searchstring parameter is not set
        :raises APIError: Unrecognized value for parameter "gsrwhat":
            wrong where parameter is given
        """
        if not namespaces and namespaces != 0:
            namespaces = [ns_id for ns_id in self.namespaces if ns_id >= 0]
        srgen = self._generator(api.PageGenerator, type_arg='search',
                                gsrsearch=searchstring, gsrwhat=where,
                                namespaces=namespaces,
                                total=total, g_content=content)
        return srgen

    def usercontribs(self, user=None, userprefix=None, start=None, end=None,
                     reverse: bool = False, namespaces=None, minor=None,
                     total: Optional[int] = None, top_only: bool = False):
        """Iterate contributions by a particular user.

        Iterated values are in the same format as recentchanges.

        .. seealso:: :api:`Usercontribs`

        :param user: Iterate contributions by this user (name or IP)
        :param userprefix: Iterate contributions by all users whose names
            or IPs start with this substring
        :param start: Iterate contributions starting at this Timestamp
        :param end: Iterate contributions ending at this Timestamp
        :param reverse: Iterate oldest contributions first (default: newest)
        :param namespaces: only iterate pages in these namespaces
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :param minor: if True, iterate only minor edits; if False and
            not None, iterate only non-minor edits (default: iterate both)
        :param total: limit result to this number of pages
        :param top_only: if True, iterate only edits which are the latest
            revision (default: False)
        :raises pywikibot.exceptions.Error: either user or userprefix must be
            non-empty
        :raises KeyError: a namespace identifier was not resolved
        :raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if not (user or userprefix):
            raise Error(
                'usercontribs: either user or userprefix must be non-empty')

        if start and end:
            self.assert_valid_iter_params('usercontribs', start, end, reverse)

        ucgen = self._generator(api.ListGenerator, type_arg='usercontribs',
                                ucprop='ids|title|timestamp|comment|flags',
                                namespaces=namespaces,
                                total=total, uctoponly=top_only)
        if user:
            ucgen.request['ucuser'] = user
        if userprefix:
            ucgen.request['ucuserprefix'] = userprefix
        if start is not None:
            ucgen.request['ucstart'] = str(start)
        if end is not None:
            ucgen.request['ucend'] = str(end)
        if reverse:
            ucgen.request['ucdir'] = 'newer'
        option_set = api.OptionSet(self, 'usercontribs', 'show')
        option_set['minor'] = minor
        ucgen.request['ucshow'] = option_set
        return ucgen

    def watchlist_revs(self, start=None, end=None, reverse: bool = False,
                       namespaces=None, minor=None, bot=None,
                       anon=None, total=None):
        """Iterate revisions to pages on the bot user's watchlist.

        Iterated values will be in same format as recentchanges.

        .. seealso:: :api:`Watchlist`

        :param start: Iterate revisions starting at this Timestamp
        :param end: Iterate revisions ending at this Timestamp
        :param reverse: Iterate oldest revisions first (default: newest)
        :param namespaces: only iterate pages in these namespaces
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :param minor: if True, only list minor edits; if False (and not
            None), only list non-minor edits
        :param bot: if True, only list bot edits; if False (and not
            None), only list non-bot edits
        :param anon: if True, only list anon edits; if False (and not
            None), only list non-anon edits
        :raises KeyError: a namespace identifier was not resolved
        :raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        if start and end:
            self.assert_valid_iter_params(
                'watchlist_revs', start, end, reverse)

        wlgen = self._generator(
            api.ListGenerator, type_arg='watchlist',
            wlprop='user|comment|timestamp|title|ids|flags',
            wlallrev='', namespaces=namespaces, total=total)
        # TODO: allow users to ask for "patrol" as well?
        if start is not None:
            wlgen.request['wlstart'] = start
        if end is not None:
            wlgen.request['wlend'] = end
        if reverse:
            wlgen.request['wldir'] = 'newer'
        filters = {'minor': minor, 'bot': bot, 'anon': anon}
        wlgen.request['wlshow'] = api.OptionSet(self, 'watchlist', 'show',
                                                filters)
        return wlgen

    def _check_view_deleted(self, msg_prefix: str, prop: List[str]) -> None:
        """Check if the user can view deleted comments and content.

        :param msg_prefix: The calling method name
        :param prop: Requested props to check
        :raises UserRightsError: user cannot view a requested prop
        """
        err = '{}: User:{} not authorized to view '.format(msg_prefix,
                                                           self.user())
        if not self.has_right('deletedhistory'):
            if self.mw_version < '1.34':
                raise UserRightsError(err + 'deleted revisions.')
            if 'comment' in prop or 'parsedcomment' in prop:
                raise UserRightsError(err + 'comments of deleted revisions.')
        if ('content' in prop and not (self.has_right('deletedtext')
                                       or self.has_right('undelete'))):
            raise UserRightsError(err + 'deleted content.')

    def deletedrevs(self, titles=None, start=None, end=None,
                    reverse: bool = False,
                    content: bool = False, total=None, **kwargs):
        """Iterate deleted revisions.

        Each value returned by the iterator will be a dict containing the
        'title' and 'ns' keys for a particular Page and a 'revisions' key
        whose value is a list of revisions in the same format as
        recentchanges plus a 'content' element with key '*' if requested
        when 'content' parameter is set. For older wikis a 'token' key is
        also given with the content request.

        .. seealso:: :api:`Deletedrevisions`

        :param titles: The page titles to check for deleted revisions
        :type titles: str (multiple titles delimited with '|')
            or pywikibot.Page or typing.Iterable[pywikibot.Page]
            or typing.Iterable[str]
        :keyword revids: Get revisions by their ID

        .. note:: either titles or revids must be set but not both

        :param start: Iterate revisions starting at this Timestamp
        :param end: Iterate revisions ending at this Timestamp
        :param reverse: Iterate oldest revisions first (default: newest)
        :param content: If True, retrieve the content of each revision
        :param total: number of revisions to retrieve
        :keyword user: List revisions by this user
        :keyword excludeuser: Exclude revisions by this user
        :keyword tag: Only list revision tagged with this tag
        :keyword prop: Which properties to get. Defaults are ids, user,
            comment, flags and timestamp
        """
        def handle_props(props):
            """Translate deletedrev props to deletedrevisions props."""
            if isinstance(props, str):
                props = props.split('|')
            if self.mw_version >= '1.25':
                return props

            old_props = []
            for item in props:
                if item == 'ids':
                    old_props += ['revid', 'parentid']
                elif item == 'flags':
                    old_props.append('minor')
                elif item != 'timestamp':
                    old_props.append(item)
                    if item == 'content' and self.mw_version < '1.24':
                        old_props.append('token')
            return old_props

        # set default properties
        prop = kwargs.pop('prop',
                          ['ids', 'user', 'comment', 'flags', 'timestamp'])
        if content:
            prop.append('content')

        if start and end:
            self.assert_valid_iter_params('deletedrevs', start, end, reverse)

        self._check_view_deleted('deletedrevs', prop)

        revids = kwargs.pop('revids', None)
        if not bool(titles) ^ (revids is not None):
            raise Error('deletedrevs: either "titles" or "revids" parameter '
                        'must be given.')
        if revids and self.mw_version < '1.25':
            raise NotImplementedError(
                'deletedrevs: "revid" is not implemented with MediaWiki {}'
                .format(self.mw_version))

        if self.mw_version >= '1.25':
            pre = 'drv'
            type_arg = 'deletedrevisions'
            generator = api.PropertyGenerator
        else:
            pre = 'dr'
            type_arg = 'deletedrevs'
            generator = api.ListGenerator

        gen = self._generator(generator, type_arg=type_arg,
                              titles=titles, revids=revids,
                              total=total)

        gen.request[pre + 'start'] = start
        gen.request[pre + 'end'] = end
        gen.request[pre + 'prop'] = handle_props(prop)

        # handle other parameters like user
        for k, v in kwargs.items():
            gen.request[pre + k] = v

        if reverse:
            gen.request[pre + 'dir'] = 'newer'

        if self.mw_version < '1.25':
            yield from gen

        else:
            # The dict result is different for both generators
            for data in gen:
                with suppress(KeyError):
                    data['revisions'] = data.pop('deletedrevisions')
                    yield data

    @need_version('1.25')
    def alldeletedrevisions(
        self,
        *,
        namespaces=None,
        reverse: bool = False,
        content: bool = False,
        total: Optional[int] = None,
        **kwargs
    ) -> typing.Iterable[Dict[str, Any]]:
        """
        Iterate all deleted revisions.

        .. seealso:: :api:`Alldeletedrevisions`

        :param namespaces: Only iterate pages in these namespaces
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :param reverse: Iterate oldest revisions first (default: newest)
        :param content: If True, retrieve the content of each revision
        :param total: Number of revisions to retrieve
        :keyword from: Start listing at this title
        :keyword to: Stop listing at this title
        :keyword prefix: Search for all page titles that begin with this value
        :keyword excludeuser: Exclude revisions by this user
        :keyword tag: Only list revisions tagged with this tag
        :keyword user: List revisions by this user
        :keyword start: Iterate revisions starting at this Timestamp
        :keyword end: Iterate revisions ending at this Timestamp
        :keyword prop: Which properties to get. Defaults are ids, timestamp,
            flags, user, and comment (if you have the right to view).
        :type prop: List[str]
        """
        if 'start' in kwargs and 'end' in kwargs:
            self.assert_valid_iter_params('alldeletedrevisions',
                                          kwargs['start'],
                                          kwargs['end'],
                                          reverse)
        prop = kwargs.pop('prop', [])
        parameters = {'adr' + k: v for k, v in kwargs.items()}
        if not prop:
            prop = ['ids', 'timestamp', 'flags', 'user']
            if self.has_right('deletedhistory'):
                prop.append('comment')
        if content:
            prop.append('content')
        self._check_view_deleted('alldeletedrevisions', prop)
        parameters['adrprop'] = prop
        if reverse:
            parameters['adrdir'] = 'newer'
        yield from self._generator(api.ListGenerator,
                                   type_arg='alldeletedrevisions',
                                   namespaces=namespaces,
                                   total=total,
                                   parameters=parameters)

    def users(self, usernames):
        """Iterate info about a list of users by name or IP.

        .. seealso:: :api:`Users`

        :param usernames: a list of user names
        :type usernames: list, or other iterable, of str
        """
        usprop = ['blockinfo', 'gender', 'groups', 'editcount', 'registration',
                  'rights', 'emailable']
        usgen = api.ListGenerator(
            'users', site=self, parameters={
                'ususers': usernames, 'usprop': usprop})
        return usgen

    def randompages(self, total=None, namespaces=None,
                    redirects: Optional[bool] = False, content: bool = False):
        """Iterate a number of random pages.

        .. seealso: :api:`Random`

        Pages are listed in a fixed sequence, only the starting point is
        random.

        :param total: the maximum number of pages to iterate
        :param namespaces: only iterate pages in these namespaces.
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :param redirects: if True, include only redirect pages in results,
            False does not include redirects and None (MW 1.26+) include both
            types. (default: False)
        :param content: if True, load the current content of each iterated page
            (default False)
        :raises KeyError: a namespace identifier was not resolved
        :raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        :raises AssertError: unsupported redirects parameter
        """
        mapping = {False: None, True: 'redirects', None: 'all'}
        assert redirects in mapping
        redirects = mapping[redirects]
        params = {}
        if redirects is not None:
            if self.mw_version < '1.26':
                if redirects == 'all':
                    warn("parameter redirects=None to retrieve 'all' random"
                         'page types is not supported by mw version {}. '
                         'Using default.'.format(self.mw_version),
                         UserWarning)
                params['grnredirect'] = redirects == 'redirects'
            else:
                params['grnfilterredir'] = redirects
        return self._generator(api.PageGenerator, type_arg='random',
                               namespaces=namespaces, total=total,
                               g_content=content, **params)

    _patrol_errors = {
        'nosuchrcid': 'There is no change with rcid {rcid}',
        'nosuchrevid': 'There is no change with revid {revid}',
        'patroldisabled': 'Patrolling is disabled on {site} wiki',
        'noautopatrol': 'User {user} has no permission to patrol its own '
                        'changes, "autopatrol" is needed',
        'notpatrollable':
            "The revision {revid} can't be patrolled as it's too old."
    }

    @need_right('patrol')
    def patrol(self, rcid=None, revid=None, revision=None):
        """Return a generator of patrolled pages.

        .. seealso:: :api:`Patrol`

        Pages to be patrolled are identified by rcid, revid or revision.
        At least one of the parameters is mandatory.
        See https://www.mediawiki.org/wiki/API:Patrol.

        :param rcid: an int/string/iterable/iterator providing rcid of pages
            to be patrolled.
        :type rcid: iterable/iterator which returns a number or string which
             contains only digits; it also supports a string (as above) or int
        :param revid: an int/string/iterable/iterator providing revid of pages
            to be patrolled.
        :type revid: iterable/iterator which returns a number or string which
             contains only digits; it also supports a string (as above) or int.
        :param revision: an Revision/iterable/iterator providing Revision
            object of pages to be patrolled.
        :type revision: iterable/iterator which returns a Revision object; it
            also supports a single Revision.
        :rtype: iterator of dict with 'rcid', 'ns' and 'title'
            of the patrolled page.

        """
        # If patrol is not enabled, attr will be set the first time a
        # request is done.
        if hasattr(self, '_patroldisabled') and self._patroldisabled:
            return

        if all(_ is None for _ in [rcid, revid, revision]):
            raise Error('No rcid, revid or revision provided.')

        if isinstance(rcid, (int, str)):
            rcid = {rcid}
        if isinstance(revid, (int, str)):
            revid = {revid}
        if isinstance(revision, pywikibot.page.Revision):
            revision = {revision}

        # Handle param=None.
        rcid = rcid or set()
        revid = revid or set()
        revision = revision or set()

        combined_revid = set(revid) | {r.revid for r in revision}

        gen = itertools.chain(
            zip_longest(rcid, [], fillvalue='rcid'),
            zip_longest(combined_revid, [], fillvalue='revid'))

        token = self.tokens['patrol']

        for idvalue, idtype in gen:
            req = self._request(parameters={'action': 'patrol',
                                            'token': token,
                                            idtype: idvalue})

            try:
                result = req.submit()
            except APIError as err:
                # patrol is disabled, store in attr to avoid other requests
                if err.code == 'patroldisabled':
                    self._patroldisabled = True
                    return

                errdata = {
                    'site': self,
                    'user': self.user(),
                    idtype: idvalue,
                }
                if err.code in self._patrol_errors:
                    raise Error(self._patrol_errors[err.code]
                                .format_map(errdata))
                pywikibot.debug("protect: Unexpected error code '{}' received."
                                .format(err.code))
                raise

            yield result['patrol']

    def newpages(
        self,
        user=None,
        returndict: bool = False,
        start=None,
        end=None,
        reverse: bool = False,
        bot: bool = False,
        redirect: bool = False,
        excludeuser=None,
        patrolled=None,
        namespaces=None,
        total=None
    ):
        """Yield new articles (as Page objects) from recent changes.

        Starts with the newest article and fetches the number of articles
        specified in the first argument.

        The objects yielded are dependent on parameter returndict.
        When true, it yields a tuple composed of a Page object and a
        dict of attributes. When false, it yields a tuple composed of
        the Page object, timestamp (str), length (int), an empty string,
        username or IP address (str), comment (str).

        :param namespaces: only iterate pages in these namespaces
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.
        :raises KeyError: a namespace identifier was not resolved
        :raises TypeError: a namespace identifier has an inappropriate
            type such as NoneType or bool
        """
        # TODO: update docstring

        # N.B. API still provides no way to access Special:Newpages content
        # directly, so we get new pages indirectly through 'recentchanges'

        gen = self.recentchanges(
            start=start, end=end, reverse=reverse,
            namespaces=namespaces, changetype='new', user=user,
            excludeuser=excludeuser, bot=bot,
            redirect=redirect, patrolled=patrolled,
            total=total
        )
        for pageitem in gen:
            newpage = pywikibot.Page(self, pageitem['title'])
            if returndict:
                yield (newpage, pageitem)
            else:
                yield (newpage, pageitem['timestamp'], pageitem['newlen'],
                       '', pageitem['user'], pageitem['comment'])

    def querypage(self, special_page, total=True):
        """Yield Page objects retrieved from Special:{special_page}.

        .. seealso:: :api:`Querypage`

        Generic function for all special pages supported by the site MW API.

        :param special_page: Special page to query
        :param total: number of pages to return
        :raise AssertionError: special_page is not supported in SpecialPages.
        """
        param = self._paraminfo.parameter('query+querypage', 'page')
        assert special_page in param['type'], (
            '{} not in {}'.format(special_page, param['type']))

        return self._generator(api.PageGenerator,
                               type_arg='querypage', gqppage=special_page,
                               total=total)

    def longpages(self, total=None):
        """Yield Pages and lengths from Special:Longpages.

        Yields a tuple of Page object, length(int).

        :param total: number of pages to return
        """
        lpgen = self._generator(api.ListGenerator,
                                type_arg='querypage', qppage='Longpages',
                                total=total)
        for pageitem in lpgen:
            yield (pywikibot.Page(self, pageitem['title']),
                   int(pageitem['value']))

    def shortpages(self, total=None):
        """Yield Pages and lengths from Special:Shortpages.

        Yields a tuple of Page object, length(int).

        :param total: number of pages to return
        """
        spgen = self._generator(api.ListGenerator,
                                type_arg='querypage', qppage='Shortpages',
                                total=total)
        for pageitem in spgen:
            yield (pywikibot.Page(self, pageitem['title']),
                   int(pageitem['value']))

    def deadendpages(self, total=None):
        """Yield Page objects retrieved from Special:Deadendpages.

        :param total: number of pages to return
        """
        return self.querypage('Deadendpages', total)

    def ancientpages(self, total=None):
        """Yield Pages, datestamps from Special:Ancientpages.

        :param total: number of pages to return
        """
        apgen = self._generator(api.ListGenerator,
                                type_arg='querypage', qppage='Ancientpages',
                                total=total)
        for pageitem in apgen:
            yield (pywikibot.Page(self, pageitem['title']),
                   pywikibot.Timestamp.fromISOformat(pageitem['timestamp']))

    def lonelypages(self, total=None):
        """Yield Pages retrieved from Special:Lonelypages.

        :param total: number of pages to return
        """
        return self.querypage('Lonelypages', total)

    def unwatchedpages(self, total=None):
        """Yield Pages from Special:Unwatchedpages (requires Admin privileges).

        :param total: number of pages to return
        """
        return self.querypage('Unwatchedpages', total)

    def wantedpages(self, total=None):
        """Yield Pages from Special:Wantedpages.

        :param total: number of pages to return
        """
        return self.querypage('Wantedpages', total)

    def wantedfiles(self, total=None):
        """Yield Pages from Special:Wantedfiles.

        :param total: number of pages to return
        """
        return self.querypage('Wantedfiles', total)

    def wantedtemplates(self, total=None):
        """Yield Pages from Special:Wantedtemplates.

        :param total: number of pages to return
        """
        return self.querypage('Wantedtemplates', total)

    def wantedcategories(self, total=None):
        """Yield Pages from Special:Wantedcategories.

        :param total: number of pages to return
        """
        return self.querypage('Wantedcategories', total)

    def uncategorizedcategories(self, total=None):
        """Yield Categories from Special:Uncategorizedcategories.

        :param total: number of pages to return
        """
        return self.querypage('Uncategorizedcategories', total)

    def uncategorizedimages(self, total=None):
        """Yield FilePages from Special:Uncategorizedimages.

        :param total: number of pages to return
        """
        return self.querypage('Uncategorizedimages', total)

    # synonym
    uncategorizedfiles = uncategorizedimages

    def uncategorizedpages(self, total=None):
        """Yield Pages from Special:Uncategorizedpages.

        :param total: number of pages to return
        """
        return self.querypage('Uncategorizedpages', total)

    def uncategorizedtemplates(self, total=None):
        """Yield Pages from Special:Uncategorizedtemplates.

        :param total: number of pages to return
        """
        return self.querypage('Uncategorizedtemplates', total)

    def unusedcategories(self, total=None):
        """Yield Category objects from Special:Unusedcategories.

        :param total: number of pages to return
        """
        return self.querypage('Unusedcategories', total)

    def unusedfiles(self, total=None):
        """Yield FilePage objects from Special:Unusedimages.

        :param total: number of pages to return
        """
        return self.querypage('Unusedimages', total)

    def withoutinterwiki(self, total=None):
        """Yield Pages without language links from Special:Withoutinterwiki.

        :param total: number of pages to return
        """
        return self.querypage('Withoutinterwiki', total)

    def broken_redirects(self, total=None):
        """Yield Pages with broken redirects from Special:BrokenRedirects.

        :param total: number of pages to return
        """
        return self.querypage('BrokenRedirects', total)

    def double_redirects(self, total=None):
        """Yield Pages with double redirects from Special:DoubleRedirects.

        :param total: number of pages to return
        """
        return self.querypage('DoubleRedirects', total)

    def redirectpages(self, total=None):
        """Yield redirect pages from Special:ListRedirects.

        :param total: number of pages to return
        """
        return self.querypage('Listredirects', total)

    def protectedpages(
        self,
        namespace=0,
        type: str = 'edit',
        level: Union[str, bool] = False,
        total=None
    ):
        """
        Return protected pages depending on protection level and type.

        For protection types which aren't 'create' it uses
        :py:obj:`APISite.allpages`, while it uses for 'create' the
        'query+protectedtitles' module.

        .. seealso:: :api:`Protectedtitles`

        :param namespace: The searched namespace.
        :type namespace: int or Namespace or str
        :param type: The protection type to search for (default 'edit').
        :type type: str
        :param level: The protection level (like 'autoconfirmed'). If False it
            shows all protection levels.
        :return: The pages which are protected.
        :rtype: typing.Iterable[pywikibot.Page]
        """
        namespaces = self.namespaces.resolve(namespace)
        # always assert that, so we are be sure that type could be 'create'
        assert 'create' in self.protection_types(), \
            "'create' should be a valid protection type."
        if type == 'create':
            return self._generator(
                api.PageGenerator, type_arg='protectedtitles',
                namespaces=namespaces, gptlevel=level, total=total)
        return self.allpages(namespace=namespaces[0], protect_level=level,
                             protect_type=type, total=total)

    def pages_with_property(self, propname: str, *,
                            total: Optional[int] = None):
        """Yield Page objects from Special:PagesWithProp.

        .. seealso:: :api:`Pageswithprop`

        :param propname: must be a valid property.
        :param total: number of pages to return
        :return: return a generator of Page objects
        :rtype: iterator
        """
        if propname not in self.get_property_names():
            raise NotImplementedError(
                '"{}" is not a valid page property'.format(propname))
        return self._generator(api.PageGenerator, type_arg='pageswithprop',
                               gpwppropname=propname, total=total)

    def watched_pages(self, force: bool = False, total=None):
        """
        Return watchlist.

        .. seealso:: :api:`Watchlistraw`

        :param force: Reload watchlist
        :param total: if not None, limit the generator to yielding this many
            items in total
        :type total: int
        :return: list of pages in watchlist
        :rtype: list of pywikibot.Page objects
        """
        expiry = None if force else pywikibot.config.API_config_expiry
        gen = api.PageGenerator(site=self, generator='watchlistraw',
                                expiry=expiry)
        gen.set_maximum_items(total)
        return gen
