#!/usr/bin/env python3
"""Test generate_family_file script."""
#
# (C) Pywikibot team, 2018-2022
#
# Distributed under the terms of the MIT license.
#
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
        self.langs = sample(save, min(len(save), 10))
        for wiki in save:  # add closed wiki due to T334714
            if wiki['prefix'] == 'ii' and 'ii' not in self.langs:
                self.langs.append(wiki)
                break

        super().getapis()
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
            raise unittest.SkipTest('skipping {} due to T297042'
                                    .format(cls.site))

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
                    self.skipTest(
                        '{} is redirected to {}'
                        .format(lang_parse.netloc, wiki_parse.netloc))

                site = Site(url=url)

                with skipping(AssertionError,
                              msg='KNOWN BUG (T194138): url has lang "{lang}" '
                                  'but Site {site} has lang "{site.lang}"'
                                  .format(site=site, lang=lang)):
                    self.assertEqual(site.lang, lang,
                                     'url has lang "{lang}" '
                                     'but Site {site} has lang "{site.lang}"'
                                     .format(site=site, lang=lang))


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
