# -*- coding: utf-8  -*-
"""Tests for xmlreader module."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'


import os.path
from pywikibot import xmlreader
from tests import _data_dir
from tests.aspects import unittest, TestCase


class XmlReaderTestCase(TestCase):

    """XML Reader test cases."""

    net = False

    def test_XmlDumpAllRevs(self):
        pages = [r for r in
                 xmlreader.XmlDump(os.path.join(_data_dir,
                                                "article-pear.xml"),
                                   allrevisions=True).parse()]
        self.assertEqual(4, len(pages))
        self.assertEqual(u"Automated conversion", pages[0].comment)
        self.assertEqual(u"Pear", pages[0].title)
        self.assertEqual(u"24278", pages[0].id)
        self.assertTrue(pages[0].text.startswith('Pears are [[tree]]s of'))
        self.assertEqual(u"Quercusrobur", pages[1].username)
        self.assertEqual(u"Pear", pages[0].title)

    def test_XmlDumpFirstRev(self):
        pages = [r for r in
                 xmlreader.XmlDump(os.path.join(_data_dir,
                                                "article-pear.xml")).parse()]
        self.assertEqual(1, len(pages))
        self.assertEqual(u"Automated conversion", pages[0].comment)
        self.assertEqual(u"Pear", pages[0].title)
        self.assertEqual(u"24278", pages[0].id)
        self.assertTrue(pages[0].text.startswith('Pears are [[tree]]s of'))
        self.assertTrue(not pages[0].isredirect)

    def test_XmlDumpRedirect(self):
        pages = [r for r in
                 xmlreader.XmlDump(os.path.join(_data_dir,
                                                "article-pyrus.xml")).parse()]
        self.assertTrue(pages[0].isredirect)

    def _compare(self, previous, variant, all_revisions):
        result = [entry.__dict__ for entry in xmlreader.XmlDump(
            os.path.join(_data_dir, 'article-pyrus' + variant),
            all_revisions).parse()]
        if previous:
            self.assertEqual(previous, result)
        return result

    def _compare_variants(self, all_revisions):
        previous = None
        previous = self._compare(previous, '.xml', all_revisions)
        previous = self._compare(previous, '-utf16.xml', all_revisions)
        previous = self._compare(previous, '.xml.bz2', all_revisions)
        previous = self._compare(previous, '-utf16.xml.bz2', all_revisions)

    def test_XmlDump_compare_all(self):
        self._compare_variants(True)

    def test_XmlDump_compare_single(self):
        self._compare_variants(False)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
