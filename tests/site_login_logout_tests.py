#!/usr/bin/python3
"""Test for login and logout methods."""
#
# (C) Pywikibot team, 2022
#
# Distributed under the terms of the MIT license.
#
import os
import unittest
from contextlib import suppress

import pywikibot
from pywikibot.exceptions import APIError

from tests.aspects import DefaultSiteTestCase


class TestLoginLogout(DefaultSiteTestCase):

    """Test for login and logout methods."""

    login = True

    def test_login_logout(self):
        """Validate login and logout methods by toggling the state."""
        site = self.get_site()
        loginstatus = pywikibot.login.LoginStatus

        self.assertTrue(site.logged_in())
        self.assertIn(site._loginstatus, (loginstatus.IN_PROGRESS,
                                          loginstatus.AS_USER))
        self.assertIn('_userinfo', site.__dict__.keys())

        self.assertIsNone(site.login())

        if site.is_oauth_token_available():
            with self.assertRaisesRegex(APIError, 'cannotlogout.*OAuth'):
                site.logout()
            self.assertTrue(site.logged_in())
            self.assertIn(site._loginstatus, (loginstatus.IN_PROGRESS,
                                              loginstatus.AS_USER))
            self.assertIn('_userinfo', site.__dict__.keys())

        # Fandom family wikis don't support API action=logout
        elif 'fandom.com' not in site.hostname():
            site.logout()
            self.assertFalse(site.logged_in())
            self.assertEqual(site._loginstatus, loginstatus.NOT_LOGGED_IN)
            self.assertNotIn('_userinfo', site.__dict__.keys())

            self.assertIsNone(site.user())


def setUpModule():  # noqa: N802
    """Skip tests if PYWIKIBOT_LOGIN_LOGOUT variable is not set."""
    if os.environ.get('PYWIKIBOT_LOGIN_LOGOUT', '0') != '1':
        raise unittest.SkipTest('login/logout tests ar disabled')


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
