#!/usr/bin/env python3
"""Tests for http module."""
#
# (C) Pywikibot team, 2014-2022
#
# Distributed under the terms of the MIT license.
#
import re
import warnings
from contextlib import suppress
from http import HTTPStatus
from unittest.mock import patch

import requests

import pywikibot
from pywikibot import config
from pywikibot.comms import http
from pywikibot.exceptions import FatalServerError, Server504Error
from pywikibot.tools import PYTHON_VERSION, suppress_warnings
from tests import join_images_path
from tests.aspects import HttpbinTestCase, TestCase, require_modules, unittest


class HttpTestCase(TestCase):

    """Tests for http module."""

    sites = {
        'www-wp': {
            'hostname': 'www.wikipedia.org',
        },
    }

    def test_fetch(self):
        """Test http.fetch using http://www.wikipedia.org/."""
        r = http.fetch('http://www.wikipedia.org/')
        self.assertIsInstance(r, requests.Response)
        self.assertEqual(r.status_code, HTTPStatus.OK.value)
        self.assertIn('<html lang="en"', r.text)
        self.assertIsInstance(r.text, str)
        self.assertIsInstance(r.content, bytes)


class TestGetAuthenticationConfig(TestCase):

    """Test http.get_authentication."""

    net = False

    def setUp(self):
        """Set up test by configuring config.authenticate."""
        super().setUp()
        self._authenticate = config.authenticate
        config.authenticate = {
            'zh.wikipedia.beta.wmflabs.org': ('1', '2'),
            '*.wikipedia.beta.wmflabs.org': ('3', '4', '3', '4'),
            '*.beta.wmflabs.org': ('5', '6'),
            '*.wmflabs.org': ('7', '8', '8'),
        }

    def tearDown(self):
        """Tear down test by resetting config.authenticate."""
        super().tearDown()
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
        with suppress_warnings(
            r'config.authenticate\["\*.wmflabs.org"] has invalid value.',
            UserWarning,
        ):
            for url, auth in pairs.items():
                self.assertEqual(http.get_authentication(url), auth)


class HttpsCertificateTestCase(TestCase):

    """HTTPS certificate test."""

    CERT_VERIFY_FAILED_RE = 'certificate verify failed'
    hostname = 'testssl-expire-r2i2.disig.sk'

    def test_https_cert_error(self):
        """Test if http.fetch respects disabled ssl certificate validation."""
        with self.assertRaisesRegex(
                FatalServerError,
                self.CERT_VERIFY_FAILED_RE):
            http.fetch('https://testssl-expire-r2i2.disig.sk/index.en.html')
        http.session.close()  # clear the connection

        with warnings.catch_warnings(record=True) as warning_log:
            response = http.fetch(
                'https://testssl-expire-r2i2.disig.sk/index.en.html',
                verify=False)
        self.assertIsInstance(response.text, str)
        self.assertTrue(re.search(r'<title>.*</title>', response.text))
        http.session.close()  # clear the connection

        # Verify that it now fails again
        with self.assertRaisesRegex(
                FatalServerError,
                self.CERT_VERIFY_FAILED_RE):
            http.fetch('https://testssl-expire-r2i2.disig.sk/index.en.html')
        http.session.close()  # clear the connection

        # Verify that the warning occurred
        self.assertIn('InsecureRequestWarning',
                      [w.category.__name__ for w in warning_log])


