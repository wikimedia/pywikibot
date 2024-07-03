#!/usr/bin/env python3
"""Test generate_family_file script."""
#
# (C) Pywikibot team, 2018-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import unittest
from contextlib import suppress
from random import sample
from urllib.parse import urlparse

from pywikibot import Site
from pywikibot.family import WikimediaFamily
from pywikibot.scripts import generate_family_file
from tests.aspects import DefaultSiteTestCase
from tests.utils import skipping


class FamilyTestGenerator(generate_family_file.FamilyFileGenerator):

    """Family file test creator."""

    def getapis(self):
        """Only load up to additional ten different wikis randomly."""
        save = self.langs

        prefixes = {lang['prefix'] for lang in self.langs}
        tests = set(sample(list(prefixes), min(len(prefixes), 10)))
        # add closed wiki due to T334714
        if 'ii' in prefixes and 'ii' not in tests:
            tests.add('ii')

        # collect wikis
        self.langs = []
        for wiki in save:
            code = wiki['prefix']
            if code in tests:
                self.langs.append(wiki)
                tests.remove(code)
                if not tests:
                    break

        super().getapis()
        # super().getapis() might change self.langs
        self.prefixes = [item['prefix'] for item in self.langs]
        self.langs = save

    def writefile(self, verify):
        """Pass writing."""


class TestGenerateFamilyFile(DefaultSiteTestCase):

    """Test generate_family_file functionality."""

    familyname = 'testgff'

    @classmethod
    def setUpClass(cls):
        """Set up tests class."""
        super().setUpClass()
        # test fails on wowwiki (T297042)
        if cls.site.family.name == 'wowwiki':
            raise unittest.SkipTest(f'skipping {cls.site} due to T297042')

    def setUp(self):
        """Set up tests."""
        super().setUp()
        answer = 's' if isinstance(self.site.family, WikimediaFamily) else 'y'
        self.generator_instance = FamilyTestGenerator(
            url=self.site.base_url(''), name=self.familyname,
            dointerwiki=answer)

    def test_initial_attributes(self):
        """Test initial FamilyFileGenerator attributes."""
        self.assertEqual(self.generator_instance.base_url,
                         self.site.base_url(''))
        self.assertEqual(self.generator_instance.name, self.familyname)
        self.assertIn(self.generator_instance.dointerwiki, ['s', 'y'])
        self.assertIsInstance(self.generator_instance.wikis, dict)
        self.assertIsInstance(self.generator_instance.langs, list)

    def test_attributes_after_run(self):
        """Test FamilyFileGenerator attributes after run()."""
        gen = self.generator_instance
        gen.run()

        with self.subTest(test='Test whether default is loaded'):
            self.assertIn(self.site.lang, gen.wikis)

        # Subtest fails on musicbrainz (T130381) and wsbeta (T243669)
        if self.site.family.name not in ('wsbeta', 'musicbrainz'):
            with self.subTest(test='Test element counts'):
                if self.site.lang not in gen.prefixes:
                    gen.prefixes.append(self.site.lang)
                self.assertCountEqual(gen.prefixes, gen.wikis)

        # test creating Site from url
        # only test Sites for downloaded wikis (T241413)
        for language in filter(lambda x: x['prefix'] in gen.wikis, gen.langs):
            lang = language['prefix']
            url = language['url']
            wiki = gen.wikis[lang]
            lang_parse = urlparse(url)
            wiki_parse = urlparse(wiki.server)

            with self.subTest(url=url):
                if lang_parse.netloc != wiki_parse.netloc:
                    # skip redirected url (T241413)
                    self.skipTest(f'{lang_parse.netloc} is redirected to '
                                  f'{wiki_parse.netloc}')

                site = Site(url=url)
                msg = (f'url has lang "{lang}" but Site {site} has lang '
                       f'"{site.lang}"')
                with skipping(AssertionError,
                              msg='KNOWN BUG (T194138): ' + msg):
                    self.assertEqual(site.lang, lang, msg)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
