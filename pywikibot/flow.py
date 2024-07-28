"""Objects representing Structured Discussions entities.

Structured Discussions was formerly known as Flow. Flow was renamed in
2017 as the focus was scoped to user-to-user discussions.

.. caution:: Structured Discussions support previously known as Flow is
   no longer tested because the test environment was disabled. Please
   use this module with care.
.. deprecated:: 9.4
   Structured Discussions extension is not maintained and will be
   removed. Users are encouraged to stop using it. (:phab:`T371180`)
.. seealso::
   - https://www.mediawiki.org/wiki/Structured_Discussions
   - https://www.mediawiki.org/wiki/Structured_Discussions/Wikis
   - https://www.mediawiki.org/wiki/Extension:StructuredDiscussions
"""
#
# (C) Pywikibot team, 2015-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import abc
import datetime
from typing import Any
from urllib.parse import parse_qs, urlparse

import pywikibot
from pywikibot import config
from pywikibot.backports import Iterator, Mapping
from pywikibot.exceptions import (
    LockedPageError,
    NoPageError,
    UnknownExtensionError,
)
from pywikibot.page import BasePage, PageSourceType, User
from pywikibot.tools import cached, deprecated_args


__all__ = (
    'Board',
    'FlowPage',
    'Post',
    'Topic',
)


class FlowPage(BasePage, abc.ABC):

    """The base page meta class for the Flow extension.

    Defines Flow page-like object for :class:`Board` and :class:`Topic`.
    It cannot be instantiated directly.
    """

    def __init__(self, source: PageSourceType, title: str = '') -> None:
        """Initializer.

        :param source: A Flow-enabled site or a Link or Page on such a site
        :param title: normalized title of the page

        :raises TypeError: incorrect use of parameters
        :raises ValueError: use of non-Flow-enabled Site
        """
        super().__init__(source, title)

        if not self.site.has_extension('Flow'):
            raise UnknownExtensionError('site is not Flow-enabled')

    @abc.abstractmethod
    def _load(self, force: bool = False) -> dict[str, Any]:
        """Abstract method to load and cache the Flow data.

        Subclasses must overwrite _load() method to load and cache
        the object's internal data from the API.
        """
        raise NotImplementedError

    @property
    @cached
    def uuid(self) -> str:
        """Return the UUID of the page.

        :return: UUID of the page
        """
        return self._load()['workflowId']

    def get(self, force: bool = False, get_redirect: bool = False
            ) -> dict[str, Any]:
        """Get the page's content."""
        if get_redirect or force:
            raise NotImplementedError(
                "Neither 'force' nor 'get_redirect' parameter is implemented "
                'in {}.get()'.format(self.__class__.__name__))

        # TODO: Return more useful data
        return getattr(self, '_data', {})


