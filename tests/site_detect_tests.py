"""Test for site detection."""
#
# (C) Pywikibot team, 2014-2021
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress
from http import HTTPStatus
from urllib.parse import urlparse

import requests.exceptions as requests_exceptions

import pywikibot
from pywikibot.exceptions import ServerError
from pywikibot.site_detect import MWSite
from tests import unittest_print
from tests.aspects import PatchingTestCase, TestCase
from tests.utils import DrySite


class SiteDetectionTestCase(TestCase):

    """Testcase for MediaWiki detection and site object creation."""

    net = True

    def assertSite(self, url: str):
        """
        Assert a MediaWiki site can be loaded from the url.

        :param url: Url of tested site
        :raises AssertionError: Site under url is not MediaWiki powered
        """
        try:
            self.assertIsInstance(MWSite(url), MWSite)
        except (ServerError, requests_exceptions.Timeout) as e:
            self.skipTest(e)

    def assertNoSite(self, url: str):
        """
        Assert a url is not a MediaWiki site.

        :param url: Url of tested site
        :raises AssertionError: Site under url is MediaWiki powered
        """
        with self.assertRaises((AttributeError,
                                RuntimeError,
                                ServerError,
                                requests_exceptions.ConnectionError,
                                requests_exceptions.Timeout,
                                requests_exceptions.TooManyRedirects)) as e:
            MWSite(url)
        unittest_print('\nassertNoSite expected exception:\n{e!r}'
                       .format(e=e.exception))


class StandardVersionSiteTestCase(SiteDetectionTestCase):

    """Test detection of MediaWiki sites."""

    def test_proofwiki(self):
        """Test detection of MediaWiki sites for www.proofwiki.org."""
        self.assertSite('http://www.proofwiki.org/wiki/$1')

    def test_ck_wissen(self):
        """Test detection of MediaWiki sites for www.ck-wissen.de."""
        self.assertSite(
            'http://www.ck-wissen.de/ckwiki/index.php?title=$1')

    def test_citizendium(self):
        """Test detection of MediaWiki sites for en.citizendium.org."""
        self.assertSite('http://en.citizendium.org/wiki/$1')

    def test_wikichristian(self):
        """Test detection of MediaWiki sites for www.wikichristian.org.

        Server that hosts www.wikichristian.org is unreliable - it
        occasionally responding with 500 error (see: T151368).
        """
        self.assertSite('http://www.wikichristian.org/index.php?title=$1')

    def test_wikifur(self):
        """Test detection of MediaWiki sites for en.wikifur.com."""
        self.assertSite('https://en.wikifur.com/wiki/$1')


class NonStandardVersionSiteTestCase(SiteDetectionTestCase):

    """Test non-standard version string sites."""

    def test_gentoo(self):
        """Test detection of MediaWiki sites for wiki.gentoo.org."""
        self.assertSite('https://wiki.gentoo.org/wiki/$1')

    def test_arabeyes(self):
        """Test detection of MediaWiki sites for www.arabeyes.org."""
        self.assertSite('https://www.arabeyes.org/$1')

    def test_tfwiki(self):
        """Test detection of MediaWiki sites for tfwiki.net."""
        self.assertNoSite('http://tfwiki.net/wiki/$1')  # 1.19.5-1+deb7u1


class Pre119SiteTestCase(SiteDetectionTestCase):

    """Test pre 1.19 sites which should be detected as unsupported."""

    def test_hrwiki(self):
        """Test detection of MediaWiki sites for www.hrwiki.org."""
        self.assertNoSite('http://www.hrwiki.org/index.php/$1')  # v 1.15.4

    def test_wikifon(self):
        """Test detection of MediaWiki sites for www.wikifon.org."""
        self.assertNoSite('http://www.wikifon.org/$1')  # v1.11.0

    def test_ecoreality(self):
        """Test detection of MediaWiki sites for www.ecoreality.org.

        api.php is not available. Anyway the wiki is outdated.
        """
        self.assertNoSite('http://www.ecoreality.org/wiki/$1')  # v1.16.2


