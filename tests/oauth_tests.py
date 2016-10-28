# -*- coding: utf-8 -*-
"""Test OAuth functionality."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import os

from pywikibot.login import OauthLoginManager

from tests.aspects import (
    unittest,
    require_modules,
    TestCase,
    DefaultSiteTestCase,
)


@require_modules('mwoauth')
class OAuthSiteTestCase(TestCase):

    """Run tests related to OAuth authentication."""

    oauth = True

    def _get_oauth_tokens(self):
        """Get valid OAuth tokens from environment variables."""
        tokens_env = 'OAUTH_TOKENS_' + self.family.upper()
        tokens = os.environ.get(tokens_env + '_' + self.code.upper(), None)
        tokens = tokens or os.environ.get(tokens_env, None)
        return tuple(tokens.split(':')) if tokens is not None else None

    def setUp(self):
        """Check if OAuth extension is installed and OAuth tokens are set."""
        super(OAuthSiteTestCase, self).setUp()
        self.site = self.get_site()
        if not self.site.has_extension('OAuth'):
            raise unittest.SkipTest('OAuth extension not loaded on test site')
        tokens = self._get_oauth_tokens()
        if tokens is None:
            raise unittest.SkipTest('OAuth tokens not set')
        self.assertEqual(len(tokens), 4)
        self.consumer_token = tokens[:2]
        self.access_token = tokens[2:]


class DefaultOAuthSiteTestCase(DefaultSiteTestCase, OAuthSiteTestCase):

    """Default OAuth site test."""

    pass


class TestOauthLoginManger(DefaultOAuthSiteTestCase):

    """Test OAuth login manager."""

    def _get_login_manager(self):
        login_manager = OauthLoginManager(self.consumer_token[1], False,
                                          self.site, self.consumer_token[0])
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
                         self.site.username(sysop=False))


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
