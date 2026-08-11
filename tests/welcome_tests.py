#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the welcome script."""
from __future__ import annotations

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from scripts import welcome
from tests.aspects import TestCase


class TestWelcomeBot(TestCase):

    """Test :class:`welcome.WelcomeBot`."""

    net = False

    def test_skip_page_reuses_edit_count(self) -> None:
        """Test that the edit count is retrieved once."""
        bot = SimpleNamespace(show_status=MagicMock())
        user = MagicMock(username='Alice')
        user.is_blocked.return_value = False
        user.is_locked.return_value = False
        user.groups.return_value = []
        user.editCount.return_value = 1

        with (
            patch.object(welcome.globalvar, 'attach_edit_count', 2),
            patch.object(welcome.pywikibot, 'info') as info,
        ):
            result = welcome.WelcomeBot.skip_page(bot, user)

        self.assertTrue(result)
        user.editCount.assert_called_once_with()
        bot.show_status.assert_called_once_with(welcome.Msg.IGNORE)
        info.assert_called_once_with('Alice has only 1 contributions.')

    def test_signature_file_closed_on_read_error(self) -> None:
        """Test that the signature file is closed when reading fails."""
        file_obj = MagicMock()
        file_obj.__enter__.return_value = file_obj
        file_obj.read.side_effect = OSError

        with (
            patch.object(
                welcome.globalvar, 'sign_file_name', 'signatures.txt'),
            patch.object(welcome.pywikibot.config, 'datafilepath',
                         return_value='signatures.txt'),
            patch('builtins.open', return_value=file_obj),
            self.assertRaises(OSError),
        ):
            welcome.WelcomeBot.define_sign(SimpleNamespace())

        file_obj.__exit__.assert_called_once()


if __name__ == '__main__':
    unittest.main()
