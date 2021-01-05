"""Tests for titletranslate module."""
#
# (C) Pywikibot team, 2021
#
# Distributed under the terms of the MIT license.
#
from pywikibot.titletranslate import translate

from tests.aspects import unittest, DefaultSiteTestCase


class TestTitleTranslate(DefaultSiteTestCase):

    """Tests for titletranslate module."""

    def setUp(self):
        """Skip sites with empty languages_by_size list."""
        super().setUp()
        if not self.site.family.languages_by_size:
            self.skipTest('languages_by_size is empty')

    def test_translate(self):
        """Test translate method."""
        result = translate(page=self.get_mainpage(), auto=False,
                           hints=['5:', 'nl,en,zh'], site=self.site)
        self.assertLength(result, 6)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
