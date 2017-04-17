# -*- coding: utf-8 -*-
"""Tests for the redirect.py script."""
#
# (C) Pywikibot team, 2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

try:
    from unittest.mock import Mock, patch
except ImportError:
    from mock import Mock, patch

import pywikibot

from pywikibot import site, Page, i18n

from scripts.redirect import RedirectRobot

from tests.aspects import DefaultSiteTestCase


# To make `self.site.logged_in(sysop=True)` always return False
@patch.object(site.APISite, 'logged_in', new=Mock(return_value=False))
@patch.object(Page, 'exists', new=Mock(return_value=True))
class TestGetSDTemplateNoSysop(DefaultSiteTestCase):

    """Test the get_sd_template method of the RedirectRobot class."""

    def test_with_delete_and_existing_sdtemplate(self):
        """Test with delete and existing sdtemplate."""
        options = {'delete': True, 'sdtemplate': '{{t}}'}
        bot = RedirectRobot('broken', **options)
        self.assertEqual(bot.sdtemplate, '{{t}}')

    @patch.object(i18n, 'twhas_key', new=Mock(return_value=True))
    @patch.object(i18n, 'twtranslate', new=Mock(return_value='{{sd_title}}'))
    def test_with_delete_and_i18n_sd(self):
        """Test with delete and i18n template."""
        bot = RedirectRobot('broken', delete=True)
        self.assertEqual(bot.sdtemplate, '{{sd_title}}')

    @patch.object(i18n, 'twhas_key', new=Mock(return_value=False))
    def test_with_delete_no_sd_no_i18n(self):
        """Test with delete and no i18n template."""
        with patch.object(pywikibot, 'warning') as w:
            bot = RedirectRobot('broken', delete=True)
        w.assert_called_with('No speedy deletion template available.')
        self.assertEqual(bot.sdtemplate, None)

    def test_with_delete_and_non_existing_sdtemplate(self):
        """Test with delete and non-exisitng sdtemplate."""
        options = {'delete': True, 'sdtemplate': 'txt {{n|a}} txt'}
        with patch.object(Page, 'exists', new=Mock(return_value=False)):
            with patch.object(pywikibot, 'warning') as w:
                bot = RedirectRobot('broken', **options)
        w.assert_called_with('No speedy deletion template "n" available.')
        self.assertEqual(bot.sdtemplate, None)
