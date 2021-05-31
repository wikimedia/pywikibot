"""Test add_text bot module."""
#
# (C) Pywikibot team, 2016-2021
#
# Distributed under the terms of the MIT license.
#
import unittest
from unittest.mock import Mock, patch

import pywikibot
import pywikibot.pagegenerators

from scripts.add_text import add_text, get_text, parse
from tests.aspects import TestCase


class TestAdding(TestCase):

    """Test adding text."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    def setUp(self):
        """Setup test."""
        super().setUp()
        self.page = pywikibot.Page(self.site, 'foo')
        self.generator_factory = pywikibot.pagegenerators.GeneratorFactory()

    @patch('pywikibot.handle_args', Mock(side_effect=lambda args: args))
    def test_parse(self):
        """Basic argument parsing."""
        args = parse(['-text:"hello world"'], self.generator_factory)
        self.assertEqual('"hello world"', args.text)
        self.assertFalse(args.up)
        self.assertTrue(args.reorder)

        args = parse(['-text:hello', '-up', '-noreorder'],
                     self.generator_factory)
        self.assertEqual('hello', args.text)
        self.assertTrue(args.up)
        self.assertFalse(args.reorder)

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
        self.assertEqual('hello world', args.text)
        input_mock.assert_called_with('What text do you want to add?')

    def test_basic(self):
        """Test adding text."""
        (_, newtext, _) = add_text(
            self.page, 'bar', putText=False,
            oldTextGiven='foo\n{{linkfa}}')
        self.assertEqual(
            'foo\n{{linkfa}}\nbar',
            newtext)

    def test_with_category(self):
        """Test adding text before categories."""
        (_, newtext, _) = add_text(
            self.page, 'bar', putText=False,
            oldTextGiven='foo\n[[Category:Foo]]')
        self.assertEqual(
            'foo\nbar\n\n[[Category:Foo]]',
            newtext)

    def test_get_text(self):
        """Test get_text with given text."""
        self.assertEqual(get_text(self.page, 'foo', False), 'foo')


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
