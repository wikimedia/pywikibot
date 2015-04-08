#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Unit tests for checkimages script."""
from __future__ import unicode_literals

from scripts import checkimages

from tests.aspects import unittest, TestCase


class TestSettings(TestCase):

    """Test checkimages settings."""

    family = 'commons'
    code = 'commons'
    user = True

    def test_load(self):
        """Test loading settings."""
        b = checkimages.checkImagesBot(self.get_site())
        rv = b.takesettings()
        item1 = rv[0]
        self.assertEqual(item1[0], 1)
        self.assertEqual(item1[1], 'a deprecated template')


if __name__ == "__main__":
    unittest.main()
