#!/usr/bin/env python3
"""API Request cache tests."""
#
# (C) Pywikibot team, 2012-2023
#
# Distributed under the terms of the MIT license.
#
import unittest

import scripts.maintenance.cache as cache
from pywikibot.login import LoginStatus
from pywikibot.site import BaseSite
from tests import join_cache_path
from tests.aspects import TestCase


class RequestCacheTests(TestCase):

    """Validate cache entries."""

    net = False

    def _check_cache_entry(self, entry):
        """Assert validity of the cache entry."""
        self.assertIsInstance(entry.site, BaseSite)
        self.assertIsInstance(entry.site._loginstatus, int)
        self.assertNotIsInstance(entry.site._username, list)
        if entry.site._loginstatus >= LoginStatus.AS_USER:
            self.assertIsNotNone(entry.site._username)
        self.assertIsInstance(entry._params, dict)
        self.assertIsNotNone(entry._params)
        # TODO: more tests on entry._params, and possibly fixes needed
        # to make it closely replicate the original object.

    def test_cache(self):
        """Test the apicache by doing _check_cache_entry over each entry."""
        cache.process_entries(join_cache_path(), self._check_cache_entry,
                              tests=25)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
