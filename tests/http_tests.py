# -*- coding: utf-8  -*-
"""Tests for http module."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import os
import sys

import requests

import pywikibot

from pywikibot import config2 as config
from pywikibot.comms import http, threadedhttp

from tests import _images_dir
from tests.aspects import unittest, TestCase, DeprecationTestCase
from tests.utils import expected_failure_if

if sys.version_info[0] > 2:
    unicode = str


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

    sites = {
        'omegawiki': {
            'hostname': 'www.omegawiki.org',
        },
        'vikidia': {
            'hostname': 'en.vikidia.org',
        },
    }

    def test_https_cert_error(self):
        """Test http.request fails on invalid omegawiki SSL certificate."""
        self.assertRaises(pywikibot.FatalServerError,
                          http.request,
                          site=None,
                          uri='https://www.omegawiki.org/')

    @expected_failure_if(sys.version_info[0] > 2)  # bug 72236
    def test_https_ignore_cert_error(self):
        """Test http.request ignoring invalid vikidia SSL certificate."""
        # As the connection is cached, the above test will cause
        # subsequent requests to go to the existing, broken, connection.
        # So, this uses a different host, which hopefully hasnt been
        # connected previously by other tests.
        r = http.request(site=None,
                         uri='https://en.vikidia.org/wiki/Main_Page',
                         disable_ssl_certificate_validation=True)
        self.assertIsInstance(r, unicode)
        self.assertIn('<title>Vikidia</title>', r)

    def test_https_cert_invalid(self):
        """Verify vikidia SSL certificate is invalid."""
        try:
            from pyasn1_modules import pem, rfc2459
            from pyasn1.codec.der import decoder
        except ImportError:
            raise unittest.SkipTest('pyasn1 and pyasn1_modules not available.')

        import ssl
        import io

        cert = ssl.get_server_certificate(addr=('en.vikidia.org', 443))
        s = io.StringIO(unicode(cert))
        substrate = pem.readPemFromFile(s)
        cert = decoder.decode(substrate, asn1Spec=rfc2459.Certificate())[0]
        tbs_cert = cert.getComponentByName('tbsCertificate')
        issuer = tbs_cert.getComponentByName('issuer')
        organisation = None
        for rdn in issuer.getComponent():
            for attr in rdn:
                attr_type = attr.getComponentByName('type')
                if attr_type == rfc2459.id_at_organizationName:
                    value, _ = decoder.decode(attr.getComponentByName('value'),
                                              asn1Spec=rfc2459.X520name())
                    organisation = str(value.getComponent())
                    break

        self.assertEqual(organisation, 'TuxFamily.org non-profit organization')


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
        self.assertIn('Python/' + str(sys.version_info[0]), http.user_agent())


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

        with open(os.path.join(_images_dir, 'MP_sounds.png'), 'rb') as f:
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


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
