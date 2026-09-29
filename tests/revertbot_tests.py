#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the revertbot script."""
from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock, patch

from scripts import revertbot
from tests.aspects import TestCase


class TestRevertBot(TestCase):

    """Test revertbot revision loading."""

    net = False

    def setUp(self) -> None:
        """Set up test bot and page."""
        super().setUp()
        self.site = Mock()
        self.site.username.return_value = 'RevertBot'
        self.site.lang = 'en'
        self.bot = revertbot.ContribRevertBot(site=self.site)
        self.page = Mock()
        self.page.site = self.site
        self.page.title.return_value = 'Test page'
        self.latest = SimpleNamespace(revid=2, text=None)
        self.previous = SimpleNamespace(
            revid=1,
            user='Example',
            timestamp=Mock(),
            text=None,
        )
        self.page.revisions.return_value = iter(
            [self.latest, self.previous])
        self.page.text = 'current text'
        self.page.get_revision.return_value = SimpleNamespace(
            text='previous text')
        self.bot.get_page = Mock(return_value=self.page)

    def test_manual_revert_batches_missing_content(self) -> None:
        """Test that a manual revert batches missing revision texts."""
        with patch.object(revertbot.i18n, 'twtranslate',
                          return_value='Revert summary'), \
             patch.object(revertbot.pywikibot, 'showDiff') as show_diff, \
             patch.object(self.bot, 'local_timestamp', return_value='date'):
            result = self.bot.revert({})

        self.assertEqual(result, 'Revert summary')
        self.page.revisions.assert_called_once_with(total=2)
        self.site.loadrevisions.assert_called_once_with(
            self.page, revids=[2, 1], content=True)
        self.page.get_revision.assert_called_once_with(1)
        show_diff.assert_called_once_with('current text', 'previous text')
        self.page.save.assert_called_once_with('Revert summary')

    def test_manual_revert_reuses_cached_content(self) -> None:
        """Test that cached revision content is not requested again."""
        self.latest.text = 'current text'

        with patch.object(revertbot.i18n, 'twtranslate',
                          return_value='Revert summary'), \
             patch.object(revertbot.pywikibot, 'showDiff'), \
             patch.object(self.bot, 'local_timestamp', return_value='date'):
            self.bot.revert({})

        self.site.loadrevisions.assert_called_once_with(
            self.page, revids=[1], content=True)


if __name__ == '__main__':
    import unittest

    unittest.main()
