#!/usr/bin/env python3
"""Tests for the redirect.py script."""
#
# (C) Pywikibot team, 2017-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress
from unittest.mock import Mock, patch

import pywikibot
from pywikibot import Page, i18n
from scripts.redirect import RedirectRobot
from tests.aspects import DefaultSiteTestCase


class RedirectTestRobot(RedirectRobot):

    """RedirectRobot test class."""

    @property
    def current_page(self):
        """Patch current_page to return any page."""
        return Page(self.site, 'Main', ns=4)

    @property
    def site(self):
        """Patch site to return a site object."""
        return pywikibot.Site()


@patch.object(Page, 'exists', new=Mock(return_value=True))
class TestGetSDTemplateNoSysop(DefaultSiteTestCase):

    """Test the get_sd_template method of the RedirectRobot class."""

    def test_with_delete_and_existing_sdtemplate(self):
        """Test with delete and existing sdtemplate."""
        options = {'delete': True, 'sdtemplate': '{{t}}'}
        bot = RedirectTestRobot('broken', **options)
        self.assertEqual(bot.sdtemplate, '{{t}}')

    @patch.object(i18n, 'twhas_key', new=Mock(return_value=True))
    @patch.object(i18n, 'twtranslate', new=Mock(return_value='{{sd_title}}'))
    def test_with_delete_and_i18n_sd(self):
        """Test with delete and i18n template."""
        bot = RedirectTestRobot('broken', delete=True)
        self.assertEqual(bot.sdtemplate, '{{sd_title}}')

    @patch.object(i18n, 'twhas_key', new=Mock(return_value=False))
    def test_with_delete_no_sd_no_i18n(self):
        """Test with delete and no i18n template."""
        bot = RedirectTestRobot('broken', delete=True)
        with patch.object(pywikibot, 'warning') as w:
            self.assertIsNone(bot.sdtemplate)
        w.assert_called_with('No speedy deletion template available.')

    def test_with_delete_and_non_existing_sdtemplate(self):
        """Test with delete and non-exisitng sdtemplate."""
        options = {'delete': True, 'sdtemplate': 'txt {{n|a}} txt'}
        bot = RedirectTestRobot('broken', **options)
        with patch.object(Page, 'exists', new=Mock(return_value=False)), \
             patch.object(pywikibot, 'warning') as w:
            self.assertIsNone(bot.sdtemplate, None)
        w.assert_called_with('No speedy deletion template "n" available.')


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
