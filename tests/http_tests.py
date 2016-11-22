# -*- coding: utf-8 -*-
"""Tests for http module."""
#
# (C) Pywikibot team, 2014-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import re
import warnings

import requests

import pywikibot

from pywikibot import config2 as config
from pywikibot.comms import http, threadedhttp
from pywikibot.tools import (
    PYTHON_VERSION,
    UnicodeType as unicode,
)

from tests import join_images_path
from tests.aspects import unittest, TestCase, DeprecationTestCase


class HttpTestCase(TestCase):

    """Tests for http module."""

    sites = {
        'www-wp': {
            'hostname': 'www.wikipedia.org',
        },
    }

    def test_async(self):
        """Test http._enqueue using http://www.wikipedia.org/."""
        r = http._enqueue('http://www.wikipedia.org/')
        self.assertIsInstance(r, threadedhttp.HttpRequest)
        self.assertEqual(r.status, 200)
        self.assertIn('<html lang="mul"', r.content)
        self.assertIsInstance(r.content, unicode)
        self.assertIsInstance(r.raw, bytes)

    def test_fetch(self):
        """Test http.fetch using http://www.wikipedia.org/."""
        r = http.fetch('http://www.wikipedia.org/')
        self.assertIsInstance(r, threadedhttp.HttpRequest)
        self.assertEqual(r.status, 200)
        self.assertIn('<html lang="mul"', r.content)
        self.assertIsInstance(r.content, unicode)
        self.assertIsInstance(r.raw, bytes)


class HttpRequestURI(DeprecationTestCase):

    """Tests using http.request without a site."""

    sites = {
        'www-wp': {
            'hostname': 'www.wikipedia.org',
        },
        'www-wq': {
            'hostname': 'www.wikiquote.org',
        },
    }

    def test_http(self):
        """Test http.request using http://www.wikipedia.org/."""
        r = http.request(site=None, uri='http://www.wikipedia.org/')
        self.assertIsInstance(r, unicode)
        self.assertIn('<html lang="mul"', r)
        self.assertOneDeprecationParts(
            'Invoking http.request without argument site', 'http.fetch()')

    def test_https(self):
        """Test http.request using https://www.wikiquote.org/."""
        r = http.request(site=None, uri='https://www.wikiquote.org/')
        self.assertIsInstance(r, unicode)
        self.assertIn('<html lang="mul"', r)
        self.assertOneDeprecationParts(
            'Invoking http.request without argument site', 'http.fetch()')


class TestGetAuthenticationConfig(TestCase):

    """Test http.get_authentication."""

    net = False

    def setUp(self):
        """Set up test by configuring config.authenticate."""
        self._authenticate = config.authenticate
        config.authenticate = {
            'zh.wikipedia.beta.wmflabs.org': ('1', '2'),
            '*.wikipedia.beta.wmflabs.org': ('3', '4', '3', '4'),
            '*.beta.wmflabs.org': ('5', '6'),
            '*.wmflabs.org': ('7', '8', '8'),
        }

    def tearDown(self):
        """Tear down test by resetting config.authenticate."""
        config.authenticate = self._authenticate

    def test_url_based_authentication(self):
        """Test url-based authentication info."""
        pairs = {
            'https://zh.wikipedia.beta.wmflabs.org': ('1', '2'),
            'https://en.wikipedia.beta.wmflabs.org': ('3', '4', '3', '4'),
            'https://wiki.beta.wmflabs.org': ('5', '6'),
            'https://beta.wmflabs.org': None,
            'https://wmflabs.org': None,
            'https://www.wikiquote.org/': None,
        }
        for url, auth in pairs.items():
            self.assertEqual(http.get_authentication(url), auth)


class HttpsCertificateTestCase(TestCase):

    """HTTPS certificate test."""

    hostname = 'testssl-expire-r2i2.disig.sk'

    def test_https_cert_error(self):
        """Test if http.fetch respects disable_ssl_certificate_validation."""
        self.assertRaises(pywikibot.FatalServerError,
                          http.fetch,
                          uri='https://testssl-expire-r2i2.disig.sk/index.en.html')
        http.session.close()  # clear the connection

        with warnings.catch_warnings(record=True) as warning_log:
            response = http.fetch(
                uri='https://testssl-expire-r2i2.disig.sk/index.en.html',
                disable_ssl_certificate_validation=True)
        r = response.content
        self.assertIsInstance(r, unicode)
        self.assertTrue(re.search(r'<title>.*</title>', r))
        http.session.close()  # clear the connection

        # Verify that it now fails again
        self.assertRaises(pywikibot.FatalServerError,
                          http.fetch,
                          uri='https://testssl-expire-r2i2.disig.sk/index.en.html')
        http.session.close()  # clear the connection

        # Verify that the warning occurred
        self.assertEqual(len(warning_log), 1)
        self.assertEqual(warning_log[0].category.__name__,
                         'InsecureRequestWarning')


