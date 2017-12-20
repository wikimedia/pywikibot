# -*- coding: utf-8 -*-
"""Tests for the User page."""
#
# (C) Pywikibot team, 2016
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import pywikibot

from pywikibot.tools import suppress_warnings
from pywikibot import User

from tests.aspects import TestCase, unittest


class TestUserClass(TestCase):

    """Test User class."""

    family = 'wikipedia'
    code = 'de'

    def test_registered_user(self):
        """Test registered user."""
        user = User(self.site, 'Xqt')
        with suppress_warnings('pywikibot.page.User.name', DeprecationWarning):
            self.assertEqual(user.name(), user.username)
        self.assertEqual(user.title(withNamespace=False), user.username)
        self.assertTrue(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsInstance(user.registration(), pywikibot.Timestamp)
        self.assertGreater(user.editCount(), 0)
        self.assertFalse(user.isBlocked())
        self.assertTrue(user.isEmailable())
        self.assertEqual(user.gender(), 'unknown')
        self.assertIn('userid', user.getprops())

    def test_registered_user_without_timestamp(self):
        """Test registered user when registration timestamp is None."""
        user = User(self.site, 'Ulfb')
        self.assertTrue(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsNone(user.registration())
        self.assertIsNone(user.getprops()['registration'])
        self.assertGreater(user.editCount(), 0)
        self.assertEqual(user.gender(), 'male')
        self.assertIn('userid', user.getprops())

    def test_female_user(self):
        """Test female user."""
        user = User(self.site, 'Alraunenstern')
        self.assertTrue(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertGreater(user.editCount(), 0)
        self.assertEqual(user.gender(), 'female')
        self.assertIn('userid', user.getprops())

    def test_anonymous_user(self):
        """Test registered user."""
        user = User(self.site, '123.45.67.89')
        with suppress_warnings('pywikibot.page.User.name', DeprecationWarning):
            self.assertEqual(user.name(), user.username)
        self.assertEqual(user.title(withNamespace=False), user.username)
        self.assertFalse(user.isRegistered())
        self.assertTrue(user.isAnonymous())
        self.assertIsNone(user.registration())
        self.assertFalse(user.isEmailable())
        self.assertEqual(user.gender(), 'unknown')
        self.assertIn('invalid', user.getprops())

    def test_unregistered_user(self):
        """Test unregistered user."""
        user = User(self.site, 'This user name is not registered yet')
        with suppress_warnings('pywikibot.page.User.name', DeprecationWarning):
            self.assertEqual(user.name(), user.username)
        self.assertEqual(user.title(withNamespace=False), user.username)
        self.assertFalse(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsNone(user.registration())
        self.assertFalse(user.isEmailable())
        self.assertEqual(user.gender(), 'unknown')
        self.assertIn('missing', user.getprops())

    def test_invalid_user(self):
        """Test invalid user."""
        user = User(self.site, 'Invalid char\x9f in Name')
        with suppress_warnings('pywikibot.page.User.name', DeprecationWarning):
            self.assertEqual(user.name(), user.username)
        self.assertEqual(user.title(withNamespace=False), user.username)
        self.assertFalse(user.isRegistered())
        self.assertFalse(user.isAnonymous())
        self.assertIsNone(user.registration())
        self.assertFalse(user.isEmailable())
        self.assertEqual(user.gender(), 'unknown')
        self.assertIn('invalid', user.getprops())


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
