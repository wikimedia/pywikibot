"""Objects representing API interface to MediaWiki site extenstions."""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
from typing import Any, Optional, Union

import pywikibot
from pywikibot.backports import Dict
from pywikibot.data import api
from pywikibot.echo import Notification
from pywikibot.exceptions import (
    APIError,
    Error,
    InconsistentTitleError,
    NoPageError,
    SiteDefinitionError,
)
from pywikibot.site._decorators import need_extension, need_right
from pywikibot.tools import merge_unique_dicts


class EchoMixin:

    """APISite mixin for Echo extension."""

    @need_extension('Echo')
    def notifications(self, **kwargs):
        """Yield Notification objects from the Echo extension.

        :keyword Optional[str] format: If specified, notifications will
            be returned formatted this way. Its value is either ``model``,
            ``special`` or ``None``. Default is ``special``.

        .. seealso:: :api:`Notifications` for other keywords.
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
    def notifications_mark_read(self, **kwargs) -> bool:
        """Mark selected notifications as read.

        .. seealso:: :api:`echomarkread`

        :return: whether the action was successful
        """
        # TODO: ensure that the 'echomarkread' action
        # is supported by the site
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
    def _cache_proofreadinfo(self, expiry=False) -> None:
        """Retrieve proofreadinfo from site and cache response.

        Applicable only to sites with ProofreadPage extension installed.

        The following info is returned by the query and cached:
        - self._proofread_index_ns: Index Namespace
        - self._proofread_page_ns: Page Namespace
        - self._proofread_levels: a dictionary with::

            keys: int in the range [0, 1, ..., 4]
            values: category name corresponding to the 'key' quality level
            e.g. on en.wikisource:

            .. code-block::
                {0: 'Without text', 1: 'Not proofread', 2: 'Problematic',
                 3: 'Proofread', 4: 'Validated'}

        :param expiry: either a number of days or a datetime.timedelta object
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


class GeoDataMixin:

    """APISite mixin for GeoData extension."""

    @need_extension('GeoData')
    def loadcoordinfo(self, page) -> None:
        """Load [[mw:Extension:GeoData]] info."""
        title = page.title(with_section=False)
        query = self._generator(api.PropertyGenerator,
                                type_arg='coordinates',
                                titles=title.encode(self.encoding()),
                                coprop=['type', 'name', 'dim',
                                        'country', 'region',
                                        'globe'],
                                coprimary='all')
        self._update_page(page, query)


class PageImagesMixin:

    """APISite mixin for PageImages extension."""

    @need_extension('PageImages')
    def loadpageimage(self, page) -> None:
        """
        Load [[mw:Extension:PageImages]] info.

        :param page: The page for which to obtain the image
        :type page: pywikibot.Page

        :raises APIError: PageImages extension is not installed
        """
        title = page.title(with_section=False)
        query = self._generator(api.PropertyGenerator,
                                type_arg='pageimages',
                                titles=title.encode(self.encoding()),
                                piprop=['name'])
        self._update_page(page, query)


class GlobalUsageMixin:

    """APISite mixin for Global Usage extension."""

    @need_extension('Global Usage')
    def globalusage(self, page, total=None):
        """Iterate global image usage for a given FilePage.

        :param page: the page to return global image usage for.
        :type page: pywikibot.FilePage
        :param total: iterate no more than this number of pages in total.
        :raises TypeError: input page is not a FilePage.
        :raises pywikibot.exceptions.SiteDefinitionError: Site could not be
            defined for a returned entry in API response.
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
                    pywikibot.warning(
                        'Site could not be defined for global'
                        ' usage for {}: {}.'.format(page, entry))
                    continue
                gu_page = pywikibot.Page(gu_site, entry['title'])
                yield gu_page


class WikibaseClientMixin:

    """APISite mixin for WikibaseClient extension."""

    @need_extension('WikibaseClient')
    def unconnected_pages(self, total=None):
        """Yield Page objects from Special:UnconnectedPages.

        :param total: number of pages to return
        """
        return self.querypage('UnconnectedPages', total)


class LinterMixin:

    """APISite mixin for Linter extension."""

    @need_extension('Linter')
    def linter_pages(self, lint_categories=None, total=None,
                     namespaces=None, pageids=None, lint_from=None):
        """Return a generator to pages containing linter errors.

        :param lint_categories: categories of lint errors
        :type lint_categories: an iterable that returns values (str),
            or a pipe-separated string of values.

        :param total: if not None, yielding this many items in total
        :type total: int

        :param namespaces: only iterate pages in these namespaces
        :type namespaces: iterable of str or Namespace key,
            or a single instance of those types. May be a '|' separated
            list of namespace identifiers.

        :param pageids: only include lint errors from the specified pageids
        :type pageids: an iterable that returns pageids (str or int),
            or a comma- or pipe-separated string of pageids
            (e.g. '945097,1483753, 956608' or '945097|483753|956608')

        :param lint_from: Lint ID to start querying from
        :type lint_from: str representing digit or integer

        :return: pages with Linter errors.
        :rtype: typing.Iterable[pywikibot.Page]
        """
        query = self._generator(api.ListGenerator, type_arg='linterrors',
                                total=total,  # Will set lntlimit
                                namespaces=namespaces)

        if lint_categories:
            if isinstance(lint_categories, str):
                lint_categories = lint_categories.split('|')
                lint_categories = [p.strip() for p in lint_categories]
            query.request['lntcategories'] = '|'.join(lint_categories)

        if pageids:
            if isinstance(pageids, str):
                pageids = pageids.split('|')
                pageids = [p.strip() for p in pageids]
            # Validate pageids.
            pageids = (str(int(p)) for p in pageids if int(p) > 0)
            query.request['lntpageid'] = '|'.join(pageids)

        if lint_from:
            query.request['lntfrom'] = int(lint_from)

        for pageitem in query:
            page = pywikibot.Page(self, pageitem['title'])
            api.update_page(page, pageitem)
            yield page


class ThanksMixin:

    """APISite mixin for Thanks extension."""

    @need_extension('Thanks')
    def thank_revision(self, revid, source=None):
        """Corresponding method to the 'action=thank' API action.

        :param revid: Revision ID for the revision to be thanked.
        :type revid: int
        :param source: A source for the thanking operation.
        :type source: str
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


