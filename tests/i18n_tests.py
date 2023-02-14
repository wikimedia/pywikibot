#!/usr/bin/env python3
"""Test i18n module."""
#
# (C) Pywikibot team, 2007-2023
#
# Distributed under the terms of the MIT license.
#
from contextlib import suppress

import pywikibot
from pywikibot import bot, config, i18n
from pywikibot.exceptions import TranslationError
from tests.aspects import DefaultSiteTestCase, PwbTestCase, TestCase, unittest


class Site:

    """An object holding code and family, duck typing a pywikibot Site."""

    class Family:

        """Nested class to hold the family name attribute."""

    def __init__(self, code, family='wikipedia'):
        """Initializer."""
        self.code = code
        self.family = self.Family()
        self.family.name = family


class TestTranslate(TestCase):

    """Test translate method with fallback True."""

    net = False

    xdict = {
        'en': 'test-localized EN',
        'commons': 'test-localized COMMONS',
        'wikipedia': {
            'nl': 'test-localized WP-NL',
            'fy': 'test-localized WP-FY',
            'wikipedia': {  # test a deeply nested xdict
                'de': 'test-localized WP-DE',
            },
        },
        'wikisource': {
            'en': 'test-localized WS-EN',
            'fy': 'test-localized WS-FY',
            'ja': 'test-localized WS-JA',
        },
    }

    def test_translate_commons(self):
        """Test localization with xdict for commons.

        Test whether the localzation is found either with the Site object
        or with the site code.
        """
        site = Site('commons')
        for code in (site, 'commons'):
            with self.subTest(code=code):
                self.assertEqual(i18n.translate(code, self.xdict),
                                 'test-localized COMMONS')

    def test_translate_de(self):
        """Test localization fallbacks for 'de' with xdict.

        'de' key is defined in a nested 'wikipedia' sub dict. This should
        always fall back to this nested 'wikipedia' entry.
        """
        site1 = Site('de', 'wikipedia')
        site2 = Site('de', 'wikibooks')
        site3 = Site('de', 'wikisource')
        for code in (site1, site2, site3, 'de'):
            with self.subTest(code=code):
                self.assertEqual(i18n.translate(code, self.xdict),
                                 'test-localized WP-DE')

    def test_translate_en(self):
        """Test localization fallbacks for 'en' with xdict.

        'en' key is defined directly in xdict. This topmost key goes over
        site specific key. Therefore 'test-localized WS-EN' is not given
        back.
        """
        site1 = Site('en', 'wikipedia')
        site2 = Site('en', 'wikibooks')
        site3 = Site('en', 'wikisource')
        for code in (site1, site2, site3, 'en'):
            with self.subTest(code=code):
                self.assertEqual(i18n.translate(code, self.xdict),
                                 'test-localized EN')

    def test_translate_fy(self):
        """Test localization fallbacks for 'fy' with xdict.

        'fy' key is defined in 'wikipedia' and  'wikisource' sub dicts.
        They should have different localizations for these two families but
        'wikisource' should have a fallback to the 'wikipedia' entry.

        Note: If the translate code is given as string, the result depends
        on the current config.family entry. Therefore there is no test with
        the code given as string.
        """
        site1 = Site('fy', 'wikipedia')
        site2 = Site('fy', 'wikibooks')
        site3 = Site('fy', 'wikisource')
        for code in (site1, site2):
            with self.subTest(code=code):
                self.assertEqual(i18n.translate(code, self.xdict),
                                 'test-localized WP-FY')
        self.assertEqual(i18n.translate(site3, self.xdict),
                         'test-localized WS-FY')

    def test_translate_nl(self):
        """Test localization fallbacks for 'nl' with xdict.

        'nl' key is defined in 'wikipedia' sub dict. Therefore all
        localizations have a fallback to the 'wikipedia' entry.
        """
        site1 = Site('nl', 'wikipedia')
        site2 = Site('nl', 'wikibooks')
        site3 = Site('nl', 'wikisource')
        for code in (site1, site2, site3, 'nl'):
            with self.subTest(code=code):
                self.assertEqual(i18n.translate(code, self.xdict),
                                 'test-localized WP-NL')

    def test_translate_ja(self):
        """Test localization fallbacks for 'ja' with xdict.

        'ja' key is defined in 'wkisource' sub dict only. Therefore there
        is no fallback to the 'wikipedia' entry and the localization result
        is None.
        """
        site1 = Site('ja', 'wikipedia')
        site2 = Site('ja', 'wikibooks')
        site3 = Site('ja', 'wikisource')
        for code in (site1, site2):
            with self.subTest(code=code):
                self.assertIsNone(i18n.translate(code, self.xdict))
        self.assertEqual(i18n.translate(site3, self.xdict),
                         'test-localized WS-JA')


