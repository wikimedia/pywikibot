#!/usr/bin/env python3
"""Test OAuth functionality."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
import os
from contextlib import suppress

from pywikibot.login import OauthLoginManager
from tests.aspects import (
    DefaultSiteTestCase,
    TestCase,
    require_modules,
    unittest,
)


@require_modules('mwoauth')
class OAuthSiteTestCase(TestCase):

    """Run tests related to OAuth authentication."""

    oauth = True

    def _get_oauth_tokens(self):
        """Get valid OAuth tokens from environment variables."""
        tokens = os.environ.get('PYWIKIBOT_TEST_OAUTH')
        return tuple(tokens.split(':')) if tokens is not None else None

    def setUp(self):
        """Check if OAuth extension is installed and OAuth tokens are set."""
        super().setUp()
        self.site = self.get_site()
        if not self.site.has_extension('OAuth'):
            self.skipTest('OAuth extension not loaded on test site')
        tokens = self._get_oauth_tokens()
        if tokens is None:
            self.skipTest('OAuth tokens not set')
        self.assertLength(tokens, 4)
        self.consumer_token = tokens[:2]
        self.access_token = tokens[2:]


class TestOauthLoginManger(DefaultSiteTestCase, OAuthSiteTestCase):

    """Test OAuth login manager."""

    def _get_login_manager(self):
        login_manager = OauthLoginManager(password=self.consumer_token[1],
                                          site=self.site,
                                          user=self.consumer_token[0])
        # Set access token directly, discard user interaction token fetching
        login_manager._access_token = self.access_token
        return login_manager

    def test_login(self):
        """Test login."""
        login_manager = self._get_login_manager()
        login_manager.login()
        self.assertEqual(login_manager.consumer_token, self.consumer_token)
        self.assertEqual(login_manager.access_token, self.access_token)

    def test_identity(self):
        """Test identity."""
        login_manager = self._get_login_manager()
        self.assertIsNotNone(login_manager.access_token)
        self.assertIsInstance(login_manager.identity, dict)
        self.assertEqual(login_manager.identity['username'],
                         self.site.username())


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
