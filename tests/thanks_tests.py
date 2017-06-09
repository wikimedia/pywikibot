# -*- coding: utf-8 -*-
"""Tests for thanks-related code."""
#
# (C) Pywikibot team, 2016-17
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot.page import Revision, User

from tests.aspects import TestCase


class TestThankRevision(TestCase):

    """Test thanks for revisions."""

    family = 'test'
    code = 'test'

    write = True

    def test_thank_revision(self):
        """Test thanks for normal revisions.

        NOTE: This test relies on activity in recentchanges, and
              there must make edits made before reruns of this test.
              Please see https://phabricator.wikimedia.org/T137836.
        """
        found_log = can_thank = False
        site = self.get_site()
        data = site.recentchanges(total=50, reverse=True)
        for i in data:
            revid = i['revid']
            username = i['user']
            user = User(site, username)
            if user.is_thankable:
                can_thank = True
                break
        if not can_thank:
            self.skipTest('There is no recent change which can be test thanked.')
        before_time = site.getcurrenttimestamp()
        Revision._thank(revid, site, source='pywikibot test')
        log_entries = site.logevents(logtype='thanks', total=5, start=before_time, page=user)
        for __ in log_entries:
            found_log = True
            break
        self.assertTrue(found_log)