class TestHttpStatus(TestCase):

    """Test HTTP status code handling and errors."""

    sites = {
        'httpbin': {
            'hostname': 'httpbin.org',
        },
        'enwp': {
            'hostname': 'en.wikipedia.org',
        },
        'gandi': {
            'hostname': 'www.gandi.eu',
        },
    }

    def test_http_504(self):
        """Test that a HTTP 504 raises the correct exception."""
        self.assertRaises(pywikibot.Server504Error,
                          http.fetch,
                          uri='http://httpbin.org/status/504')

    def test_server_not_found(self):
        """Test server not found exception."""
        self.assertRaises(requests.exceptions.ConnectionError,
                          http.fetch,
                          uri='http://ru-sib.wikipedia.org/w/api.php',
                          default_error_handling=True)

    def test_invalid_scheme(self):
        """Test invalid scheme."""
        # A InvalidSchema is raised within requests
        self.assertRaises(requests.exceptions.InvalidSchema,
                          http.fetch,
                          uri='invalid://url')

    def test_follow_redirects(self):
        """Test follow 301 redirects correctly."""
        # The following will redirect from ' ' -> '_', and maybe to https://
        r = http.fetch(uri='http://en.wikipedia.org/wiki/Main%20Page')
        self.assertEqual(r.status, 200)
        self.assertIsNotNone(r.data.history)
        self.assertIn('//en.wikipedia.org/wiki/Main_Page',
                      r.data.url)

        r = http.fetch(uri='http://www.gandi.eu')
        self.assertEqual(r.status, 200)
        self.assertEqual(r.data.url,
                         'http://www.gandi.net')


class UserAgentTestCase(TestCase):

    """User agent formatting tests using a format string."""

    net = False

    def test_user_agent(self):
        """Test http.user_agent function."""
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
        """Test http.user_agent_username function."""
        self.assertEqual('%25', http.user_agent_username('%'))
        self.assertEqual('%2525', http.user_agent_username('%25'))
        self.assertEqual(';', http.user_agent_username(';'))
        self.assertEqual('-', http.user_agent_username('-'))
        self.assertEqual('.', http.user_agent_username('.'))
        self.assertEqual("'", http.user_agent_username("'"))
        self.assertEqual('foo_bar', http.user_agent_username('foo bar'))

        self.assertEqual('%E2%81%82', http.user_agent_username(u'⁂'))

    def test_version(self):
        """Test http.user_agent {version}."""
        old_cache = pywikibot.version.cache
        try:
            pywikibot.version.cache = None
            http.user_agent(format_string='version does not appear')
            self.assertIsNone(pywikibot.version.cache)
            pywikibot.version.cache = {'rev': 'dummy'}
            self.assertEqual(http.user_agent(format_string='{version} does appear'),
                             'dummy does appear')
            self.assertIsNotNone(pywikibot.version.cache)
        finally:
            pywikibot.version.cache = old_cache


class DefaultUserAgentTestCase(TestCase):

    """User agent formatting tests using the default config format string."""

    net = False

    def setUp(self):
        """Set up unit test."""
        self.orig_format = config.user_agent_format
        config.user_agent_format = ('{script_product} ({script_comments}) {pwb} '
                                    '({revision}) {http_backend} {python}')

    def tearDown(self):
        """Tear down unit test."""
        config.user_agent_format = self.orig_format

    def test_default_user_agent(self):
        """Config defined format string test."""
        self.assertTrue(http.user_agent().startswith(
            pywikibot.calledModuleName()))
        self.assertIn('Pywikibot/' + pywikibot.__release__, http.user_agent())
        self.assertNotIn('  ', http.user_agent())
        self.assertNotIn('()', http.user_agent())
        self.assertNotIn('(;', http.user_agent())
        self.assertNotIn(';)', http.user_agent())
        self.assertIn('requests/', http.user_agent())
        self.assertIn('Python/' + str(PYTHON_VERSION[0]), http.user_agent())


