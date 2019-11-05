# -*- coding: utf-8 -*-
"""Test generate_family_files script."""
#
# (C) Pywikibot team, 2018-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from random import choice

from pywikibot import Site

from tests.aspects import unittest, DefaultSiteTestCase
from tests.utils import allowed_failure

import generate_family_file


class FamilyTestGenerator(generate_family_file.FamilyFileGenerator):

    """Family file test creator."""

    def getapis(self):
        """Only load additional two additional wikis randomly."""
        save = self.langs
        self.langs = [choice(save), choice(save)]
        self.prefixes = [item['prefix'] for item in self.langs]
        super(FamilyTestGenerator, self).getapis()
        self.langs = save

    def writefile(self):
        """Pass writing."""
        pass


class TestGenerateFamilyFiles(DefaultSiteTestCase):

    """Test generate_family_file functionality."""

    def setUp(self):
        """Set up tests class."""
        super(TestGenerateFamilyFiles, self).setUp()
        self.generator_instance = FamilyTestGenerator(
            url=self.site.base_url(''), name='gff-test', dointerwiki='y')

    def test_initial_attributes(self):
        """Test initial FamilyFileGenerator attributes."""
        self.assertEqual(self.generator_instance.base_url,
                         self.site.base_url(''))
        self.assertEqual(self.generator_instance.name, 'gff-test')
        self.assertEqual(self.generator_instance.dointerwiki, 'y')
        self.assertIsInstance(self.generator_instance.wikis, dict)
        self.assertIsInstance(self.generator_instance.langs, list)

    @allowed_failure  # T194138
    def test_attributes_after_run(self):
        """Test FamilyFileGenerator attributes after run()."""
        self.generator_instance.run()
        langs = [self.site.lang] + self.generator_instance.prefixes
        for lang in langs:
            self.assertIn(lang, self.generator_instance.wikis)
        for i in range(10):
            lang = choice(self.generator_instance.langs)
            site = Site(url=lang['url'])
            self.assertEqual(site.lang, lang['prefix'])


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
