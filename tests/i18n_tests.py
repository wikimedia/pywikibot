# -*- coding: utf-8 -*-
"""Test i18n module."""
#
# (C) Pywikibot team, 2007-2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import pywikibot

from pywikibot import i18n, bot, plural
from pywikibot.tools import StringTypes

from tests.aspects import (
    unittest, TestCase, DefaultSiteTestCase, PwbTestCase,
    AutoDeprecationTestCase,
)


class TestTranslate(TestCase):

    """Test translate method."""

    net = False

    def setUp(self):
        """Set up test method."""
        self.msg_localized = {'en': u'test-localized EN',
                              'nl': u'test-localized NL',
                              'fy': u'test-localized FY'}
        self.msg_semi_localized = {'en': u'test-semi-localized EN',
                                   'nl': u'test-semi-localized NL'}
        self.msg_non_localized = {'en': u'test-non-localized EN'}
        self.msg_no_english = {'ja': u'test-no-english JA'}
        super(TestTranslate, self).setUp()

    def testLocalized(self):
        """Test fully localized translations."""
        self.assertEqual(i18n.translate('en', self.msg_localized,
                                        fallback=True),
                         u'test-localized EN')
        self.assertEqual(i18n.translate('nl', self.msg_localized,
                                        fallback=True),
                         u'test-localized NL')
        self.assertEqual(i18n.translate('fy', self.msg_localized,
                                        fallback=True),
                         u'test-localized FY')

    def testSemiLocalized(self):
        """Test translate by fallback to an alternative language."""
        self.assertEqual(i18n.translate('en', self.msg_semi_localized,
                                        fallback=True),
                         u'test-semi-localized EN')
        self.assertEqual(i18n.translate('nl', self.msg_semi_localized,
                                        fallback=True),
                         u'test-semi-localized NL')
        self.assertEqual(i18n.translate('fy', self.msg_semi_localized,
                                        fallback=True),
                         u'test-semi-localized NL')

    def testNonLocalized(self):
        """Test translate with missing localisation."""
        self.assertEqual(i18n.translate('en', self.msg_non_localized,
                                        fallback=True),
                         u'test-non-localized EN')
        self.assertEqual(i18n.translate('fy', self.msg_non_localized,
                                        fallback=True),
                         u'test-non-localized EN')
        self.assertEqual(i18n.translate('nl', self.msg_non_localized,
                                        fallback=True),
                         u'test-non-localized EN')
        self.assertEqual(i18n.translate('ru', self.msg_non_localized,
                                        fallback=True),
                         u'test-non-localized EN')

    def testNoEnglish(self):
        """Test translate with missing English text."""
        self.assertEqual(i18n.translate('en', self.msg_no_english,
                                        fallback=True),
                         u'test-no-english JA')
        self.assertEqual(i18n.translate('fy', self.msg_no_english,
                                        fallback=True),
                         u'test-no-english JA')
        self.assertEqual(i18n.translate('nl', self.msg_no_english,
                                        fallback=True),
                         u'test-no-english JA')


class UserInterfaceLangTestCase(TestCase):

    """Base class for tests using config.userinterface_lang."""

    def setUp(self):
        """Change the userinterface language to the site's code."""
        super(UserInterfaceLangTestCase, self).setUp()
        self.orig_userinterface_lang = pywikibot.config.userinterface_lang
        pywikibot.config.userinterface_lang = self.get_site().code

    def tearDown(self):
        """Reset the userinterface language."""
        pywikibot.config.userinterface_lang = self.orig_userinterface_lang
        super(UserInterfaceLangTestCase, self).tearDown()


class TWNSetMessagePackageBase(TestCase):

    """Partial base class for TranslateWiki tests."""

    message_package = None

    def setUp(self):
        """Load the test translations."""
        self.orig_messages_package_name = i18n._messages_package_name
        i18n.set_messages_package(self.message_package)
        super(TWNSetMessagePackageBase, self).setUp()

    def tearDown(self):
        """Load the original translations back."""
        super(TWNSetMessagePackageBase, self).tearDown()
        i18n.set_messages_package(self.orig_messages_package_name)


