"""Test i18n module."""
#
# (C) Pywikibot team, 2007-2020
#
# Distributed under the terms of the MIT license.
#
from contextlib import suppress

import pywikibot

from pywikibot import bot, i18n, plural

from tests.aspects import (
    AutoDeprecationTestCase,
    DefaultSiteTestCase,
    PwbTestCase,
    TestCase,
    unittest,
)


class Site:

    """An object holding code and family, duck typing a pywikibot Site."""

    class Family:

        """Nested class to hold the family name attribute."""

        pass

    def __init__(self, code, family='wikipedia'):
        """Initializer."""
        self.code = code
        self.family = self.Family()
        setattr(self.family, 'name', family)

    def __repr__(self):
        return "'{site.family.name}:{site.code}'".format(site=self)


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
        site = Site('commons', 'commons')
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
            with self.subTest(code=code):
                with self.assertRaises(KeyError):
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
                            .format(cls.__name__))
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
        self.assertRaises(i18n.TranslationError, i18n.twtranslate,
                          'en', 'test-no-english')


class TestTWNTranslate(TWNTestCaseBase, AutoDeprecationTestCase):

    """Test {{PLURAL:}} support."""

    net = False
    message_package = 'tests.i18n'

    def testNumber(self):
        """Use a number."""
        self.assertEqual(
            i18n.twntranslate('de', 'test-plural', 0) % {'num': 0},
            'Bot: Ändere 0 Seiten.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-plural', 1) % {'num': 1},
            'Bot: Ändere 1 Seite.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-plural', 2) % {'num': 2},
            'Bot: Ändere 2 Seiten.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-plural', 3) % {'num': 3},
            'Bot: Ändere 3 Seiten.')
        self.assertEqual(
            i18n.twntranslate('en', 'test-plural', 0) % {'num': 'no'},
            'Bot: Changing no pages.')
        self.assertEqual(
            i18n.twntranslate('en', 'test-plural', 1) % {'num': 'one'},
            'Bot: Changing one page.')
        self.assertEqual(
            i18n.twntranslate('en', 'test-plural', 2) % {'num': 'two'},
            'Bot: Changing two pages.')
        self.assertEqual(
            i18n.twntranslate('en', 'test-plural', 3) % {'num': 'three'},
            'Bot: Changing three pages.')

    def testString(self):
        """Use a string."""
        self.assertEqual(
            i18n.twntranslate('en', 'test-plural', '1') % {'num': 'one'},
            'Bot: Changing one page.')

    def testDict(self):
        """Use a dictionary."""
        self.assertEqual(
            i18n.twntranslate('en', 'test-plural', {'num': 2}),
            'Bot: Changing 2 pages.')

    def testExtended(self):
        """Use additional format strings."""
        self.assertEqual(
            i18n.twntranslate('fr', 'test-plural',
                              {'num': 1, 'descr': 'seulement'}),
            'Robot: Changer seulement une page.')

    def testExtendedOutside(self):
        """Use additional format strings also outside."""
        self.assertEqual(
            i18n.twntranslate('fr', 'test-plural', 1) % {'descr': 'seulement'},
            'Robot: Changer seulement une page.')

    def testMultiple(self):
        """Test using multiple plural entries."""
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals', 1)
            % {'action': 'Ändere', 'line': 'eine'},
            'Bot: Ändere eine Zeile von einer Seite.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals', 2)
            % {'action': 'Ändere', 'line': 'zwei'},
            'Bot: Ändere zwei Zeilen von mehreren Seiten.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals', 3)
            % {'action': 'Ändere', 'line': 'drei'},
            'Bot: Ändere drei Zeilen von mehreren Seiten.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals', (1, 2, 2))
            % {'action': 'Ändere', 'line': 'eine'},
            'Bot: Ändere eine Zeile von mehreren Seiten.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals', [3, 1, 1])
            % {'action': 'Ändere', 'line': 'drei'},
            'Bot: Ändere drei Zeilen von einer Seite.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals', ['3', 1, 1])
            % {'action': 'Ändere', 'line': 'drei'},
            'Bot: Ändere drei Zeilen von einer Seite.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals', '321')
            % {'action': 'Ändere', 'line': 'dreihunderteinundzwanzig'},
            'Bot: Ändere dreihunderteinundzwanzig Zeilen von mehreren Seiten.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals',
                              {'action': 'Ändere', 'line': 1, 'page': 1}),
            'Bot: Ändere 1 Zeile von einer Seite.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals',
                              {'action': 'Ändere', 'line': 1, 'page': 2}),
            'Bot: Ändere 1 Zeile von mehreren Seiten.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals',
                              {'action': 'Ändere', 'line': '11', 'page': 2}),
            'Bot: Ändere 11 Zeilen von mehreren Seiten.')

    def testMultipleWrongParameterLength(self):
        """Test wrong parameter length."""
        err_msg = 'Length of parameter does not match PLURAL occurrences'
        with self.assertRaisesRegex(ValueError, err_msg):
            i18n.twntranslate('de', 'test-multiple-plurals', (1, 2))

        with self.assertRaisesRegex(ValueError, err_msg):
            i18n.twntranslate('de', 'test-multiple-plurals', ['321'])

    def testMultipleNonNumbers(self):
        """Test error handling for multiple non-numbers."""
        with self.assertRaisesRegex(
            ValueError, r"invalid literal for int\(\) with base 10: 'drei'"
        ):
            i18n.twntranslate('de', 'test-multiple-plurals', ['drei', '1', 1])
        with self.assertRaisesRegex(
            ValueError, r"invalid literal for int\(\) with base 10: 'elf'"
        ):
            i18n.twntranslate('de', 'test-multiple-plurals',
                              {'action': 'Ändere', 'line': 'elf', 'page': 2})

    def testAllParametersExist(self):
        """Test that all parameters are required when using a dict."""
        # all parameters must be inside twntranslate
        self.assertEqual(i18n.twntranslate('de', 'test-multiple-plurals',
                                           {'line': 1, 'page': 1}),
                         'Bot: %(action)s %(line)s Zeile von einer Seite.')

    def test_fallback_lang(self):
        """
        Test that twntranslate uses the translation's language.

        twntranslate calls _twtranslate which might return the translation for
        a different language and then the plural rules from that language need
        to be applied.
        """
        # co has fr as altlang but has no plural rules defined (otherwise this
        # test might not catch problems) so it's using the plural variant for 0
        # although French uses the plural variant for numbers > 1 (so not 0)
        assert 'co' not in plural.plural_rules
        assert plural.plural_rules['fr']['plural'](0) is False
        self.assertEqual(
            i18n.twntranslate('co', 'test-plural',
                              {'num': 0, 'descr': 'seulement'}),
            'Robot: Changer seulement une page.')
        self.assertEqual(
            i18n.twntranslate('co', 'test-plural',
                              {'num': 1, 'descr': 'seulement'}),
            'Robot: Changer seulement une page.')


