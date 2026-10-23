#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the coordinate_import script."""
from __future__ import annotations

import unittest
from collections import Counter
from contextlib import suppress
from types import SimpleNamespace
from unittest.mock import Mock, patch

from pywikibot.exceptions import CoordinateGlobeUnknownError
from scripts.coordinate_import import CoordImportRobot
from tests.aspects import TestCase


class TestCoordinateImport(TestCase):

    """Test coordinate saves through the standard bot helper."""

    net = False

    def test_save_result(self) -> None:
        """Preserve sources, confirmation, and synchronous error handling."""
        bot = object.__new__(CoordImportRobot)
        bot.repo = Mock()
        bot.prop = 'P625'
        bot.opt = SimpleNamespace(always=True)
        bot.counter = Counter()
        page, item, claim, source = Mock(), Mock(), Mock(), Mock()
        bot._current_page = item

        with patch('scripts.coordinate_import.pywikibot.Claim',
                   return_value=claim), \
                patch.object(bot, 'getSource', return_value=source) as get_src:
            self.assertTrue(bot.try_import_coordinates_from_page(page, item))
            claim.setTarget.assert_called_once_with(
                page.coordinates.return_value)
            get_src.assert_called_once_with(page.site)
            claim.addSource.assert_called_once_with(source)
            item.addClaim.assert_called_once_with(
                claim, bot=True, asynchronous=False)
            self.assertEqual(bot.counter['write'], 1)

            item.addClaim.reset_mock()
            with patch.object(bot, 'user_confirm', return_value=False):
                self.assertFalse(
                    bot.try_import_coordinates_from_page(page, item))
            item.addClaim.assert_not_called()
            self.assertEqual(bot.counter['write'], 1)

            item.addClaim.side_effect = CoordinateGlobeUnknownError('unknown')
            self.assertFalse(bot.try_import_coordinates_from_page(page, item))
            self.assertEqual(bot.counter['write'], 1)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
