# -*- coding: utf-8  -*-
"""Test for site detection."""
#
# (C) Pywikibot team, 2014-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

from requests.exceptions import Timeout

from pywikibot.site_detect import MWSite
from pywikibot.tools import PY2

from tests.aspects import unittest, TestCase

if not PY2:
    basestring = (str,)


class TestWikiSiteDetection(TestCase):

    """Test Case for MediaWiki detection and site object creation."""

    family = 'meta'
    code = 'meta'
    net = True

    def setUp(self):
        """Set up test."""
        self.skips = {}
        self.failures = {}
        self.errors = {}
        self.passes = {}
        self.all = []
        super(TestWikiSiteDetection, self).setUp()

    def tearDown(self):
        """Tear Down test."""
        def norm(url):
            res = None
            typ = -1
            for pos, result in enumerate([self.passes, self.errors,
                                          self.failures, self.skips]):
                if url in result:
                    assert res is None
                    res = result[url]
                    typ = pos
            if res is None:
                typ = len(PREFIXES) - 1
                res = 'Missing'
            assert 0 <= pos < len(PREFIXES)
            return typ, url, res

        super(TestWikiSiteDetection, self).tearDown()
        print('Out of %d sites, %d tests passed, %d tests failed, '
              '%d tests skiped and %d tests raised an error'
              % (len(self.all), len(self.passes), len(self.failures),
                 len(self.skips), len(self.errors))
              )

        PREFIXES = ['PASS', 'ERR ', 'FAIL', 'SKIP', 'MISS']

        sorted_all = sorted((norm(url) for url in self.all),
                            key=lambda item: item[0])
        width = max(len(item[1]) for item in sorted_all)
        print('Results:\n' + '\n'.join(
            '{0} {1:{3}} : {2}'.format(PREFIXES[i[0]], i[1], i[2], width)
            for i in sorted_all))

    def _wiki_detection(self, url, result):
        """Perform one load test."""
        self.all += [url]
        try:
            site = MWSite(url)
        except Timeout as e:
            self.skips[url] = e
            return
        except Exception as e:
            print('failure {0} on {1}: {2}'.format(
                url, type(e), e))
            self.errors[url] = e
            return
        try:
            if result is None:
                self.assertIsNone(site)
            else:
                self.assertIsInstance(site, result)
            self.passes[url] = result
        except AssertionError as error:
            self.failures[url] = error

    def assertSite(self, url):
        """Assert a MediaWiki site can be loaded from the url."""
        self._wiki_detection(url, MWSite)

    def assertNoSite(self, url):
        """Assert a url is not a MediaWiki site."""
        self._wiki_detection(url, None)

    def assertAllPass(self):
        """Assert that all urls were detected as a MediaWiki site."""
        self.assertEqual(len(self.passes), len(self.all) - len(self.skips))
        self.assertEqual(len(self.failures), 0)
        self.assertEqual(len(self.errors), 0)

    def assertAllError(self):
        """Assert that all urls were not detected as a MediaWiki site."""
        self.assertEqual(len(self.passes), 0)
        self.assertEqual(len(self.failures), 0)
        self.assertEqual(len(self.errors), len(self.all) - len(self.skips))

    def test_IWM(self):
        """Test the load_site method for MW sites on the IWM list."""
        data = self.get_site().siteinfo['interwikimap']
        for item in data:
            if 'local' not in item:
                url = item['url']
                self.all += [url]
                try:
                    site = MWSite(url)
                except Exception as error:
                    print('failed to load ' + url)
                    self.errors[url] = error
                    continue
                if type(site) is MWSite:
                    try:
                        version = site.version
                    except Exception as error:
                        print('failed to get version of ' + url)
                        self.errors[url] = error
                    else:
                        try:
                            self.assertIsInstance(version, basestring)
                            self.assertRegex(version, r'^\d\.\d+.*')
                            self.passes[url] = site
                        except AssertionError as error:
                            print('failed to parse version of ' + url)
                            self.failures[url] = error

    def test_detect_site(self):
        """Test detection of MediaWiki sites."""
        self.assertSite('http://botwiki.sno.cc/wiki/$1')
        self.assertSite('http://glossary.reuters.com/index.php?title=$1')
        self.assertSite('http://www.livepedia.gr/index.php?title=$1')
        self.assertSite('http://guildwars.wikia.com/wiki/$1')
        self.assertSite('http://www.hrwiki.org/index.php/$1')
        self.assertSite('http://www.proofwiki.org/wiki/$1')
        self.assertSite(
            'http://www.ck-wissen.de/ckwiki/index.php?title=$1')
        self.assertSite('http://en.citizendium.org/wiki/$1')
        self.assertSite(
            'http://www.lojban.org/tiki/tiki-index.php?page=$1')
        self.assertSite('http://www.EcoReality.org/wiki/$1')
        self.assertSite('http://www.wikichristian.org/index.php?title=$1')
        self.assertSite('http://wikitree.org/index.php?title=$1')
        self.assertAllPass()

    def test_detect_failure(self):
        """Test detection failure for MediaWiki sites with an API."""
        self.assertNoSite('https://en.wikifur.com/wiki/$1')
        # api.php is not available
        self.assertNoSite('http://wiki.animutationportal.com/index.php/$1')
        # API is disabled
        self.assertNoSite('http://wiki.linuxquestions.org/wiki/$1')
        # offline
        self.assertNoSite('http://seattlewiki.org/wiki/$1')
        self.assertAllError()

    def test_pre_api_sites(self):
        """Test detection of MediaWiki sites prior to the API."""
        self.assertNoSite('http://www.wikif1.org/$1')
        self.assertNoSite('http://www.thelemapedia.org/index.php/$1')
        self.assertNoSite('http://esperanto.blahus.cz/cxej/vikio/index.php/$1')
        self.assertNoSite('http://www.werelate.org/wiki/$1')
        self.assertNoSite('http://www.otterstedt.de/wiki/index.php/$1')
        self.assertNoSite('http://kb.mozillazine.org/$1')
        self.assertAllError()

    def test_detect_nosite(self):
        """Test detection of non-wiki sites."""
        self.assertNoSite('http://bluwiki.com/go/$1')
        self.assertNoSite('http://www.imdb.com/name/nm$1/')
        self.assertNoSite('http://www.ecyrd.com/JSPWiki/Wiki.jsp?page=$1')
        self.assertNoSite('http://operawiki.info/$1')
        self.assertNoSite(
            'http://www.tvtropes.org/pmwiki/pmwiki.php/Main/$1')
        self.assertNoSite('http://c2.com/cgi/wiki?$1')
        self.assertNoSite('https://phabricator.wikimedia.org/$1')
        self.assertNoSite(
            'http://www.merriam-webster.com/cgi-bin/dictionary?book=Dictionary&va=$1')
        self.assertNoSite('http://arxiv.org/abs/$1')
        self.assertNoSite('http://musicbrainz.org/doc/$1')
        self.assertNoSite('http://wiki.animutationportal.com/index.php/$1')
        self.assertAllError()


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
