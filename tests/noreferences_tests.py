#!/usr/bin/env python3
#
# (C) Pywikibot team, 2018-2026
#
# Distributed under the terms of the MIT license.
#
"""Test noreferences bot module."""
from __future__ import annotations

import unittest

import pywikibot
from scripts.noreferences import NoReferencesBot
from tests.aspects import TestCase


class TestAddingReferences(TestCase):

    """Test adding references to section."""

    family = 'wikipedia'
    code = 'cs'

    def test_add(self) -> None:
        """Test adding references section."""
        page = pywikibot.Page(self.site, 'foo')
        bot = NoReferencesBot()
        bot.site = self.site
        page.text = '\n== Reference ==\n* [http://www.baz.org Baz]'
        new_text = bot.addReferences(page.text)
        expected = ('\n== Reference ==\n<references />'
                    '\n\n* [http://www.baz.org Baz]')
        self.assertEqual(new_text, expected)

    def test_add_under_templates(self) -> None:
        """Test adding references section under templates in section."""
        page = pywikibot.Page(self.site, 'foo')
        bot = NoReferencesBot()
        bot.site = self.site
        page.text = '\n== Reference ==\n{{Překlad|en|Baz|123456}}'
        new_text = bot.addReferences(page.text)
        expected = page.text + '\n<references />\n'
        self.assertEqual(new_text, expected)

    def test_add_under_comments(self) -> None:
        """Test adding references section under comments in section."""
        page = pywikibot.Page(self.site, 'foo')
        bot = NoReferencesBot()
        bot.site = self.site
        page.text = '\n== Reference ==\n<!-- comment -->\nSome text'
        new_text = bot.addReferences(page.text)
        expected = ('\n== Reference ==\n<!-- comment -->\n<references />\n'
                    '\nSome text')
        self.assertEqual(new_text, expected)


class TestReferencesSpacing(TestCase):

    """Test the blank lines around a newly created references section."""

    family = 'wikipedia'
    code = 'cs'
    dry = True

    def add_references(self, text: str) -> str:
        """Return text with a references section added."""
        bot = NoReferencesBot(site=self.site)
        return bot.addReferences(text)

    def test_bottom_template(self) -> None:
        """Test one blank line before a bottom template."""
        expected = 'Text.\n\n== Reference ==\n<references />\n\n{{tmpl}}\n'
        for newlines in ('\n', '\n\n', '\n\n\n'):
            with self.subTest(newlines=newlines):
                text = f'Text.{newlines}{{{{tmpl}}}}\n'
                self.assertEqual(self.add_references(text), expected)

    def test_category(self) -> None:
        """Test one blank line before a category."""
        expected = ('Text.\n\n== Reference ==\n<references />\n\n'
                    '[[Category:Foo]]\n')
        for newlines in ('\n', '\n\n'):
            with self.subTest(newlines=newlines):
                text = f'Text.{newlines}[[Category:Foo]]\n'
                self.assertEqual(self.add_references(text), expected)

    def test_no_following_text(self) -> None:
        """Test that nothing is added after the references section."""
        self.assertEqual(self.add_references('Text.'),
                         'Text.\n\n== Reference ==\n<references />\n')


if __name__ == '__main__':
    unittest.main()
