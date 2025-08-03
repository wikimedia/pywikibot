#!/usr/bin/env python3
"""Tests for the redirect.py script."""
#
# (C) Pywikibot team, 2017-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import unittest
from contextlib import suppress
from unittest.mock import Mock, patch

import pywikibot
from pywikibot import Page
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

    def test_with_delete_and_existing_sdtemplate(self) -> None:
        """Test with delete and existing sdtemplate."""
        options = {'delete': True, 'sdtemplate': '{{t}}'}
        bot = RedirectTestRobot('broken', **options)
        self.assertEqual(bot.sdtemplate, '{{t}}')

    def test_with_delete_and_i18n_sd(self) -> None:
        """Test with delete and wikibase template."""
        with patch.object(
            pywikibot.site.APISite, 'page_from_repository',
            new=Mock(return_value=pywikibot.Page(self.site, 'Sd_title'))
        ):
            bot = RedirectTestRobot('broken', delete=True)
            self.assertEqual(bot.sdtemplate, '{{Sd title}}')

    def test_with_delete_no_sd_no_i18n(self) -> None:
        """Test with delete and no wikibase template."""
        with patch.object(pywikibot.site.APISite, 'page_from_repository',
                          new=Mock(return_value=None)):
            bot = RedirectTestRobot('broken', delete=True)
            with patch.object(pywikibot, 'warning') as w:
                self.assertEqual(bot.sdtemplate, '')
            w.assert_called_with('No speedy deletion template available.')

    def test_with_delete_and_non_existing_sdtemplate(self) -> None:
        """Test with delete and non-existing sdtemplate."""
        options = {'delete': True, 'sdtemplate': 'txt {{n|a}} txt'}
        bot = RedirectTestRobot('broken', **options)
        with patch.object(Page, 'exists', new=Mock(return_value=False)), \
                patch.object(pywikibot, 'warning') as w:
            self.assertEqual(bot.sdtemplate, '')
        w.assert_called_with('No speedy deletion template "n" available.')


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
