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

    def test_rejected_bad_account_not_queued(self) -> None:
        """Test rejecting the first bad account leaves an empty queue."""
        site = MagicMock()

        def init(bot, **kwargs) -> None:
            bot._site = site

        with (
            patch.object(welcome.SingleSiteBot, '__init__', init),
            patch.object(welcome.i18n, 'translate', return_value='Log'),
            patch.object(welcome, 'get_welcome_text'),
            patch.object(welcome.globalvar, 'random_sign', False),
        ):
            bot = welcome.WelcomeBot()

        with (
            patch.object(welcome.globalvar, 'confirm', True),
            patch.object(welcome.pywikibot, 'input_choice', return_value='n'),
        ):
            bot.collect_bad_accounts('Bad name')

        self.assertIsEmpty(bot._BAQueue)

    def test_report_bad_account_clears_queue(self) -> None:
        """Test that reported bad accounts are removed from the queue."""
        report_page = MagicMock()
        report_page.exists.return_value = False
        site = MagicMock()
        site.code = 'en'
        bot = SimpleNamespace(
            _BAQueue=['Bad name'], bname={}, show_status=MagicMock(),
            site=site)

        with (
            patch.object(welcome.pywikibot, 'Page',
                         return_value=report_page),
            # T75017: report_bad_account still uses compat's url2link.
            patch.object(welcome.pywikibot, 'url2link',
                         create=True, return_value='Bad name'),
            patch.object(welcome.i18n, 'translate',
                         side_effect=['Report page', '* %s']),
            patch.object(welcome.i18n, 'twtranslate',
                         return_value='Report bad username'),
        ):
            welcome.WelcomeBot.report_bad_account(bot)

        self.assertIsEmpty(bot._BAQueue)

    def test_write_log_ignores_empty_bad_account_queue(self) -> None:
        """Test that an empty bad-account queue is not reported."""
        bot = SimpleNamespace(
            _BAQueue=[], report_bad_account=MagicMock(),
            show_status=MagicMock(), welcomed_users=[])

        with patch.object(welcome.globalvar, 'make_welcome_log', False):
            welcome.WelcomeBot.write_log(bot)

        bot.report_bad_account.assert_not_called()

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
