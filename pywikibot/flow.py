# -*- coding: utf-8  -*-
"""Objects representing Flow entities, like boards, topics, and posts."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import logging

from pywikibot.page import BasePage


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
        """Constructor.

        @param source: A Flow-enabled site or a Link or Page on such a site
        @type source: Site, Link, or Page
        @param title: normalized title of the page
        @type title: unicode

        @raise TypeError: incorrect use of parameters
        @raise ValueError: use of non-Flow-enabled Site
        """
        super(FlowPage, self).__init__(source, title)

        if not self.site.has_extension('Flow'):
            raise ValueError('site is not Flow-enabled')

    def _load_uuid(self):
        """Load and save the UUID of the page."""
        self._uuid = self._load()['workflowId']

    @property
    def uuid(self):
        """Return the UUID of the page.

        @return: UUID of the page
        @rtype: unicode
        """
        if not hasattr(self, '_uuid'):
            self._load_uuid()
        return self._uuid


class Board(FlowPage):

    """A Flow discussion board."""

    def _load(self):
        """Load and cache the Board's data, derived from its topic list."""
        if not hasattr(self, '_data'):
            self._data = self.site.load_board(self)
        return self._data


class Topic(FlowPage):

    """A Flow discussion topic."""

    def _load(self):
        """Load and cache the Topic's data."""
        if not hasattr(self, '_data'):
            self._data = self.site.load_topic(self)
        return self._data


# Flow non-page-like objects (currently just posts)
class Post(object):

    """A post to a Flow discussion topic."""

    def __init__(self, page, uuid):
        """
        Constructor.

        @param page: Flow topic or board
        @type page: FlowPage
        @param uuid: UUID of a Flow post
        @type uuid: unicode

        @raise TypeError: incorrect types of parameters
        @raise ValueError: use of non-Flow-enabled Site or invalid UUID
        """
        if not isinstance(page, FlowPage):
            raise TypeError('page must be a FlowPage object')

        if not uuid:
            raise ValueError('post UUID must be provided')

        self._page = page
        self._uuid = uuid

    @property
    def uuid(self):
        """Return the UUID of the post.

        @return: UUID of the post
        @rtype: unicode
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
