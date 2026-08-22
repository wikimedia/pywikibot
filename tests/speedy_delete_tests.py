#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
"""Tests for scripts/speedy_delete.py."""
from __future__ import annotations

import unittest
from contextlib import suppress
from types import SimpleNamespace
from unittest import mock

from scripts import speedy_delete
from tests.aspects import TestCase


class SpeedyBotTestCase(TestCase):

    """Test the speedy deletion bot."""

    net = False

    def test_reuses_subject_page(self) -> None:
        """Test that the associated subject page is reused."""
        bot = SimpleNamespace(
            site=SimpleNamespace(code='en'),
            talk_deletion_msg={},
        )
        page = mock.Mock()
        subject_page = page.toggleTalkPage.return_value
        page.isTalkPage.return_value = True
        subject_page.isRedirectPage.return_value = False
        subject_page.exists.return_value = False

        with mock.patch.object(speedy_delete.i18n, 'translate',
                               return_value='Orphaned talk page'):
            reason = speedy_delete.SpeedyBot.guess_reason_for_deletion(
                bot, page)

        self.assertEqual(reason, 'Orphaned talk page')
        page.toggleTalkPage.assert_called_once_with()
        subject_page.isRedirectPage.assert_called_once_with()
        subject_page.exists.assert_called_once_with()


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
