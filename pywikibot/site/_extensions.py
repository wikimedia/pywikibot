#
# (C) Pywikibot team, 2008-2026
#
# Distributed under the terms of the MIT license.
#
"""Objects representing API interface to MediaWiki site extensions."""
from __future__ import annotations

import re
from collections.abc import Generator, Iterable
from ipaddress import ip_network
from typing import TYPE_CHECKING, Any, Protocol

import pywikibot
from pywikibot.data import api
from pywikibot.echo import Notification
from pywikibot.exceptions import (
    APIError,
    Error,
    InconsistentTitleError,
    NoPageError,
    SiteDefinitionError,
    UnexpectedAPIDataError,
)
from pywikibot.site._decorators import need_extension, need_right
from pywikibot.site._namespace import NamespaceArgType
from pywikibot.tools import merge_unique_dicts


if TYPE_CHECKING:
    from pywikibot.site import NamespacesDict


class BaseSiteProtocol(Protocol):
    _paraminfo: api.ParamInfo
    _proofread_levels: dict[int, str]
    tokens: dict[str, str]

    def _generator(self, *args, **kwargs) -> api.Request:
        ...

    def _request(self, **kwargs) -> api.Request:
        ...

    def _update_page(self, *args, **kwargs) -> None:
        ...

    def encoding(self) -> str:
        ...

    @property
    def namespaces(self) -> NamespacesDict:
        ...

    def simple_request(self, **kwargs) -> api.Request:
        ...

    def querypage(
        self, *args, **kwargs
    ) -> Generator[tuple[pywikibot.Page, int]]:
        ...


class EchoMixin:

    """APISite mixin for Echo extension."""

    @need_extension('Echo')
    def notifications(self, **kwargs):
        """Yield Notification objects from the Echo extension.

        .. seealso:: :api:`Notifications` for other keywords.

        :keyword str | None format: Notification output format.
            Possible values are ``model``, ``special``, or ``None``.
            The default is ``special``.
        """
        params = {
            'action': 'query',
            'meta': 'notifications',
            'notformat': 'special',
        }

        for key, value in kwargs.items():
            params['not' + key] = value

        data = self.simple_request(**params).submit()
        notifications = data['query']['notifications']['list']

        return (Notification.fromJSON(self, notification)
                for notification in notifications)

    @need_extension('Echo')
    def notifications_mark_read(self: BaseSiteProtocol, **kwargs) -> bool:
        """Mark selected notifications as read.

        .. seealso:: :api:`echomarkread`

        :return: Whether the action was successful
        """
        kwargs = merge_unique_dicts(kwargs, action='echomarkread',
                                    token=self.tokens['csrf'])
        req = self.simple_request(**kwargs)
        data = req.submit()
        try:
            return data['query']['echomarkread']['result'] == 'success'
        except KeyError:
            return False


