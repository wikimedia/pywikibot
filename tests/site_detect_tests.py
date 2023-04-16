#!/usr/bin/env python3
"""Test for site detection."""
#
# (C) Pywikibot team, 2014-2023
#
# Distributed under the terms of the MIT license.
#
import os
import unittest
from contextlib import suppress
from http import HTTPStatus
from urllib.parse import urlparse

import requests.exceptions as requests_exceptions

import pywikibot
from pywikibot.exceptions import ClientError, ServerError
from pywikibot.site_detect import MWSite

from tests.aspects import PatchingTestCase, TestCase
from tests.utils import DrySite, skipping


class SiteDetectionTestCase(TestCase):

    """Testcase for MediaWiki detection and site object creation."""

    net = True

    def assertSite(self, url: str):
        """
        Assert a MediaWiki site can be loaded from the url.

        :param url: Url of tested site
        :raises AssertionError: Site under url is not MediaWiki powered
        """
        with skipping(ServerError, requests_exceptions.Timeout):
            self.assertIsInstance(MWSite(url), MWSite)

    def assertNoSite(self, url: str):
        """Assert a url is not a MediaWiki site.

        :param url: Url of tested site
        :raises AssertionError: Site under url is MediaWiki powered
        """
        with self.assertRaises((AttributeError,
                                ClientError,
                                ConnectionError,  # different from requests
                                RuntimeError,
                                ServerError,
                                requests_exceptions.ConnectionError,
                                requests_exceptions.Timeout,
                                requests_exceptions.TooManyRedirects)):
            MWSite(url)


class MediaWikiSiteTestCase(SiteDetectionTestCase):

    """Test detection of MediaWiki sites."""

    standard_version_sites = (
        'http://www.ck-wissen.de/ckwiki/index.php?title=$1',
        'http://en.citizendium.org/wiki/$1',
        # Server that hosts www.wikichristian.org is unreliable - it
        # occasionally responding with 500 error (see: T151368).
        'http://www.wikichristian.org/index.php?title=$1',
    )

    non_standard_version_sites = (
        'https://wiki.gentoo.org/wiki/$1',
        'https://www.arabeyes.org/$1',
    )

    old_version_sites = (
        'http://tfwiki.net/wiki/$1',  # 1.19.5-1+deb7u1
        'http://www.hrwiki.org/index.php/$1',  # v 1.15.4
        'http://www.thelemapedia.org/index.php/$1',
        'http://www.werelate.org/wiki/$1',
        'http://www.otterstedt.de/wiki/index.php/$1',
        'https://en.wikifur.com/wiki/$1',  # 1.23.16
        'http://kb.mozillazine.org/$1'  # 1.26.4
    )

    no_sites = (
        'http://www.imdb.com/name/nm$1/',
        'http://www.ecyrd.com/JSPWiki/Wiki.jsp?page=$1',
        'http://www.tvtropes.org/pmwiki/pmwiki.php/Main/$1',
        'http://c2.com/cgi/wiki?$1',
        'https://phabricator.wikimedia.org/$1',
        'http://www.merriam-webster.com/'
        'cgi-bin/dictionary?book=Dictionary&va=$1',
        'http://arxiv.org/abs/$1',
    )

    failing_sites = [
        ('http://wikisophia.org/index.php?title=$1',
         '/index.php?title=$1 reports 404, '
         'however a wiki exists there, but the API is also hidden'),
        ('http://wiki.animutationportal.com/index.php/$1',
         'SSL certificate verification fails'),
        ('http://wiki.opensprints.org/index.php?title=$1',
         'offline'),
        ('http://musicbrainz.org/doc/$1',
         'Possible false positive caused by the existence of a page called '
         'http://musicbrainz.org/doc/api.php.'),
    ]

    def test_standard_version_sites(self):
        """Test detection of standard MediaWiki sites."""
        for url in self.standard_version_sites:
            with self.subTest(url=urlparse(url).netloc):
                self.assertSite(url)

    def test_proofreadwiki(self):
        """Test detection of proofwiki.org site."""
        if os.getenv('GITHUB_ACTIONS'):
            self.skipTest('Skip test on github due to T331223')
        self.assertSite('http://www.proofwiki.org/wiki/$1')

    def test_non_standard_version_sites(self):
        """Test detection of non standard MediaWiki sites."""
        for url in self.non_standard_version_sites:
            with self.subTest(url=urlparse(url).netloc):
                self.assertSite(url)

    def test_old_version_sites(self):
        """Test detection of old MediaWiki sites."""
        for url in self.old_version_sites:
            with self.subTest(url=urlparse(url).netloc):
                self.assertNoSite(url)

    def test_no_sites(self):
        """Test detection of non-MediaWiki sites."""
        for url in self.no_sites:
            with self.subTest(url=urlparse(url).netloc):
                self.assertNoSite(url)

    def test_failing_sites(self):
        """Test detection of failing MediaWiki sites."""
        for url, reason in self.failing_sites:
            with self.subTest(url=urlparse(url).netloc, reason=reason):
                self.assertNoSite(url)


