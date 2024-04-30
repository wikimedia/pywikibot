#!/usr/bin/env python3
"""Tests for xmlreader module."""
#
# (C) Pywikibot team, 2009-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import unittest
from contextlib import suppress

from pywikibot import xmlreader
from pywikibot.tools import suppress_warnings
from tests import join_xml_data_path
from tests.aspects import TestCase


def get_entries(filename, **kwargs):
    """Get all entries via XmlDump."""
    return list(xmlreader.XmlDump(join_xml_data_path(filename),
                                  **kwargs).parse())


class ExportDotThreeTestCase(TestCase):

    """XML export version 0.3 tests."""

    net = False

    def test_XmlDumpAllRevs(self):
        """Test loading all revisions."""
        pages = get_entries('article-pear.xml', revisions='all')
        self.assertLength(pages, 4)
        self.assertEqual('Automated conversion', pages[0].comment)
        self.assertEqual('Pear', pages[0].title)
        self.assertEqual('24278', pages[0].id)
        self.assertEqual('185185', pages[0].revisionid)
        self.assertEqual('188924', pages[3].revisionid)
        self.assertTrue(pages[0].text.startswith('Pears are [[tree]]s of'))
        self.assertEqual('Quercusrobur', pages[1].username)
        self.assertEqual('Pear', pages[0].title)

    def test_XmlDumpFoundRev(self):
        """Test loading the first, earliest and latest revision."""
        tests = {
            'first_found': ('Automated conversion', '185185'),
            'earliest': ('Automated conversion', '185185'),
            'latest': ('sp', '188924'),
        }
        for revisions, (comment, revid) in tests.items():
            with suppress_warnings(
                    r".+'allrevisions' is deprecated since release 9\.0\.0"):
                pages = get_entries('article-pear.xml', revisions=revisions)
            with self.subTest(revisions=revisions):
                self.assertLength(pages, 1)
                page = pages[0]
                self.assertEqual(comment, page.comment)
                self.assertEqual('Pear', page.title)
                self.assertEqual('24278', page.id)
                self.assertEqual(revid, page.revisionid)
                self.assertTrue(page.text.startswith('Pears are [[tree]]s of'))
                self.assertTrue(not page.isredirect)

    def test_XmlDumpRedirect(self):
        """Test XmlDump correctly parsing whether a page is a redirect."""
        get_entries('article-pyrus.xml', revisions='all')
        pages = list(xmlreader.XmlDump(
            join_xml_data_path('article-pyrus.xml')).parse())
        self.assertTrue(pages[0].isredirect)

    def _compare(self, previous, variant, revisions):
        """Compare the tested variant with the previous (if not None)."""
        entries = get_entries('article-pyrus' + variant,
                              revisions=revisions)
        result = [entry.__dict__ for entry in entries]
        if previous:
            self.assertEqual(previous, result)
        return result

    def _compare_variants(self, revisions):
        """Compare the different XML file variants."""
        previous = None
        previous = self._compare(previous, '.xml', revisions)
        previous = self._compare(previous, '-utf16.xml', revisions)
        previous = self._compare(previous, '.xml.bz2', revisions)
        self._compare(previous, '-utf16.xml.bz2', revisions)

    def test_XmlDump_compare_all(self):
        """Compare the different XML files using all revisions."""
        self._compare_variants('all')

    def test_XmlDump_compare_single(self):
        """Compare the different XML files using only a single revision."""
        self._compare_variants('latest')


class ExportDotTenTestCase(TestCase):

    """XML export version 0.10 tests."""

    net = False

    def test_pair(self):
        """Test reading the main page/user talk page pair file."""
        entries = get_entries('pair-0.10.xml', revisions='all')
        self.assertLength(entries, 4)
        for entry in entries:
            self.assertEqual(entry.username, 'Carlossuarez46')
            self.assertFalse(entry.isredirect)

        articles = entries[0:2]
        talks = entries[2:4]

        self.assertLength(articles, 2)
        for entry in articles:
            self.assertEqual(entry.id, '19252820')
            self.assertEqual(entry.title, 'Çullu, Agdam')
            self.assertIn('Çullu, Quzanlı', entry.text)

        self.assertLength(talks, 2)
        for entry in talks:
            self.assertEqual(entry.id, '19252824')
            self.assertEqual(entry.title, 'Talk:Çullu, Agdam')

        self.assertEqual(articles[0].text, '#REDIRECT [[Çullu, Quzanlı]]')
        self.assertEqual(talks[1].text, '{{DisambigProject}}')
        self.assertEqual(talks[1].comment, 'proj')

    def test_edit_summary_decoding(self):
        """Test edit summaries are decoded."""
        entries = get_entries('pair-0.10.xml', revisions='all')
        articles = [entry for entry in entries if entry.ns == '0']

        # It does not decode the edit summary
        self.assertEqual(
            articles[0].comment,
            'moved [[Çullu, Agdam]] to [[Çullu, Quzanlı]]:&#32;dab')


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
