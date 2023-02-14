#!/usr/bin/env python3
"""Tests for thanks-related code."""
#
# (C) Pywikibot team, 2016-2023
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

from pywikibot.flow import Topic
from tests.aspects import TestCase


NO_THANKABLE_POSTS = 'There is no recent post which can be test thanked.'


class TestThankFlowPost(TestCase):

    """Test thanks for Flow posts."""

    family = 'wikipedia'
    code = 'test'

    write = True

    @classmethod
    def setUpClass(cls):
        """Set up class."""
        super().setUpClass()
        cls._topic_title = 'Topic:Tvkityksg1ukyrrw'

    def test_thank_post(self):
        """Test thanks for Flow posts."""
        site = self.get_site()
        topic = Topic(site, self._topic_title)
        for post in reversed(topic.replies()):
            user = post.creator
            if site.user() == user.username:
                continue
            if user.is_thankable:
                break
        else:
            self.skipTest(NO_THANKABLE_POSTS)
        before_time = site.getcurrenttimestamp()
        post.thank()
        log_entries = site.logevents(logtype='thanks', total=5, page=user,
                                     start=before_time, reverse=True)
        self.assertTrue(bool(next(log_entries, None)))

    def test_self_thank(self):
        """Test that thanking one's own Flow post causes an error."""
        site = self.get_site()
        topic = Topic(site, self._topic_title)
        my_reply = topic.reply('My attempt to thank myself.')
        self.assertAPIError('invalidrecipient', None, my_reply.thank)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
