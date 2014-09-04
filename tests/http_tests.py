# -*- coding: utf-8  -*-
"""Tests for http module."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import sys
import pywikibot
from pywikibot.comms import http, threadedhttp
from pywikibot import config2 as config
from tests.utils import unittest, NoSiteTestCase


class HttpTestCase(NoSiteTestCase):

    net = True

    def test_get(self):
        r = http.request(site=None, uri='http://www.wikipedia.org/')
        self.assertIsInstance(r, str if sys.version_info[0] >= 3 else unicode)
        self.assertIn('<html lang="mul"', r)

    def test_request(self):
        o = threadedhttp.Http()
        r = o.request('http://www.wikipedia.org/')
        self.assertIsInstance(r, tuple)
        self.assertIsInstance(r[0], dict)
        self.assertIn('status', r[0])
        self.assertIsInstance(r[0]['status'], str)
        self.assertEqual(r[0]['status'], '200')

        self.assertIsInstance(r[1], bytes if sys.version_info[0] >= 3 else str)
        self.assertIn(b'<html lang="mul"', r[1])
        self.assertEqual(int(r[0]['content-length']), len(r[1]))

    def test_gzip(self):
        o = threadedhttp.Http()
        r = o.request('http://www.wikipedia.org/')
        self.assertIn('-content-encoding', r[0])
        self.assertEqual(r[0]['-content-encoding'], 'gzip')

        url = 'https://test.wikidata.org/w/api.php?action=query&meta=siteinfo'
        r = o.request(url)
        self.assertIn('-content-encoding', r[0])
        self.assertEqual(r[0]['-content-encoding'], 'gzip')

    def test_user_agent(self):
        self.assertEqual('', http.user_agent(format_string='  '))
        self.assertEqual('', http.user_agent(format_string=' '))
        self.assertEqual('a', http.user_agent(format_string=' a '))

        # if there is no site, these can't have a value
        self.assertEqual('', http.user_agent(format_string='{username}'))
        self.assertEqual('', http.user_agent(format_string='{family}'))
        self.assertEqual('', http.user_agent(format_string='{lang}'))

        self.assertEqual('Pywikibot/' + pywikibot.__release__,
                          http.user_agent(format_string='{pwb}'))
        self.assertNotIn(' ', http.user_agent(format_string=' {pwb} '))

        self.assertIn('Pywikibot/' + pywikibot.__release__,
                      http.user_agent(format_string='SVN/1.7.5 {pwb}'))

    def test_user_agent_username(self):
        self.assertEqual('%25', http.user_agent_username('%'))
        self.assertEqual('%2525', http.user_agent_username('%25'))
        self.assertEqual(';', http.user_agent_username(';'))
        self.assertEqual('-', http.user_agent_username('-'))
        self.assertEqual('.', http.user_agent_username('.'))
        self.assertEqual("'", http.user_agent_username("'"))
        self.assertEqual('foo_bar', http.user_agent_username('foo bar'))

        self.assertEqual('%E2%81%82', http.user_agent_username(u'⁂'))


class DefaultUserAgentTestCase(NoSiteTestCase):

    def setUp(self):
        self.orig_format = config.user_agent_format
        config.user_agent_format = '{script_product} ({script_comments}) {pwb} ({revision}) {httplib2} {python}'

    def tearDown(self):
        config.user_agent_format = self.orig_format

    def test_default_user_agent(self):
        """ Config defined format string test. """
        self.assertTrue(http.user_agent().startswith(
            pywikibot.calledModuleName()))
        self.assertIn('Pywikibot/' + pywikibot.__release__, http.user_agent())
        self.assertNotIn('  ', http.user_agent())
        self.assertNotIn('()', http.user_agent())
        self.assertNotIn('(;', http.user_agent())
        self.assertNotIn(';)', http.user_agent())
        self.assertIn('httplib2/', http.user_agent())
        self.assertIn('Python/' + str(sys.version_info[0]), http.user_agent())


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