class ProofreadPageMixin:

    """APISite mixin for ProofreadPage extension."""

    @need_extension('ProofreadPage')
    def _cache_proofreadinfo(self: BaseSiteProtocol, expiry=False) -> None:
        """Retrieve proofreadinfo from site and cache response.

        Applicable only to sites with ProofreadPage extension installed.

        The following info is returned by the query and cached:
        - self._proofread_index_ns: Index Namespace
        - self._proofread_page_ns: Page Namespace
        - self._proofread_levels: a dictionary with::

            keys: int in the range [0, 1, ..., 4]
            values: category name corresponding to the 'key' quality level
            e.g. on en.wikisource:

            .. code-block:: python

               {0: 'Without text', 1: 'Not proofread', 2: 'Problematic',
                3: 'Proofread', 4: 'Validated'}

        :param expiry: Either a number of days or a datetime.timedelta object
        :type expiry: int (days), :py:obj:`datetime.timedelta`, False (config)
        :return: A tuple containing _proofread_index_ns,
            self._proofread_page_ns and self._proofread_levels.
        :rtype: Namespace, Namespace, dict
        """
        if (not hasattr(self, '_proofread_index_ns')
                or not hasattr(self, '_proofread_page_ns')
                or not hasattr(self, '_proofread_levels')):

            pirequest = self._request(
                expiry=pywikibot.config.API_config_expiry
                if expiry is False else expiry,
                parameters={'action': 'query', 'meta': 'proofreadinfo'}
            )

            pidata = pirequest.submit()
            ns_id = pidata['query']['proofreadnamespaces']['index']['id']
            self._proofread_index_ns = self.namespaces[ns_id]

            ns_id = pidata['query']['proofreadnamespaces']['page']['id']
            self._proofread_page_ns = self.namespaces[ns_id]

            self._proofread_levels = {}
            for ql in pidata['query']['proofreadqualitylevels']:
                self._proofread_levels[ql['id']] = ql['category']

    @property
    def proofread_index_ns(self):
        """Return Index namespace for the ProofreadPage extension."""
        if not hasattr(self, '_proofread_index_ns'):
            self._cache_proofreadinfo()
        return self._proofread_index_ns

    @property
    def proofread_page_ns(self):
        """Return Page namespace for the ProofreadPage extension."""
        if not hasattr(self, '_proofread_page_ns'):
            self._cache_proofreadinfo()
        return self._proofread_page_ns

    @property
    def proofread_levels(self):
        """Return Quality Levels for the ProofreadPage extension."""
        if not hasattr(self, '_proofread_levels'):
            self._cache_proofreadinfo()
        return self._proofread_levels

    @need_extension('ProofreadPage')
    def loadpageurls(self: BaseSiteProtocol,
                     page: pywikibot.page.BasePage) -> None:
        """Load URLs from api and store in page attributes.

        Load URLs to images for a given page in the "Page:" namespace.
        No effect for pages in other namespaces.

        .. version-added:: 8.6

        .. seealso:: :api:`imageforpage`
        """
        title = page.title(with_section=False)
        # responsiveimages: server would try to render the other images as well
        # let's not load the server unless needed.
        prppifpprop = 'filename|size|fullsize'

        query = self._generator(api.PropertyGenerator,
                                type_arg='imageforpage',
                                titles=title,
                                prppifpprop=prppifpprop)
        self._update_page(page, query)


class GeoDataMixin:

    """APISite mixin for GeoData extension."""

    @need_extension('GeoData')
    def geosearch(
        self: BaseSiteProtocol,
        *,
        coord: tuple[float, float] | None = None,
        page: pywikibot.page.BasePage | str | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        radius: int | None = None,
        namespaces: NamespaceArgType = 0,
        total: int | None = 10,
    ) -> Generator[dict[str, Any]]:
        """Yield geographic search records from the GeoData extension.

        Specify exactly one of *coord*, *page* or *bbox*. Results retain
        the API's order and metadata, including ``pageid``, ``ns``,
        ``title``, ``lat``, ``lon``, ``dist`` and ``primary``. Additional
        coordinate properties are included where available. Distances
        are in metres, measured from the search point or box centre.

        Only primary coordinates are searched, using the site's default
        globe (normally Earth). When searching around a page, that page
        is excluded from the results.

        GeoSearch does not support continuation. The API caps the result
        count (normally 500, or 5000 with the ``apihighlimits`` right), so
        this method cannot enumerate every page in a densely mapped area.
        The radius and bounding-box size are also limited by the site.

        For example, search within 5 km of a point in Lagos:

        .. code-block:: python

           for result in site.geosearch(coord=(6.455, 3.3841), radius=5000):
               print(result['title'], result['dist'])

        .. version-added:: 11.8
        .. seealso:: :api:`Geosearch`

        :param coord: Search centre as ``(latitude, longitude)``.
        :param page: Title or page on this site whose primary coordinates
            define the search centre. The page must have coordinates.
        :param bbox: Bounding box as ``(north, west, south, east)``.
        :param radius: Search radius in metres for *coord* or *page*.
            If None, use the site's default (normally 500 metres).
            Cannot be combined with *bbox*.
        :param namespaces: Namespace identifiers or names, optionally
            separated by ``|``. Defaults to the main namespace.
            None or an empty iterable searches all namespaces.
        :param total: Maximum records to yield, subject to the API limit.
            None requests the API maximum; nonpositive values yield none.
        :raises ValueError: Conflicting or malformed search inputs.
        :raises RuntimeError: The reference page belongs to another site.
        :raises UnknownExtensionError: GeoData is not installed.
        :raises APIError: The reference page is missing or has no
            coordinates (``no-coordinates``), or the API rejects the query.
        :raises UnexpectedAPIDataError: The response does not contain a
            list of search records.
        """
        if sum(value is not None for value in (coord, page, bbox)) != 1:
            raise ValueError('Specify exactly one of coord, page or bbox.')
        if bbox is not None and radius is not None:
            raise ValueError('radius cannot be combined with bbox.')

        parameters: dict[str, Any] = {
            'action': 'query',
            'list': 'geosearch',
            'gslimit': 'max' if total is None else total,
            'gsprop': ['type', 'name', 'dim', 'country', 'region', 'globe'],
            'formatversion': 2,
        }
        if coord is not None:
            if len(coord) != 2:
                raise ValueError('coord must contain latitude and longitude.')
            parameters['gscoord'] = coord
        elif bbox is not None:
            if len(bbox) != 4:
                raise ValueError('bbox must contain north, west, south, east.')
            parameters['gsbbox'] = bbox
        else:
            parameters['gspage'] = page

        if radius is not None:
            parameters['gsradius'] = radius
        if isinstance(namespaces, str):
            namespaces = namespaces.split('|')
        parameters['gsnamespace'] = (
            [ns.id for ns in self.namespaces.resolve(namespaces)]
            if namespaces is not None else []
        ) or '*'

        if total is not None and total <= 0:
            return

        # This module has no continuation; a smaller batch loses results.
        request = self.simple_request(**parameters)
        data = request.submit()
        try:
            records = data['query']['geosearch']
        except (KeyError, TypeError) as e:
            raise UnexpectedAPIDataError(
                'GeoSearch response is missing the search result list') from e
        if not isinstance(records, list) or any(
            not isinstance(record, dict) for record in records
        ):
            raise UnexpectedAPIDataError(
                'GeoSearch response must contain a list of search records')
        yield from records

    @need_extension('GeoData')
    def loadcoordinfo(self: BaseSiteProtocol, page) -> None:
        """Load [[mw:Extension:GeoData]] info."""
        title = page.title(with_section=False)
        query = self._generator(api.PropertyGenerator,
                                type_arg='coordinates',
                                titles=title,
                                coprop=['type', 'name', 'dim',
                                        'country', 'region',
                                        'globe'],
                                coprimary='all')
        self._update_page(page, query)


