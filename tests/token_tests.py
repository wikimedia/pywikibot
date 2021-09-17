"""Tests for tokens."""
#
# (C) Pywikibot team, 2015-2021
#
# Distributed under the terms of the MIT license.
#
from contextlib import suppress

from pywikibot.exceptions import APIError, Error
from pywikibot.tools import MediaWikiVersion
from pywikibot.site import TokenWallet
from tests.aspects import DefaultSiteTestCase, TestCase, TestCaseBase, unittest


class TestSiteTokens(DefaultSiteTestCase):

    """Test cases for tokens in Site methods.

    Versions of sites are simulated if actual versions are higher than
    needed by the test case.

    Test is skipped if site version is not compatible.

    """

    login = True

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
        del self.mysite._mw_version_time  # remove cached mw_version

        redirected_tokens = ['edit', 'move', 'delete']
        for ttype in redirected_tokens + ['patrol', additional_token]:
            try:
                token = self.mysite.tokens[ttype]
            except Error as error_msg:
                if self.mysite.validate_tokens([ttype]):
                    pattern = ("Action '[a-z]+' is not allowed "
                               'for user .* on .* wiki.')
                else:
                    pattern = "Requested token '[a-z]+' is invalid on .* wiki."

                self.assertRegex(str(error_msg), pattern)

            else:
                self.assertIsInstance(token, str)
                self.assertEqual(token, self.mysite.tokens[ttype])
                # test __contains__
                if test_version < '1.24wmf19':
                    self.assertIn(ttype, self.mysite.tokens)
                elif ttype in redirected_tokens:
                    self.assertEqual(self.mysite.tokens[ttype],
                                     self.mysite.tokens['csrf'])

    def test_tokens_in_mw_123_124wmf18(self):
        """Test ability to get page tokens."""
        if MediaWikiVersion(self.orig_version()) >= '1.37wmf24':
            self.skipTest('Site {} version {} is too new for this tests.'
                          .format(self.mysite, self._version))
        self._test_tokens('1.23', '1.24wmf18', 'deleteglobalaccount')

    def test_tokens_in_mw_124wmf19(self):
        """Test ability to get page tokens."""
        self._test_tokens('1.24wmf19', '1.24wmf20', 'deleteglobalaccount')

    def test_invalid_token(self):
        """Test invalid token."""
        with self.assertRaises(Error):
            self.mysite.tokens['invalidtype']


class TokenTestBase(TestCaseBase):

    """Verify token exists before running tests."""

    def setUp(self):
        """Skip test if user does not have token and clear site wallet."""
        super().setUp()
        mysite = self.get_site()
        ttype = self.token_type
        try:
            token = mysite.tokens[ttype]
        except Error as error_msg:
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
    token_type = 'patrol'

    login = True
    write = True

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
            self.skipTest('Patrolling is disabled on {} wiki.'.format(mysite))

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
