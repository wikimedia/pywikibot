# -*- coding: utf-8 -*-
"""Objects representing Flow entities, like boards, topics, and posts."""
#
# (C) Pywikibot team, 2015-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import logging

from pywikibot.exceptions import NoPage, UnknownExtension, LockedPage
from pywikibot.page import BasePage, User
from pywikibot.tools import PY2, UnicodeType

if not PY2:
    from urllib.parse import urlparse, parse_qs
else:
    from urlparse import urlparse, parse_qs


logger = logging.getLogger('pywiki.wiki.flow')


# Flow page-like objects (boards and topics)
class FlowPage(BasePage):

    """
    The base page for the Flow extension.

    There should be no need to instantiate this directly.

    Subclasses must provide a _load() method to load and cache
    the object's internal data from the API.
    """

    def __init__(self, source, title=''):
        """Initializer.

        @param source: A Flow-enabled site or a Link or Page on such a site
        @type source: Site, pywikibot.page.Link, or pywikibot.page.Page
        @param title: normalized title of the page
        @type title: str

        @raises TypeError: incorrect use of parameters
        @raises ValueError: use of non-Flow-enabled Site
        """
        super(FlowPage, self).__init__(source, title)

        if not self.site.has_extension('Flow'):
            raise UnknownExtension('site is not Flow-enabled')

    def _load_uuid(self):
        """Load and save the UUID of the page."""
        self._uuid = self._load()['workflowId']

    @property
    def uuid(self):
        """Return the UUID of the page.

        @return: UUID of the page
        @rtype: str
        """
        if not hasattr(self, '_uuid'):
            self._load_uuid()
        return self._uuid

    def get(self, force=False, get_redirect=False):
        """Get the page's content."""
        if get_redirect or force:
            raise NotImplementedError

        # TODO: Return more useful data
        return self._data


class Board(FlowPage):

    """A Flow discussion board."""

    def _load(self, force=False):
        """Load and cache the Board's data, derived from its topic list."""
        if not hasattr(self, '_data') or force:
            self._data = self.site.load_board(self)
        return self._data

    def _parse_url(self, links):
        """Parse a URL retrieved from the API."""
        rule = links['fwd']
        parsed_url = urlparse(rule['url'])
        params = parse_qs(parsed_url.query)
        new_params = {}
        for key, value in params.items():
            if key != 'title':
                key = key.replace('topiclist_', '').replace('-', '_')
                if key == 'offset_dir':
                    new_params['reverse'] = (value == 'rev')
                else:
                    new_params[key] = value
        return new_params

    def topics(self, format='wikitext', limit=100, sort_by='newest',
               offset=None, offset_uuid='', reverse=False,
               include_offset=False, toc_only=False):
        """Load this board's topics.

        @param format: The content format to request the data in.
        @type format: str (either 'wikitext', 'html', or 'fixed-html')
        @param limit: The number of topics to fetch in each request.
        @type limit: int
        @param sort_by: Algorithm to sort topics by.
        @type sort_by: str (either 'newest' or 'updated')
        @param offset: The timestamp to start at (when sortby is 'updated').
        @type offset: Timestamp or equivalent str
        @param offset_uuid: The UUID to start at (when sortby is 'newest').
        @type offset_uuid: str (in the form of a UUID)
        @param reverse: Whether to reverse the topic ordering.
        @type reverse: bool
        @param include_offset: Whether to include the offset topic.
        @type include_offset: bool
        @param toc_only: Whether to only include information for the TOC.
        @type toc_only: bool
        @return: A generator of this board's topics.
        @rtype: generator of Topic objects
        """
        data = self.site.load_topiclist(self, format=format, limit=limit,
                                        sortby=sort_by, toconly=toc_only,
                                        offset=offset, offset_id=offset_uuid,
                                        reverse=reverse,
                                        include_offset=include_offset)
        while data['roots']:
            for root in data['roots']:
                topic = Topic.from_topiclist_data(self, root, data)
                yield topic
            cont_args = self._parse_url(data['links']['pagination'])
            data = self.site.load_topiclist(self, **cont_args)

    def new_topic(self, title, content, format='wikitext'):
        """Create and return a Topic object for a new topic on this Board.

        @param title: The title of the new topic (must be in plaintext)
        @type title: str
        @param content: The content of the topic's initial post
        @type content: str
        @param format: The content format of the value supplied for content
        @type format: str (either 'wikitext' or 'html')
        @return: The new topic
        @rtype: Topic
        """
        return Topic.create_topic(self, title, content, format)


