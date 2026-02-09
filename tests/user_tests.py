#!/usr/bin/env python3
"""Tests for the User page."""
#
# (C) Pywikibot team, 2016-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import unittest
from contextlib import suppress
from unittest.mock import patch

import pywikibot
from pywikibot import Page, Timestamp, User
from pywikibot.exceptions import AutoblockUserError
from tests.aspects import DefaultSiteTestCase, TestCase


class TestUserClass(TestCase):

    """Test User class."""

    family = 'wikipedia'
    code = 'de'

    def _tests_unregistered_user(self, user, prop='invalid') -> None:
        """Proceed user tests."""
        self.assertEqual(user.title(with_ns=False), user.username)
        self.assertFalse(user.isRegistered())
        self.assertIsNone(user.registration())
        self.assertFalse(user.isEmailable())
        self.assertEqual(user.gender(), 'unknown')
        self.assertFalse(user.is_thankable)
        self.assertIn(prop, user.getprops())

    def test_anonymous_user(self) -> None:
        """Test registered user."""
        user = User(self.site, '123.45.67.89')
        self._tests_unregistered_user(user)
        self.assertTrue(user.isAnonymous())

    def test_unregistered_user(self) -> None:
        """Test unregistered user."""
        user = User(self.site, 'This user name is not registered yet')
        self._tests_unregistered_user(user, prop='missing')
        self.assertFalse(user.isAnonymous())

    def test_invalid_user(self) -> None:
        """Test invalid user."""
        user = User(self.site, 'Invalid char\x9f in Name')
        self._tests_unregistered_user(user)
        self.assertFalse(user.isAnonymous())

    def test_registered_user(self) -> None:
        """Test registered user."""
        user = User(self.site, 'Xqt')
        self.assertEqual(user.title(with_ns=False), user.username)
        self.assertTrue(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsInstance(user.registration(), pywikibot.Timestamp)
        self.assertGreater(user.editCount(), 0)
        self.assertFalse(user.is_blocked())
        self.assertFalse(user.is_locked())
        self.assertTrue(user.isEmailable())
        self.assertEqual(user.gender(), 'unknown')
        self.assertIn('userid', user.getprops())
        self.assertEqual(user.getprops()['userid'], 287832)
        self.assertEqual(user.pageid, 6927779)
        self.assertEqual(user.getUserPage(),
                         pywikibot.Page(self.site, 'Benutzer:Xqt'))
        self.assertEqual(user.getUserPage(subpage='pwb'),
                         pywikibot.Page(self.site, 'Benutzer:Xqt/pwb'))
        self.assertEqual(user.getUserTalkPage(),
                         pywikibot.Page(self.site, 'Benutzer Diskussion:Xqt'))
        self.assertEqual(user.getUserTalkPage(subpage='pwb'),
                         pywikibot.Page(self.site,
                                        'Benutzer Diskussion:Xqt/pwb'))
        self.assertTrue(user.is_thankable)
        contribs = list(user.contributions(total=10))
        self.assertLength(contribs, 10)

        for contrib in contribs:
            self.assertIsInstance(contrib, tuple)
            self.assertIsInstance(contrib[0], pywikibot.Page)
            self.assertIsInstance(contrib[1], int)
            self.assertIsInstance(contrib[2], pywikibot.Timestamp)

        self.assertIn('user', user.groups())
        self.assertIn('edit', user.rights())
        self.assertFalse(user.is_locked())

    def test_registered_user_without_timestamp(self) -> None:
        """Test registered user when registration timestamp is None."""
        user = User(self.site, 'Ulfb')
        self.assertTrue(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsNone(user.registration())
        self.assertIsNone(user.getprops()['registration'])
        self.assertGreater(user.editCount(), 0)
        self.assertEqual(user.gender(), 'unknown')
        self.assertIn('userid', user.getprops())
        self.assertTrue(user.is_thankable)

    def test_female_user(self) -> None:
        """Test female user."""
        user = User(self.site, 'Catrin')
        self.assertTrue(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertGreater(user.editCount(), 0)
        self.assertEqual(user.gender(), 'female')
        self.assertIn('userid', user.getprops())
        self.assertTrue(user.is_thankable)

    def test_bot_user(self) -> None:
        """Test bot user."""
        user = User(self.site, 'Xqbot')
        self.assertIn('bot', user.groups())
        self.assertFalse(user.is_thankable)

    def test_autoblocked_user(self) -> None:
        """Test autoblocked user."""
        with patch.object(pywikibot, 'info') as p:
            user = User(self.site, '#1242976')
        p.assert_called_once_with(
            'This is an autoblock ID, you can only use to unblock it.')
        self.assertEqual('#1242976', user.username)
        self.assertEqual(user.title(with_ns=False), user.username[1:])
        self.assertFalse(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsNone(user.registration())
        self.assertFalse(user.isEmailable())
        self.assertIn('invalid', user.getprops())
        self.assertTrue(user._isAutoblock)
        with self.assertRaisesRegex(
                AutoblockUserError,
                'This is an autoblock ID'):
            user.getUserPage()
        with self.assertRaisesRegex(
                AutoblockUserError,
                'This is an autoblock ID'):
            user.getUserTalkPage()

    def test_autoblocked_user_with_namespace(self) -> None:
        """Test autoblocked user."""
        # Suppress output: This is an autoblock ID, you can only use to unblock
        with patch.object(pywikibot, 'info'):
            user = User(self.site, 'User:#1242976')
        self.assertEqual('#1242976', user.username)
        self.assertEqual(user.title(with_ns=False), user.username[1:])
        self.assertFalse(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsNone(user.registration())
        self.assertFalse(user.isEmailable())
        self.assertIn('invalid', user.getprops())
        self.assertTrue(user._isAutoblock)
        with self.assertRaisesRegex(
                AutoblockUserError,
                'This is an autoblock ID'):
            user.getUserPage()
        with self.assertRaisesRegex(
                AutoblockUserError,
                'This is an autoblock ID'):
            user.getUserTalkPage()

    def test_locked_user(self) -> None:
        """Test global lock."""
        user = User(self.site, 'TonjaHeritage2')
        self.assertTrue(user.is_locked())

    def test_block_info(self) -> None:
        """Test block information methods."""
        # 1. Test partial block detection
        user = User(self.site, 'PartialUser')
        user._userprops = {
            'userid': 1234,
            'blockid': 12345,
            'blockpartial': '',
            'blockreason': 'Test partial'
        }

        self.assertTrue(user.is_partial_blocked())
        info = user.get_block_info()
        self.assertIsNotNone(info)
        self.assertIn('blockpartial', info)
        self.assertEqual(info['blockid'], 12345)

        # 2. Test full block (not partial)
        user = User(self.site, 'FullUser')
        user._userprops = {
            'userid': 5678,
            'blockid': 67890,
            'blockreason': 'Test full'
        }

        self.assertFalse(user.is_partial_blocked())
        info = user.get_block_info()
        self.assertIsNotNone(info)
        self.assertNotIn('blockpartial', info)
        self.assertEqual(info['blockid'], 67890)

        # 3. Test unblocked user
        user = User(self.site, 'NormalUser')
        user._userprops = {'userid': 999}

        self.assertFalse(user.is_partial_blocked())
        self.assertIsNone(user.get_block_info())


class TestUserMethods(DefaultSiteTestCase):

    """Test User methods with bot user."""

    login = True

    def test_contribution(self) -> None:
        """Test the User.usercontribs() method."""
        total = 50
        mysite = self.get_site()
        user = User(mysite, mysite.user())
        uc = list(user.contributions(total=total))
        if not uc:
            self.skipTest(
                f'User {mysite.user()} has no contributions on site {mysite}.')
        self.assertLessEqual(len(uc), total)
        self.assertEqual(uc[0], user.last_edit)
        first_edit = uc[-1] if len(uc) < total else list(
            user.contributions(total=1, reverse=True))[0]
        self.assertEqual(first_edit, user.first_edit)
        for contrib in uc:
            self.assertIsInstance(contrib, tuple)
            self.assertLength(contrib, 4)
            p, i, t, c = contrib
            self.assertIsInstance(p, Page)
            self.assertIsInstance(i, int)
            self.assertIsInstance(t, Timestamp)
            self.assertIsInstance(c, str)

    def test_logevents(self) -> None:
        """Test the User.logevents() method."""
        mysite = self.get_site()
        user = User(mysite, mysite.user())
        le = list(user.logevents(total=10))
        if not le:
            self.skipTest(
                f'User {mysite.user()} has no logevents on site {mysite}.')
        self.assertLessEqual(len(le), 10)
        last = le[0]
        self.assertEqual(last, user.last_event)
        for event in le:
            self.assertEqual(event.user(), user.username)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