class TWNTestCaseBase(TWNSetMessagePackageBase):

    """Base class for TranslateWiki tests."""

    @classmethod
    def setUpClass(cls):
        """Verify that the test translations are not empty."""
        if not isinstance(cls.message_package, StringTypes):
            raise TypeError('%s.message_package must be a package name'
                            % cls.__name__)
        # The call to set_messages_package below exists only to confirm
        # that the package exists and messages are available, so
        # that tests can be skipped if the i18n data doesnt exist.
        cls.orig_messages_package_name = i18n._messages_package_name
        i18n.set_messages_package(cls.message_package)
        has_messages = i18n.messages_available()
        i18n._messages_package_name = cls.orig_messages_package_name
        if not has_messages:
            raise unittest.SkipTest("i18n messages package '%s' not available."
                                    % cls.message_package)
        super(TWNTestCaseBase, cls).setUpClass()


class TestTWTranslate(TWNTestCaseBase):

    """Test twtranslate method."""

    net = False
    message_package = 'tests.i18n'

    def testLocalized(self):
        """Test fully localized entry."""
        self.assertEqual(i18n.twtranslate('en', 'test-localized'),
                         u'test-localized EN')
        self.assertEqual(i18n.twtranslate('nl', 'test-localized'),
                         u'test-localized NL')
        self.assertEqual(i18n.twtranslate('fy', 'test-localized'),
                         u'test-localized FY')

    def testSemiLocalized(self):
        """Test translating with fallback to alternative language."""
        self.assertEqual(i18n.twtranslate('en', 'test-semi-localized'),
                         u'test-semi-localized EN')
        self.assertEqual(i18n.twtranslate('nl', 'test-semi-localized'),
                         u'test-semi-localized NL')
        self.assertEqual(i18n.twtranslate('fy', 'test-semi-localized'),
                         u'test-semi-localized NL')

    def testNonLocalized(self):
        """Test translating non localized entries."""
        self.assertEqual(i18n.twtranslate('en', 'test-non-localized'),
                         u'test-non-localized EN')
        self.assertEqual(i18n.twtranslate('fy', 'test-non-localized'),
                         u'test-non-localized EN')
        self.assertEqual(i18n.twtranslate('nl', 'test-non-localized'),
                         u'test-non-localized EN')
        self.assertEqual(i18n.twtranslate('ru', 'test-non-localized'),
                         u'test-non-localized EN')

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
            u'Bot: Ändere 0 Seiten.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-plural', 1) % {'num': 1},
            u'Bot: Ändere 1 Seite.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-plural', 2) % {'num': 2},
            u'Bot: Ändere 2 Seiten.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-plural', 3) % {'num': 3},
            u'Bot: Ändere 3 Seiten.')
        self.assertEqual(
            i18n.twntranslate('en', 'test-plural', 0) % {'num': 'no'},
            u'Bot: Changing no pages.')
        self.assertEqual(
            i18n.twntranslate('en', 'test-plural', 1) % {'num': 'one'},
            u'Bot: Changing one page.')
        self.assertEqual(
            i18n.twntranslate('en', 'test-plural', 2) % {'num': 'two'},
            u'Bot: Changing two pages.')
        self.assertEqual(
            i18n.twntranslate('en', 'test-plural', 3) % {'num': 'three'},
            u'Bot: Changing three pages.')

    def testString(self):
        """Use a string."""
        self.assertEqual(
            i18n.twntranslate('en', 'test-plural', '1') % {'num': 'one'},
            u'Bot: Changing one page.')

    def testDict(self):
        """Use a dictionary."""
        self.assertEqual(
            i18n.twntranslate('en', 'test-plural', {'num': 2}),
            u'Bot: Changing 2 pages.')

    def testExtended(self):
        """Use additional format strings."""
        self.assertEqual(
            i18n.twntranslate('fr', 'test-plural', {'num': 1, 'descr': 'seulement'}),
            u'Robot: Changer seulement une page.')

    def testExtendedOutside(self):
        """Use additional format strings also outside."""
        self.assertEqual(
            i18n.twntranslate('fr', 'test-plural', 1) % {'descr': 'seulement'},
            u'Robot: Changer seulement une page.')

    def testMultiple(self):
        """Test using multiple plural entries."""
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals', 1)
            % {'action': u'Ändere', 'line': u'eine'},
            u'Bot: Ändere eine Zeile von einer Seite.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals', 2)
            % {'action': u'Ändere', 'line': u'zwei'},
            u'Bot: Ändere zwei Zeilen von mehreren Seiten.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals', 3)
            % {'action': u'Ändere', 'line': u'drei'},
            u'Bot: Ändere drei Zeilen von mehreren Seiten.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals', (1, 2, 2))
            % {'action': u'Ändere', 'line': u'eine'},
            u'Bot: Ändere eine Zeile von mehreren Seiten.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals', [3, 1, 1])
            % {'action': u'Ändere', 'line': u'drei'},
            u'Bot: Ändere drei Zeilen von einer Seite.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals', ["3", 1, 1])
            % {'action': u'Ändere', 'line': u'drei'},
            u'Bot: Ändere drei Zeilen von einer Seite.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals', "321")
            % {'action': u'Ändere', 'line': u'dreihunderteinundzwanzig'},
            u'Bot: Ändere dreihunderteinundzwanzig Zeilen von mehreren Seiten.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals',
                              {'action': u'Ändere', 'line': 1, 'page': 1}),
            u'Bot: Ändere 1 Zeile von einer Seite.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals',
                              {'action': u'Ändere', 'line': 1, 'page': 2}),
            u'Bot: Ändere 1 Zeile von mehreren Seiten.')
        self.assertEqual(
            i18n.twntranslate('de', 'test-multiple-plurals',
                              {'action': u'Ändere', 'line': "11", 'page': 2}),
            u'Bot: Ändere 11 Zeilen von mehreren Seiten.')

    def testMultipleWrongParameterLength(self):
        """Test wrong parameter length."""
        err_msg = 'Length of parameter does not match PLURAL occurrences'
        with self.assertRaisesRegex(ValueError, err_msg):
            i18n.twntranslate('de', 'test-multiple-plurals', (1, 2))

        with self.assertRaisesRegex(ValueError, err_msg):
            i18n.twntranslate('de', 'test-multiple-plurals', ["321"])

    def testMultipleNonNumbers(self):
        """Test error handling for multiple non-numbers."""
        with self.assertRaisesRegex(
            ValueError, r"invalid literal for int\(\) with base 10: 'drei'"
        ):
            i18n.twntranslate('de', 'test-multiple-plurals', ["drei", "1", 1])
        with self.assertRaisesRegex(
            ValueError, r"invalid literal for int\(\) with base 10: 'elf'"
        ):
            i18n.twntranslate('de', 'test-multiple-plurals',
                              {'action': u'Ändere', 'line': "elf", 'page': 2})

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
            i18n.twntranslate('co', 'test-plural', {'num': 0, 'descr': 'seulement'}),
            u'Robot: Changer seulement une page.')
        self.assertEqual(
            i18n.twntranslate('co', 'test-plural', {'num': 1, 'descr': 'seulement'}),
            u'Robot: Changer seulement une page.')


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
        super(InputTestCase, cls).setUpClass()

        if cls.code in i18n.twget_keys(cls.message):
            raise unittest.SkipTest(
                '%s has a translation for %s'
                % (cls.code, cls.message))

    def test_pagegen_i18n_input(self):
        """Test i18n.input fallback via pwb."""
        expect = i18n.twtranslate(self.alt_code, self.message, fallback=False)
        result = self._execute(args=['listpages', '-cat'],
                               data_in='non-existant-category\r\n')
        self.assertIn(expect, result['stderr'])