class Topic(FlowPage):

    """A Flow discussion topic."""

    def _load(self, format='wikitext', force=False):
        """Load and cache the Topic's data."""
        if not hasattr(self, '_data') or force:
            self._data = self.site.load_topic(self, format)
        return self._data

    def _reload(self):
        """Forcibly reload the topic's root post."""
        self.root._load(load_from_topic=True)

    @classmethod
    def create_topic(cls, board, title, content, format='wikitext'):
        """Create and return a Topic object for a new topic on a Board.

        @param board: The topic's parent board
        @type board: Board
        @param title: The title of the new topic (must be in plaintext)
        @type title: str
        @param content: The content of the topic's initial post
        @type content: str
        @param format: The content format of the value supplied for content
        @type format: str (either 'wikitext' or 'html')
        @return: The new topic
        @rtype: Topic
        """
        data = board.site.create_new_topic(board, title, content, format)
        return cls(board.site, data['topic-page'])

    @classmethod
    def from_topiclist_data(cls, board, root_uuid, topiclist_data):
        """Create a Topic object from API data.

        @param board: The topic's parent Flow board
        @type board: Board
        @param root_uuid: The UUID of the topic and its root post
        @type root_uuid: str
        @param topiclist_data: The data returned by view-topiclist
        @type topiclist_data: dict
        @return: A Topic object derived from the supplied data
        @rtype: Topic
        @raises TypeError: any passed parameters have wrong types
        @raises ValueError: the passed topiclist_data is missing required data
        """
        if not isinstance(board, Board):
            raise TypeError('board must be a pywikibot.flow.Board object.')
        if not isinstance(root_uuid, UnicodeType):
            raise TypeError('Topic/root UUID must be a string.')

        topic = cls(board.site, 'Topic:' + root_uuid)
        topic._root = Post.fromJSON(topic, root_uuid, topiclist_data)
        topic._uuid = root_uuid
        return topic

    @property
    def root(self):
        """The root post of this topic."""
        if not hasattr(self, '_root'):
            self._root = Post.fromJSON(self, self.uuid, self._data)
        return self._root

    @property
    def is_locked(self):
        """Whether this topic is locked."""
        return self.root._current_revision['isLocked']

    @property
    def is_moderated(self):
        """Whether this topic is moderated."""
        return self.root._current_revision['isModerated']

    def replies(self, format='wikitext', force=False):
        """A list of replies to this topic's root post.

        @param format: Content format to return contents in
        @type format: str ('wikitext', 'html', or 'fixed-html')
        @param force: Whether to reload from the API instead of using the cache
        @type force: bool
        @return: The replies of this topic's root post
        @rtype: list of Posts
        """
        return self.root.replies(format=format, force=force)

    def reply(self, content, format='wikitext'):
        """A convenience method to reply to this topic's root post.

        @param content: The content of the new post
        @type content: str
        @param format: The format of the given content
        @type format: str ('wikitext' or 'html')
        @return: The new reply to this topic's root post
        @rtype: Post
        """
        return self.root.reply(content, format)

    # Moderation
    def lock(self, reason):
        """Lock this topic.

        @param reason: The reason for locking this topic
        @type reason: str
        """
        self.site.lock_topic(self, True, reason)
        self._reload()

    def unlock(self, reason):
        """Unlock this topic.

        @param reason: The reason for unlocking this topic
        @type reason: str
        """
        self.site.lock_topic(self, False, reason)
        self._reload()

    def delete_mod(self, reason):
        """Delete this topic through the Flow moderation system.

        @param reason: The reason for deleting this topic.
        @type reason: str
        """
        self.site.delete_topic(self, reason)
        self._reload()

    def hide(self, reason):
        """Hide this topic.

        @param reason: The reason for hiding this topic.
        @type reason: str
        """
        self.site.hide_topic(self, reason)
        self._reload()

    def suppress(self, reason):
        """Suppress this topic.

        @param reason: The reason for suppressing this topic.
        @type reason: str
        """
        self.site.suppress_topic(self, reason)
        self._reload()

    def restore(self, reason):
        """Restore this topic.

        @param reason: The reason for restoring this topic.
        @type reason: str
        """
        self.site.restore_topic(self, reason)
        self._reload()


