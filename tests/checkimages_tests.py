#!/usr/bin/python3
"""Unit tests for checkimages script."""
#
# (C) Pywikibot team, 2015-2021
#
# Distributed under the terms of the MIT license.
#
import unittest

from scripts import checkimages
from tests.aspects import TestCase


class TestSettings(TestCase):

    """Test checkimages settings."""

    family = 'commons'
    code = 'commons'
    login = True

    def test_load(self):
        """Test loading settings."""
        b = checkimages.CheckImagesBot(self.get_site())
        b.takesettings()
        rv = b.settings_data
        item1 = rv[0]
        self.assertEqual(item1[0], 1)
        self.assertEqual(item1[1], 'a deprecated template')


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