class ScriptMessagesTestCase(TWNTestCaseBase, AutoDeprecationTestCase):

    """Real messages test."""

    net = False
    message_package = 'scripts.i18n'

    def test_basic(self):
        """Verify that real messages are able to be loaded."""
        self.assertEqual(i18n.twntranslate('en', 'pywikibot-enter-new-text'),
                         'Please enter the new text:')

    def test_missing(self):
        """Test a missing message from a real message bundle."""
        self.assertRaises(i18n.TranslationError,
                          i18n.twntranslate, 'en', 'pywikibot-missing-key')


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
        self.output_text = ''
        self.orig_raw_input = bot.ui._raw_input
        self.orig_output = bot.ui.output
        bot.ui._raw_input = lambda *args, **kwargs: 'dummy input'
        bot.ui.output = self._capture_output

    def tearDown(self):
        """Restore the output and input methods."""
        bot.ui._raw_input = self.orig_raw_input
        bot.ui.output = self.orig_output
        super().tearDown()

    def test_pagegen_i18n_input(self):
        """Test i18n.input falls back with missing message package."""
        rv = i18n.input('pywikibot-enter-category-name',
                        fallback_prompt='dummy output')
        self.assertEqual(rv, 'dummy input')
        self.assertIn('dummy output: ', self.output_text)


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
