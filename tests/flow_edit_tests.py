# -*- coding: utf-8 -*-
"""Edit tests for the flow module."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot.exceptions import LockedPage
from pywikibot.flow import Board, Topic, Post
from pywikibot.tools import UnicodeType as unicode

from tests.aspects import TestCase


class TestFlowCreateTopic(TestCase):

    """Test the creation of Flow topics."""

    family = 'test'
    code = 'test'

    user = True
    write = True

    def test_create_topic(self):
        """Test creation of topic."""
        content = 'If you can read this, the Flow code in Pywikibot works!'
        board = Board(self.site, 'Talk:Pywikibot test')
        topic = board.new_topic('Pywikibot test', content, 'wikitext')
        first_post = topic.replies()[0]
        wikitext = first_post.get(format='wikitext')
        self.assertIn('wikitext', first_post._content)
        self.assertNotIn('html', first_post._content)
        self.assertIsInstance(wikitext, unicode)
        self.assertEqual(wikitext, content)


class TestFlowReply(TestCase):

    """Test replying to existing posts."""

    family = 'test'
    code = 'test'

    user = True
    write = True

    @classmethod
    def setUpClass(cls):
        """Set up class."""
        super(TestFlowReply, cls).setUpClass()
        cls._topic_title = 'Topic:Stf56oxx0sd4dkj1'

    def test_reply_to_topic(self):
        """Test replying to "topic" (really the topic's root post)."""
        # Setup
        content = 'I am a reply to the topic. Replying works!'
        topic = Topic(self.site, self._topic_title)
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
        topic = Topic(self.site, self._topic_title)
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
        topic = Topic(self.site, self._topic_title)
        root_post = Post(topic, 'stf5bamzx32rj1gt')
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
        topic = Topic(self.site, self._topic_title)
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


class TestFlowLockTopic(TestCase):

    """Locking and unlocking topics."""

    family = 'test'
    code = 'test'

    user = True
    write = True

    def test_lock_unlock_topic(self):
        """Lock and unlock a test topic."""
        # Setup
        topic = Topic(self.site, 'Topic:Sn12rdih4iducjsd')
        if topic.is_locked:
            topic.unlock()
        self.assertFalse(topic.is_locked)
        # Lock topic
        topic.lock('Pywikibot test')
        self.assertTrue(topic.is_locked)
        # Unlock topic
        topic.unlock('Pywikibot test')
        self.assertFalse(topic.is_locked)


class TestFlowHide(TestCase):

    """Hiding topics and posts."""

    family = 'test'
    code = 'test'

    user = True
    write = True

    def test_hide_topic(self):
        """Hide and restore a test topic."""
        # Setup
        topic = Topic(self.site, 'Topic:Sl4svodmrhzmpjjh')
        if topic.is_moderated:
            topic.restore('Pywikibot test')
        self.assertFalse(topic.is_moderated)
        # Hide
        topic.hide('Pywikibot test')
        self.assertTrue(topic.is_moderated)
        # Restore
        topic.restore('Pywikibot test')
        self.assertFalse(topic.is_moderated)

    def test_hide_post(self):
        """Hide and restore a test post."""
        # Setup
        topic = Topic(self.site, 'Topic:Sl4svodmrhzmpjjh')
        post = Post(topic, 'sq1qvoig1az8w7cd')
        if post.is_moderated:
            post.restore('Pywikibot test')
        self.assertFalse(post.is_moderated)
        # Hide
        post.hide('Pywikibot test')
        self.assertTrue(post.is_moderated)
        # Restore
        post.restore('Pywikibot test')
        self.assertFalse(post.is_moderated)


class TestFlowDelete(TestCase):

    """Deleting topics and posts."""

    family = 'test'
    code = 'test'

    user = True
    write = True
    sysop = True

    def test_delete_topic(self):
        """Delete and restore a test topic."""
        # Setup
        topic = Topic(self.site, 'Topic:Sl4svodmrhzmpjjh')
        if topic.is_moderated:
            topic.restore('Pywikibot test')
        self.assertFalse(topic.is_moderated)
        # Delete
        topic.delete_mod('Pywikibot test')
        self.assertTrue(topic.is_moderated)
        # Restore
        topic.restore('Pywikibot test')
        self.assertFalse(topic.is_moderated)

    def test_delete_post(self):
        """Delete and restore a test post."""
        # Setup
        topic = Topic(self.site, 'Topic:Sl4svodmrhzmpjjh')
        post = Post(topic, 'sq1qvoig1az8w7cd')
        if post.is_moderated:
            post.restore('Pywikibot test')
        self.assertFalse(post.is_moderated)
        # Delete
        post.delete('Pywikibot test')
        self.assertTrue(post.is_moderated)
        # Restore
        post.restore('Pywikibot test')
        self.assertFalse(post.is_moderated)


class TestFlowSuppress(TestCase):

    """Suppressing topics and posts."""

    family = 'test'
    code = 'test'

    user = True
    write = True
    sysop = True

    def test_suppress_post(self):
        """Suppress and restore a test post."""
        # Setup
        topic = Topic(self.site, 'Topic:Sl4svodmrhzmpjjh')
        post = Post(topic, 'sq1qvoig1az8w7cd')
        if post.is_moderated:
            post.restore('Pywikibot test')
        self.assertFalse(post.is_moderated)
        # Suppress
        post.suppress('Pywikibot test')
        self.assertTrue(post.is_moderated)
        # Restore
        post.restore('Pywikibot test')
        self.assertFalse(post.is_moderated)

    def test_suppress_topic(self):
        """Suppress and restore a test topic."""
        # Setup
        topic = Topic(self.site, 'Topic:Sl4svodmrhzmpjjh')
        if topic.is_moderated:
            topic.restore('Pywikibot test')
        self.assertFalse(topic.is_moderated)
        # Suppress
        topic.suppress('Pywikibot test')
        self.assertTrue(topic.is_moderated)
        # Restore
        topic.restore('Pywikibot test')
        self.assertFalse(topic.is_moderated)


class TestFlowEditFailure(TestCase):

    """Flow-related edit failure tests."""

    family = 'test'
    code = 'test'

    user = True
    write = -1

    def test_reply_to_locked_topic(self):
        """Test replying to locked topic (should raise exception)."""
        # Setup
        content = 'I am a reply to a locked topic. This is not good!'
        topic = Topic(self.site, 'Topic:Smxnipjfs8umm1wt')
        # Reply (should raise a LockedPage exception)
        self.assertRaises(LockedPage, topic.reply, content, 'wikitext')
        topic_root = topic.root
        self.assertRaises(LockedPage, topic_root.reply, content, 'wikitext')
        topic_reply = topic.root.replies(force=True)[0]
        self.assertRaises(LockedPage, topic_reply.reply, content, 'wikitext')