class MissingPackageTestCase(TWNSetMessagePackageBase,
                             UserInterfaceLangTestCase,
                             DefaultSiteTestCase):

    """Test misssing messages package."""

    message_package = 'scripts.foobar.i18n'

    def _capture_output(self, text, *args, **kwargs):
        self.output_text = text

    def setUp(self):
        """Patch the output and input methods."""
        super(MissingPackageTestCase, self).setUp()
        self.output_text = ''
        self.orig_raw_input = bot.ui._raw_input
        self.orig_output = bot.ui.output
        bot.ui._raw_input = lambda *args, **kwargs: 'dummy input'
        bot.ui.output = self._capture_output

    def tearDown(self):
        """Restore the output and input methods."""
        bot.ui._raw_input = self.orig_raw_input
        bot.ui.output = self.orig_output
        super(MissingPackageTestCase, self).tearDown()

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
            i18n._extract_plural('en', '{{PLURAL:foo|one|other}}', {'foo': 42}),
            'other')
        self.assertEqual(
            i18n._extract_plural('en', '{{PLURAL:foo|one|other}}', {'foo': 1}),
            'one')
        self.assertEqual(
            i18n._extract_plural('en', '{{PLURAL:foo|one|other}}', {'foo': 0}),
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
        with self.assertRaises(IndexError):
            i18n._extract_plural('en', '{{PLURAL:foo|one}}', {'foo': 0})

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


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
