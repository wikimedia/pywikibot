# -*- coding: utf-8  -*-
"""
Tests for xmlreader module.
"""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'


import os.path
from pywikibot import xmlreader
from tests.utils import unittest


class XmlReaderTestCase(unittest.TestCase):

    def setUp(self):
        self.path = os.path.dirname(os.path.abspath(__file__))

    def test_XmlDumpAllRevs(self):
        pages = [r for r in
                 xmlreader.XmlDump(os.path.join(self.path, 'data',
                                                "article-pear.xml"),
                                   allrevisions=True).parse()]
        self.assertEquals(4, len(pages))
        self.assertEquals(u"Automated conversion", pages[0].comment)
        self.assertEquals(u"Pear", pages[0].title)
        self.assertEquals(u"24278", pages[0].id)
        self.assertTrue(pages[0].text.startswith('Pears are [[tree]]s of'))
        self.assertEquals(u"Quercusrobur", pages[1].username)
        self.assertEquals(u"Pear", pages[0].title)

    def test_XmlDumpFirstRev(self):
        pages = [r for r in
                 xmlreader.XmlDump(os.path.join(self.path, 'data',
                                                "article-pear.xml")).parse()]
        self.assertEquals(1, len(pages))
        self.assertEquals(u"Automated conversion", pages[0].comment)
        self.assertEquals(u"Pear", pages[0].title)
        self.assertEquals(u"24278", pages[0].id)
        self.assertTrue(pages[0].text.startswith('Pears are [[tree]]s of'))
        self.assertTrue(not pages[0].isredirect)

    def test_XmlDumpRedirect(self):
        pages = [r for r in
                 xmlreader.XmlDump(os.path.join(self.path, 'data',
                                                "article-pyrus.xml")).parse()]
        self.assertTrue(pages[0].isredirect)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
