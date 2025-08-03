#!/usr/bin/env python3
"""Tests for the site module."""
#
# (C) Pywikibot team, 2008-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from contextlib import suppress

import pywikibot
from pywikibot.backports import NoneType
from pywikibot.exceptions import Error
from tests.aspects import DefaultSiteTestCase, TestCase, unittest


WARN_SELF_CALL = (r'Referencing this attribute like a function '
                  r'is deprecated .+; use it directly instead')


class TestBaseSiteProperties(TestCase):

    """Test properties for BaseSite."""

    sites = {
        'enwikinews': {
            'family': 'wikinews',
            'code': 'en',
            'result': ('/doc',),
        },
        'enwikibooks': {
            'family': 'wikibooks',
            'code': 'en',
            'result': ('/doc',),
        },
        'enwikiquote': {
            'family': 'wikiquote',
            'code': 'en',
            'result': ('/doc',),
        },
        'enwiktionary': {
            'family': 'wiktionary',
            'code': 'en',
            'result': ('/doc',),
        },
        'enws': {
            'family': 'wikisource',
            'code': 'en',
            'result': ('/doc',),
        },
        'dews': {
            'family': 'wikisource',
            'code': 'de',
            'result': ('/Doku', '/Meta'),
        },
        'commons': {
            'family': 'commons',
            'code': 'commons',
            'result': ('/doc', ),
        },
        'wikidata': {
            'family': 'wikidata',
            'code': 'wikidata',
            'result': ('/doc', ),
        },
    }

    dry = True

    def test_properties(self, key) -> None:
        """Test cases for BaseSite properties."""
        mysite = self.get_site(key)
        self.assertEqual(mysite.doc_subpage, self.sites[key]['result'])


class TestSiteObject(DefaultSiteTestCase):

    """Test cases for Site methods."""

    cached = True

    def test_base_methods(self) -> None:
        """Test cases for BaseSite methods."""
        mysite = self.get_site()
        code = self.site.family.obsolete.get(self.code) or self.code
        self.assertEqual(mysite.family.name, self.family)
        self.assertEqual(mysite.code, code)
        self.assertIsInstance(mysite.lang, str)
        self.assertEqual(mysite, pywikibot.Site(self.code, self.family))
        self.assertIsInstance(mysite.user(), (str, NoneType))
        self.assertEqual(mysite.sitename, f'{self.family}:{code}')
        self.assertIsInstance(mysite.linktrail(), str)
        self.assertIsInstance(mysite.redirect(), str)

        try:
            dabcat = mysite.disambcategory()
        except Error as e:
            try:
                self.assertIn('No disambiguation category name found', str(e))
            except AssertionError:
                self.assertIn(
                    f'No {mysite.data_repository().family.name} qualifier'
                    ' found for disambiguation category name in '
                    f'{mysite.family.name}_family file',
                    str(e)
                )
        else:
            self.assertIsInstance(dabcat, pywikibot.Category)

        foo = str(pywikibot.Link('foo', source=mysite))
        if self.site.namespaces[0].case == 'case-sensitive':
            self.assertEqual(foo, '[[foo]]')
        else:
            self.assertEqual(foo, '[[Foo]]')

        self.assertFalse(mysite.isInterwikiLink('foo'))
        self.assertIsInstance(mysite.redirect_regex.pattern, str)
        self.assertIsInstance(mysite.category_on_one_line(), bool)
        self.assertTrue(mysite.sametitle('Template:Test', 'Template:Test'))
        self.assertTrue(mysite.sametitle('Template: Test', 'Template:   Test'))
        self.assertTrue(mysite.sametitle('Test name', 'Test name'))
        self.assertFalse(mysite.sametitle('Test name', 'Test Name'))
        # User, MediaWiki and Special are always
        # first-letter (== only first non-namespace letter is case insensitive)
        # See also: https://www.mediawiki.org/wiki/Manual:$wgCapitalLinks
        self.assertTrue(mysite.sametitle('Special:Always', 'Special:always'))
        self.assertTrue(mysite.sametitle('User:Always', 'User:always'))
        self.assertTrue(mysite.sametitle('MediaWiki:Always',
                                         'MediaWiki:always'))

    def test_site_with_url(self) -> None:
        """Test site constructor with url."""
        for fam in ('commons', 'meta'):
            with self.subTest(family=fam):
                site = pywikibot.Site(url=f'https://{fam}.wikimedia.org')
                self.assertEqual(site, pywikibot.Site(fam))
                self.assertEqual(site.family.name, fam)
                self.assertEqual(site.code, fam)

    def test_site_with_url_and_path(self) -> None:
        """Test site constructor with trailing slash."""
        for path in ('', '/'):
            url = f'https://fr.wikipedia.org{path}'
            with self.subTest(url=url):
                site = pywikibot.Site(url=url)
                self.assertEqual(site, pywikibot.Site('wikipedia:fr'))
                self.assertEqual(site.family.name, 'wikipedia')
                self.assertEqual(site.code, 'fr')


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