class Board(FlowPage):

    """A Flow discussion board."""

    def _load(self, force: bool = False) -> dict[str, Any]:
        """Load and cache the Board's data, derived from its topic list.

        :param force: Whether to force a reload if the data is already loaded
        """
        if not hasattr(self, '_data') or force:
            self._data = self.site.load_board(self)
        return self._data

    @staticmethod
    def _parse_url(links: Mapping[str, Any]) -> dict[str, Any]:
        """Parse a URL retrieved from the API."""
        if 'fwd' in links:
            rule = links['fwd']
        elif 'rev' in links:
            rule = links['rev']
        else:
            raise ValueError('Illegal board data (missing required data).')
        parsed_url = urlparse(rule['url'])
        params = parse_qs(parsed_url.query)
        new_params: dict[str, Any] = {}
        for key, value in params.items():
            if key != 'title':
                key = key.replace('topiclist_', '').replace('-', '_')
                if key == 'offset_dir':
                    new_params['reverse'] = value == 'rev'
                else:
                    new_params[key] = value
        return new_params

    @deprecated_args(limit='total')  # since 8.0.0
    def topics(self, *,
               content_format: str = 'wikitext',
               total: int | None = None,
               sort_by: str = 'newest',
               offset: str | datetime.datetime | None = None,
               offset_uuid: str = '',
               reverse: bool = False,
               include_offset: bool = False,
               toc_only: bool = False
               ) -> Iterator[Topic]:
        """Load this board's topics.

        .. versionchanged:: 8.0
           The *total* parameter was added as a per request limit.
           All parameters are keyword only parameters.
        .. deprecated:: 8.0
           The *limit* parameter. Use ``-step`` global option or
           :ref:`config.step<Settings to Avoid Server Overload>` instead.

        :param content_format: The content format to request the data in;
            must be either 'wikitext', 'html', or 'fixed-html'
        :param total: The number of topics to fetch.
        :param sort_by: Algorithm to sort topics by;
            must be either 'newest' or 'updated'
        :param offset: The timestamp to start at (when sortby is 'updated').
        :param offset_uuid: The UUID to start at (when sortby is 'newest').
        :param reverse: Whether to reverse the topic ordering.
        :param include_offset: Whether to include the offset topic.
        :param toc_only: Whether to only include information for the TOC.
        :yield: A generator of this board's topics.
        """
        maxlimit = min(config.step, 100) if config.step > 0 else 100
        request_limit = min(total, maxlimit)
        data = self.site.load_topiclist(self, content_format=content_format,
                                        limit=request_limit, sortby=sort_by,
                                        toconly=toc_only, offset=offset,
                                        offset_id=offset_uuid, reverse=reverse,
                                        include_offset=include_offset)
        count = 0
        while data['roots']:
            for root in data['roots']:
                topic = Topic.from_topiclist_data(self, root, data)
                yield topic

                count += 1
                if count >= total:
                    return

            continue_args = self._parse_url(data['links']['pagination'])
            data = self.site.load_topiclist(self, **continue_args)

    def new_topic(self, title: str, content: str,
                  content_format: str = 'wikitext') -> Topic:
        """Create and return a Topic object for a new topic on this Board.

        :param title: The title of the new topic (must be in plaintext)
        :param content: The content of the topic's initial post
        :param content_format: The content format of the supplied content;
            either 'wikitext' or 'html'
        :return: The new topic
        """
        return Topic.create_topic(self, title, content, content_format)


class Topic(FlowPage):

    """A Flow discussion topic."""

    def _load(self, force: bool = False, content_format: str = 'wikitext'
              ) -> dict[str, Any]:
        """Load and cache the Topic's data.

        :param force: Whether to force a reload if the data is already loaded
        :param content_format: The post format in which to load
        """
        if not hasattr(self, '_data') or force:
            self._data = self.site.load_topic(self, content_format)
        return self._data

    def _reload(self) -> None:
        """Forcibly reload the topic's root post."""
        self.root._load(load_from_topic=True)

    @classmethod
    def create_topic(cls, board: Board, title: str,
                     content: str, content_format: str = 'wikitext'
                     ) -> Topic:
        """Create and return a Topic object for a new topic on a Board.

        :param board: The topic's parent board
        :param title: The title of the new topic (must be in plaintext)
        :param content: The content of the topic's initial post
        :param content_format: The content format of the supplied content;
            either 'wikitext' or 'html'
        :return: The new topic
        """
        data = board.site.create_new_topic(board, title, content,
                                           content_format)
        return cls(board.site, data['topic-page'])

    @classmethod
    def from_topiclist_data(cls, board: Board,
                            root_uuid: str,
                            topiclist_data: dict[str, Any]) -> Topic:
        """Create a Topic object from API data.

        :param board: The topic's parent Flow board
        :param root_uuid: The UUID of the topic and its root post
        :param topiclist_data: The data returned by view-topiclist
        :return: A Topic object derived from the supplied data
        :raises TypeError: any passed parameters have wrong types
        :raises ValueError: the passed topiclist_data is missing required data
        """
        if not isinstance(board, Board):
            raise TypeError('board must be a pywikibot.flow.Board object.')
        if not isinstance(root_uuid, str):
            raise TypeError('Topic/root UUID must be a string.')

        topic = cls(board.site, 'Topic:' + root_uuid)
        topic._root = Post.fromJSON(topic, root_uuid, topiclist_data)
        topic._uuid = root_uuid
        return topic

    @property
    def root(self) -> Post:
        """The root post of this topic."""
        if not hasattr(self, '_root'):
            self._root = Post.fromJSON(self, self.uuid, self._data)
        return self._root

    @property
    def is_locked(self) -> bool:
        """Whether this topic is locked."""
        return self.root._current_revision['isLocked']

    @property
    def is_moderated(self) -> bool:
        """Whether this topic is moderated."""
        return self.root._current_revision['isModerated']

    def replies(self, content_format: str = 'wikitext', force: bool = False
                ) -> list[Post]:
        """A list of replies to this topic's root post.

        :param content_format: Content format to return contents in;
            must be 'wikitext', 'html', or 'fixed-html'
        :param force: Whether to reload from the API instead of using the cache
        :return: The replies of this topic's root post
        """
        return self.root.replies(content_format=content_format, force=force)

    def reply(self, content: str, content_format: str = 'wikitext') -> Post:
        """A convenience method to reply to this topic's root post.

        :param content: The content of the new post
        :param content_format: The format of the given content;
            must be 'wikitext' or 'html')
        :return: The new reply to this topic's root post
        """
        return self.root.reply(content, content_format)

    # Moderation
    def lock(self, reason: str) -> None:
        """Lock this topic.

        :param reason: The reason for locking this topic
        """
        self.site.lock_topic(self, True, reason)
        self._reload()

    def unlock(self, reason: str) -> None:
        """Unlock this topic.

        :param reason: The reason for unlocking this topic
        """
        self.site.lock_topic(self, False, reason)
        self._reload()

    def delete_mod(self, reason: str) -> None:
        """Delete this topic through the Flow moderation system.

        :param reason: The reason for deleting this topic.
        """
        self.site.delete_topic(self, reason)
        self._reload()

    def hide(self, reason: str) -> None:
        """Hide this topic.

        :param reason: The reason for hiding this topic.
        """
        self.site.hide_topic(self, reason)
        self._reload()

    def suppress(self, reason: str) -> None:
        """Suppress this topic.

        :param reason: The reason for suppressing this topic.
        """
        self.site.suppress_topic(self, reason)
        self._reload()

    def restore(self, reason: str) -> None:
        """Restore this topic.

        :param reason: The reason for restoring this topic.
        """
        self.site.restore_topic(self, reason)
        self._reload()

    def summary(self) -> str | None:
        """Get this topic summary, if any.

        :return: summary or None
        """
        if 'summary' in self.root._current_revision:
            return self.root._current_revision['summary']['revision'][
                'content']['content']
        return None

    def summarize(self, summary: str) -> None:
        """Summarize this topic.

        :param summary: The summary that will be added to the topic.
        """
        self.site.summarize_topic(self, summary)
        self._reload()


