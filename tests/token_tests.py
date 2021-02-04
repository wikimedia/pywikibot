"""Tests for tokens."""
#
# (C) Pywikibot team, 2015-2021
#
# Distributed under the terms of the MIT license.
#
from contextlib import suppress

import pywikibot

from pywikibot.data import api
from pywikibot.site import TokenWallet

from tests.aspects import (
    DefaultSiteTestCase,
    DeprecationTestCase,
    TestCase,
    TestCaseBase,
    unittest,
)


class TestSiteTokens(DefaultSiteTestCase):

    """Test cases for tokens in Site methods.

    Versions of sites are simulated if actual versions are higher than
    needed by the test case.

    Test is skipped if site version is not compatible.

    """

    user = True

    def setUp(self):
        """Store version."""
        super().setUp()
        self.mysite = self.get_site()
        self._version = self.mysite.mw_version
        self.orig_version = self.mysite.version

    def tearDown(self):
        """Restore version."""
        super().tearDown()
        self.mysite.version = self.orig_version

    def _test_tokens(self, version, test_version, additional_token):
        """Test tokens."""
        if version and (self._version < version
                        or self._version < test_version):
            raise unittest.SkipTest(
                'Site {} version {} is too low for this tests.'
                .format(self.mysite, self._version))

        self.mysite.version = lambda: test_version

        for ttype in ('edit', 'move', additional_token):
            tokentype = self.mysite.validate_tokens([ttype])
            try:
                token = self.mysite.tokens[ttype]
            except pywikibot.Error as error_msg:
                if tokentype:
                    self.assertRegex(
                        str(error_msg),
                        "Action '[a-z]+' is not allowed "
                        'for user .* on .* wiki.')
                    # test __contains__
                    self.assertNotIn(tokentype[0], self.mysite.tokens)
                else:
                    self.assertRegex(
                        str(error_msg),
                        "Requested token '[a-z]+' is invalid on .* wiki.")
            else:
                self.assertIsInstance(token, str)
                self.assertEqual(token, self.mysite.tokens[ttype])
                # test __contains__
                self.assertIn(tokentype[0], self.mysite.tokens)

    def test_tokens_in_mw_119(self):
        """Test ability to get page tokens."""
        self._test_tokens(None, '1.19', 'delete')

    def test_patrol_tokens_in_mw_119(self):
        """Test ability to get patrol token on MW 1.19 wiki."""
        self._test_tokens('1.19', '1.19', 'patrol')

    def test_tokens_in_mw_120_124wmf18(self):
        """Test ability to get page tokens."""
        self._test_tokens('1.20', '1.21', 'deleteglobalaccount')

    def test_patrol_tokens_in_mw_120(self):
        """Test ability to get patrol token."""
        self._test_tokens('1.19', '1.20', 'patrol')

    def test_tokens_in_mw_124wmf19(self):
        """Test ability to get page tokens."""
        self._test_tokens('1.24wmf19', '1.24wmf20', 'deleteglobalaccount')

    def test_invalid_token(self):
        """Test invalid token."""
        self.assertRaises(pywikibot.Error, lambda t: self.mysite.tokens[t],
                          'invalidtype')


class TokenTestBase(TestCaseBase):

    """Verify token exists before running tests."""

    def setUp(self):
        """Skip test if user does not have token and clear site wallet."""
        super().setUp()
        mysite = self.get_site()
        ttype = self.token_type
        try:
            token = mysite.tokens[ttype]
        except pywikibot.Error as error_msg:
            self.assertRegex(
                str(error_msg),
                "Action '[a-z]+' is not allowed for user .* on .* wiki.")
            self.assertNotIn(self.token_type, self.site.tokens)
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

    user = True
    token_type = 'patrol'
    write = True

    def test_patrol(self):
        """Test the site.patrol() method."""
        mysite = self.get_site()

        rc = list(mysite.recentchanges(total=1))
        if not rc:
            self.skipTest('no recent changes to patrol')

        rc = rc[0]

        # site.patrol() needs params
        self.assertRaises(pywikibot.Error, lambda x: list(x), mysite.patrol())
        try:
            result = list(mysite.patrol(rcid=rc['rcid']))
        except api.APIError as error:
            if error.code == 'permissiondenied':
                self.skipTest(error)
            raise

        if hasattr(mysite, '_patroldisabled') and mysite._patroldisabled:
            self.skipTest('Patrolling is disabled on {} wiki.'.format(mysite))

        result = result[0]
        self.assertIsInstance(result, dict)

        params = {'rcid': 0}
        if mysite.mw_version >= '1.22':
            params['revid'] = [0, 1]

        raised = False
        try:
            # no such rcid, revid or too old revid
            list(mysite.patrol(**params))
        except api.APIError as error:
            if error.code == 'badtoken':
                self.skipTest(error)
        except pywikibot.Error:
            # expected result
            raised = True
        self.assertTrue(raised, msg='pywikibot.Error not raised')


class TestDeprecatedPatrolToken(DefaultSiteTestCase, DeprecationTestCase):

    """Test cases for Site patrol token deprecated methods."""

    cached = True
    user = True

    def test_get_patrol_token(self):
        """Test site.getPatrolToken."""
        self.mysite = self.site
        try:
            self.assertEqual(self.mysite.getPatrolToken(),
                             self.mysite.tokens['patrol'])
            self.assertOneDeprecation()
        except pywikibot.Error as error_msg:
            self.assertRegex(
                str(error_msg),
                "Action '[a-z]+' is not allowed for user .* on .* wiki.")
            # test __contains__
            self.assertNotIn('patrol', self.mysite.tokens)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