class PageImagesMixin:

    """APISite mixin for PageImages extension."""

    @need_extension('PageImages')
    def loadpageimage(self: BaseSiteProtocol, page) -> None:
        """Load [[mw:Extension:PageImages]] info.

        :param page: The page for which to obtain the image
        :type page: pywikibot.Page
        :raises APIError: PageImages extension is not installed
        """
        title = page.title(with_section=False)
        query = self._generator(api.PropertyGenerator,
                                type_arg='pageimages',
                                titles=title,
                                piprop=['name'])
        self._update_page(page, query)


class PageViewInfoMixin:

    """APISite mixin for PageViewInfo extension.

    .. version-added:: 11.8
    """

    @need_extension('PageViewInfo')
    def pageviews(
        self: BaseSiteProtocol,
        page: pywikibot.Page,
        days: int | None = None,
        *,
        metric: str = 'pageviews',
    ) -> dict[str, int | None]:
        """Return daily page views for *page*.

        :param page: Page for which to retrieve view counts.
        :param days: Number of days to return, up to the site-configured
            maximum. If ``None``, use the site's default.
        :param metric: Page view metric supported by the site.
        :raises NoPageError: The page does not exist.
        :return: Mapping of ISO date strings to view counts. A count may
            be ``None`` when data is unavailable.
        """
        if page.namespace() >= 0 and not page.exists():
            raise NoPageError(page)

        parameters = {
            'titles': page.title(with_section=False),
            'pvipmetric': metric,
        }
        if days is not None:
            parameters['pvipdays'] = days
        query = self._generator(api.PropertyGenerator,
                                type_arg='pageviews', **parameters)
        try:
            pagedata = next(iter(query))
            return pagedata['pageviews']
        except (KeyError, StopIteration) as e:
            raise UnexpectedAPIDataError(
                f'PageViewInfo response contains no data for {page}'
            ) from e

    @need_extension('PageViewInfo')
    def siteviews(
        self: BaseSiteProtocol,
        days: int | None = None,
        *,
        metric: str = 'pageviews',
    ) -> dict[str, int | None]:
        """Return daily view totals for this site.

        :param days: Number of days to return, up to the site-configured
            maximum. If ``None``, use the site's default.
        :param metric: Site view metric supported by the site.
        :return: Mapping of ISO date strings to view counts. A count may
            be ``None`` when data is unavailable.
        """
        parameters = {
            'action': 'query',
            'meta': 'siteviews',
            'pvismetric': metric,
            'formatversion': 2,
        }
        if days is not None:
            parameters['pvisdays'] = days
        request = self.simple_request(**parameters)
        try:
            return request.submit()['query']['siteviews']
        except KeyError as e:
            raise UnexpectedAPIDataError(
                'PageViewInfo response contains no site view data'
            ) from e

    @need_extension('PageViewInfo')
    def mostviewed(
        self: BaseSiteProtocol,
        total: int | None = 10,
        *,
        metric: str = 'pageviews',
    ) -> Generator[tuple[pywikibot.Page, int]]:
        """Yield the most viewed pages and their view counts.

        :param total: Maximum number of pages to return, or ``None`` for
            all available pages.
        :param metric: Page view metric supported by the site.
        :yield: A page and its view count for the previous day.
        """
        query = self._generator(
            api.ListGenerator,
            type_arg='mostviewed',
            total=total,
            pvimmetric=metric,
        )
        for pagedata in query:
            yield pywikibot.Page(self, pagedata['title']), pagedata['count']