class TestHttpStatus(HttpbinTestCase):

    """Test HTTP status code handling and errors."""

    sites = {
        'httpbin': {
            'hostname': 'httpbin.org',
        },
        'enwp': {
            'hostname': 'en.wikipedia.org',
        },
        'wikia': {
            'hostname': 'en.wikia.com',
        },
    }

    def test_http_504(self):
        """Test that a HTTP 504 raises the correct exception."""
        with self.assertRaisesRegex(
                Server504Error,
                r'Server ([^\:]+|[^\:]+:[0-9]+)'
                r' timed out'):
            http.fetch(self.get_httpbin_url('/status/504'))

    def test_server_not_found(self):
        """Test server not found exception."""
        with self.assertRaisesRegex(
                ConnectionError,
                'Max retries exceeded with url: /w/api.php'):
            http.fetch('http://ru-sib.wikipedia.org/w/api.php',
                       default_error_handling=True)

    def test_invalid_scheme(self):
        """Test invalid scheme."""
        # A InvalidSchema is raised within requests
        with self.assertRaisesRegex(
                requests.exceptions.InvalidSchema,
                "No connection adapters were found for u?'invalid://url'"):
            http.fetch('invalid://url')

    def test_follow_redirects(self):
        """Test follow 301 redirects correctly."""
        # The following will redirect from ' ' -> '_', and maybe to https://
        r = http.fetch('http://en.wikipedia.org/wiki/Main%20Page')
        self.assertEqual(r.status_code, HTTPStatus.OK.value)
        self.assertIsNotNone(r.history)
        self.assertIn('//en.wikipedia.org/wiki/Main_Page', r.url)

        r = http.fetch('http://en.wikia.com')
        self.assertEqual(r.status_code, HTTPStatus.OK.value)
        self.assertEqual(r.url,
                         'https://community.fandom.com/wiki/Community_Central')


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

        self.assertEqual('Pywikibot/' + pywikibot.__version__,
                         http.user_agent(format_string='{pwb}'))
        self.assertNotIn(' ', http.user_agent(format_string=' {pwb} '))

        self.assertIn('Pywikibot/' + pywikibot.__version__,
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
        self.assertEqual('%E2%81%82', http.user_agent_username('⁂'))


class DefaultUserAgentTestCase(TestCase):

    """User agent formatting tests using the default config format string."""

    net = False

    def setUp(self):
        """Set up unit test."""
        super().setUp()
        self.orig_format = config.user_agent_format
        config.user_agent_format = ('{script_product} ({script_comments}) '
                                    '{pwb} ({revision}) {http_backend} '
                                    '{python}')

    def tearDown(self):
        """Tear down unit test."""
        super().tearDown()
        config.user_agent_format = self.orig_format

    def test_default_user_agent(self):
        """Config defined format string test."""
        self.assertTrue(http.user_agent().startswith(
            pywikibot.calledModuleName()))
        self.assertIn('Pywikibot/' + pywikibot.__version__, http.user_agent())
        self.assertNotIn('  ', http.user_agent())
        self.assertNotIn('()', http.user_agent())
        self.assertNotIn('(;', http.user_agent())
        self.assertNotIn(';)', http.user_agent())
        self.assertIn('requests/', http.user_agent())
        self.assertIn('Python/' + str(PYTHON_VERSION[0]), http.user_agent())


class LiveFakeUserAgentTestCase(HttpbinTestCase):

    """Test the usage of fake user agent."""

    def setUp(self):
        """Set up the unit test."""
        self.orig_fake_user_agent_exceptions = (
            config.fake_user_agent_exceptions)
        super().setUp()

    def tearDown(self):
        """Tear down unit test."""
        config.fake_user_agent_exceptions = (
            self.orig_fake_user_agent_exceptions)
        super().tearDown()

    def _test_fetch_use_fake_user_agent(self):
        """Test `use_fake_user_agent` argument of http.fetch."""
        # Existing headers
        r = http.fetch(
            self.get_httpbin_url('/status/200'),
            headers={'user-agent': 'EXISTING'})
        self.assertEqual(r.request.headers['user-agent'], 'EXISTING')

        # Argument value changes
        r = http.fetch(self.get_httpbin_url('/status/200'),
                       use_fake_user_agent=True)
        self.assertNotEqual(r.request.headers['user-agent'], http.user_agent())
        r = http.fetch(self.get_httpbin_url('/status/200'),
                       use_fake_user_agent=False)
        self.assertEqual(r.request.headers['user-agent'], http.user_agent())
        r = http.fetch(
            self.get_httpbin_url('/status/200'),
            use_fake_user_agent='ARBITRARY')
        self.assertEqual(r.request.headers['user-agent'], 'ARBITRARY')

        # Empty value
        with self.assertRaisesRegex(
                ValueError,
                'Invalid parameter: use_fake_user_agent'):
            http.fetch(self.get_httpbin_url('/status/200'),
                       use_fake_user_agent='')

        # Parameter wrongly set to None
        with self.assertRaisesRegex(
                ValueError,
                'Invalid parameter: use_fake_user_agent'):
            http.fetch(self.get_httpbin_url('/status/200'),
                       use_fake_user_agent=None)

        # Manually overridden domains
        config.fake_user_agent_exceptions = {
            self.get_httpbin_hostname(): 'OVERRIDDEN'}
        r = http.fetch(
            self.get_httpbin_url('/status/200'), use_fake_user_agent=False)
        self.assertEqual(r.request.headers['user-agent'], 'OVERRIDDEN')

    @require_modules('fake_useragent')
    def test_fetch_with_fake_useragent(self):
        """Test method with fake_useragent module."""
        self._test_fetch_use_fake_user_agent()


class CharsetTestCase(TestCase):

    """Test that HttpRequest correct handles the charsets given."""

    CODEC_CANT_DECODE_RE = "codec can't decode byte"
    net = False

    STR = 'äöü'
    LATIN1_BYTES = STR.encode('latin1')
    UTF8_BYTES = STR.encode('utf8')

    @staticmethod
    def _create_response(headers=None, data=UTF8_BYTES):
        """Helper method."""
        resp = requests.Response()
        resp.request = requests.Request()
        if headers is not None:
            resp.headers = headers
        else:
            resp.headers = {'content-type': 'charset=utf-8'}
        resp._content = data[:]
        return resp

    def test_no_content_type(self):
        """Test decoding without content-type (and then no charset)."""
        resp = CharsetTestCase._create_response(
            headers={},
            data=CharsetTestCase.LATIN1_BYTES)
        resp.encoding = http._decide_encoding(resp)
        self.assertEqual('latin1', resp.encoding)
        self.assertEqual(resp.content, CharsetTestCase.LATIN1_BYTES)
        self.assertEqual(resp.text, CharsetTestCase.STR)

    def test_no_charset(self):
        """Test decoding without explicit charset."""
        resp = CharsetTestCase._create_response(
            headers={'content-type': ''},
            data=CharsetTestCase.LATIN1_BYTES)
        resp.encoding = http._decide_encoding(resp)
        self.assertEqual('latin1', resp.encoding)
        self.assertEqual(resp.content, CharsetTestCase.LATIN1_BYTES)
        self.assertEqual(resp.text, CharsetTestCase.STR)

    def test_content_type_application_json_without_charset(self):
        """Test decoding without explicit charset but JSON content."""
        resp = CharsetTestCase._create_response(
            headers={'content-type': 'application/json'},
            data=CharsetTestCase.UTF8_BYTES)
        resp.encoding = http._decide_encoding(resp)
        self.assertEqual('utf-8', resp.encoding)

    def test_content_type_sparql_json_without_charset(self):
        """Test decoding without explicit charset but JSON content."""
        resp = CharsetTestCase._create_response(
            headers={'content-type': 'application/sparql-results+json'},
            data=CharsetTestCase.UTF8_BYTES)
        resp.encoding = http._decide_encoding(resp)
        self.assertEqual('utf-8', resp.encoding)

    def test_content_type_xml(self):
        """Test xml content with encoding given in content."""
        tests = [
            ('Test decoding without explicit charset but xml content',
             self.UTF8_BYTES, 'utf-8'),

            ('Test xml content with utf-8 encoding given in content',
             b'<?xml version="1.0" encoding="UTF-8"?>', 'UTF-8'),

            ('Test xml content with utf-8 encoding given in content',
             b'<?xml version="1.0" encoding="UTF-8" someparam="ignored"?>',
             'UTF-8'),

            ('Test xml content with latin1 encoding given in content',
             b"<?xml version='1.0' encoding='latin1'?>", 'latin1')
        ]
        for msg, data, result in tests:
            with self.subTest(msg=msg):
                resp = CharsetTestCase._create_response(
                    headers={'content-type': 'application/xml'}, data=data)
                resp.encoding = http._decide_encoding(resp)
                self.assertEqual(resp.encoding, result)

    def test_charset_not_last(self):
        """Test charset not last part of content-type header."""
        resp = CharsetTestCase._create_response(
            headers={
                'content-type': (
                    'text/html; charset=utf-8; profile='
                    '"https://www.mediawiki.org/wiki/Specs/HTML/2.4.0"'
                )
            },
            data=CharsetTestCase.UTF8_BYTES)
        resp.encoding = http._decide_encoding(resp)
        self.assertEqual('utf-8', resp.encoding)

    def test_server_charset(self):
        """Test decoding with server explicit charset."""
        resp = CharsetTestCase._create_response()
        resp.encoding = http._decide_encoding(resp)
        self.assertEqual('utf-8', resp.encoding)
        self.assertEqual(resp.content, CharsetTestCase.UTF8_BYTES)
        self.assertEqual(resp.text, CharsetTestCase.STR)

    def test_same_charset(self):
        """Test decoding with explicit and equal charsets."""
        resp = CharsetTestCase._create_response()
        resp.encoding = http._decide_encoding(resp, 'utf-8')
        self.assertEqual('utf-8', resp.encoding)
        self.assertEqual(resp.content, CharsetTestCase.UTF8_BYTES)
        self.assertEqual(resp.text, CharsetTestCase.STR)

    def test_header_charset(self):
        """Test decoding with different charsets and valid header charset."""
        resp = CharsetTestCase._create_response()
        resp.encoding = http._decide_encoding(resp, 'latin1')
        # Ignore WARNING: Encoding "latin1" requested but "utf-8" received
        with patch('pywikibot.warning'):
            self.assertEqual('utf-8', resp.encoding)
        self.assertEqual(resp.content, CharsetTestCase.UTF8_BYTES)
        self.assertEqual(resp.text, CharsetTestCase.STR)

    def test_code_charset(self):
        """Test decoding with different charsets and invalid header charset."""
        resp = CharsetTestCase._create_response(
            data=CharsetTestCase.LATIN1_BYTES)
        resp.encoding = http._decide_encoding(resp, 'latin1')
        # Ignore WARNING: Encoding "latin1" requested but "utf-8" received
        with patch('pywikibot.warning'):
            self.assertEqual('latin1', resp.encoding)
        self.assertEqual(resp.content, CharsetTestCase.LATIN1_BYTES)
        self.assertEqual(resp.text, CharsetTestCase.STR)

    def test_invalid_charset(self):
        """Test decoding with different and invalid charsets."""
        invalid_charsets = ('utf16', 'win-1251')
        for charset in invalid_charsets:
            with self.subTest(charset=charset):
                resp = CharsetTestCase._create_response(
                    data=CharsetTestCase.LATIN1_BYTES)

                with patch('pywikibot.warning'):  # Ignore WARNING:
                    resp.encoding = http._decide_encoding(resp, charset)
                self.assertIsNone(resp.encoding)
                self.assertIsNotNone(resp.apparent_encoding)
                self.assertEqual(resp.content, CharsetTestCase.LATIN1_BYTES)

                # test Response.apparent_encoding
                self.assertEqual(resp.text, str(resp.content,
                                                resp.apparent_encoding,
                                                errors='replace'))

    def test_get_charset_from_content_type(self):
        """Test get_charset_from_content_type function."""
        self.assertEqual(
            http.get_charset_from_content_type('charset="cp-1251"'), 'cp1251')
        self.assertEqual(
            http.get_charset_from_content_type('charset="win-1251"'), 'cp1251')
        self.assertEqual(
            http.get_charset_from_content_type('charset="ru-win1251"'),
            'cp1251')


class BinaryTestCase(TestCase):

    """Get binary file using requests and pywikibot."""

    hostname = 'upload.wikimedia.org'
    url = 'https://upload.wikimedia.org/wikipedia/commons/f/fc/MP_sounds.png'

    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        super().setUpClass()

        with open(join_images_path('MP_sounds.png'), 'rb') as f:
            cls.png = f.read()

    def test_requests(self):
        """Test with requests, underlying package."""
        with requests.Session() as s:
            r = s.get(self.url)

            self.assertEqual(r.headers['content-type'], 'image/png')
            self.assertEqual(r.content, self.png)

    def test_http(self):
        """Test with http, standard http interface for pywikibot."""
        r = http.fetch(self.url)

        self.assertEqual(r.headers['content-type'], 'image/png')
        self.assertEqual(r.content, self.png)


class QueryStringParamsTestCase(HttpbinTestCase):

    """
    Test the query string parameter of request methods.

    The /get endpoint of httpbin returns JSON that can include an
    'args' key with urldecoded query string parameters.
    """

    def setUp(self):
        """Set up tests."""
        super().setUp()
        self.url = self.get_httpbin_url('/get')

    def test_no_params(self):
        """Test fetch method with no parameters."""
        r = http.fetch(self.url, params={})

        fail_status = HTTPStatus.SERVICE_UNAVAILABLE
        if r.status_code == fail_status:  # T203637
            self.skipTest('{status.value}: {status.description} for {url}'
                          .format(status=fail_status, url=self.url))

        self.assertEqual(r.status_code, HTTPStatus.OK)
        self.assertEqual(r.json()['args'], {})

    def test_unencoded_params(self):
        """
        Test fetch method with unencoded parameters to be encoded internally.

        HTTPBin returns the args in their urldecoded form, so what we put in
        should be the same as what we get out.
        """
        r = http.fetch(self.url, params={'fish&chips': 'delicious'})

        fail_status = HTTPStatus.SERVICE_UNAVAILABLE
        if r.status_code == fail_status:  # T203637
            self.skipTest('{status.value}: {status.description} for {url}'
                          .format(status=fail_status, url=self.url))

        self.assertEqual(r.status_code, HTTPStatus.OK)
        self.assertEqual(r.json()['args'], {'fish&chips': 'delicious'})

    def test_encoded_params(self):
        """
        Test fetch method with encoded parameters to be re-encoded internally.

        HTTPBin returns the args in their urldecoded form, so what we put in
        should be the same as what we get out.
        """
        r = http.fetch(self.url, params={'fish%26chips': 'delicious'})

        fail_status = HTTPStatus.SERVICE_UNAVAILABLE
        if r.status_code == fail_status:  # T203637
            self.skipTest('{status.value}: {status.description} for {url}'
                          .format(status=fail_status, url=self.url))

        self.assertEqual(r.status_code, HTTPStatus.OK)
        self.assertEqual(r.json()['args'], {'fish%26chips': 'delicious'})


class DataBodyParameterTestCase(HttpbinTestCase):
    """Test data and body params of fetch/request methods are equivalent."""

    maxDiff = None

    def test_fetch(self):
        """Test that using the data and body params produce same results."""
        tracker = (
            'X-Amzn-Trace-Id', 'X-B3-Parentspanid', 'X-B3-Spanid',
            'X-B3-Traceid', 'X-Forwarded-Client-Cert',
        )
        r_data_request = http.fetch(self.get_httpbin_url('/post'),
                                    method='POST',
                                    data={'fish&chips': 'delicious'})
        r_body_request = http.fetch(self.get_httpbin_url('/post'),
                                    method='POST',
                                    data={'fish&chips': 'delicious'})

        r_data = r_data_request.json()
        r_body = r_body_request.json()

        # remove tracker ids if present (T243662, T255862)
        for tracker_id in tracker:
            r_data['headers'].pop(tracker_id, None)
            r_body['headers'].pop(tracker_id, None)

        self.assertEqual(r_data, r_body)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
