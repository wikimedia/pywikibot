#!/usr/bin/env python3
#
# (C) Pywikibot team, 2014-2026
#
# Distributed under the terms of the MIT license.
#
"""Special BaseUnlinkBot test."""
from __future__ import annotations

import unittest
from contextlib import suppress

from pywikibot.specialbots import BaseUnlinkBot, EditReplacementError
from tests.aspects import TestCase


class TestDryUnlinkbot(TestCase):

    """Dry tests UploadRobot."""

    net = False

    def test_unlink_bot(self) -> None:
        """Test UploadRobot attributes and methods."""
        bot = BaseUnlinkBot(always=True, namespaces=[0, 2])
        self.assertTrue(bot.opt.always)
        self.assertEqual(bot.opt.namespaces, [0, 2])  # ignore_warning


class TestChoiceOptions(TestCase):

    """Test cases for unlink bot_choice Options."""

    net = False

    def test_edit_replacement_excepton(self) -> None:
        """Test ChoiceException."""
        option = EditReplacementError()
        self.assertTrue(option.stop)
        self.assertEqual(option.result('*'), option)
        with self.assertRaises(EditReplacementError):
            raise EditReplacementError


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
