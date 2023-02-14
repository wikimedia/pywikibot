#!/usr/bin/env python3
"""Unit tests for checkimages script."""
#
# (C) Pywikibot team, 2015-2023
#
# Distributed under the terms of the MIT license.
#
import unittest

from pywikibot import FilePage
from scripts import checkimages
from tests.aspects import DefaultSiteTestCase, TestCase


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


class TestMethods(DefaultSiteTestCase):

    """Test methods of CheckImagesBot."""

    def test_important_image(self):
        """Test important_image method."""
        filenames = ('Example.jpg', 'Demo.jpg')
        images = [(0.0, FilePage(self.site, name)) for name in filenames]
        self.assertEqual(checkimages.CheckImagesBot.important_image(images),
                         FilePage(self.site, 'Example.jpg'))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
