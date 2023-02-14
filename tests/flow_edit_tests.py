#!/usr/bin/env python3
"""Edit tests for the flow module."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import contextmanager, suppress

from pywikibot.exceptions import LockedPageError, TimeoutError
from pywikibot.flow import Board, Post, Topic
from tests.aspects import TestCase
from tests.utils import skipping


MODERATION_REASON = 'Pywikibot test'


class TestFlowCreateTopic(TestCase):

    """Test the creation of Flow topics."""

    family = 'wikipedia'
    code = 'test'

    login = True
    write = True

    def test_create_topic(self):
        """Test creation of topic."""
        content = 'If you can read this, the Flow code in Pywikibot works!'
        board = Board(self.site, 'Talk:Pywikibot test')
        topic = board.new_topic(MODERATION_REASON, content, 'wikitext')
        first_post = topic.replies()[0]
        wikitext = first_post.get(content_format='wikitext')
        self.assertIn('wikitext', first_post._content)
        self.assertNotIn('html', first_post._content)
        self.assertIsInstance(wikitext, str)
        self.assertEqual(wikitext, content)


class TestFlowReply(TestCase):

    """Test replying to existing posts."""

    family = 'wikipedia'
    code = 'test'

    login = True
    write = True

    @classmethod
    def setUpClass(cls):
        """Set up class."""
        super().setUpClass()
        cls._topic_title = 'Topic:Stf56oxx0sd4dkj1'

    def test_reply_to_topic(self):
        """Test replying to "topic" (really the topic's root post)."""
        # Setup
        content = 'I am a reply to the topic. Replying works!'
        topic = Topic(self.site, self._topic_title)
        with skipping(TimeoutError):
            old_replies = topic.replies(force=True)[:]
        # Reply
        reply_post = topic.reply(content, 'wikitext')
        # Test content
        wikitext = reply_post.get(content_format='wikitext')
        self.assertIn('wikitext', reply_post._content)
        self.assertNotIn('html', reply_post._content)
        self.assertIsInstance(wikitext, str)
        self.assertEqual(wikitext, content)
        # Test reply list in topic
        new_replies = topic.replies(force=True)
        self.assertLength(new_replies, len(old_replies) + 1)

    def test_reply_to_topic_root(self):
        """Test replying to the topic's root post directly."""
        # Setup
        content = ("I am a reply to the topic's root post. "
                   'Replying still works!')
        topic = Topic(self.site, self._topic_title)
        with skipping(TimeoutError):
            topic_root = topic.root
        old_replies = topic_root.replies(force=True)[:]
        # Reply
        reply_post = topic_root.reply(content, 'wikitext')
        # Test content
        wikitext = reply_post.get(content_format='wikitext')
        self.assertIn('wikitext', reply_post._content)
        self.assertNotIn('html', reply_post._content)
        self.assertIsInstance(wikitext, str)
        self.assertEqual(wikitext, content)
        # Test reply list in topic
        new_replies = topic_root.replies(force=True)
        self.assertLength(new_replies, len(old_replies) + 1)

    def test_reply_to_post(self):
        """Test replying to an ordinary post."""
        # Setup
        content = 'I am a nested reply to a regular post. Still going strong!'
        topic = Topic(self.site, self._topic_title)
        root_post = Post(topic, 'stf5bamzx32rj1gt')
        with skipping(TimeoutError):
            old_replies = root_post.replies(force=True)[:]
        # Reply
        reply_post = root_post.reply(content, 'wikitext')
        # Test content
        wikitext = reply_post.get(content_format='wikitext')
        self.assertIn('wikitext', reply_post._content)
        self.assertNotIn('html', reply_post._content)
        self.assertIsInstance(wikitext, str)
        self.assertEqual(wikitext, content)
        # Test reply list in topic
        new_replies = root_post.replies(force=True)
        self.assertLength(new_replies, len(old_replies) + 1)

    def test_nested_reply(self):
        """Test replying to a previous reply to a topic."""
        # Setup
        first_content = 'I am a reply to the topic with my own replies. Great!'
        second_content = ('I am a nested reply. This conversation is '
                          'getting pretty good!')
        topic = Topic(self.site, self._topic_title)
        with skipping(TimeoutError):
            topic_root = topic.root
        # First reply
        old_root_replies = topic_root.replies(force=True)[:]
        first_reply_post = topic_root.reply(first_content, 'wikitext')
        # Test first reply's content
        first_wikitext = first_reply_post.get(content_format='wikitext')
        self.assertIn('wikitext', first_reply_post._content)
        self.assertNotIn('html', first_reply_post._content)
        self.assertIsInstance(first_wikitext, str)
        self.assertEqual(first_wikitext, first_content)
        # Test reply list in topic
        new_root_replies = topic_root.replies(force=True)
        self.assertLength(new_root_replies, len(old_root_replies) + 1)

        # Nested reply
        old_nested_replies = first_reply_post.replies(force=True)[:]
        self.assertEqual(old_nested_replies, [])
        second_reply_post = first_reply_post.reply(second_content,
                                                   'wikitext')
        # Test nested reply's content
        second_wikitext = second_reply_post.get(content_format='wikitext')
        self.assertIn('wikitext', second_reply_post._content)
        self.assertNotIn('html', second_reply_post._content)
        self.assertIsInstance(second_wikitext, str)
        self.assertEqual(second_wikitext, second_content)

        # Test reply list in first reply
        # Broken due to current Flow reply structure (T105438)
        # new_nested_replies = first_reply_post.replies(force=True)
        # self.assertLength(new_nested_replies, len(old_nested_replies) + 1)

        # Current test for nested reply list
        self.assertEqual(old_nested_replies, [])
        more_root_replies = topic_root.replies(force=True)
        self.assertLength(more_root_replies, len(new_root_replies) + 1)


class TestFlowLockTopic(TestCase):

    """Locking and unlocking topics."""

    family = 'wikipedia'
    code = 'test'

    login = True
    write = True

    def test_lock_unlock_topic(self):
        """Lock and unlock a test topic."""
        # Setup
        topic = Topic(self.site, 'Topic:Sn12rdih4iducjsd')
        if topic.is_locked:
            topic.unlock(MODERATION_REASON)
        self.assertFalse(topic.is_locked)
        # Lock topic
        topic.lock(MODERATION_REASON)
        self.assertTrue(topic.is_locked)
        # Unlock topic
        topic.unlock(MODERATION_REASON)
        self.assertFalse(topic.is_locked)


class TestFlowEditFailure(TestCase):

    """Flow-related edit failure tests."""

    family = 'wikipedia'
    code = 'test'

    login = True
    write = -1

    def test_reply_to_locked_topic(self):
        """Test replying to locked topic (should raise exception)."""
        # Setup
        content = 'I am a reply to a locked topic. This is not good!'
        topic = Topic(self.site, 'Topic:Smxnipjfs8umm1wt')
        # Reply (should raise a LockedPageError exception)
        with self.assertRaises(LockedPageError):
            topic.reply(content, 'wikitext')
        topic_root = topic.root
        with self.assertRaises(LockedPageError):
            topic_root.reply(content, 'wikitext')
        topic_reply = topic.root.replies(force=True)[0]
        with self.assertRaises(LockedPageError):
            topic_reply.reply(content, 'wikitext')


class FlowTests(TestCase):

    """Flow tests base class."""

    family = 'wikipedia'
    code = 'test'

    login = True
    write = True

    def setUp(self):
        """Setup tests."""
        super().setUp()
        self.topic = Topic(self.site, 'Topic:Sl4svodmrhzmpjjh')
        self.post = Post(self.topic, 'sq1qvoig1az8w7cd')

    @contextmanager
    def restored(self, flow):
        """Setup and restore test."""
        # Setup
        if flow.is_moderated:
            flow.restore(MODERATION_REASON)
        self.assertFalse(flow.is_moderated)
        try:
            yield flow
        finally:
            # Restore
            flow.restore(MODERATION_REASON)
            self.assertFalse(flow.is_moderated)


class TestFlowHide(FlowTests):

    """Hiding topics and posts."""

    def test_hide(self):
        """Hide and restore a test topic and post."""
        for flow in (self.topic, self.post):
            with self.subTest(flow=flow.__class__.__name__), \
                 self.restored(flow):
                # Hide
                flow.hide(MODERATION_REASON)
                self.assertTrue(flow.is_moderated)


class TestFlowSysop(FlowTests):

    """Deleting and Suppressing topics and posts."""

    rights = 'flow-delete,flow-suppress'

    def test_delete(self):
        """Delete and restore a test topic and post."""
        for flow in (self.topic, self.post):
            with self.subTest(flow=flow.__class__.__name__), \
                 self.restored(flow):
                # Delete
                flow.delete_mod(MODERATION_REASON)
                self.assertTrue(flow.is_moderated)

    def test_suppress(self):
        """Suppress and restore a test topic and post."""
        for flow in (self.topic, self.post):
            with self.subTest(flow=flow.__class__.__name__), \
                 self.restored(flow):
                # Suppress
                flow.suppress(MODERATION_REASON)
                self.assertTrue(flow.is_moderated)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