class ThanksFlowMixin:

    """APISite mixin for Thanks and Flow extension."""

    @need_extension('Flow')
    @need_extension('Thanks')
    def thank_post(self, post):
        """Corresponding method to the 'action=flowthank' API action.

        :param post: The post to be thanked for.
        :type post: Post
        :raise APIError: On thanking oneself or other API errors.
        :return: The API response.
        """
        post_id = post.uuid
        token = self.tokens['csrf']
        req = self.simple_request(action='flowthank', postid=post_id,
                                  token=token)
        data = req.submit()
        if data['result']['success'] != 1:
            raise APIError('Thanking unsuccessful', '')
        return data


class FlowMixin:

    """APISite mixin for Flow extension."""

    @need_extension('Flow')
    def load_board(self, page):
        """
        Retrieve the data for a Flow board.

        :param page: A Flow board
        :type page: Board
        :return: A dict representing the board's metadata.
        :rtype: dict
        """
        req = self.simple_request(action='flow', page=page,
                                  submodule='view-topiclist', vtllimit=1)
        data = req.submit()
        return data['flow']['view-topiclist']['result']['topiclist']

    @need_extension('Flow')
    def load_topiclist(self,
                       page: 'pywikibot.flow.Board',
                       *,
                       content_format: str = 'wikitext',
                       limit: int = 100,
                       sortby: str = 'newest',
                       toconly: bool = False,
                       offset: Union['pywikibot.Timestamp', str, None] = None,
                       offset_id: Optional[str] = None,
                       reverse: bool = False,
                       include_offset: bool = False) -> Dict[str, Any]:
        """
        Retrieve the topiclist of a Flow board.

        .. versionchanged:: 8.0
           All parameters except *page* are keyword only parameters.

        :param page: A Flow board
        :param content_format: The content format to request the data in.
            must be either 'wikitext', 'html', or 'fixed-html'
        :param limit: The number of topics to fetch in each single request.
        :param sortby: Algorithm to sort topics by ('newest' or 'updated').
        :param toconly: Whether to only include information for the TOC.
        :param offset: The timestamp to start at (when sortby is 'updated').
        :param offset_id: The topic UUID to start at (when sortby is 'newest').
        :param reverse: Whether to reverse the topic ordering.
        :param include_offset: Whether to include the offset topic.
        :return: A dict representing the board's topiclist.
        """
        if offset:
            offset = pywikibot.Timestamp.fromtimestampformat(offset)
        offset_dir = 'rev' if reverse else 'fwd'

        params = {'action': 'flow', 'submodule': 'view-topiclist',
                  'page': page,
                  'vtlformat': content_format, 'vtlsortby': sortby,
                  'vtllimit': limit, 'vtloffset-dir': offset_dir,
                  'vtloffset': offset, 'vtloffset-id': offset_id,
                  'vtlinclude-offset': include_offset, 'vtltoconly': toconly}
        req = self._request(parameters=params)
        data = req.submit()
        return data['flow']['view-topiclist']['result']['topiclist']

    @need_extension('Flow')
    def load_topic(self, page, content_format: str):
        """
        Retrieve the data for a Flow topic.

        :param page: A Flow topic
        :type page: Topic
        :param content_format: The content format to request the data in.
            Must ne either 'wikitext', 'html', or 'fixed-html'
        :return: A dict representing the topic's data.
        :rtype: dict
        """
        req = self.simple_request(action='flow', page=page,
                                  submodule='view-topic',
                                  vtformat=content_format)
        data = req.submit()
        return data['flow']['view-topic']['result']['topic']

    @need_extension('Flow')
    def load_post_current_revision(self, page, post_id, content_format: str):
        """
        Retrieve the data for a post to a Flow topic.

        :param page: A Flow topic
        :type page: Topic
        :param post_id: The UUID of the Post
        :type post_id: str
        :param content_format: The content format used for the returned
            content; must be either 'wikitext', 'html', or 'fixed-html'
        :return: A dict representing the post data for the given UUID.
        :rtype: dict
        """
        req = self.simple_request(action='flow', page=page,
                                  submodule='view-post', vppostId=post_id,
                                  vpformat=content_format)
        data = req.submit()
        return data['flow']['view-post']['result']['topic']

    @need_right('edit')
    @need_extension('Flow')
    def create_new_topic(self, page, title, content, content_format):
        """
        Create a new topic on a Flow board.

        :param page: A Flow board
        :type page: Board
        :param title: The title of the new topic (must be in plaintext)
        :type title: str
        :param content: The content of the topic's initial post
        :type content: str
        :param content_format: The content format of the supplied content
        :type content_format: str (either 'wikitext' or 'html')
        :return: The metadata of the new topic
        :rtype: dict
        """
        token = self.tokens['csrf']
        params = {'action': 'flow', 'page': page, 'token': token,
                  'submodule': 'new-topic', 'ntformat': content_format,
                  'nttopic': title, 'ntcontent': content}
        req = self._request(parameters=params, use_get=False)
        data = req.submit()
        return data['flow']['new-topic']['committed']['topiclist']

    @need_right('edit')
    @need_extension('Flow')
    def reply_to_post(self, page, reply_to_uuid: str, content: str,
                      content_format: str) -> dict:
        """Reply to a post on a Flow topic.

        :param page: A Flow topic
        :type page: Topic
        :param reply_to_uuid: The UUID of the Post to create a reply to
        :param content: The content of the reply
        :param content_format: The content format used for the supplied
            content; must be either 'wikitext' or 'html'
        :return: Metadata returned by the API
        """
        token = self.tokens['csrf']
        params = {'action': 'flow', 'page': page, 'token': token,
                  'submodule': 'reply', 'repreplyTo': reply_to_uuid,
                  'repcontent': content, 'repformat': content_format}
        req = self._request(parameters=params, use_get=False)
        data = req.submit()
        return data['flow']['reply']['committed']['topic']

    @need_right('flow-lock')
    @need_extension('Flow')
    def lock_topic(self, page, lock, reason):
        """
        Lock or unlock a Flow topic.

        :param page: A Flow topic
        :type page: Topic
        :param lock: Whether to lock or unlock the topic
        :type lock: bool (True corresponds to locking the topic.)
        :param reason: The reason to lock or unlock the topic
        :type reason: str
        :return: Metadata returned by the API
        :rtype: dict
        """
        status = 'lock' if lock else 'unlock'
        token = self.tokens['csrf']
        params = {'action': 'flow', 'page': page, 'token': token,
                  'submodule': 'lock-topic', 'cotreason': reason,
                  'cotmoderationState': status}
        req = self._request(parameters=params, use_get=False)
        data = req.submit()
        return data['flow']['lock-topic']['committed']['topic']

    @need_right('edit')
    @need_extension('Flow')
    def moderate_topic(self, page, state, reason):
        """
        Moderate a Flow topic.

        :param page: A Flow topic
        :type page: Topic
        :param state: The new moderation state
        :type state: str
        :param reason: The reason to moderate the topic
        :type reason: str
        :return: Metadata returned by the API
        :rtype: dict
        """
        token = self.tokens['csrf']
        params = {'action': 'flow', 'page': page, 'token': token,
                  'submodule': 'moderate-topic', 'mtreason': reason,
                  'mtmoderationState': state}
        req = self._request(parameters=params, use_get=False)
        data = req.submit()
        return data['flow']['moderate-topic']['committed']['topic']

    @need_right('flow-delete')
    @need_extension('Flow')
    def delete_topic(self, page, reason):
        """
        Delete a Flow topic.

        :param page: A Flow topic
        :type page: Topic
        :param reason: The reason to delete the topic
        :type reason: str
        :return: Metadata returned by the API
        :rtype: dict
        """
        return self.moderate_topic(page, 'delete', reason)

    @need_right('flow-hide')
    @need_extension('Flow')
    def hide_topic(self, page, reason):
        """
        Hide a Flow topic.

        :param page: A Flow topic
        :type page: Topic
        :param reason: The reason to hide the topic
        :type reason: str
        :return: Metadata returned by the API
        :rtype: dict
        """
        return self.moderate_topic(page, 'hide', reason)

    @need_right('flow-suppress')
    @need_extension('Flow')
    def suppress_topic(self, page, reason):
        """
        Suppress a Flow topic.

        :param page: A Flow topic
        :type page: Topic
        :param reason: The reason to suppress the topic
        :type reason: str
        :return: Metadata returned by the API
        :rtype: dict
        """
        return self.moderate_topic(page, 'suppress', reason)

    @need_right('edit')
    @need_extension('Flow')
    def restore_topic(self, page, reason):
        """
        Restore a Flow topic.

        :param page: A Flow topic
        :type page: Topic
        :param reason: The reason to restore the topic
        :type reason: str
        :return: Metadata returned by the API
        :rtype: dict
        """
        return self.moderate_topic(page, 'restore', reason)

    @need_right('edit')
    @need_extension('Flow')
    def moderate_post(self, post, state, reason):
        """
        Moderate a Flow post.

        :param post: A Flow post
        :type post: Post
        :param state: The new moderation state
        :type state: str
        :param reason: The reason to moderate the topic
        :type reason: str
        :return: Metadata returned by the API
        :rtype: dict
        """
        page = post.page
        uuid = post.uuid
        token = self.tokens['csrf']
        params = {'action': 'flow', 'page': page, 'token': token,
                  'submodule': 'moderate-post', 'mpreason': reason,
                  'mpmoderationState': state, 'mppostId': uuid}
        req = self._request(parameters=params, use_get=False)
        data = req.submit()
        return data['flow']['moderate-post']['committed']['topic']

    @need_right('flow-delete')
    @need_extension('Flow')
    def delete_post(self, post, reason):
        """
        Delete a Flow post.

        :param post: A Flow post
        :type post: Post
        :param reason: The reason to delete the post
        :type reason: str
        :return: Metadata returned by the API
        :rtype: dict
        """
        return self.moderate_post(post, 'delete', reason)

    @need_right('flow-hide')
    @need_extension('Flow')
    def hide_post(self, post, reason):
        """
        Hide a Flow post.

        :param post: A Flow post
        :type post: Post
        :param reason: The reason to hide the post
        :type reason: str
        :return: Metadata returned by the API
        :rtype: dict
        """
        return self.moderate_post(post, 'hide', reason)

    @need_right('flow-suppress')
    @need_extension('Flow')
    def suppress_post(self, post, reason):
        """
        Suppress a Flow post.

        :param post: A Flow post
        :type post: Post
        :param reason: The reason to suppress the post
        :type reason: str
        :return: Metadata returned by the API
        :rtype: dict
        """
        return self.moderate_post(post, 'suppress', reason)

    @need_right('edit')
    @need_extension('Flow')
    def restore_post(self, post, reason):
        """
        Restore a Flow post.

        :param post: A Flow post
        :type post: Post
        :param reason: The reason to restore the post
        :type reason: str
        :return: Metadata returned by the API
        :rtype: dict
        """
        return self.moderate_post(post, 'restore', reason)


