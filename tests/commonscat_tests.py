#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Unit tests for commonscat script."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, call

from scripts.commonscat import CommonscatBot
from tests.aspects import TestCase


class TestCommonscatBot(TestCase):

    """Test CommonscatBot methods."""

    dry = True

    def test_change_commonscat_reuses_page_data(self) -> None:
        """Test that changing a Commons category reuses page data."""
        page = MagicMock()
        page.title.side_effect = lambda with_ns=True: (
            'Category:New category' if with_ns else 'New category')
        page.text = '{{Old|New category}}'
        page.get.return_value = page.text
        bot = MagicMock()
        bot.opt.summary = 'summary'

        CommonscatBot.changeCommonscat(
            bot, page, 'Old', 'New category', 'New', 'New category')

        self.assertEqual(page.title.call_args_list,
                         [call(), call(with_ns=False)])
        page.get.assert_called_once_with()
        bot.userPut.assert_called_once_with(
            page, page.text, '{{New}}', summary='summary',
            ignore_save_related_errors=True)

    def test_change_commonscat_replacement_branches(self) -> None:
        """Test the remaining Commons category replacement branches."""
        cases = (
            ('Link title', '{{New|New category|Link title}}'),
            ('', '{{New|New category}}'),
        )
        for linktitle, expected in cases:
            with self.subTest(linktitle=linktitle):
                page = MagicMock()
                page.title.side_effect = lambda with_ns=True: (
                    'Category:Page' if with_ns else 'Page')
                page.text = '{{Old|Old category}}'
                page.get.return_value = page.text
                bot = MagicMock()
                bot.opt.summary = 'summary'

                CommonscatBot.changeCommonscat(
                    bot, page, 'Old', 'Old category', 'New',
                    'New category', linktitle)

                page.get.assert_called_once_with()
                bot.userPut.assert_called_once_with(
                    page, page.text, expected, summary='summary',
                    ignore_save_related_errors=True)

    def test_change_commonscat_unchanged(self) -> None:
        """Test that unchanged Commons categories do not load page text."""
        page = MagicMock()
        page.title.side_effect = lambda with_ns=True: (
            'Category:Page' if with_ns else 'Page')
        bot = MagicMock()

        CommonscatBot.changeCommonscat(
            bot, page, 'Old', 'Same category', 'New', 'Same category')

        page.get.assert_not_called()
        bot.userPut.assert_not_called()


if __name__ == '__main__':
    unittest.main()
