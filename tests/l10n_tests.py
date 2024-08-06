#!/usr/bin/env python3
"""Test valid templates."""
#
# (C) Pywikibot team, 2015-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import unittest
from contextlib import suppress
from itertools import chain

import pywikibot
from pywikibot import i18n
from pywikibot.textlib import extract_templates_and_params_regex_simple
from tests.aspects import MetaTestCaseClass, TestCase


PACKAGES = (
    'redirect-broken-redirect-template',  # speedy deletion template
    'archivebot-archiveheader',  # archive header template
)


class TestValidTemplateMeta(MetaTestCaseClass):

    """Test meta class."""

    def __new__(cls, name, bases, dct):
        """Create the new class."""
        def test_method(site, package):

            def test_template(self):
                """Test validity of template."""
                lang = site.lang
                if lang not in keys:
                    return

                if not i18n.twhas_key(lang, package):
                    return

                msg = i18n.twtranslate(lang, package, fallback=False)

                # check whether the message contains a template
                templates = extract_templates_and_params_regex_simple(msg)
                self.assertIsInstance(templates, list)
                self.assertIsNotEmpty(templates)

                # known problems
                if (package == PACKAGES[0] and site.code in ['simple', 'test2']
                        or package == PACKAGES[1] and site.code == 'test'):
                    raise unittest.SkipTest(
                        f"{site} wiki has '{site.lang}' language code but "
                        f"missing template for package '{package}'. Must be "
                        'solved by the corresponding script.'
                    )

                # check whether template exists
                title = templates[0][0]
                page = pywikibot.Page(site, title, ns=10)
                self.assertTrue(
                    page.exists(),
                    msg=f'Invalid L10N in package "{package}"\n'
                    f'template "{title}" does not exist for lang '
                    f'"{site.lang}" on site "{site}"'
                )

            return test_template

        # create test methods for package messages processed by unittest
        site = pywikibot.Site(dct['code'], dct['family'])
        codes = site.family.codes
        del site
        for package in PACKAGES:
            keys = i18n.twget_keys(package)
            for code in codes:
                current_site = pywikibot.Site(code, dct['family'])
                test_name = f'test_{package}_{code}'.replace('-', '_')
                cls.add_method(
                    dct, test_name, test_method(current_site, package),
                    doc_suffix=f'{package} and language {code}')

        return super().__new__(cls, name, bases, dct)


class TestValidTemplate(TestCase, metaclass=TestValidTemplateMeta):

    """Test cases L10N message templates processed by unittest."""

    family = 'wikipedia'
    code = 'en'

    @classmethod
    def setUpClass(cls):
        """Skip test gracefully if i18n package is missing."""
        super().setUpClass()
        if not i18n.messages_available():
            raise unittest.SkipTest(
                f'i18n messages package {i18n._messages_package_name!r} not'
                ' available.')


class TestPackages(TestCase):

    """Other test L10N cases processed by unittest."""

    net = False

    def test_valid_package(self):
        """Test whether package has entries."""
        for package in chain(['cosmetic_changes-standalone',
                              'pywikibot-cosmetic-changes'], PACKAGES):
            keys = i18n.twget_keys(package)
            with self.subTest(package=package):
                self.assertIsNotEmpty(keys)
                self.assertIn('en', keys)

    def test_package_bundles(self):
        """Test whether package bundles has valid entries."""
        langs = i18n.known_languages()
        self.assertIsInstance(langs, list)
        self.assertIsNotEmpty(langs)
        for dirname in i18n.bundles(stem=True):
            for lang in langs:
                with self.subTest(bundle=dirname, lang=lang):
                    bundle = i18n._get_bundle(lang, dirname)
                    if lang in ('en', 'qqq'):
                        self.assertIsNotEmpty(bundle)
                    for key in bundle:
                        if key == '@metadata':
                            continue
                        self.assertTrue(
                            key.startswith(dirname),
                            f'{key!r} does not start with {dirname!r}'
                        )


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
