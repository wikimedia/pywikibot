# -*- coding: utf-8  -*-
"""Tests for editing pages."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import time

import pywikibot

from pywikibot import page_put_queue
from pywikibot import config

from tests.aspects import unittest, TestCase
from tests.oauth_tests import OAuthSiteTestCase

called_back = False


class TestGeneralWrite(TestCase):

    """Run general write tests."""

    family = 'test'
    code = 'test'

    user = True
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
        p.save(async=True, callback=callback)

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
        self.assertTrue(p.text != ts)


class OAuthEditTest(OAuthSiteTestCase):

    """Run edit test with OAuth enabled."""

    family = 'wikipedia'
    code = 'test'

    write = True

    def setUp(self):
        """Set up test by checking site and initialization."""
        super(OAuthEditTest, self).setUp()
        self._authenticate = config.authenticate
        oauth_tokens = self.consumer_token + self.access_token
        config.authenticate[self.site.hostname()] = oauth_tokens

    def tearDown(self):
        """Tear down test by resetting config.authenticate."""
        config.authenticate = self._authenticate

    def test_edit(self):
        """Test editing to a page."""
        self.site.login()
        self.assertTrue(self.site.logged_in())
        ts = str(time.time())
        p = pywikibot.Page(self.site,
                           'User:%s/edit test' % self.site.username())
        p.site.editpage(p, appendtext=ts)
        revision_id = p.latest_revision_id
        p = pywikibot.Page(self.site,
                           'User:%s/edit test' % self.site.username())
        self.assertEqual(revision_id, p.latest_revision_id)
        self.assertTrue(p.text.endswith(ts))


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
