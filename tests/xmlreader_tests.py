# -*- coding: utf-8  -*-
"""Tests for xmlreader module."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import os.path

from pywikibot import xmlreader

from tests import _data_dir
from tests.aspects import unittest, TestCase

_xml_data_dir = os.path.join(_data_dir, 'xml')


class XmlReaderTestCase(TestCase):

    """XML Reader test cases."""

    net = False

    def _get_entries(self, filename, **kwargs):
        entries = [r for r in
                   xmlreader.XmlDump(os.path.join(_xml_data_dir, filename),
                                     **kwargs).parse()]
        return entries


class ExportDotThreeTestCase(XmlReaderTestCase):

    """XML export version 0.3 tests."""

    def test_XmlDumpAllRevs(self):
        pages = self._get_entries('article-pear.xml', allrevisions=True)
        self.assertEqual(4, len(pages))
        self.assertEqual(u"Automated conversion", pages[0].comment)
        self.assertEqual(u"Pear", pages[0].title)
        self.assertEqual(u"24278", pages[0].id)
        self.assertTrue(pages[0].text.startswith('Pears are [[tree]]s of'))
        self.assertEqual(u"Quercusrobur", pages[1].username)
        self.assertEqual(u"Pear", pages[0].title)

    def test_XmlDumpFirstRev(self):
        pages = self._get_entries("article-pear.xml", allrevisions=False)
        self.assertEqual(1, len(pages))
        self.assertEqual(u"Automated conversion", pages[0].comment)
        self.assertEqual(u"Pear", pages[0].title)
        self.assertEqual(u"24278", pages[0].id)
        self.assertTrue(pages[0].text.startswith('Pears are [[tree]]s of'))
        self.assertTrue(not pages[0].isredirect)

    def test_XmlDumpRedirect(self):
        pages = self._get_entries('article-pyrus.xml', allrevisions=True)
        pages = [r for r in
                 xmlreader.XmlDump(os.path.join(_xml_data_dir,
                                                "article-pyrus.xml")).parse()]
        self.assertTrue(pages[0].isredirect)

    def _compare(self, previous, variant, all_revisions):
        entries = self._get_entries('article-pyrus' + variant,
                                    allrevisions=all_revisions)
        result = [entry.__dict__ for entry in entries]
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


class ExportDotTenTestCase(XmlReaderTestCase):

    """XML export version 0.10 tests."""

    def test_pair(self):
        entries = self._get_entries('pair-0.10.xml', allrevisions=True)
        self.assertEqual(4, len(entries))
        self.assertTrue(all(entry.username == 'Carlossuarez46'
                            for entry in entries))
        self.assertTrue(all(entry.isredirect is False for entry in entries))

        articles = entries[0:2]
        talks = entries[2:4]

        self.assertEqual(2, len(articles))
        self.assertTrue(all(entry.id == "19252820" for entry in articles))
        self.assertTrue(all(entry.title == u"Çullu, Agdam"
                            for entry in articles))
        self.assertTrue(all(u'Çullu, Quzanlı' in entry.text
                            for entry in articles))
        self.assertEqual(articles[0].text, u'#REDIRECT [[Çullu, Quzanlı]]')

        self.assertEqual(2, len(talks))
        self.assertTrue(all(entry.id == "19252824" for entry in talks))
        self.assertTrue(all(entry.title == u"Talk:Çullu, Agdam"
                            for entry in talks))
        self.assertEqual(talks[1].text, '{{DisambigProject}}')
        self.assertEqual(talks[1].comment, 'proj')

    def test_edit_summary_decoding(self):
        """Test edit summaries are decoded."""
        entries = self._get_entries('pair-0.10.xml', allrevisions=True)
        articles = [entry for entry in entries if entry.ns == "0"]

        # It does not decode the edit summary
        self.assertEqual(articles[0].comment,
                         u'moved [[Çullu, Agdam]] to [[Çullu, Quzanlı]]:&#32;dab')


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
