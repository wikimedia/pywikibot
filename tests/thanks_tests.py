#!/usr/bin/env python3
"""Tests for thanks-related code."""
#
# (C) Pywikibot team, 2016-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

from pywikibot.page import Page, User
from tests.aspects import TestCase


NO_THANKABLE_REVS = 'There is no recent change which can be test thanked.'


class TestThankRevision(TestCase):

    """Test thanks for revisions."""

    family = 'wikipedia'
    code = 'test'

    login = True
    write = True

    def test_thank_revision(self):
        """Test thanks for normal revisions.

        .. note:: This test relies on activity in recentchanges, and
           there must make edits made before reruns of this test.
        .. seealso:: :phab:`T137836`.
        """
        site = self.get_site()
        data = site.recentchanges(total=20)
        for rev in data:
            revid = rev['revid']
            username = rev['user']
            user = User(site, username)
            if user.is_thankable:
                break
        else:
            self.skipTest(NO_THANKABLE_REVS)
        before_time = site.getcurrenttimestamp()
        site.thank_revision(revid, source='pywikibot test')
        log_entries = site.logevents(logtype='thanks', total=5, page=user,
                                     start=before_time, reverse=True)
        self.assertTrue(bool(next(log_entries, None)))

    def test_self_thank(self):
        """Test that thanking oneself causes an error.

        This test is not in TestThankRevisionErrors because it may require
        making a successful edit in order to test the API call thanking
        the user running the test.
        """
        site = self.get_site()
        my_name = self.get_userpage().username
        data = site.usercontribs(user=my_name, total=1)
        for rev in data:
            revid = rev['revid']
            break
        else:
            test_page = Page(site, 'Pywikibot Thanks test')
            test_page.text += '* ~~~~\n'
            test_page.save('Pywikibot Thanks test')
            revid = test_page.latest_revision_id
        self.assertAPIError('invalidrecipient', None, site.thank_revision,
                            revid, source='pywikibot test')


class TestThankRevisionErrors(TestCase):

    """Test errors when thanking revisions."""

    family = 'wikipedia'
    code = 'test'

    write = -1

    def test_bad_recipient(self):
        """Test that thanking a bad recipient causes an error."""
        site = self.get_site()
        data = site.recentchanges(total=20)
        for rev in data:
            revid = rev['revid']
            username = rev['user']
            user = User(site, username)
            if not user.is_thankable:
                break
        else:
            self.skipTest(NO_THANKABLE_REVS)
        self.assertAPIError('invalidrecipient', None, site.thank_revision,
                            revid, source='pywikibot test')

    def test_invalid_revision(self):
        """Test that passing an invalid revision ID causes an error."""
        site = self.get_site()
        invalid_revids = (0.99, (0, -1), (0, -1, 0.99,), [0, -1, 0.99], 'zero',
                          'minus one, and point nine nine')
        code = 'invalidrevision' if site.mw_version < '1.35' else 'badinteger'
        for invalid_revid in invalid_revids:
            with self.subTest(revids=invalid_revid):
                self.assertAPIError(code, None, site.thank_revision,
                                    invalid_revid, source='pywikibot test')
        for invalid_revid in [0, -1, [0], [-1]]:
            with self.subTest(revids=invalid_revid):
                self.assertAPIError('invalidrevision', None,
                                    site.thank_revision, invalid_revid,
                                    source='pywikibot test')


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
