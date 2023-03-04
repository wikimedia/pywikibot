#!/usr/bin/env python3
"""Tests for the flow module."""
#
# (C) Pywikibot team, 2015-2023
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

from pywikibot import config
from pywikibot.exceptions import NoPageError
from pywikibot.flow import Board, Post, Topic
from tests.aspects import TestCase
from tests.basepage import (
    BasePageLoadRevisionsCachingTestBase,
    BasePageMethodsTestBase,
)


class TestMediaWikiFlowSandbox(TestCase):

    """Test the Flow sandbox on MediaWiki.org."""

    family = 'mediawiki'
    code = 'mediawiki'

    def setUp(self):
        """Set up unit test."""
        self._page = Board(self.site,
                           'Project talk:Sandbox/Structured_Discussions_test')
        super().setUp()


class TestBoardBasePageMethods(BasePageMethodsTestBase,
                               TestMediaWikiFlowSandbox):

    """Test Flow board pages using BasePage-defined methods."""

    def test_basepage_methods(self):
        """Test basic Page methods on a Flow board page."""
        self._test_invoke()
        self._test_return_datatypes()
        self.assertFalse(self._page.isRedirectPage())

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
        super().setUp()

    def test_basepage_methods(self):
        """Test basic Page methods on a Flow topic page."""
        self._test_invoke()
        self._test_return_datatypes()
        self.assertFalse(self._page.isRedirectPage())
        self.assertEqual(self._page.latest_revision.parentid, 0)

    def test_content_model(self):
        """Test Flow topic page content model."""
        self.assertEqual(self._page.content_model, 'flow-board')


class TestLoadRevisionsCaching(BasePageLoadRevisionsCachingTestBase,
                               TestMediaWikiFlowSandbox):

    """Test site.loadrevisions() caching."""

    def test_page_text(self):
        """Test site.loadrevisions() with Page.text."""
        self._test_page_text(get_text=False)  # See T107537


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
        wikitext = post.get(content_format='wikitext')
        self.assertIn('wikitext', post._content)
        self.assertNotIn('html', post._content)
        self.assertIsInstance(wikitext, str)
        self.assertNotEqual(wikitext, '')
        # HTML
        html = post.get(content_format='html')
        self.assertIn('html', post._content)
        self.assertIn('wikitext', post._content)
        self.assertIsInstance(html, str)
        self.assertNotEqual(html, '')
        # Caching (hit)
        post._content['html'] = 'something'
        html = post.get(content_format='html')
        self.assertIsInstance(html, str)
        self.assertEqual(html, 'something')
        self.assertIn('html', post._content)
        # Caching (reload)
        post._content['html'] = 'something'
        html = post.get(content_format='html', force=True)
        self.assertIsInstance(html, str)
        self.assertNotEqual(html, 'something')
        self.assertIn('html', post._content)

    def test_topiclist(self):
        """Test loading of topiclist."""
        board = self._page
        total = 7
        saved_step = config.step
        for step in (-1, 5, 100):
            with self.subTest(step=step):
                config.step = step
                for i, _ in enumerate(board.topics(total=total), start=1):
                    if i > total:
                        break  # pragma: no cover
                self.assertEqual(i, total)
        config.step = saved_step


class TestFlowFactoryErrors(TestCase):

    """Test errors associated with class methods generating Flow objects."""

    family = 'wikipedia'
    code = 'test'

    cached = True

    def test_illegal_arguments(self):
        """Test illegal method arguments."""
        board = Board(self.site, 'Talk:Pywikibot test')
        real_topic = Topic(self.site, 'Topic:Slbktgav46omarsd')
        fake_topic = Topic(self.site, 'Topic:Abcdefgh12345678')
        # Topic.from_topiclist_data
        with self.assertRaises(TypeError):
            Topic.from_topiclist_data(self.site, '', {})
        with self.assertRaises(TypeError):
            Topic.from_topiclist_data(board, 521, {})
        with self.assertRaises(TypeError):
            Topic.from_topiclist_data(board,
                                      'slbktgav46omarsd', [0, 1, 2])
        with self.assertRaises(NoPageError):
            Topic.from_topiclist_data(board,
                                      'abc', {'stuff': 'blah'})

        # Post.fromJSON
        with self.assertRaises(TypeError):
            Post.fromJSON(board, 'abc', {})
        with self.assertRaises(TypeError):
            Post.fromJSON(real_topic, 1234, {})
        with self.assertRaises(TypeError):
            Post.fromJSON(real_topic, 'abc', [])
        with self.assertRaises(NoPageError):
            Post.fromJSON(fake_topic, 'abc',
                          {'posts': [], 'revisions': []})

    def test_invalid_data(self):
        """Test invalid "API" data."""
        board = Board(self.site, 'Talk:Pywikibot test')
        real_topic = Topic(self.site, 'Topic:Slbktgav46omarsd')
        # Topic.from_topiclist_data
        with self.assertRaises(ValueError):
            Topic.from_topiclist_data(board,
                                      'slbktgav46omarsd', {'stuff': 'blah'})
        with self.assertRaises(ValueError):
            Topic.from_topiclist_data(board,
                                      'slbktgav46omarsd',
                                      {'posts': [], 'revisions': []})
        with self.assertRaises(ValueError):
            Topic.from_topiclist_data(board,
                                      'slbktgav46omarsd',
                                      {'posts': {'slbktgav46omarsd': ['123']},
                                       'revisions': {'456': []}})
        with self.assertRaises(AssertionError):
            Topic.from_topiclist_data(board,
                                      'slbktgav46omarsd',
                                      {'posts': {'slbktgav46omarsd': ['123']},
                                       'revisions': {'123': {'content': 789}}})

        # Post.fromJSON
        with self.assertRaises(ValueError):
            Post.fromJSON(real_topic, 'abc', {})
        with self.assertRaises(ValueError):
            Post.fromJSON(real_topic, 'abc',
                          {'stuff': 'blah'})
        with self.assertRaises(ValueError):
            Post.fromJSON(real_topic, 'abc',
                          {'posts': {'abc': ['123']},
                           'revisions': {'456': []}})
        with self.assertRaises(AssertionError):
            Post.fromJSON(real_topic, 'abc',
                          {'posts': {'abc': ['123']},
                           'revisions': {'123': {'content': 789}}})


class TestFlowTopic(TestCase):
    """Test Topic functions."""

    family = 'wikipedia'
    code = 'test'

    def test_topic(self):
        """Test general functions of the Topic class."""
        topic = Topic(self.site, 'Topic:U5y4l1rzitlplyc5')
        self.assertEqual(topic.root.uuid, 'u5y4l1rzitlplyc5')
        replies = topic.replies()
        self.assertLength(replies, 4)
        for reply in replies:
            self.assertIsInstance(reply, Post)
        self.assertEqual(replies[1].uuid, 'u5y5lysqcvyne4k1')

    def test_topic_moderation(self):
        """Test Topic functions about moderation."""
        topic_closed = Topic(self.site, 'Topic:U5y4efgaprfe7ssi')
        self.assertTrue(topic_closed.is_locked)
        self.assertTrue(topic_closed.is_moderated)

        topic_open = Topic(self.site, 'Topic:U5y4l1rzitlplyc5')
        self.assertFalse(topic_open.is_locked)
        self.assertFalse(topic_open.is_moderated)

        topic_hidden = Topic(self.site, 'Topic:U5y53rn0dp6h70nw')
        self.assertFalse(topic_hidden.is_locked)
        self.assertTrue(topic_hidden.is_moderated)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
