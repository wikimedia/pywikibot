# -*- coding: utf-8  -*-
#
# (C) Pywikipedia bot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

from pywikibot import config2 as config
from pywikibot.page import Link
from tests.aspects import unittest, TestCase


class TestPartiallyQualifiedLinkDifferentCodeParser(TestCase):

    family = 'wikipedia'
    code = 'en'
    cached = True

    def setUp(self):
        self.old_lang = config.mylang
        self.old_family = config.family

    def tearDown(self):
        config.mylang = self.old_lang
        config.family = self.old_family

    def test_partially_qualified_NS0_family(self):
        """Test that Link uses config.family for namespace 0."""
        config.mylang = 'de'
        config.family = 'wikipedia'
        link = Link('en:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 0)

    def test_partially_qualified_NS1_family(self):
        """Test that Link uses config.family for namespace 1."""
        config.mylang = 'de'
        config.family = 'wikipedia'
        link = Link('en:Talk:Main Page')
        link.parse()
        self.assertEqual(link.site, self.get_site())
        self.assertEqual(link.title, 'Main Page')
        self.assertEqual(link.namespace, 1)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