class TestFallbackTranslate(TestCase):

    """Test translate method with fallback True."""

    net = False

    msg_localized = {'en': 'test-localized EN',
                     'nl': 'test-localized NL',
                     'fy': 'test-localized FY'}
    msg_semi_localized = {'en': 'test-semi-localized EN',
                          'nl': 'test-semi-localized NL'}
    msg_non_localized = {'en': 'test-non-localized EN'}
    msg_no_english = {'ja': 'test-no-english JA'}

    def test_localized(self):
        """Test fully localized translations."""
        for code, msg in self.msg_localized.items():
            with self.subTest(code=code):
                self.assertEqual(i18n.translate(code, self.msg_localized,
                                                fallback=True),
                                 msg)

    def test_semi_localized(self):
        """Test translate by fallback to an alternative language."""
        self.assertEqual(i18n.translate('en', self.msg_semi_localized,
                                        fallback=True),
                         'test-semi-localized EN')
        for code in ('nl', 'fy'):
            with self.subTest(code=code):
                self.assertEqual(i18n.translate(code, self.msg_semi_localized,
                                                fallback=True),
                                 'test-semi-localized NL')

    def test_non_localized(self):
        """Test translate with missing localisation."""
        for code in ('en', 'fy', 'nl', 'ru'):
            with self.subTest(code=code):
                self.assertEqual(i18n.translate(code, self.msg_non_localized,
                                                fallback=True),
                                 'test-non-localized EN')

    def testNoEnglish(self):
        """Test translate with missing English text."""
        for code in ('en', 'fy', 'nl'):
            with self.subTest(code=code), self.assertRaises(KeyError):
                i18n.translate(code, self.msg_no_english, fallback=True)


class UserInterfaceLangTestCase(TestCase):

    """Base class for tests using config.userinterface_lang."""

    def setUp(self):
        """Change the userinterface language to the site's code."""
        super().setUp()
        self.orig_userinterface_lang = pywikibot.config.userinterface_lang
        pywikibot.config.userinterface_lang = self.get_site().code

    def tearDown(self):
        """Reset the userinterface language."""
        pywikibot.config.userinterface_lang = self.orig_userinterface_lang
        super().tearDown()


class TWNSetMessagePackageBase(TestCase):

    """Partial base class for TranslateWiki tests."""

    message_package = None

    def setUp(self):
        """Load the test translations."""
        self.orig_messages_package_name = i18n._messages_package_name
        i18n.set_messages_package(self.message_package)
        super().setUp()

    def tearDown(self):
        """Load the original translations back."""
        super().tearDown()
        i18n.set_messages_package(self.orig_messages_package_name)


