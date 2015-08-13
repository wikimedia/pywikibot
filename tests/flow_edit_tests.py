# -*- coding: utf-8  -*-
"""Edit tests for the flow module."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

from pywikibot.flow import Topic, Post
from pywikibot.tools import PY2

from tests.aspects import TestCase

if not PY2:
    unicode = str


class TestFlowReply(TestCase):

    """Test replying to existing posts."""

    family = 'test'
    code = 'test'

    user = True
    write = True

    def test_reply_to_topic(self):
        """Test replying to "topic" (really the topic's root post)."""
        # Setup
        content = 'I am a reply to the topic. Replying works!'
        topic = Topic(self.site, 'Topic:Sl4ssgh123c3e1bh')
        old_replies = topic.replies(force=True)[:]
        # Reply
        reply_post = topic.reply(content, 'wikitext')
        # Test content
        wikitext = reply_post.get(format='wikitext')
        self.assertIn('wikitext', reply_post._content)
        self.assertNotIn('html', reply_post._content)
        self.assertIsInstance(wikitext, unicode)
        self.assertEqual(wikitext, content)
        # Test reply list in topic
        new_replies = topic.replies(force=True)
        self.assertEqual(len(new_replies), len(old_replies) + 1)

    def test_reply_to_topic_root(self):
        """Test replying to the topic's root post directly."""
        # Setup
        content = "I am a reply to the topic's root post. Replying still works!"
        topic = Topic(self.site, 'Topic:Sl4ssgh123c3e1bh')
        topic_root = topic.root
        old_replies = topic_root.replies(force=True)[:]
        # Reply
        reply_post = topic_root.reply(content, 'wikitext')
        # Test content
        wikitext = reply_post.get(format='wikitext')
        self.assertIn('wikitext', reply_post._content)
        self.assertNotIn('html', reply_post._content)
        self.assertIsInstance(wikitext, unicode)
        self.assertEqual(wikitext, content)
        # Test reply list in topic
        new_replies = topic_root.replies(force=True)
        self.assertEqual(len(new_replies), len(old_replies) + 1)

    def test_reply_to_post(self):
        """Test replying to an ordinary post."""
        # Setup
        content = 'I am a nested reply to a regular post. Still going strong!'
        topic = Topic(self.site, 'Topic:Sl4ssgh123c3e1bh')
        root_post = Post(topic, 'smjnql768bl0h0kt')
        old_replies = root_post.replies(force=True)[:]
        # Reply
        reply_post = root_post.reply(content, 'wikitext')
        # Test content
        wikitext = reply_post.get(format='wikitext')
        self.assertIn('wikitext', reply_post._content)
        self.assertNotIn('html', reply_post._content)
        self.assertIsInstance(wikitext, unicode)
        self.assertEqual(wikitext, content)
        # Test reply list in topic
        new_replies = root_post.replies(force=True)
        self.assertEqual(len(new_replies), len(old_replies) + 1)

    def test_nested_reply(self):
        """Test replying to a previous reply to a topic."""
        # Setup
        first_content = 'I am a reply to the topic with my own replies. Great!'
        second_content = 'I am a nested reply. This conversation is getting pretty good!'
        topic = Topic(self.site, 'Topic:Sl4ssgh123c3e1bh')
        topic_root = topic.root
        # First reply
        old_root_replies = topic_root.replies(force=True)[:]
        first_reply_post = topic_root.reply(first_content, 'wikitext')
        # Test first reply's content
        first_wikitext = first_reply_post.get(format='wikitext')
        self.assertIn('wikitext', first_reply_post._content)
        self.assertNotIn('html', first_reply_post._content)
        self.assertIsInstance(first_wikitext, unicode)
        self.assertEqual(first_wikitext, first_content)
        # Test reply list in topic
        new_root_replies = topic_root.replies(force=True)
        self.assertEqual(len(new_root_replies), len(old_root_replies) + 1)

        # Nested reply
        old_nested_replies = first_reply_post.replies(force=True)[:]
        self.assertListEqual(old_nested_replies, [])
        second_reply_post = first_reply_post.reply(second_content,
                                                   'wikitext')
        # Test nested reply's content
        second_wikitext = second_reply_post.get(format='wikitext')
        self.assertIn('wikitext', second_reply_post._content)
        self.assertNotIn('html', second_reply_post._content)
        self.assertIsInstance(second_wikitext, unicode)
        self.assertEqual(second_wikitext, second_content)

        # Test reply list in first reply
        # Broken due to current Flow reply structure (T105438)
        # new_nested_replies = first_reply_post.replies(force=True)
        # self.assertEqual(len(new_nested_replies), len(old_nested_replies) + 1)

        # Current test for nested reply list
        self.assertListEqual(old_nested_replies, [])
        more_root_replies = topic_root.replies(force=True)
        self.assertEqual(len(more_root_replies), len(new_root_replies) + 1)
