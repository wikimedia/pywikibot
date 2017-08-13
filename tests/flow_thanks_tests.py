# -*- coding: utf-8 -*-
"""Tests for thanks-related code."""
#
# (C) Pywikibot team, 2016-17
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot.flow import Topic

from tests.aspects import TestCase


NO_THANKABLE_POSTS = 'There is no recent post which can be test thanked.'


class TestThankFlowPost(TestCase):

    """Test thanks for Flow posts."""

    family = 'test'
    code = 'test'

    write = True

    @classmethod
    def setUpClass(cls):
        """Set up class."""
        super(TestThankFlowPost, cls).setUpClass()
        cls._topic_title = 'Topic:Tvkityksg1ukyrrw'

    def test_thank_post(self):
        """Test thanks for Flow posts."""
        found_log = False
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
        for __ in log_entries:
            found_log = True
            break
        self.assertTrue(found_log)

    def test_self_thank(self):
        """Test that thanking one's own Flow post causes an error."""
        site = self.get_site()
        topic = Topic(site, self._topic_title)
        my_reply = topic.reply('My attempt to thank myself.')
        self.assertAPIError('invalidrecipient', None, my_reply.thank)
