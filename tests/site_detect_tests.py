# -*- coding: utf-8 -*-
"""Test for site detection."""
#
# (C) Pywikibot team, 2014-2016
#
# Distributed under the terms of the MIT license.
#

from __future__ import absolute_import, unicode_literals

from requests.exceptions import ConnectionError, Timeout

from pywikibot.exceptions import ServerError
from pywikibot.site_detect import MWSite

from tests.aspects import unittest, TestCase


__version__ = '$Id$'


class SiteDetectionTestCase(TestCase):

    """Testcase for MediaWiki detection and site object creation."""

    net = True

    def assertSite(self, url):
        """
        Assert a MediaWiki site can be loaded from the url.

        @param url: Url of tested site
        @type url: str
        @raises AssertionError: Site under url is not MediaWiki powered
        """
        try:
            self.assertIsInstance(MWSite(url), MWSite)
        except (ServerError, Timeout) as e:
            self.skipTest(e)

    def assertNoSite(self, url):
        """
        Assert a url is not a MediaWiki site.

        @param url: Url of tested site
        @type url: str
        @raises AssertionError: Site under url is MediaWiki powered
        """
        self.assertRaises((AttributeError, ConnectionError, RuntimeError,
                           ServerError, Timeout), MWSite, url)


class StandardVersionSiteTestCase(SiteDetectionTestCase):

    """Test detection of MediaWiki sites."""

    def test_hrwiki(self):
        """Test detection of MediaWiki sites for www.hrwiki.org."""
        self.assertSite('http://www.hrwiki.org/index.php/$1')  # v 1.15

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

        Server that hosts www.wikichristian.org is unreliable - it occasionally
        responding with 500 error (see: T151368).
        """
        self.assertSite('http://www.wikichristian.org/index.php?title=$1')

    def test_wikifur(self):
        """Test detection of MediaWiki sites for en.wikifur.com."""
        self.assertSite('https://en.wikifur.com/wiki/$1')

    def test_bluwiki(self):
        """Test detection of MediaWiki sites for bluwiki.com."""
        self.assertSite('http://bluwiki.com/go/$1')

    def test_kino_skirpov(self):
        """Test detection of MediaWiki sites for kino.skripov.com."""
        self.assertSite('http://kino.skripov.com/index.php/$1')


class NonStandardVersionSiteTestCase(SiteDetectionTestCase):

    """Test non-standard version string sites."""

    def test_gentoo(self):
        """Test detection of MediaWiki sites for wiki.gentoo.org."""
        self.assertSite('https://wiki.gentoo.org/wiki/$1')

    def test_arabeyes(self):
        """Test detection of MediaWiki sites for wiki.arabeyes.org."""
        self.assertSite('http://wiki.arabeyes.org/$1')

    def test_tfwiki(self):
        """Test detection of MediaWiki sites for tfwiki.net."""
        self.assertSite('http://tfwiki.net/wiki/$1')


class Pre114SiteTestCase(SiteDetectionTestCase):

    """Test pre 1.14 sites which should be detected as unsupported."""

    def test_livepedia(self):
        """Test detection of MediaWiki sites for www.livepedia.gr."""
        self.assertNoSite(
            'http://www.livepedia.gr/index.php?title=$1')  # v1.12

    def test_wikifon(self):
        """Test detection of MediaWiki sites for www.wikifon.org."""
        self.assertNoSite('http://www.wikifon.org/$1')  # v1.11

    def test_reuters(self):
        """Test detection of MediaWiki sites for glossary.reuters.com."""
        self.assertNoSite(
            'http://glossary.reuters.com/index.php?title=$1')  # v1.11

    def test_wikitree(self):
        """Test detection of MediaWiki sites for wikitree.org."""
        # v1.11, with no query module
        self.assertNoSite('http://wikitree.org/index.php?title=$1')

    def test_wikinvest(self):
        """Test detection of MediaWiki sites for www.wikinvest.com."""
        self.assertNoSite('http://www.wikinvest.com/$1')  # v1.9


class PreAPISiteTestCase(SiteDetectionTestCase):

    """Test detection of MediaWiki sites prior to the API."""

    def test_wikif1(self):
        """Test detection of MediaWiki sites for www.wikif1.org."""
        self.assertNoSite('http://www.wikif1.org/$1')

    def test_thelemapedia(self):
        """Test detection of MediaWiki sites for www.thelemapedia.org."""
        self.assertNoSite('http://www.thelemapedia.org/index.php/$1')

    def test_blahus(self):
        """Test detection of MediaWiki sites for esperanto.blahus.cz."""
        self.assertNoSite('http://esperanto.blahus.cz/cxej/vikio/index.php/$1')

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

    @unittest.expectedFailure
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

    @unittest.expectedFailure
    def test_hackerspaces(self):
        """Test detection of MediaWiki sites for hackerspaces.org."""
        self.assertNoSite('http://hackerspaces.org/wiki/$1')


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

    def test_operawiki(self):
        """Test detection of MediaWiki sites for operawiki.info."""
        self.assertNoSite('http://operawiki.info/$1')

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

    def test_seattlewiki(self):
        """Test detection of MediaWiki sites for seattlewiki.org."""
        self.assertNoSite('http://seattlewiki.org/wiki/$1')


class OtherSiteTestCase(SiteDetectionTestCase):

    """Test other non-MediaWiki sites."""

    def test_musicbrainz(self):
        """Test http://musicbrainz.org/doc/ which has a page 'api.php'.

        Possible false positive caused by the existance of a page called
        http://musicbrainz.org/doc/api.php.
        """
        self.assertNoSite('http://musicbrainz.org/doc/$1')


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