class Post:

    """A post to a Flow discussion topic. This is a non-page-like object."""

    def __init__(self, page: Topic, uuid: str) -> None:
        """Initializer.

        :param page: Flow topic
        :param uuid: UUID of a Flow post

        :raises TypeError: incorrect types of parameters
        """
        if not isinstance(page, Topic):
            raise TypeError('Page must be a Topic object')
        if not page.exists():
            raise NoPageError(page, 'Topic must exist: %s')
        if not isinstance(uuid, str):
            raise TypeError('Post UUID must be a string')

        self._page = page
        self._uuid = uuid

        self._content: dict[str, Any] = {}

    @classmethod
    def fromJSON(cls, page: Topic, post_uuid: str,  # noqa: N802
                 data: dict[str, Any]) -> Post:
        """
        Create a Post object using the data returned from the API call.

        :param page: A Flow topic
        :param post_uuid: The UUID of the post
        :param data: The JSON data returned from the API

        :return: A Post object
        :raises TypeError: data is not a dict
        :raises ValueError: data is missing required entries
        """
        post = cls(page, post_uuid)
        post._set_data(data)

        return post

    def _set_data(self, data: dict[str, Any]) -> None:
        """Set internal data and cache content.

        :param data: The data to store internally
        :raises TypeError: data is not a dict
        :raises ValueError: missing data entries or post/revision not found
        """
        if not isinstance(data, dict):
            raise TypeError('Illegal post data (must be a dictionary).')
        if ('posts' not in data) or ('revisions' not in data):
            raise ValueError('Illegal post data (missing required data).')
        if self.uuid not in data['posts']:
            raise ValueError('Post not found in supplied data.')

        current_revision_id = data['posts'][self.uuid][0]
        if current_revision_id not in data['revisions']:
            raise ValueError('Current revision of post'
                             'not found in supplied data.')

        self._current_revision = data['revisions'][current_revision_id]
        if 'content' in self._current_revision:
            content = self._current_revision.pop('content')
            assert isinstance(content, dict)
            assert isinstance(content['content'], str)
            self._content[content['format']] = content['content']

    def _load(self, force: bool = True, content_format: str = 'wikitext',
              load_from_topic: bool = False) -> dict[str, Any]:
        """Load and cache the Post's data using the given content format.

        :param load_from_topic: Whether to load the post from the whole topic
        """
        if load_from_topic:
            data = self.page._load(force=force, content_format=content_format)
        else:
            data = self.site.load_post_current_revision(self.page, self.uuid,
                                                        content_format)
        self._set_data(data)
        return self._current_revision

    @property
    def uuid(self) -> str:
        """Return the UUID of the post.

        :return: UUID of the post
        """
        return self._uuid

    @property
    def site(self) -> pywikibot.site.BaseSite:
        """Return the site associated with the post.

        :return: Site associated with the post
        """
        return self._page.site

    @property
    def page(self) -> Topic:
        """Return the page associated with the post.

        :return: Page associated with the post
        """
        return self._page

    @property
    def is_moderated(self) -> bool:
        """Whether this post is moderated."""
        if not hasattr(self, '_current_revision'):
            self._load()
        return self._current_revision['isModerated']

    @property
    def creator(self) -> User:
        """The creator of this post."""
        if not hasattr(self, '_current_revision'):
            self._load()
        if not hasattr(self, '_creator'):
            self._creator = User(self.site,
                                 self._current_revision['creator']['name'])
        return self._creator

    def get(self, content_format: str = 'wikitext',
            force: bool = False) -> str:
        """Return the contents of the post in the given format.

        :param force: Whether to reload from the API instead of using the cache
        :param content_format: Content format to return contents in
        :return: The contents of the post in the given content format
        """
        if content_format not in self._content or force:
            self._load(content_format=content_format)
        return self._content[content_format]

    def replies(self, content_format: str = 'wikitext', force: bool = False
                ) -> list[Post]:
        """Return this post's replies.

        :param content_format: Content format to return contents in;
            must be 'wikitext', 'html', or 'fixed-html'
        :param force: Whether to reload from the API instead of using the cache
        :return: This post's replies
        """
        if content_format not in ('wikitext', 'html', 'fixed-html'):
            raise ValueError('Invalid content format.')

        if hasattr(self, '_replies') and not force:
            return self._replies  # type: ignore[has-type]

        # load_from_topic workaround due to T106733
        # (replies not returned by view-post)
        if not hasattr(self, '_current_revision') or force:
            self._load(content_format=content_format, load_from_topic=True)

        reply_uuids = self._current_revision['replies']
        self._replies = [Post(self.page, uuid) for uuid in reply_uuids]

        return self._replies

    def reply(self, content: str, content_format: str = 'wikitext') -> Post:
        """Reply to this post.

        :param content: The content of the new post
        :param content_format: The format of the given content;
            must be 'wikitext' or 'html'
        :return: The new reply post
        """
        self._load()
        if self.page.is_locked:
            raise LockedPageError(self.page, 'Topic %s is locked.')

        reply_url = self._current_revision['actions']['reply']['url']
        parsed_url = urlparse(reply_url)
        params = parse_qs(parsed_url.query)
        reply_to = params['topic_postId']
        if self.uuid == reply_to:
            del self._current_revision
            del self._replies
        data = self.site.reply_to_post(self.page, reply_to, content,
                                       content_format)
        return Post(self.page, data['post-id'])

    # Moderation
    def delete(self, reason: str) -> None:
        """Delete this post through the Flow moderation system.

        :param reason: The reason for deleting this post.
        """
        self.site.delete_post(self, reason)
        self._load()

    def hide(self, reason: str) -> None:
        """Hide this post.

        :param reason: The reason for hiding this post.
        """
        self.site.hide_post(self, reason)
        self._load()

    def suppress(self, reason: str) -> None:
        """Suppress this post.

        :param reason: The reason for suppressing this post.
        """
        self.site.suppress_post(self, reason)
        self._load()

    def restore(self, reason: str) -> None:
        """Restore this post.

        :param reason: The reason for restoring this post.
        """
        self.site.restore_post(self, reason)
        self._load()

    def thank(self) -> None:
        """Thank the user who made this post."""
        self.site.thank_post(self)