# Flow non-page-like objects
class Post(object):

    """A post to a Flow discussion topic."""

    def __init__(self, page, uuid):
        """
        Initializer.

        @param page: Flow topic
        @type page: Topic
        @param uuid: UUID of a Flow post
        @type uuid: str

        @raises TypeError: incorrect types of parameters
        """
        if not isinstance(page, Topic):
            raise TypeError('Page must be a Topic object')
        if not page.exists():
            raise NoPage(page, 'Topic must exist: %s')
        if not isinstance(uuid, UnicodeType):
            raise TypeError('Post UUID must be a string')

        self._page = page
        self._uuid = uuid

        self._content = {}

    @classmethod
    def fromJSON(cls, page, post_uuid, data):
        """
        Create a Post object using the data returned from the API call.

        @param page: A Flow topic
        @type page: Topic
        @param post_uuid: The UUID of the post
        @type post_uuid: str
        @param data: The JSON data returned from the API
        @type data: dict

        @return: A Post object
        @raises TypeError: data is not a dict
        @raises ValueError: data is missing required entries
        """
        post = cls(page, post_uuid)
        post._set_data(data)

        return post

    def _set_data(self, data):
        """Set internal data and cache content.

        @param data: The data to store internally
        @type data: dict
        @raises TypeError: data is not a dict
        @raises ValueError: missing data entries or post/revision not found
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
            assert isinstance(content['content'], UnicodeType)
            self._content[content['format']] = content['content']

    def _load(self, format='wikitext', load_from_topic=False):
        """Load and cache the Post's data using the given content format."""
        if load_from_topic:
            data = self.page._load(format=format, force=True)
        else:
            data = self.site.load_post_current_revision(self.page, self.uuid,
                                                        format)
        self._set_data(data)
        return self._current_revision

    @property
    def uuid(self):
        """Return the UUID of the post.

        @return: UUID of the post
        @rtype: str
        """
        return self._uuid

    @property
    def site(self):
        """Return the site associated with the post.

        @return: Site associated with the post
        @rtype: Site
        """
        return self._page.site

    @property
    def page(self):
        """Return the page associated with the post.

        @return: Page associated with the post
        @rtype: FlowPage
        """
        return self._page

    @property
    def is_moderated(self):
        """Whether this post is moderated."""
        if not hasattr(self, '_current_revision'):
            self._load()
        return self._current_revision['isModerated']

    @property
    def creator(self):
        """The creator of this post."""
        if not hasattr(self, '_current_revision'):
            self._load()
        if not hasattr(self, '_creator'):
            self._creator = User(self.site,
                                 self._current_revision['creator']['name'])
        return self._creator

    def get(self, format='wikitext', force=False):
        """Return the contents of the post in the given format.

        @param force: Whether to reload from the API instead of using the cache
        @type force: bool
        @param format: Content format to return contents in
        @type format: str
        @return: The contents of the post in the given content format
        @rtype: str
        """
        if format not in self._content or force:
            self._load(format)
        return self._content[format]

    def replies(self, format='wikitext', force=False):
        """Return this post's replies.

        @param format: Content format to return contents in
        @type format: str ('wikitext', 'html', or 'fixed-html')
        @param force: Whether to reload from the API instead of using the cache
        @type force: bool
        @return: This post's replies
        @rtype: list of Posts
        """
        if format not in ('wikitext', 'html', 'fixed-html'):
            raise ValueError('Invalid content format.')

        if hasattr(self, '_replies') and not force:
            return self._replies

        # load_from_topic workaround due to T106733
        # (replies not returned by view-post)
        if not hasattr(self, '_current_revision') or force:
            self._load(format, load_from_topic=True)

        reply_uuids = self._current_revision['replies']
        self._replies = [Post(self.page, uuid) for uuid in reply_uuids]

        return self._replies

    def reply(self, content, format='wikitext'):
        """Reply to this post.

        @param content: The content of the new post
        @type content: str
        @param format: The format of the given content
        @type format: str ('wikitext' or 'html')
        @return: The new reply post
        @rtype: Post
        """
        self._load()
        if self.page.is_locked:
            raise LockedPage(self.page, 'Topic %s is locked.')

        reply_url = self._current_revision['actions']['reply']['url']
        parsed_url = urlparse(reply_url)
        params = parse_qs(parsed_url.query)
        reply_to = params['topic_postId']
        if self.uuid == reply_to:
            del self._current_revision
            del self._replies
        data = self.site.reply_to_post(self.page, reply_to, content, format)
        post = Post(self.page, data['post-id'])
        return post

    # Moderation
    def delete(self, reason):
        """Delete this post through the Flow moderation system.

        @param reason: The reason for deleting this post.
        @type reason: str
        """
        self.site.delete_post(self, reason)
        self._load()

    def hide(self, reason):
        """Hide this post.

        @param reason: The reason for hiding this post.
        @type reason: str
        """
        self.site.hide_post(self, reason)
        self._load()

    def suppress(self, reason):
        """Suppress this post.

        @param reason: The reason for suppressing this post.
        @type reason: str
        """
        self.site.suppress_post(self, reason)
        self._load()

    def restore(self, reason):
        """Restore this post.

        @param reason: The reason for restoring this post.
        @type reason: str
        """
        self.site.restore_post(self, reason)
        self._load()

    def thank(self):
        """Thank the user who made this post."""
        self.site.thank_post(self)