class PrivateWikiTestCase(PatchingTestCase):

    """Test generate_family_file works for private wikis."""

    net = False

    SCHEME = 'https'
    NETLOC = 'privatewiki.example.com'
    WEBPATH = '/wiki/'
    SCRIPTPATH = '/w'
    APIPATH = SCRIPTPATH + '/api.php'
    USERNAME = 'Private Wiki User'
    VERSION = '1.33.0'
    LANG = 'ike-cans'

    _server = SCHEME + '://' + NETLOC
    _weburl = _server + WEBPATH
    _apiurl = _server + APIPATH
    _generator = 'MediaWiki ' + VERSION

    _responses = {
        # site_detect.MWSite.__init__ first fetches whatever is at
        # the user-supplied URL. We need to return enough data for
        # site_detect.WikiHTMLPageParser to determine the server
        # version and the API URL.
        WEBPATH: ''.join((
            '<meta name="generator" content="', _generator,
            '"/>\n<link rel="EditURI" type="application/rsd+xml" '
            'href="', _apiurl, '?action=rsd"/>')),
        APIPATH: '{"error":{"code":"readapidenied"}}',
    }

    _siteinfo = {
        'generator': _generator,
        'server': _server,
        'scriptpath': SCRIPTPATH,
        'articlepath': WEBPATH.rstrip('/') + '/$1',
        'lang': LANG,
    }

    @PatchingTestCase.patched(pywikibot.site_detect, 'fetch')
    def fetch(self, url, *args, **kwargs):
        """Patched version of pywikibot.site_detect.fetch."""
        parsed_url = urlparse(url)
        self.assertEqual(parsed_url.scheme, self.SCHEME)
        self.assertEqual(parsed_url.netloc, self.NETLOC)
        self.assertIn(parsed_url.path, self._responses)

        return type('Response',
                    (object,),
                    {'status_code': HTTPStatus.OK.value,
                     'text': self._responses[parsed_url.path],
                     'url': url})

    @PatchingTestCase.patched(pywikibot, 'input')
    def input(self, question, *args, **kwargs):
        """Patched version of pywikibot.input."""
        self.assertTrue(question.endswith('username?'))
        return self.USERNAME

    @PatchingTestCase.patched(pywikibot, 'Site')
    def Site(self, code=None, fam=None, user=None, *args, **kwargs):
        """Patched version of pywikibot.Site."""
        self.assertEqual(code, fam.code)
        self.assertEqual(fam.domain, self.NETLOC)
        self.assertEqual(user, self.USERNAME)
        site = DrySite(code, fam, user, *args, **kwargs)
        site._siteinfo._cache.update(
            (key, (value, True))
            for key, value in self._siteinfo.items())
        return site

    def test_T235768_failure(self):
        """Test generate_family_file works for private wikis.

        generate_family_file.FamilyFileGenerator.run() does:
          w = self.Wiki(self.base_url)
          self.wikis[w.lang] = w

        where self.Wiki is pywikibot.site_detect.MWSite.__init__.
        That calls MWSite._parse_post_117() which sets lang, but
        that call's wrapped to log exceptions and then continue
        past them.  In T235768, the code that handles private
        wikis raises an exception that's consumed in that way.
        The value returned to FamilyFileGenerator.run() does not
        have lang set, causing generate_family_file to bomb.
        """
        site = MWSite(self._weburl)
        self.assertIsInstance(site, MWSite)
        self.assertTrue(hasattr(site, 'lang'))
        self.assertEqual(site.lang, self.LANG)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
