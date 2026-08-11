#!/usr/bin/env python3
#
# (C) Pywikibot team, 2012-2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for LoginManager classes.

e.g. used to test password-file based login.
"""
from __future__ import annotations

import builtins
import datetime
import unittest
import uuid
from collections import defaultdict
from io import StringIO
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from pywikibot.exceptions import NoUsernameError
from pywikibot.login import ClientLoginManager, LoginManager
from pywikibot.tools import PYTHON_VERSION
from tests.aspects import DefaultSiteTestCase, TestCase


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
class TestOfflineLoginManager(DefaultSiteTestCase):

    """Test offline operation of login.LoginManager."""

    dry = True

    def test_default_init(self) -> None:
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
    def test_star_family(self) -> None:
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


class TestClientLoginManager(TestCase):

    """Test offline ClientLoginManager behavior."""

    net = False

    def test_reuses_retry_time(self) -> None:
        """Test that retry calculation uses one time snapshot."""
        now = datetime.datetime(2026, 1, 1, 12)
        manager = object.__new__(ClientLoginManager)
        manager.site = SimpleNamespace()
        manager.login_name = None
        manager.password = None
        manager._waituntil = now + datetime.timedelta(seconds=10)
        clock = mock.Mock(side_effect=[
            now,
            now + datetime.timedelta(seconds=4),
        ])
        # Replacing datetime.datetime mutates the shared datetime module and
        # breaks PyPy's datetime comparison type check.
        datetime_module = SimpleNamespace(
            datetime=SimpleNamespace(now=clock),
            timedelta=datetime.timedelta,
        )

        with (
            mock.patch('pywikibot.login.datetime', datetime_module),
            mock.patch('pywikibot.login.pywikibot.sleep') as sleep,
            mock.patch('pywikibot.login.pywikibot.warning') as warning,
            self.assertRaisesRegex(RuntimeError, 'login_name'),
        ):
            manager.login_to_site()

        clock.assert_called_once_with()
        sleep.assert_called_once_with(10)
        warning.assert_called_once_with(
            'Too many tries, waiting 10 seconds before retrying.')


@mock.patch('pywikibot.Site', FakeSite)
class TestPasswordFile(DefaultSiteTestCase):

    """Test parsing password files."""

    dry = True

    def patch(self, name):
        """Patch up <name> in self.setUp."""
        patcher = mock.patch(name)
        self.addCleanup(patcher.stop)
        return patcher.start()

    def setUp(self) -> None:
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

        if PYTHON_VERSION[:2] == (3, 10):
            self.open = self.patch('pathlib.Path._accessor.open')
        else:
            self.open = self.patch('io.open')

        self.open.return_value = StringIO()

    def test_auto_chmod_OK(self) -> None:
        """Do not chmod files that have mode private_files_permission."""
        self.stat.return_value.st_mode = 0o100600
        LoginManager()
        self.stat.assert_called_with(Path(self.config.password_file))
        self.assertFalse(self.chmod.called)

    def test_auto_chmod_not_OK(self) -> None:
        """Chmod files that do not have mode private_files_permission."""
        self.stat.return_value.st_mode = 0o100644
        LoginManager()
        self.stat.assert_called_with(Path(self.config.password_file))
        self.chmod.assert_called_once_with(
            Path(self.config.password_file),
            0o600
        )

    def _test_pwfile(self, contents, password):
        self.open.return_value = StringIO(contents)
        obj = LoginManager()
        self.assertEqual(obj.password, password)
        return obj

    def test_none_matching(self) -> None:
        """No matching passwords."""
        self._test_pwfile("""
            ('NotTheUsername', 'NotThePassword')
            """, None)

    def test_match_global_username(self) -> None:
        """Test global username/password declaration."""
        self._test_pwfile("""
            ('~FakeUsername', '~FakePassword')
            """, '~FakePassword')

    def test_match_family_username(self) -> None:
        """Test matching by family."""
        self._test_pwfile("""
            ('~FakeFamily', '~FakeUsername', '~FakePassword')
            """, '~FakePassword')

    def test_match_code_username(self) -> None:
        """Test matching by full configuration."""
        self._test_pwfile("""
            ('~FakeCode', '~FakeFamily', '~FakeUsername', '~FakePassword')
            """, '~FakePassword')

    def test_ordering(self) -> None:
        """Test that the last matching password is selected."""
        self._test_pwfile("""
            ('~FakeCode', '~FakeFamily', '~FakeUsername', '~FakePasswordA')
            ('~FakeUsername', '~FakePasswordB')
            """, '~FakePasswordB')

        self._test_pwfile("""
            ('~FakeUsername', '~FakePasswordA')
            ('~FakeCode', '~FakeFamily', '~FakeUsername', '~FakePasswordB')
            """, '~FakePasswordB')

    def test_BotPassword(self) -> None:
        """Test BotPassword entries.

        When a BotPassword is used, the login_name changes to contain a
        suffix, while the password is read from an object (instead of
        being read from the password file directly).
        """
        obj = self._test_pwfile("""
            ('~FakeUsername', BotPassword('~FakeSuffix', '~FakePassword'))
            """, '~FakePassword')
        self.assertEqual(obj.login_name, '~FakeUsername@~FakeSuffix')

    def test_eval_security(self) -> None:
        """Test security that password file does not use eval() function."""
        # File-based checks are limited to Python 3.9 only.
        # On newer versions, self.stat patching in setUp() fails,
        # making the file appear to exist.
        use_file = PYTHON_VERSION[:2] == (3, 9)

        builtins.exploit_value = False
        exploit_code = (
            "__import__('builtins').__dict__"
            ".__setitem__('exploit_value', True)"
        )
        if use_file:
            exploit_filename = f'pwb_rce_{uuid.uuid4().hex[:8]}.txt'
            exploit_file = Path(exploit_filename)
            exploit_code = (
                f"__import__('pathlib').Path('{exploit_filename}').touch() or "
                + exploit_code
            )

        with self.subTest(test='Test ValueError'), \
             self.assertRaisesRegex(ValueError,
                                    'Invalid password line format'):
            self._test_pwfile(f"""
                ('en', 'wikipedia', 'victim', {exploit_code})
                """, None)

        with self.subTest(test='Test value was modified'):
            self.assertFalse(exploit_value)  # noqa: F821

        if use_file:
            with self.subTest(test='Test file exists'):
                self.assertFalse(exploit_file.exists())

            # cleanup file (should never happen)
            exploit_file.unlink(missing_ok=True)


if __name__ == '__main__':
    unittest.main()
