# -*- coding: utf-8  -*-
"""Test valid templates."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import re

import pywikibot
from pywikibot import i18n

from tests.aspects import unittest, MetaTestCaseClass, TestCase
from tests.utils import add_metaclass

PACKAGES = (
    'redirect-broken-redirect-template',  # speedy deletion template
    'archivebot-archiveheader',  # archive header template
)


class TestValidTemplateMeta(MetaTestCaseClass):

    """Test meta class."""

    def __new__(cls, name, bases, dct):
        """Create the new class."""
        def test_method(site):

            def test_template(self):
                """Test validity of template."""
                lang = site.lang
                if lang not in keys:
                    return
                msg = i18n.twtranslate(lang, package, fallback=False)
                if msg:
                    # check whether the message contains a template
                    template = re.findall(u'.*?{{(.*?)[|}]', msg)
                    self.assertTrue(template)

                    # known problem
                    if site.code == 'simple':
                        raise unittest.SkipTest(
                            "'simple' wiki has 'en' language  code but "
                            "missing template. Must be solved by the "
                            "corresponding script.")
                    # check whether template exists
                    title = template[0]
                    page = pywikibot.Page(site, title, ns=10)
                    self.assertTrue(page.exists())

            return test_template

        # create test methods for package messages processed by unittest
        site = pywikibot.Site(dct['code'], dct['family'])
        codes = site.family.languages_by_size
        del site
        for package in PACKAGES:
            keys = i18n.twget_keys(package)
            for code in codes:
                current_site = pywikibot.Site(code, dct['family'])
                test_name = ("test_%s_%s" % (package, code)).replace('-', '_')
                dct[test_name] = test_method(current_site)
        return super(TestValidTemplateMeta, cls).__new__(cls, name, bases, dct)


@add_metaclass
class TestValidTemplate(TestCase):

    """Test cases L10N message templates processed by unittest."""

    __metaclass__ = TestValidTemplateMeta

    family = 'wikipedia'
    code = 'en'


class TestSites(TestCase):

    """Other test L10N cases processed by unittest."""

    family = 'wikipedia'
    code = 'en'

    def test_valid_sites(self):
        """Test whether language key has a corresponding site."""
        codes = self.site.family.languages_by_size
        languages = [pywikibot.Site(code, self.family).lang for code in codes]
        for package in PACKAGES:
            keys = i18n.twget_keys(package)
            for key in keys:
                self.assertIn(key, languages,
                              "'%s' - json key '%s' is not a site language"
                              % (package, key))


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
