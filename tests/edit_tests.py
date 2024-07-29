#!/usr/bin/env python3
"""Tests for editing pages."""
#
# (C) Pywikibot team, 2015-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import time
import unittest
from contextlib import suppress

import pywikibot
from pywikibot import page_put_queue
from pywikibot.exceptions import Error
from tests.aspects import TestCase, require_version


called_back = False


class TestGeneralWrite(TestCase):

    """Run general write tests."""

    family = 'wikipedia'
    code = 'test'

    login = True
    write = True

    def test_createonly(self):
        """Test save with createonly enforced."""
        ts = str(time.time())
        p = pywikibot.Page(self.site, 'User:John Vandenberg/createonly/' + ts)
        p.save(createonly=True)

    def test_async(self):
        """Test writing to a page."""
        global called_back

        def callback(page, err):
            global called_back
            self.assertEqual(page, p)
            self.assertIsNone(err)
            called_back = True

        self.assertTrue(page_put_queue.empty())
        called_back = False
        ts = str(time.time())
        p = pywikibot.Page(self.site, 'User:John Vandenberg/async test write')
        p.text = ts
        p.save(asynchronous=True, callback=callback)

        page_put_queue.join()

        p = pywikibot.Page(self.site, 'User:John Vandenberg/async test write')
        self.assertEqual(p.text, ts)
        self.assertTrue(called_back)

    def test_appendtext(self):
        """Test writing to a page without preloading the .text."""
        ts = str(time.time())
        p = pywikibot.Page(self.site, 'User:John Vandenberg/appendtext test')
        self.assertFalse(hasattr(p, '_text'))
        p.site.editpage(p, appendtext=ts)
        self.assertFalse(hasattr(p, '_text'))
        p = pywikibot.Page(self.site, 'User:John Vandenberg/appendtext test')
        self.assertTrue(p.text.endswith(ts))
        self.assertNotEqual(p.text, ts)


class TestSiteMergeHistory(TestCase):
    """Test history merge action."""

    family = 'wikipedia'
    code = 'test'

    write = True
    rights = 'mergehistory'

    @require_version('>=1.27.0wmf.13', 'support the history merge API')
    def setup_test_pages(self):
        """Helper function to set up pages that we will use in these tests."""
        site = self.get_site()
        source = pywikibot.Page(site, 'User:Sn1per/MergeTest1')
        dest = pywikibot.Page(site, 'User:Sn1per/MergeTest2')

        if source.exists():
            source.delete('Pywikibot merge history unit test', prompt=False)
        if dest.exists():
            dest.delete('Pywikibot merge history unit test', prompt=False)

        source.text = 'Lorem ipsum dolor sit amet'
        source.save()
        first_rev = source.latest_revision.timestamp

        source.text = 'Lorem ipsum dolor sit amet is a common test phrase'
        source.save()
        second_rev = source.latest_revision.timestamp

        dest.text = 'Merge history page unit test destination'
        dest.save()

        return first_rev, second_rev

    def test_merge_history_validation(self):
        """Test Site.merge_history validity checks."""
        site = self.get_site()

        page_source = pywikibot.Page(site, 'User:Sn1per/MergeTest1')
        page_nonexist = pywikibot.Page(site, 'User:Sn1per/Nonexistent')

        # Test source and dest validation
        test_errors = [
            (
                {  # source same as dest
                    'source': page_source,
                    'dest': page_source,
                },
                'Cannot merge revisions of [[test:User:Sn1per/MergeTest1]] '
                'to itself'
            ),
            (
                {  # nonexistent source
                    'source': page_nonexist,
                    'dest': page_source,
                },
                'Cannot merge revisions from source '
                '[[test:User:Sn1per/Nonexistent]] because it does not exist '
                'on wikipedia:test'
            ),
            (
                {  # nonexistent dest
                    'source': page_source,
                    'dest': page_nonexist,
                },
                'Cannot merge revisions to destination '
                '[[test:User:Sn1per/Nonexistent]] because it does not exist '
                'on wikipedia:test'
            ),
        ]

        self.setup_test_pages()
        for params, error_msg in test_errors:
            try:
                site.merge_history(**params)
            except Error as err:
                self.assertEqual(str(err), error_msg)

    def test_merge_history(self):
        """Test Site.merge_history functionality."""
        site = self.get_site()
        source = pywikibot.Page(site, 'User:Sn1per/MergeTest1')
        dest = pywikibot.Page(site, 'User:Sn1per/MergeTest2')

        # Without timestamp
        self.setup_test_pages()
        site.merge_history(source, dest)
        self.assertEqual(dest.revision_count(), 3)

        # With latest timestamp
        revs = self.setup_test_pages()
        source.clear_cache()  # clear revision cache when page is recreated
        dest.clear_cache()
        site.merge_history(source, dest, revs[1])
        self.assertEqual(dest.revision_count(), 3)

        # With middle timestamp
        revs = self.setup_test_pages()
        source.clear_cache()
        dest.clear_cache()
        site.merge_history(source, dest, revs[0])
        self.assertEqual(dest.revision_count(), 2)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
