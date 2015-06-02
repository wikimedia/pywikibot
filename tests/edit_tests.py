# -*- coding: utf-8  -*-
"""Tests for editing pages."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import time

import pywikibot

from pywikibot import page_put_queue

from tests.aspects import unittest, TestCase

called_back = False


class TestGeneralWrite(TestCase):

    """Run general write tests."""

    family = 'test'
    code = 'test'

    user = True
    write = True

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
        p.save(async=True, callback=callback)

        page_put_queue.join()

        p = pywikibot.Page(self.site, 'User:John Vandenberg/async test write')
        self.assertEqual(p.text, ts)
        self.assertTrue(called_back)

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