class PreAPISiteTestCase(SiteDetectionTestCase):

    """Test detection of MediaWiki sites prior to the API."""

    def test_thelemapedia(self):
        """Test detection of MediaWiki sites for www.thelemapedia.org."""
        self.assertNoSite('http://www.thelemapedia.org/index.php/$1')

    def test_werelate(self):
        """Test detection of MediaWiki sites for www.werelate.org."""
        self.assertNoSite('http://www.werelate.org/wiki/$1')

    def test_otterstedt(self):
        """Test detection of MediaWiki sites for www.otterstedt.de."""
        self.assertNoSite('http://www.otterstedt.de/wiki/index.php/$1')

    def test_mozillazine(self):
        """Test detection of MediaWiki sites for kb.mozillazine.org."""
        self.assertNoSite('http://kb.mozillazine.org/$1')


class APIHiddenTestCase(SiteDetectionTestCase):

    """Test MediaWiki sites with a hidden enabled API."""

    def test_wikisophia(self):
        """Test wikisophia.org which has redirect problems.

        /index.php?title=$1 reports 404, however a wiki exists there,
        but the API is also hidden.
        """
        self.assertNoSite('http://wikisophia.org/index.php?title=$1')

    def test_ecoreality(self):
        """Test detection of MediaWiki sites for www.EcoReality.org.

        api.php is not available. HTML looks like it has an API, but redirect
        rules prevent access.
        """
        self.assertNoSite('http://www.EcoReality.org/wiki/$1')


class FailingSiteTestCase(SiteDetectionTestCase):

    """Test detection failure for MediaWiki sites with an API."""

    def test_animutationportal(self):
        """Test detection of MediaWiki sites for wiki.animutationportal.com.

        SSL certificate verification fails.
        """
        self.assertNoSite('http://wiki.animutationportal.com/index.php/$1')


class APIDisabledTestCase(SiteDetectionTestCase):

    """Test MediaWiki sites without an enabled API."""

    def test_linuxquestions(self):
        """Test detection of MediaWiki sites for wiki.linuxquestions.org."""
        self.assertNoSite('http://wiki.linuxquestions.org/wiki/$1')


class NoSiteTestCase(SiteDetectionTestCase):

    """Test detection of non-wiki sites."""

    def test_imdb(self):
        """Test detection of MediaWiki sites for www.imdb.com."""
        self.assertNoSite('http://www.imdb.com/name/nm$1/')

    def test_ecyrd(self):
        """Test detection of MediaWiki sites for www.ecyrd.com."""
        self.assertNoSite('http://www.ecyrd.com/JSPWiki/Wiki.jsp?page=$1')

    def test_tvtropes(self):
        """Test detection of MediaWiki sites for www.tvtropes.org."""
        self.assertNoSite('http://www.tvtropes.org/pmwiki/pmwiki.php/Main/$1')

    def test_c2(self):
        """Test detection of MediaWiki sites for c2.com."""
        self.assertNoSite('http://c2.com/cgi/wiki?$1')

    def test_phabricator(self):
        """Test detection of MediaWiki sites for phabricator.wikimedia.org."""
        self.assertNoSite('https://phabricator.wikimedia.org/$1')

    def test_merriam_webster(self):
        """Test detection of MediaWiki sites for www.merriam-webster.com."""
        self.assertNoSite(
            'http://www.merriam-webster.com/'
            'cgi-bin/dictionary?book=Dictionary&va=$1')

    def test_arxiv(self):
        """Test detection of MediaWiki sites for arxiv.org."""
        self.assertNoSite('http://arxiv.org/abs/$1')


class OfflineSiteTestCase(SiteDetectionTestCase):

    """Test offline sites."""

    def test_opensprints_wiki(self):
        """Test detection of MediaWiki sites for wiki.opensprints.org."""
        self.assertNoSite('http://wiki.opensprints.org/index.php?title=$1')


class OtherSiteTestCase(SiteDetectionTestCase):

    """Test other non-MediaWiki sites."""

    def test_musicbrainz(self):
        """Test http://musicbrainz.org/doc/ which has a page 'api.php'.

        Possible false positive caused by the existence of a page called
        http://musicbrainz.org/doc/api.php.
        """
        self.assertNoSite('http://musicbrainz.org/doc/$1')


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

        return type(str('Response'),
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
