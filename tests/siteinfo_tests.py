#!/usr/bin/env python3
"""Tests for the site module."""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import re
import unittest
from contextlib import suppress
from datetime import datetime
from unittest.mock import MagicMock, patch

import pywikibot
from pywikibot import async_request, page_put_queue
from tests.aspects import DefaultDrySiteTestCase, DefaultSiteTestCase
from tests.utils import entered_loop


class TestSiteInfo(DefaultSiteTestCase):

    """Test cases for Site metadata and capabilities."""

    cached = True

    def setUp(self):
        """Clear siteinfo cache."""
        super().setUp()
        self.site.siteinfo.clear()

    def test_siteinfo(self):
        """Test the siteinfo property."""
        # general enteries
        mysite = self.get_site()
        self.assertIsInstance(mysite.siteinfo['timeoffset'], (int, float))
        self.assertTrue(-12 * 60 <= mysite.siteinfo['timeoffset'] <= +14 * 60)
        self.assertEqual(mysite.siteinfo['timeoffset'] % 15, 0)
        self.assertRegex(mysite.siteinfo['timezone'],
                         '([A-Z]{3,4}|[A-Z][a-z]+/[A-Z][a-z]+)')
        self.assertIn(mysite.siteinfo['case'], ['first-letter',
                                                'case-sensitive'])
        self.assertIsInstance(
            datetime.strptime(mysite.siteinfo['time'], '%Y-%m-%dT%H:%M:%SZ'),
            datetime)
        self.assertEqual(re.findall(r'\$1', mysite.siteinfo['articlepath']),
                         ['$1'])

    def test_siteinfo_boolean(self):
        """Test conversion of boolean properties from empty strings."""
        mysite = self.get_site()
        self.assertIsInstance(mysite.siteinfo['titleconversion'], bool)

        self.assertIsInstance(mysite.namespaces[0].subpages, bool)
        self.assertIsInstance(mysite.namespaces[0].content, bool)

    def test_properties_with_defaults(self):
        """Test the siteinfo properties with defaults."""
        # This does not test that the defaults work correct,
        # unless the default site is a version needing these defaults
        # 'fileextensions' introduced in v1.15:
        self.assertIsInstance(self.site.siteinfo.get('fileextensions'), list)
        self.assertIn('fileextensions', self.site.siteinfo)
        fileextensions = self.site.siteinfo.get('fileextensions')
        self.assertIn({'ext': 'png'}, fileextensions)
        # 'restrictions' introduced in v1.23:
        mysite = self.site
        self.assertIsInstance(mysite.siteinfo.get('restrictions'), dict)
        self.assertIn('restrictions', mysite.siteinfo)
        restrictions = self.site.siteinfo.get('restrictions')
        self.assertIn('cascadinglevels', restrictions)

    def test_no_cache(self):
        """Test siteinfo caching can be disabled."""
        if 'fileextensions' in self.site.siteinfo._cache:
            del self.site.siteinfo._cache['fileextensions']  # pragma: no cover
        self.site.siteinfo.get('fileextensions', cache=False)
        self.assertFalse(self.site.siteinfo.is_cached('fileextensions'))

    def test_not_exists(self):
        """Test accessing a property not in siteinfo."""
        not_exists = 'this-property-does-not-exist'
        mysite = self.site
        with self.assertRaises(KeyError):
            mysite.siteinfo.__getitem__(not_exists)
        self.assertNotIn(not_exists, mysite.siteinfo)
        self.assertIsEmpty(mysite.siteinfo.get(not_exists))
        self.assertFalse(entered_loop(mysite.siteinfo.get(not_exists)))
        self.assertFalse(
            entered_loop(mysite.siteinfo.get(not_exists).items()))
        self.assertFalse(
            entered_loop(mysite.siteinfo.get(not_exists).values()))
        self.assertFalse(entered_loop(mysite.siteinfo.get(not_exists).keys()))

    def test_container(self):
        """Test Siteinfo container methods."""
        self.assertFalse(self.site.siteinfo.is_cached('general'))
        self.assertIn('general', self.site.siteinfo)
        self.assertTrue(self.site.siteinfo.is_cached('general'))
        self.assertNotIn('### key not in siteinfo ###', self.site.siteinfo)


class TestSiteinfoDry(DefaultDrySiteTestCase):

    """Test Siteinfo in dry mode."""

    def test_siteinfo_timestamps(self):
        """Test that cache has the timestamp of CachedRequest."""
        site = self.get_site()
        request_mock = MagicMock()
        request_mock.submit = lambda: {'query': {'_prop': '_value'}}
        request_mock._cachetime = '_cache_time'
        with patch.object(site, '_request', return_value=request_mock):
            siteinfo = pywikibot.site.Siteinfo(site)
            result = siteinfo._get_siteinfo('_prop', False)
        self.assertEqual(result, {'_prop': ('_value', '_cache_time')})


class TestSiteinfoAsync(DefaultSiteTestCase):

    """Test asynchronous siteinfo fetch."""

    def test_async_request(self):
        """Test async request."""
        self.assertTrue(page_put_queue.empty())
        self.assertFalse(self.site.siteinfo.is_cached('statistics'))
        async_request(self.site.siteinfo.get, 'statistics')
        page_put_queue.join()
        self.assertTrue(self.site.siteinfo.is_cached('statistics'))


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
