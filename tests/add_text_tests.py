#!/usr/bin/env python3
"""Test add_text script."""
#
# (C) Pywikibot team, 2016-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from unittest.mock import ANY, MagicMock, Mock, mock_open, patch

import pywikibot
import pywikibot.pagegenerators
from scripts.add_text import AddTextBot, main, parse
from tests.aspects import TestCase


def _mock_page(exists=True, redirect=False, talk=False, url='wikipedia.org'):
    """Provides a page with these attributes."""
    page = MagicMock()

    page.exists.return_value = exists
    page.isRedirectPage.return_value = redirect
    page.isTalkPage.return_value = talk
    page.site.getUrl.return_value = url

    page.__str__.return_value = 'mock_page'
    page.site.__str__.return_value = 'mock_site'

    return page


class TestAddTextScript(TestCase):

    """Test add_text script."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    def setUp(self):
        """Setup test."""
        super().setUp()
        pywikibot.bot.ui.clear()
        self.generator_factory = pywikibot.pagegenerators.GeneratorFactory()

    @patch('pywikibot.handle_args', Mock(side_effect=lambda args: args))
    def test_parse(self):
        """Basic argument parsing."""
        args = parse(['-text:"hello world"'], self.generator_factory)
        self.assertEqual('"hello world"', args['text'])
        self.assertFalse(args['up'])
        self.assertTrue(args['reorder'])

        args = parse(['-text:hello', '-up', '-noreorder'],
                     self.generator_factory)
        self.assertEqual('hello', args['text'])
        self.assertTrue(args['up'])
        self.assertFalse(args['reorder'])

    @patch('pywikibot.handle_args', Mock(side_effect=lambda args: args))
    def test_unrecognized_argument(self):
        """Provide an argument that doesn't exist."""
        expected_error = "Argument '-no_such_arg' is unrecognized"

        for invalid_arg in ('-no_such_arg', '-no_such_arg:hello'):
            with self.assertRaisesRegex(ValueError, expected_error):
                parse([invalid_arg], self.generator_factory)

    @patch('pywikibot.handle_args', Mock(side_effect=lambda args: args))
    def test_neither_text_argument(self):
        """Don't provide either -text or -textfile."""
        expected_error = "Either the '-text' or '-textfile' is required"

        with self.assertRaisesRegex(ValueError, expected_error):
            parse(['-noreorder'], self.generator_factory)

    @patch('pywikibot.handle_args', Mock(side_effect=lambda args: args))
    def test_both_text_arguments(self):
        """Provide both -text and -textfile."""
        expected_error = "'-text' and '-textfile' cannot both be used"

        with self.assertRaisesRegex(ValueError, expected_error):
            parse(['-text:hello', '-textfile:/some/path'],
                  self.generator_factory)

    @patch('pywikibot.input')
    @patch('pywikibot.handle_args', Mock(side_effect=lambda args: args))
    def test_argument_prompt(self, input_mock):
        """Reqest an argument that requres a prompt."""
        input_mock.return_value = 'hello world'

        args = parse(['-text'], self.generator_factory)
        self.assertEqual('hello world', args['text'])
        input_mock.assert_called_with('What text do you want to add?')

    @patch('pywikibot.handle_args', Mock(side_effect=lambda args: args))
    def test_main_no_arguments(self):
        """Invoke our main method without any arguments."""
        main()

        self.assertEqual([
            "Either the '-text' or '-textfile' is required\n"
            'Use -help for further information.'
        ], pywikibot.bot.ui.pop_output())

    @patch('pywikibot.handle_args', Mock(side_effect=lambda args: args))
    def test_main_unrecognized_argument(self):
        """Invoke our main method with an invalid argument."""
        main('no_such_arg')

        self.assertEqual([
            "Argument 'no_such_arg' is unrecognized\n"
            'Use -help for further information.',
        ], pywikibot.bot.ui.pop_output())

    @patch('pywikibot.handle_args', Mock(side_effect=lambda args: args))
    def test_main_no_generator_found(self):
        """Invoke main when our generator_factory can't provide a generator."""
        main('-text:hello')

        self.assertEqual([
            'Unable to execute script because no generator was defined.\n'
            'Use -help for further information.'
        ], pywikibot.bot.ui.pop_output())

    def test_setup_with_text(self):
        """Exercise bot with a -text argument."""
        bot = AddTextBot(text='hello\\nworld')

        # setup unescapes any newlines

        self.assertEqual('hello\\nworld', bot.opt.text)
        bot.setup()
        self.assertEqual('hello\nworld', bot.opt.text)

    @patch('builtins.open', new_callable=mock_open, read_data=b'file data')
    def test_setup_with_textfile(self, mock_file):
        """Exercise both with a -textfile argument."""
        bot = AddTextBot(textfile='/path/to/my/file.txt')

        # setup reads the file content

        self.assertEqual('', bot.opt.text)
        bot.setup()
        self.assertEqual('file data', bot.opt.text)

        mock_file.assert_called_with('/path/to/my/file.txt', 'rb', ANY)

    def test_not_skipped(self):
        """Exercise skip_page() with a page we should accept."""
        bot = AddTextBot()
        page = _mock_page()

        self.assertFalse(bot.skip_page(page))
        self.assertEqual([], pywikibot.bot.ui.pop_output())

    def test_skip_missing_standard(self):
        """Exercise skip_page() with a non-talk page that doesn't exist."""
        bot = AddTextBot()
        page = _mock_page(exists=False)

        self.assertTrue(bot.skip_page(page))
        self.assertEqual([
            'Page mock_page does not exist on mock_site.'
        ], pywikibot.bot.ui.pop_output())

    def test_skip_missing_talk(self):
        """Exercise skip_page() with a talk page that doesn't exist."""
        bot = AddTextBot()
        page = _mock_page(exists=False, talk=True)

        self.assertFalse(bot.skip_page(page))
        self.assertEqual([
            "mock_page doesn't exist, creating it!"
        ], pywikibot.bot.ui.pop_output())

    def test_skip_missing_standard_with_create(self):
        """Exercise skip_page() with -create option for a non-talk page."""
        bot = AddTextBot(create=True)
        for exists in (True, False):
            with self.subTest(exists=exists):
                page = _mock_page(exists=exists)

                self.assertFalse(bot.skip_page(page))
                self.assertIsEmpty(pywikibot.bot.ui.pop_output())

    def test_skip_if_redirect(self):
        """Exercise skip_page() with a page that is a redirect."""
        bot = AddTextBot()
        page = _mock_page(redirect=True)

        self.assertTrue(bot.skip_page(page))
        self.assertEqual([
            'Page mock_page on mock_site is skipped because it is a redirect'
        ], pywikibot.bot.ui.pop_output())

    def test_skip_if_url_match(self):
        """Exercise skip_page() with a '-excepturl' argument."""
        bot = AddTextBot(regex_skip_url='.*\\.com')

        page = _mock_page(url='wikipedia.org')
        self.assertFalse(bot.skip_page(page))
        self.assertEqual([], pywikibot.bot.ui.pop_output())

        page = _mock_page(url='wikipedia.com')
        self.assertTrue(bot.skip_page(page))
        self.assertEqual([
            "Skipping mock_page because -excepturl matches ['wikipedia.com']."
        ], pywikibot.bot.ui.pop_output())


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
