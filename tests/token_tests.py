#!/usr/bin/env python3
"""Tests for tokens."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

from pywikibot.exceptions import APIError, Error
from pywikibot.site import TokenWallet
from tests.aspects import (
    DefaultSiteTestCase,
    DeprecationTestCase,
    TestCase,
    TestCaseBase,
)


class TestSiteTokens(DeprecationTestCase, DefaultSiteTestCase):

    """Test cases for tokens in Site methods.

    Versions of sites are simulated if actual versions are higher than
    needed by the test case.

    Test is skipped if site version is not compatible.

    """

    login = True

    def test_tokens(self):
        """Test tokens."""
        redirected_tokens = ['edit', 'move', 'delete']
        for ttype in redirected_tokens + ['patrol', 'deleteglobalaccount']:
            self.assertIsInstance(self.site.tokens[ttype], str)
            self.assertIn(ttype, self.site.tokens)  # test __contains__
            if ttype in redirected_tokens:
                self.assertEqual(self.site.tokens[ttype],
                                 self.site.tokens['csrf'])
                self._do_test_warning_filename = False
                self.assertDeprecationParts(f'Token {ttype!r}', "'csrf'")

    def test_invalid_token(self):
        """Test invalid token."""
        with self.assertRaises(KeyError):
            self.site.tokens['invalidtype']


class TokenTestBase(TestCaseBase):

    """Verify token exists before running tests."""

    def setUp(self):
        """Skip test if user does not have token and clear site wallet."""
        super().setUp()
        mysite = self.get_site()
        ttype = self.token_type
        try:
            token = mysite.tokens[ttype]
        except KeyError as error_msg:
            self.assertRegex(
                str(error_msg),
                f'Invalid token {ttype!r} for user .+ on {mysite} wiki.')
            self.assertNotIn(ttype, self.site.tokens)
            self.skipTest(error_msg)

        self.token = token
        self._orig_wallet = self.site.tokens
        self.site.tokens = TokenWallet(self.site)

    def tearDown(self):
        """Restore site tokens."""
        self.site.tokens = self._orig_wallet
        super().tearDown()


class PatrolTestCase(TokenTestBase, TestCase):

    """Test patrol method."""

    family = 'wikipedia'
    code = 'test'
    token_type = 'patrol'

    login = True
    write = True
    rights = 'patrol'

    def test_patrol(self):
        """Test the site.patrol() method."""
        mysite = self.get_site()

        rc = list(mysite.recentchanges(total=1))
        if not rc:
            self.skipTest('no recent changes to patrol')

        rc = rc[0]

        # site.patrol() needs params
        with self.assertRaises(Error):
            list(mysite.patrol())
        try:
            result = list(mysite.patrol(rcid=rc['rcid']))
        except APIError as error:
            if error.code == 'permissiondenied':
                self.skipTest(error)
            raise

        if hasattr(mysite, '_patroldisabled') and mysite._patroldisabled:
            self.skipTest(f'Patrolling is disabled on {mysite} wiki.')

        result = result[0]
        self.assertIsInstance(result, dict)

        params = {'rcid': 0, 'revid': [0, 1]}

        raised = False
        try:
            # no such rcid, revid or too old revid
            list(mysite.patrol(**params))
        except APIError as error:
            if error.code == 'badtoken':
                self.skipTest(error)
        except Error:
            # expected result
            raised = True
        self.assertTrue(raised, msg='pywikibot.exceptions.Error not raised')


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