class GlobalBlockingMixin:

    """APISite mixin for the GlobalBlocking extension.

    .. version-added:: 11.8
    """

    @need_extension('GlobalBlocking')
    def is_globally_blocked(self: BaseSiteProtocol, user: str) -> bool:
        """Return whether an active global block matches the target.

        IP lookups include covering range blocks. For a CIDR range, a
        matching block must cover the entire range. Account lookups
        require an API supporting the ``bgtargets`` parameter.

        This checks global block records, including locally disabled
        blocks. It does not check exemptions or CentralAuth locks, and
        does not determine whether an edit is permitted. Results are not
        cached.

        This method cannot detect hidden global autoblocks through an IP
        lookup because the API excludes them from these results.

        .. seealso::
           - :ext:`GlobalBlocking/API#list=globalblocks_(bg)`
           - :meth:`pywikibot.User.is_globally_blocked`
           - :meth:`pywikibot.site._apisite.APISite.is_locked`

        :param user: Username, IP address or CIDR range to check
        :raises ValueError: The target is empty or contains list separators.
        :raises NotImplementedError: The API cannot query account blocks.
        :raises UnknownExtensionError: GlobalBlocking is not installed.
        """
        user = user.strip()
        if not user:
            raise ValueError('The global block target must not be empty.')
        if '|' in user or '\x1f' in user:
            raise ValueError('The global block target must not contain '
                             'list separators.')

        # Recognize leading-zero IPv4 addresses accepted by MediaWiki.
        address, separator, prefix = user.partition('/')
        if re.fullmatch(r'[0-9]{1,3}(?:\.[0-9]{1,3}){3}', address):
            address = '.'.join(str(int(part)) for part in address.split('.'))
        try:
            # MediaWiki accepts CIDR ranges with nonzero host bits.
            ip_network(address + separator + prefix, strict=False)
        except ValueError:
            if self._paraminfo.parameter('query+globalblocks',
                                         'targets') is None:
                raise NotImplementedError(
                    'This site does not support global account block queries.')
            parameter = 'bgtargets'
        else:
            parameter = 'bgip'

        req = self.simple_request(action='query', list='globalblocks',
                                  bgprop='id', bglimit=1,
                                  **{parameter: [user]})
        return bool(req.submit()['query']['globalblocks'])


class GlobalUsageMixin:

    """APISite mixin for Global Usage extension."""

    @need_extension('Global Usage')
    def globalusage(self, page, total=None):
        """Iterate global image usage for a given FilePage.

        :param page: The page to return global image usage for.
        :type page: pywikibot.FilePage
        :param total: Iterate no more than this number of pages in
            total.
        :raises TypeError: Input page is not a FilePage.
        :raises pywikibot.exceptions.SiteDefinitionError: Site could not
            be defined for a returned entry in API response.
        """
        if not isinstance(page, pywikibot.FilePage):
            raise TypeError(f'Page {page} must be a FilePage.')

        title = page.title(with_section=False)
        args = {'titles': title,
                'gufilterlocal': False,
                }
        query = self._generator(api.PropertyGenerator,
                                type_arg='globalusage',
                                guprop=['url', 'pageid', 'namespace'],
                                total=total,  # will set gulimit=total in api,
                                **args)

        for pageitem in query:
            if not self.sametitle(pageitem['title'],
                                  page.title(with_section=False)):
                raise InconsistentTitleError(page, pageitem['title'])

            api.update_page(page, pageitem, query.props)

            assert 'globalusage' in pageitem, \
                   "API globalusage response lacks 'globalusage' key"
            for entry in pageitem['globalusage']:
                try:
                    gu_site = pywikibot.Site(url=entry['url'])
                except SiteDefinitionError:
                    pywikibot.warning('Site could not be defined for global '
                                      f'usage for {page}: {entry}.')
                    continue
                gu_page = pywikibot.Page(gu_site, entry['title'])
                yield gu_page


