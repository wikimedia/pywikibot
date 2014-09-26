# -*- coding: utf-8  -*-
"""Tests for the tools.MediaWikiVersion class."""
#
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'


from pywikibot.tools import MediaWikiVersion as V

from tests.aspects import unittest, TestCase


class TestMediaWikiVersion(TestCase):

    """Test MediaWikiVersion class comparisons."""

    net = False

    def test_normal_versions(self):
        self.assertGreater(V('1.23'), V('1.22.0'))
        self.assertTrue(V('1.23') == V('1.23'))
        self.assertEqual(V('1.23'), V('1.23'))

    def test_wmf_versions(self):
        self.assertGreater(V('1.23wmf10'), V('1.23wmf9'))
        self.assertEqual(V('1.23wmf10'), V('1.23wmf10'))

    def test_combined_versions(self):
        self.assertGreater(V('1.23wmf10'), V('1.22.3'))
        self.assertGreater(V('1.23'), V('1.23wmf10'))


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
