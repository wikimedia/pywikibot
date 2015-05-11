# -*- coding: utf-8  -*-
"""API Request cache tests."""
#
# (C) Pywikibot team, 2012-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

from pywikibot.site import BaseSite
import scripts.maintenance.cache as cache

from tests import _cache_dir
from tests.aspects import unittest, TestCase


class RequestCacheTests(TestCase):

    """Validate cache entries."""

    net = False

    def _check_cache_entry(self, entry):
        """Assert validity of the cache entry."""
        self.assertIsInstance(entry.site, BaseSite)
        self.assertIsInstance(entry.site._loginstatus, int)
        self.assertIsInstance(entry.site._username, list)
        if entry.site._loginstatus >= 1:
            self.assertIsNotNone(entry.site._username[0])
        self.assertIsInstance(entry._params, dict)
        self.assertIsNotNone(entry._params)
        # TODO: more tests on entry._params, and possibly fixes needed
        # to make it closely replicate the original object.

    def test_cache(self):
        """Test the apicache by doing _check_cache_entry over each entry."""
        cache.process_entries(_cache_dir, self._check_cache_entry)


if __name__ == '__main__':
    unittest.main()
