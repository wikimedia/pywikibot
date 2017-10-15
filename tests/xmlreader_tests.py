# -*- coding: utf-8 -*-
"""Tests for xmlreader module."""
#
# (C) Pywikibot team, 2009-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

from pywikibot import xmlreader

from tests import join_xml_data_path
from tests.aspects import unittest, TestCase


class XmlReaderTestCase(TestCase):

    """XML Reader test cases."""

    net = False

    def _get_entries(self, filename, **kwargs):
        """Get all entries via XmlDump."""
        entries = [r for r in
                   xmlreader.XmlDump(join_xml_data_path(filename),
                                     **kwargs).parse()]
        return entries


class ExportDotThreeTestCase(XmlReaderTestCase):

    """XML export version 0.3 tests."""

    def test_XmlDumpAllRevs(self):
        """Test loading all revisions."""
        pages = self._get_entries('article-pear.xml', allrevisions=True)
        self.assertEqual(4, len(pages))
        self.assertEqual(u"Automated conversion", pages[0].comment)
        self.assertEqual(u"Pear", pages[0].title)
        self.assertEqual(u"24278", pages[0].id)
        self.assertTrue(pages[0].text.startswith('Pears are [[tree]]s of'))
        self.assertEqual(u"Quercusrobur", pages[1].username)
        self.assertEqual(u"Pear", pages[0].title)

    def test_XmlDumpFirstRev(self):
        """Test loading the first revision."""
        pages = self._get_entries("article-pear.xml", allrevisions=False)
        self.assertEqual(1, len(pages))
        self.assertEqual(u"Automated conversion", pages[0].comment)
        self.assertEqual(u"Pear", pages[0].title)
        self.assertEqual(u"24278", pages[0].id)
        self.assertTrue(pages[0].text.startswith('Pears are [[tree]]s of'))
        self.assertTrue(not pages[0].isredirect)

    def test_XmlDumpRedirect(self):
        """Test XmlDump correctly parsing whether a page is a redirect."""
        pages = self._get_entries('article-pyrus.xml', allrevisions=True)
        pages = [r for r in
                 xmlreader.XmlDump(join_xml_data_path('article-pyrus.xml')).parse()]
        self.assertTrue(pages[0].isredirect)

    def _compare(self, previous, variant, all_revisions):
        """Compare the tested variant with the previous (if not None)."""
        entries = self._get_entries('article-pyrus' + variant,
                                    allrevisions=all_revisions)
        result = [entry.__dict__ for entry in entries]
        if previous:
            self.assertEqual(previous, result)
        return result

    def _compare_variants(self, all_revisions):
        """Compare the different XML file variants."""
        previous = None
        previous = self._compare(previous, '.xml', all_revisions)
        previous = self._compare(previous, '-utf16.xml', all_revisions)
        previous = self._compare(previous, '.xml.bz2', all_revisions)
        previous = self._compare(previous, '-utf16.xml.bz2', all_revisions)

    def test_XmlDump_compare_all(self):
        """Compare the different XML files using all revisions."""
        self._compare_variants(True)

    def test_XmlDump_compare_single(self):
        """Compare the different XML files using only a single revision."""
        self._compare_variants(False)


class ExportDotTenTestCase(XmlReaderTestCase):

    """XML export version 0.10 tests."""

    def test_pair(self):
        """Test reading the main page/user talk page pair file."""
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


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