class TWNTestCaseBase(TWNSetMessagePackageBase):

    """Base class for TranslateWiki tests."""

    @classmethod
    def setUpClass(cls):
        """Verify that the test translations are not empty."""
        if not isinstance(cls.message_package, str):
            raise TypeError('{}.message_package must be a package name'
                            .format(cls.__name__))  # pragma: no cover
        # The call to set_messages_package below exists only to confirm
        # that the package exists and messages are available, so
        # that tests can be skipped if the i18n data doesn't exist.
        cls.orig_messages_package_name = i18n._messages_package_name
        i18n.set_messages_package(cls.message_package)
        has_messages = i18n.messages_available()
        i18n._messages_package_name = cls.orig_messages_package_name
        if not has_messages:
            raise unittest.SkipTest("i18n messages package '{}' not available."
                                    .format(cls.message_package))
        super().setUpClass()


class TestTWTranslate(TWNTestCaseBase):

    """Test twtranslate method."""

    net = False
    message_package = 'tests.i18n'

    def testLocalized(self):
        """Test fully localized entry."""
        self.assertEqual(i18n.twtranslate('en', 'test-localized'),
                         'test-localized EN')
        self.assertEqual(i18n.twtranslate('nl', 'test-localized'),
                         'test-localized NL')
        self.assertEqual(i18n.twtranslate('fy', 'test-localized'),
                         'test-localized FY')

    def testSemiLocalized(self):
        """Test translating with fallback to alternative language."""
        self.assertEqual(i18n.twtranslate('en', 'test-semi-localized'),
                         'test-semi-localized EN')
        for code in ('nl', 'fy'):
            with self.subTest(code=code):
                self.assertEqual(i18n.twtranslate(code, 'test-semi-localized'),
                                 'test-semi-localized NL')

    def testNonLocalized(self):
        """Test translating non localized entries."""
        for code in ('en', 'fy', 'nl', 'ru'):
            with self.subTest(code=code):
                self.assertEqual(i18n.twtranslate(code, 'test-non-localized'),
                                 'test-non-localized EN')

    def testNoEnglish(self):
        """Test translating into English with missing entry."""
        with self.assertRaises(TranslationError):
            i18n.twtranslate('en', 'test-no-english')


class InputTestCase(TWNTestCaseBase, UserInterfaceLangTestCase, PwbTestCase):

    """Test i18n.input."""

    family = 'wikipedia'
    code = 'nn'
    alt_code = 'nb'

    message_package = 'scripts.i18n'
    message = 'pywikibot-enter-category-name'

    @classmethod
    def setUpClass(cls):
        """Verify that a translation does not yet exist."""
        super().setUpClass()

        if cls.code in i18n.twget_keys(cls.message):
            raise unittest.SkipTest(
                '{} has a translation for {}'
                .format(cls.code, cls.message))

    def test_pagegen_i18n_input(self):
        """Test i18n.input fallback via pwb."""
        expect = i18n.twtranslate(self.alt_code, self.message, fallback=False)
        result = self._execute(args=['listpages', '-cat'],
                               data_in='non-existant-category\r\n')
        self.assertIn(expect, result['stderr'])


class MissingPackageTestCase(TWNSetMessagePackageBase,
                             UserInterfaceLangTestCase,
                             DefaultSiteTestCase):

    """Test missing messages package."""

    message_package = 'scripts.foobar.i18n'

    def _capture_output(self, text, *args, **kwargs):
        self.output_text = text

    def setUp(self):
        """Patch the output and input methods."""
        super().setUp()
        bot.set_interface('terminal')
        self.output_text = ''
        self.orig_raw_input = bot.ui._raw_input
        self.orig_output = bot.ui.stream_output
        bot.ui._raw_input = lambda *args, **kwargs: 'dummy input'
        bot.ui.stream_output = self._capture_output
        self.old_cc_setting = config.cosmetic_changes_mylang_only

    def tearDown(self):
        """Restore the output and input methods."""
        config.cosmetic_changes_mylang_only = self.old_cc_setting
        bot.ui._raw_input = self.orig_raw_input
        bot.ui.output = self.orig_output
        bot.set_interface('buffer')
        super().tearDown()

    def test_i18n_input(self):
        """Test i18n.input falls back with missing message package."""
        rv = i18n.input('pywikibot-enter-category-name',
                        fallback_prompt='dummy output')
        self.assertEqual(rv, 'dummy input')
        self.assertIn('dummy output: ', self.output_text)

    def test_i18n_twtranslate(self):
        """Test i18n.twtranslate falls back with missing message package."""
        rv = i18n.twtranslate(self.site, 'pywikibot-enter-category-name',
                              fallback_prompt='dummy message')
        self.assertEqual(rv, 'dummy message')


