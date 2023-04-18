#!/usr/bin/env python3
"""Tests for the site module."""
#
# (C) Pywikibot team, 2015-2023
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress
from http import HTTPStatus

import pywikibot
from pywikibot.comms import http
from pywikibot.tools import suppress_warnings

from tests import WARN_SITE_CODE
from tests.aspects import DefaultSiteTestCase


class TestObsoleteSite(DefaultSiteTestCase):

    """Test 'closed' and obsolete code sites."""

    def test_locked_site(self):
        """Test Wikimedia closed/locked site."""
        with suppress_warnings('Interwiki removal mh is in wikipedia codes'):
            site = pywikibot.Site('mh', 'wikipedia')
        self.assertIsInstance(site, pywikibot.site.ClosedSite)
        self.assertEqual(site.code, 'mh')
        self.assertIsInstance(site.obsolete, bool)
        self.assertTrue(site.obsolete)
        self.assertEqual(site.hostname(), 'mh.wikipedia.org')
        r = http.fetch('http://mh.wikipedia.org/w/api.php',
                       default_error_handling=False)
        self.assertEqual(r.status_code, HTTPStatus.OK.value)
        self.assertEqual(site.siteinfo['lang'], 'mh')
        self.assertTrue(site.is_uploaddisabled())

    def test_removed_site(self):
        """Test Wikimedia offline site."""
        site = pywikibot.Site('ru-sib', 'wikipedia')
        self.assertIsInstance(site, pywikibot.site.RemovedSite)
        self.assertEqual(site.code, 'ru-sib')
        self.assertIsInstance(site.obsolete, bool)
        self.assertTrue(site.obsolete)
        with self.assertRaises(KeyError):
            site.hostname()
        # See also http_tests, which tests that ru-sib.wikipedia.org is offline

    def test_alias_code_site(self):
        """Test Wikimedia site with an alias code."""
        with suppress_warnings(WARN_SITE_CODE, category=UserWarning):
            site = pywikibot.Site('jp', 'wikipedia')
        self.assertIsInstance(site.obsolete, bool)
        self.assertEqual(site.code, 'ja')
        self.assertFalse(site.obsolete)
        self.assertEqual(site.hostname(), 'ja.wikipedia.org')
        self.assertEqual(site.ssl_hostname(), 'ja.wikipedia.org')


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