class WikibaseClientMixin:

    """APISite mixin for WikibaseClient extension."""

    @need_extension('WikibaseClient')
    def unconnected_pages(
        self: BaseSiteProtocol,
        total: int | None = None,
        *,
        strict: bool = False
    ) -> Generator[pywikibot.Page]:
        """Yield Page objects from Special:UnconnectedPages.

        .. warning:: The retrieved pages may be connected in meantime.
           To avoid this, use *strict* parameter to check.

        .. version-changed:: 10.4.0
           The *strict* parameter was added.

        :param total: Maximum number of pages to return, or ``None`` for
            all.
        :param strict: If ``True``, verify that each page still has no
            data item before yielding it.
        """
        if total is not None and total <= 0:
            return

        if not strict:
            yield from self.querypage('UnconnectedPages', total)
            return

        count = 0
        for page in self.querypage('UnconnectedPages'):
            if total is not None and count >= total:
                break

            try:
                page.data_item()
            except NoPageError:
                yield page
                count += 1


class LinterMixin:

    """APISite mixin for Linter extension."""

    @need_extension('Linter')
    def linter_pages(
        self: BaseSiteProtocol,
        lint_categories: Iterable[str] | str | None = None,
        total: int | None = None,
        namespaces=None,
        pageids: Iterable[str | int] | str | int | None = None,
        lint_from: str | int | None = None
    ) -> Iterable[pywikibot.Page]:
        """Return a generator to pages containing linter errors.

        .. seealso:: :ext:`Linter`

        :param lint_categories: Categories of lint errors. Must be an
            iterable of lint categories, or a pipe-separated string of
            lint categories.
        :param total: If not None, yield this many items in total.
        :param namespaces: Only iterate pages in these namespaces.
        :type namespaces: Iterable of str or Namespace key, or a single
            instance of those types. May be a '|' separated list of
            namespace identifiers.
        :param pageids: Only include lint errors from the specified
            pageids. Must be given as an iterable of page ids, or a
            pipe-separated string of page ids
            (e.g. '945097|483753|956608').
        :param lint_from: Lint ID to start querying from
        :return: Pages with Linter errors.
        """
        query = self._generator(api.ListGenerator, type_arg='linterrors',
                                total=total, namespaces=namespaces,
                                lntfrom=lint_from)

        if lint_categories:
            if isinstance(lint_categories, str):
                lint_categories = lint_categories.replace(' ', '')
            query.request['lntcategories'] = lint_categories

        if pageids:
            if isinstance(pageids, str):
                pageids = pageids.replace(' ', '')
            query.request['lntpageid'] = pageids

        for pageitem in query:
            page = pywikibot.Page(self, pageitem['title'])
            api.update_page(page, pageitem)
            yield page


class ThanksMixin:

    """APISite mixin for Thanks extension."""

    @need_extension('Thanks')
    def thank_revision(self, revid: int, source: str | None = None):
        """Corresponding method to the 'action=thank' API action.

        :param revid: Revision ID for the revision to be thanked.
        :param source: A source for the thanking operation.
        :raise APIError: On thanking oneself or other API errors.
        :return: The API response.
        """
        token = self.tokens['csrf']
        req = self.simple_request(action='thank', rev=revid, token=token,
                                  source=source)
        data = req.submit()
        if data['result']['success'] != 1:
            raise APIError('Thanking unsuccessful', '')
        return data


class UrlShortenerMixin:

    """APISite mixin for UrlShortener extension."""

    @need_extension('UrlShortener')
    def create_short_link(self, url: str) -> str:
        """Return a shortened link.

        Note that on Wikimedia wikis only metawiki supports this action,
        and this wiki can process links to all WM domains.

        :param url: The link to reduce, with protocol prefix.
        :return: The reduced link, without protocol prefix.
        """
        req = self.simple_request(action='shortenurl', url=url)
        data = req.submit()
        return data['shortenurl']['shorturl']