class PywikibotPackageTestCase(TestCase):

    """Test pywikibot i18n package."""

    family = 'wikipedia'
    code = 'de'

    def test_cosmetic_changes_hook(self):
        """Test summary result of Page._cosmetic_changes_hook."""
        page = pywikibot.Page(self.site, 'Test')
        page.text = 'Some    content    with    spaces.'
        # check cc settings
        config.cosmetic_changes_mylang_only = False
        self.assertFalse(page.isTalkPage())
        self.assertNotIn(pywikibot.calledModuleName(),
                         config.cosmetic_changes_deny_script)
        self.assertFalse(config.cosmetic_changes_mylang_only)

        if page.content_model != 'wikitext':
            self.skipTest('Wrong content model {!r} for cosmetic_changes'
                          .format(page.content_model))

        summary = f'Working on Test page at site {self.site}'
        msg = page._cosmetic_changes_hook(summary)
        self.assertEqual(msg, summary + '; kosmetische Änderungen')


class TestExtractPlural(TestCase):

    """Test extracting plurals from a dummy string."""

    net = False

    def test_standard(self):
        """Test default usage using a dict and no specific plurals."""
        self.assertEqual(
            i18n._extract_plural('en', '{{PLURAL:foo|one|other}}',
                                 {'foo': 42}),
            'other')
        self.assertEqual(
            i18n._extract_plural('en', '{{PLURAL:foo|one|other}}',
                                 {'foo': 1}),
            'one')
        self.assertEqual(
            i18n._extract_plural('en', '{{PLURAL:foo|one|other}}',
                                 {'foo': 0}),
            'other')

    def test_empty_fields(self):
        """Test default usage using a dict and no specific plurals."""
        self.assertEqual(
            i18n._extract_plural('en', '{{PLURAL:foo||other}}', {'foo': 42}),
            'other')
        self.assertEqual(
            i18n._extract_plural('en', '{{PLURAL:foo||other}}', {'foo': 1}),
            '')
        self.assertEqual(
            i18n._extract_plural('en', '{{PLURAL:foo|one|}}', {'foo': 1}),
            'one')

        # two variants expected but only one given
        self.assertEqual(
            i18n._extract_plural('en', '{{PLURAL:foo|one}}', {'foo': 0}),
            'one')

    def test_specific(self):
        """Test using a specific plural."""
        self.assertEqual(
            i18n._extract_plural('en', '{{PLURAL:foo|one|other|12=dozen}}',
                                 {'foo': 42}),
            'other')
        self.assertEqual(
            i18n._extract_plural('en', '{{PLURAL:foo|one|other|12=dozen}}',
                                 {'foo': 12}),
            'dozen')

    def test_more(self):
        """Test the number of plurals are more than expected."""
        test = [(0, 2), (1, 0), (2, 1), (3, 2), (4, 2), (7, 2), (8, 3)]
        for num, result in test:
            self.assertEqual(
                i18n._extract_plural(
                    'cy',
                    '{{PLURAL:num|0|1|2|3|4|5}}',
                    {'num': num}),
                str(result))

    def test_less(self):
        """Test the number of plurals are less than expected."""
        test = [(0, 2), (1, 0), (2, 1), (3, 2), (4, 2), (7, 2), (8, 3)]
        for num, result in test:
            self.assertEqual(
                i18n._extract_plural(
                    'cy',
                    '{{PLURAL:num|0|1}}',
                    {'num': num}),
                str(min(result, 1)))


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
