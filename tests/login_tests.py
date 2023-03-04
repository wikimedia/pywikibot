#!/usr/bin/env python3
"""
Tests for LoginManager classes.

e.g. used to test password-file based login.
"""
#
# (C) Pywikibot team, 2012-2022
#
# Distributed under the terms of the MIT license.
#
from collections import defaultdict
from io import StringIO
from unittest import mock

from pywikibot.exceptions import NoUsernameError
from pywikibot.login import LoginManager
from tests.aspects import DefaultDrySiteTestCase, unittest


class FakeFamily:
    """Mock."""

    name = '~FakeFamily'


class FakeSite:
    """Mock."""

    code = '~FakeCode'
    family = FakeFamily


FakeUsername = '~FakeUsername'


class FakeConfig:
    """Mock."""

    usernames = defaultdict(dict)
    usernames[FakeFamily.name] = {FakeSite.code: FakeUsername}


@mock.patch('pywikibot.Site', FakeSite)
@mock.patch('pywikibot.login.config', FakeConfig)
class TestOfflineLoginManager(DefaultDrySiteTestCase):
    """Test offline operation of login.LoginManager."""

    dry = True

    def test_default_init(self):
        """Test initialization of LoginManager without parameters."""
        obj = LoginManager()
        self.assertIsInstance(obj.site, FakeSite)
        self.assertEqual(obj.username, FakeUsername)
        self.assertEqual(obj.login_name, FakeUsername)
        self.assertIsNone(obj.password)

    @mock.patch.dict(
        FakeConfig.usernames,
        {'*': {'*': FakeUsername}},
        clear=True
    )
    def test_star_family(self):
        """Test LoginManager with '*' as family."""
        lm = LoginManager()
        self.assertEqual(lm.username, FakeUsername)

        del FakeConfig.usernames['*']
        FakeConfig.usernames['*']['en'] = FakeUsername
        error_undefined_username = 'ERROR: username for.*is undefined.\nIf'
        with self.assertRaisesRegex(
                NoUsernameError,
                error_undefined_username):
            LoginManager()
        FakeConfig.usernames['*']['*'] = FakeUsername
        lm = LoginManager()
        self.assertEqual(lm.username, FakeUsername)


@mock.patch('pywikibot.Site', FakeSite)
class TestPasswordFile(DefaultDrySiteTestCase):
    """Test parsing password files."""

    def patch(self, name):
        """Patch up <name> in self.setUp."""
        patcher = mock.patch(name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def setUp(self):
        """Patch a variety of dependencies."""
        super().setUp()
        self.config = self.patch('pywikibot.login.config')
        self.config.usernames = FakeConfig.usernames
        self.config.password_file = '~FakeFile'
        self.config.private_files_permission = 0o600
        self.config.base_dir = ''  # ensure that no path modifies password_file

        self.stat = self.patch('os.stat')
        self.stat.return_value.st_mode = 0o100600

        self.chmod = self.patch('os.chmod')

        self.open = self.patch('codecs.open')
        self.open.return_value = StringIO()

    def test_auto_chmod_OK(self):
        """Do not chmod files that have mode private_files_permission."""
        self.stat.return_value.st_mode = 0o100600
        LoginManager()
        self.stat.assert_called_with(self.config.password_file)
        self.assertFalse(self.chmod.called)

    def test_auto_chmod_not_OK(self):
        """Chmod files that do not have mode private_files_permission."""
        self.stat.return_value.st_mode = 0o100644
        LoginManager()
        self.stat.assert_called_with(self.config.password_file)
        self.chmod.assert_called_once_with(
            self.config.password_file,
            0o600
        )

    def _test_pwfile(self, contents, password):
        self.open.return_value = StringIO(contents)
        obj = LoginManager()
        self.assertEqual(obj.password, password)
        return obj

    def test_none_matching(self):
        """No matching passwords."""
        self._test_pwfile("""
            ('NotTheUsername', 'NotThePassword')
            """, None)

    def test_match_global_username(self):
        """Test global username/password declaration."""
        self._test_pwfile("""
            ('~FakeUsername', '~FakePassword')
            """, '~FakePassword')

    def test_match_family_username(self):
        """Test matching by family."""
        self._test_pwfile("""
            ('~FakeFamily', '~FakeUsername', '~FakePassword')
            """, '~FakePassword')

    def test_match_code_username(self):
        """Test matching by full configuration."""
        self._test_pwfile("""
            ('~FakeCode', '~FakeFamily', '~FakeUsername', '~FakePassword')
            """, '~FakePassword')

    def test_ordering(self):
        """Test that the last matching password is selected."""
        self._test_pwfile("""
            ('~FakeCode', '~FakeFamily', '~FakeUsername', '~FakePasswordA')
            ('~FakeUsername', '~FakePasswordB')
            """, '~FakePasswordB')

        self._test_pwfile("""
            ('~FakeUsername', '~FakePasswordA')
            ('~FakeCode', '~FakeFamily', '~FakeUsername', '~FakePasswordB')
            """, '~FakePasswordB')

    def test_BotPassword(self):
        """Test BotPassword entries.

        When a BotPassword is used, the login_name changes to contain a
        suffix, while the password is read from an object (instead of being
        read from the password file directly).
        """
        obj = self._test_pwfile("""
            ('~FakeUsername', BotPassword('~FakeSuffix', '~FakePassword'))
            """, '~FakePassword')
        self.assertEqual(obj.login_name, '~FakeUsername@~FakeSuffix')


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