class UrlShortenerMixin:

    """APISite mixin for UrlShortener extension."""

    @need_extension('UrlShortener')
    def create_short_link(self, url):
        """
        Return a shortened link.

        Note that on Wikimedia wikis only metawiki supports this action,
        and this wiki can process links to all WM domains.

        :param url: The link to reduce, with propotol prefix.
        :type url: str
        :return: The reduced link, without protocol prefix.
        :rtype: str
        """
        req = self.simple_request(action='shortenurl', url=url)
        data = req.submit()
        return data['shortenurl']['shorturl']


class TextExtractsMixin:

    """APISite mixin for TextExtracts extension.

    .. versionadded:: 7.1
    """

    @need_extension('TextExtracts')
    def extract(self, page: 'pywikibot.Page', *,
                chars: Optional[int] = None,
                sentences: Optional[int] = None,
                intro: bool = True,
                plaintext: bool = True) -> str:
        """Retrieve an extract of a page.

        :param page: The Page object for which the extract is read
        :param chars: How many characters to return.  Actual text
            returned might be slightly longer.
        :param sentences: How many sentences to return
        :param intro: Return only content before the first section
        :param plaintext: if True, return extracts as plain text instead
            of limited HTML

        .. seealso::

           - https://www.mediawiki.org/wiki/Extension:TextExtracts

           - :meth:`page.BasePage.extract`.
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
                                 'Unknown exception:\n{}'.format(data['-1']))
            raise Error(msg)

        return data[str(page.pageid)]['extract']
