"""Tests for the WikiHistoryMixin."""
#
# (C) Pywikibot team, 2022-2023
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

import pywikibot
from tests.aspects import TestCase


class TestWikiBlameMixin(TestCase):

    """Test WikiBlameMixin using nds wiki."""

    family = 'wikipedia'
    code = 'nds'

    def test_main_authors(self):
        """Test main_authors() method."""
        page = pywikibot.Page(self.site, 'Python (Programmeerspraak)')
        auth = page.main_authors(onlynew=False)
        self.assertLessEqual(len(auth), 5)
        self.assertLessEqual(sum(auth.values()), 100)
        user, value = auth.most_common(1)[0]
        self.assertEqual(user, 'RebeccaBreu')
        self.assertGreater(value, 0)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
