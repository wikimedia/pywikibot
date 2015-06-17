# -*- coding: utf-8  -*-
"""Tests for the flow module."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import pywikibot
import pywikibot.flow

from tests.aspects import (
    TestCase,
)

from tests.basepage_tests import (
    BasePageMethodsTestBase,
    BasePageLoadRevisionsCachingTestBase,
)


class TestBoardBasePageMethods(BasePageMethodsTestBase):

    """Test Flow pages using BasePage-defined methods."""

    family = 'mediawiki'
    code = 'mediawiki'

    def setUp(self):
        self._page = pywikibot.flow.Board(
            self.site, 'Talk:Sandbox')
        super(TestBoardBasePageMethods, self).setUp()

    def test_basepage_methods(self):
        """Test basic Page methods on a Flow page."""
        self._test_invoke()
        self._test_return_datatypes()
        self.assertEqual(self._page.isRedirectPage(), False)
        self.assertEqual(self._page.latest_revision.parent_id, 0)

    def test_content_model(self):
        """Test Flow page content model."""
        self.assertEqual(self._page.content_model, 'flow-board')


class TestLoadRevisionsCaching(BasePageLoadRevisionsCachingTestBase):

    """Test site.loadrevisions() caching."""

    family = 'mediawiki'
    code = 'mediawiki'

    def setUp(self):
        self._page = pywikibot.flow.Board(
            self.site, 'Talk:Sandbox')
        super(TestLoadRevisionsCaching, self).setUp()

    def test_page_text(self):
        """Test site.loadrevisions() with Page.text."""
        self._test_page_text()


class TestFlowLoading(TestCase):

    """Test loading of Flow objects from the API."""

    family = 'mediawiki'
    code = 'mediawiki'

    cached = True

    def test_board_uuid(self):
        """Test retrieval of Flow board UUID."""
        site = self.get_site()
        board = pywikibot.flow.Board(site, u'Talk:Sandbox')
        self.assertEqual(board.uuid, u'rl7iby6wgksbpfno')

    def test_topic_uuid(self):
        """Test retrieval of Flow topic UUID."""
        site = self.get_site()
        topic = pywikibot.flow.Topic(site, u'Topic:Sh6wgo5tu3qui1w2')
        self.assertEqual(topic.uuid, u'sh6wgo5tu3qui1w2')

    def test_post_uuid(self):
        """Test retrieval of Flow post UUID.

        This doesn't really "load" anything from the API. It just tests
        the property to make sure the UUID passed to the constructor is
        stored properly.
        """
        site = self.get_site()
        topic = pywikibot.flow.Topic(site, u'Topic:Sh6wgo5tu3qui1w2')
        post = pywikibot.flow.Post(topic, u'sh6wgoagna97q0ia')
        self.assertEqual(post.uuid, u'sh6wgoagna97q0ia')
