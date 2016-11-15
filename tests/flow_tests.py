# -*- coding: utf-8 -*-
"""Tests for the flow module."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot.exceptions import NoPage
from pywikibot.flow import Board, Topic, Post
from pywikibot.tools import UnicodeType as unicode

from tests.aspects import (
    TestCase,
)
from tests.basepage_tests import (
    BasePageMethodsTestBase,
    BasePageLoadRevisionsCachingTestBase,
)


class TestMediaWikiFlowSandbox(TestCase):

    """Test the Flow sandbox on MediaWiki.org."""

    family = 'mediawiki'
    code = 'mediawiki'

    def setUp(self):
        """Set up unit test."""
        self._page = Board(self.site, 'Project_talk:Sandbox/Flow test')
        super(TestMediaWikiFlowSandbox, self).setUp()


class TestBoardBasePageMethods(BasePageMethodsTestBase,
                               TestMediaWikiFlowSandbox):

    """Test Flow board pages using BasePage-defined methods."""

    def test_basepage_methods(self):
        """Test basic Page methods on a Flow board page."""
        self._test_invoke()
        self._test_return_datatypes()
        self.assertFalse(self._page.isRedirectPage())
        self.assertGreater(self._page.latest_revision.parent_id, 0)

    def test_content_model(self):
        """Test Flow page content model."""
        self.assertEqual(self._page.content_model, 'flow-board')


class TestTopicBasePageMethods(BasePageMethodsTestBase):

    """Test Flow topic pages using BasePage-defined methods."""

    family = 'mediawiki'
    code = 'mediawiki'

    def setUp(self):
        """Set up unit test."""
        self._page = Topic(self.site, 'Topic:Sh6wgo5tu3qui1w2')
        super(TestTopicBasePageMethods, self).setUp()

    def test_basepage_methods(self):
        """Test basic Page methods on a Flow topic page."""
        self._test_invoke()
        self._test_return_datatypes()
        self.assertFalse(self._page.isRedirectPage())
        self.assertEqual(self._page.latest_revision.parent_id, 0)

    def test_content_model(self):
        """Test Flow topic page content model."""
        self.assertEqual(self._page.content_model, 'flow-board')


class TestLoadRevisionsCaching(BasePageLoadRevisionsCachingTestBase,
                               TestMediaWikiFlowSandbox):

    """Test site.loadrevisions() caching."""

    def test_page_text(self):
        """Test site.loadrevisions() with Page.text."""
        self.skipTest('See T107537')
        self._test_page_text()


class TestFlowLoading(TestMediaWikiFlowSandbox):

    """Test loading of Flow objects from the API."""

    cached = True

    def test_board_uuid(self):
        """Test retrieval of Flow board UUID."""
        board = self._page
        self.assertEqual(board.uuid, 'rl7iby6wgksbpfno')

    def test_topic_uuid(self):
        """Test retrieval of Flow topic UUID."""
        topic = Topic(self.site, 'Topic:Sh6wgo5tu3qui1w2')
        self.assertEqual(topic.uuid, 'sh6wgo5tu3qui1w2')

    def test_post_uuid(self):
        """Test retrieval of Flow post UUID.

        This doesn't really "load" anything from the API. It just tests
        the property to make sure the UUID passed to the constructor is
        stored properly.
        """
        topic = Topic(self.site, 'Topic:Sh6wgo5tu3qui1w2')
        post = Post(topic, 'sh6wgoagna97q0ia')
        self.assertEqual(post.uuid, 'sh6wgoagna97q0ia')

    def test_post_contents(self):
        """Test retrieval of Flow post contents."""
        # Load
        topic = Topic(self.site, 'Topic:Sh6wgo5tu3qui1w2')
        post = Post(topic, 'sh6wgoagna97q0ia')
        # Wikitext
        wikitext = post.get(format='wikitext')
        self.assertIn('wikitext', post._content)
        self.assertNotIn('html', post._content)
        self.assertIsInstance(wikitext, unicode)
        self.assertNotEqual(wikitext, '')
        # HTML
        html = post.get(format='html')
        self.assertIn('html', post._content)
        self.assertIn('wikitext', post._content)
        self.assertIsInstance(html, unicode)
        self.assertNotEqual(html, '')
        # Caching (hit)
        post._content['html'] = 'something'
        html = post.get(format='html')
        self.assertIsInstance(html, unicode)
        self.assertEqual(html, 'something')
        self.assertIn('html', post._content)
        # Caching (reload)
        post._content['html'] = 'something'
        html = post.get(format='html', force=True)
        self.assertIsInstance(html, unicode)
        self.assertNotEqual(html, 'something')
        self.assertIn('html', post._content)

    def test_topiclist(self):
        """Test loading of topiclist."""
        board = self._page
        i = 0
        for topic in board.topics(limit=7):
            i += 1
            if i == 10:
                break
        self.assertEqual(i, 10)


class TestFlowFactoryErrors(TestCase):

    """Test errors associated with class methods generating Flow objects."""

    family = 'test'
    code = 'test'

    cached = True

    def test_illegal_arguments(self):
        """Test illegal method arguments."""
        board = Board(self.site, 'Talk:Pywikibot test')
        real_topic = Topic(self.site, 'Topic:Slbktgav46omarsd')
        fake_topic = Topic(self.site, 'Topic:Abcdefgh12345678')
        # Topic.from_topiclist_data
        self.assertRaises(TypeError, Topic.from_topiclist_data, self.site, '', {})
        self.assertRaises(TypeError, Topic.from_topiclist_data, board, 521, {})
        self.assertRaises(TypeError, Topic.from_topiclist_data, board,
                          'slbktgav46omarsd', [0, 1, 2])
        self.assertRaises(NoPage, Topic.from_topiclist_data, board,
                          'abc', {'stuff': 'blah'})

        # Post.fromJSON
        self.assertRaises(TypeError, Post.fromJSON, board, 'abc', {})
        self.assertRaises(TypeError, Post.fromJSON, real_topic, 1234, {})
        self.assertRaises(TypeError, Post.fromJSON, real_topic, 'abc', [])
        self.assertRaises(NoPage, Post.fromJSON, fake_topic, 'abc',
                          {'posts': [], 'revisions': []})

    def test_invalid_data(self):
        """Test invalid "API" data."""
        board = Board(self.site, 'Talk:Pywikibot test')
        real_topic = Topic(self.site, 'Topic:Slbktgav46omarsd')
        # Topic.from_topiclist_data
        self.assertRaises(ValueError, Topic.from_topiclist_data,
                          board, 'slbktgav46omarsd', {'stuff': 'blah'})
        self.assertRaises(ValueError, Topic.from_topiclist_data,
                          board, 'slbktgav46omarsd',
                          {'posts': [], 'revisions': []})
        self.assertRaises(ValueError, Topic.from_topiclist_data, board,
                          'slbktgav46omarsd',
                          {'posts': {'slbktgav46omarsd': ['123']},
                           'revisions': {'456': []}})
        self.assertRaises(AssertionError, Topic.from_topiclist_data, board,
                          'slbktgav46omarsd',
                          {'posts': {'slbktgav46omarsd': ['123']},
                           'revisions': {'123': {'content': 789}}})

        # Post.fromJSON
        self.assertRaises(ValueError, Post.fromJSON, real_topic, 'abc', {})
        self.assertRaises(ValueError, Post.fromJSON, real_topic, 'abc',
                          {'stuff': 'blah'})
        self.assertRaises(ValueError, Post.fromJSON, real_topic, 'abc',
                          {'posts': {'abc': ['123']},
                           'revisions': {'456': []}})
        self.assertRaises(AssertionError, Post.fromJSON, real_topic, 'abc',
                          {'posts': {'abc': ['123']},
                           'revisions': {'123': {'content': 789}}})
