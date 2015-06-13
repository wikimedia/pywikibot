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


class TestFlowBasePage(TestCase):

    """Test Flow pages using BasePage-defined methods."""

    family = 'mediawiki'
    code = 'mediawiki'

    cached = True

    def test_methods(self):
        """Test basic Page methods on a Flow page."""
        site = self.get_site()
        page = pywikibot.Page(site, u'Talk:Sandbox')
        self.assertEqual(page.exists(), True)
        page.get()
        self.assertEqual(page.isRedirectPage(), False)

    def test_content_model(self):
        """Test Flow page content model."""
        site = self.get_site()
        page = pywikibot.Page(site, u'Talk:Sandbox')
        self.assertEqual(page.content_model, 'flow-board')


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
