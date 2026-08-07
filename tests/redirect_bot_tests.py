#!/usr/bin/env python3
#
# (C) Pywikibot team, 2017-2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the redirect.py script."""
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


class TestFixMovedBrokenRedirects(DefaultSiteTestCase):

    """Test fix_moved_broken_redirects() loop handling."""

    def test_cyclic_move_chain_terminates_without_editing_or_deleting(
            self) -> None:
        """Move chain A -> B -> C -> A must terminate without edits."""
        page_a, page_b, page_c = Mock(), Mock(), Mock()
        page_a.moved_target.return_value = page_b
        page_b.moved_target.return_value = page_c
        page_c.moved_target.return_value = page_a  # closes the loop
        page_b.exists.return_value = False
        page_c.exists.return_value = False

        bot = RedirectTestRobot('broken', delete=True)
        bot.delete_redirect = Mock()
        bot.userPut = Mock(return_value=True)

        bot.fix_moved_broken_redirects(page_a)  # must not hang/recurse

        bot.delete_redirect.assert_not_called()
        bot.userPut.assert_not_called()


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