class CharsetTestCase(TestCase):

    """Test that HttpRequest correct handles the charsets given."""

    net = False

    STR = u'äöü'
    LATIN1_BYTES = STR.encode('latin1')
    UTF8_BYTES = STR.encode('utf8')

    @staticmethod
    def _create_request(charset=None, data=UTF8_BYTES):
        """Helper method."""
        req = threadedhttp.HttpRequest('', charset=charset)
        resp = requests.Response()
        resp.headers = {'content-type': 'charset=utf-8'}
        resp._content = data[:]
        req._data = resp
        return req

    def test_no_charset(self):
        """Test decoding without explicit charset."""
        req = threadedhttp.HttpRequest('')
        resp = requests.Response()
        resp.headers = {'content-type': ''}
        resp._content = CharsetTestCase.LATIN1_BYTES[:]
        req._data = resp
        self.assertIsNone(req.charset)
        self.assertEqual('latin1', req.encoding)
        self.assertEqual(req.raw, CharsetTestCase.LATIN1_BYTES)
        self.assertEqual(req.content, CharsetTestCase.STR)

    def test_content_type_application_json_without_charset(self):
        """Test decoding without explicit charset but JSON content."""
        req = CharsetTestCase._create_request()
        resp = requests.Response()
        req._data = resp
        resp._content = CharsetTestCase.UTF8_BYTES[:]
        resp.headers = {'content-type': 'application/json'}
        self.assertIsNone(req.charset)
        self.assertEqual('utf-8', req.encoding)

    def test_content_type_sparql_json_without_charset(self):
        """Test decoding without explicit charset but JSON content."""
        req = CharsetTestCase._create_request()
        resp = requests.Response()
        req._data = resp
        resp._content = CharsetTestCase.UTF8_BYTES[:]
        resp.headers = {'content-type': 'application/sparql-results+json'}
        self.assertIsNone(req.charset)
        self.assertEqual('utf-8', req.encoding)

    def test_server_charset(self):
        """Test decoding with server explicit charset."""
        req = CharsetTestCase._create_request()
        self.assertIsNone(req.charset)
        self.assertEqual('utf-8', req.encoding)
        self.assertEqual(req.raw, CharsetTestCase.UTF8_BYTES)
        self.assertEqual(req.content, CharsetTestCase.STR)

    def test_same_charset(self):
        """Test decoding with explicit and equal charsets."""
        req = CharsetTestCase._create_request('utf-8')
        self.assertEqual('utf-8', req.charset)
        self.assertEqual('utf-8', req.encoding)
        self.assertEqual(req.raw, CharsetTestCase.UTF8_BYTES)
        self.assertEqual(req.content, CharsetTestCase.STR)

    def test_header_charset(self):
        """Test decoding with different charsets and valid header charset."""
        req = CharsetTestCase._create_request('latin1')
        self.assertEqual('latin1', req.charset)
        self.assertEqual('utf-8', req.encoding)
        self.assertEqual(req.raw, CharsetTestCase.UTF8_BYTES)
        self.assertEqual(req.content, CharsetTestCase.STR)

    def test_code_charset(self):
        """Test decoding with different charsets and invalid header charset."""
        req = CharsetTestCase._create_request('latin1',
                                              CharsetTestCase.LATIN1_BYTES)
        self.assertEqual('latin1', req.charset)
        self.assertEqual('latin1', req.encoding)
        self.assertEqual(req.raw, CharsetTestCase.LATIN1_BYTES)
        self.assertEqual(req.content, CharsetTestCase.STR)

    def test_invalid_charset(self):
        """Test decoding with different and invalid charsets."""
        req = CharsetTestCase._create_request('utf16',
                                              CharsetTestCase.LATIN1_BYTES)
        self.assertEqual('utf16', req.charset)
        self.assertRaises(UnicodeDecodeError, lambda: req.encoding)
        self.assertEqual(req.raw, CharsetTestCase.LATIN1_BYTES)
        self.assertRaises(UnicodeDecodeError, lambda: req.content)


class BinaryTestCase(TestCase):

    """Get binary file using requests and pywikibot."""

    hostname = 'upload.wikimedia.org'
    url = 'https://upload.wikimedia.org/wikipedia/commons/f/fc/MP_sounds.png'

    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        super(BinaryTestCase, cls).setUpClass()

        with open(join_images_path('MP_sounds.png'), 'rb') as f:
            cls.png = f.read()

    def test_requests(self):
        """Test with requests, underlying package."""
        s = requests.Session()
        r = s.get(self.url)

        self.assertEqual(r.headers['content-type'], 'image/png')
        self.assertEqual(r.content, self.png)

        s.close()

    def test_http(self):
        """Test with http, standard http interface for pywikibot."""
        r = http.fetch(uri=self.url)

        self.assertEqual(r.raw, self.png)


class TestDeprecatedGlobalCookieJar(DeprecationTestCase):

    """Test usage of deprecated pywikibot.cookie_jar."""

    net = False

    def test_cookie_jar(self):
        """Test pywikibot.cookie_jar is deprecated."""
        # Accessing from the main package should be deprecated.
        main_module_cookie_jar = pywikibot.cookie_jar

        self.assertOneDeprecationParts('pywikibot.cookie_jar',
                                       'pywikibot.comms.http.cookie_jar')

        self.assertIs(main_module_cookie_jar, http.cookie_jar)


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