class TextExtractsMixin:

    """APISite mixin for TextExtracts extension.

    .. version-added:: 7.1
    """

    @need_extension('TextExtracts')
    def extract(self: BaseSiteProtocol,
                page: pywikibot.Page, *,
                chars: int | None = None,
                sentences: int | None = None,
                intro: bool = True,
                plaintext: bool = True) -> str:
        """Retrieve an extract of a page.

        :param page: The Page object for which the extract is read.
        :param chars: Maximum characters to return.
        :param sentences: How many sentences to return.
        :param intro: Return only content before the first section.
        :param plaintext: Return extracts as plain text instead of
            limited HTML.
        :return: The extract of the page.

        .. seealso::
           - :ext:`TextExtracts`
           - :meth:`page.BasePage.extract`
        """
        if not page.exists():
            raise NoPageError(page)
        req = self.simple_request(action='query',
                                  prop='extracts',
                                  titles=page.title(with_section=False),
                                  exchars=chars,
                                  exsentences=sentences,
                                  exintro=intro,
                                  explaintext=plaintext)
        data = req.submit()['query']['pages']
        if '-1' in data:
            msg = data['-1'].get('invalidreason',
                                 f"Unknown exception:\n{data['-1']}")
            raise Error(msg)

        return data[str(page.pageid)]['extract']


class FlaggedRevsMixin:

    """APISite mixin for the FlaggesRevs extension.

    .. version-added:: 11.7
    .. seealso:: :ext:`FlaggedRevs`
    """

    @need_extension('FlaggedRevs')
    def flagged_state(self: BaseSiteProtocol,
                      page: pywikibot.Page) -> dict | None:
        """Return the FlaggedRevs info dict for a page, if any.

        Uses ``prop=flagged`` and returns the ``flagged`` object from the
        API (keys such as ``stable_revid``, ``level``, ``level_text``,
        ``pending_since``), or ``None`` if the page has no flagged data.

        .. version-added:: 11.8
        .. seealso::
           - :meth:`stable_revid`
           - :attr:`BasePage.flagged_state
             <page.BasePage.flagged_state>`

        :param page: The page to inspect.
        :return: Flagged info dict or None if not available.
        :raises UnknownExtensionError: FlaggedRevs not available
        """
        req = self.simple_request(
            action='query',
            prop='flagged',
            titles=page.title(with_section=False),
            formatversion=2
        )
        data = req.submit()

        pages = data.get('query', {}).get('pages', [])
        if not pages:
            return None

        flagged = pages[0].get('flagged')
        return flagged or None

    @need_extension('FlaggedRevs')
    def stable_revid(self: BaseSiteProtocol,
                     page: pywikibot.Page) -> int | None:
        """Return the stable (reviewed) revision id for a page, if any.

        :param page: The page to inspect.
        :return: The stable revision id or None if not available.
        :raises UnknownExtensionError: FlaggedRevs not available
        """
        flagged = self.flagged_state(page)
        if not flagged:
            return None
        return flagged.get('stable_revid')

    @need_extension('FlaggedRevs')
    @need_right('review')
    def review_revision(
        self,
        revid: int,
        *,
        comment: str | None = None,
        unapprove: bool = False,
        flag: int | None = None,
    ) -> None:
        """Review a revision using the FlaggedRevs ``action=review`` API.

        .. note::
           Reviewing or unapproving a revision may change the stable
           revision of the associated page. Cached
           :attr:`BasePage.stable_revision_id
           <page.BasePage.stable_revision_id>` values are not
           invalidated automatically.

        :param revid: Revision ID to review.
        :param comment: Optional review comment.
        :param unapprove: If True, the revision will be *unapproved*.
        :param flag: Set the review flag value.
        :raises APIError: On API failure.
        :raises UnexpectedAPIDataError: Unexpected API data for review
            parameters or review result.
        :raises UnknownExtensionError: FlaggedRevs not available.
        :raises UserRightsError: User has insufficient rights.
        :raises ValueError: Unsupported *flag* parameter.
        """
        try:
            review_params = self._paraminfo['review']['parameters']
        except KeyError as e:
            raise UnexpectedAPIDataError(
                'Unexpected API data: no param info found') from e

        names = {item['name'] for item in review_params}
        flag_param = next((p for p in names if p.startswith('flag_')), None)

        params = {
            'action': 'review',
            'token': self.tokens['csrf'],
            'revid': revid,
            'comment': comment,
        }

        if flag is not None:
            if flag_param is None:
                raise ValueError(
                    "The 'flag' parameter is not supported by this wiki")
            params[flag_param] = flag

        if unapprove:
            params['unapprove'] = '1'

        request = self.simple_request(**params, formatversion=2)
        data = request.submit()

        if data.get('review', {}).get('result') != 'Success':
            raise UnexpectedAPIDataError(
                f'Unexpected review result:\n{data!r}')
