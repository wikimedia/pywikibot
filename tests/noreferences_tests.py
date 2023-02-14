#!/usr/bin/env python3
"""Test noreferences bot module."""
#
# (C) Pywikibot team, 2018-2022
#
# Distributed under the terms of the MIT license.
#
import pywikibot
from scripts.noreferences import NoReferencesBot
from tests.aspects import TestCase, unittest


class TestAddingReferences(TestCase):
    """Test adding references to section."""

    family = 'wikipedia'
    code = 'cs'

    def test_add(self):
        """Test adding references section."""
        page = pywikibot.Page(self.site, 'foo')
        bot = NoReferencesBot()
        bot.site = self.site
        page.text = '\n== Reference ==\n* [http://www.baz.org Baz]'
        new_text = bot.addReferences(page.text)
        expected = ('\n== Reference ==\n<references />'
                    '\n\n* [http://www.baz.org Baz]')
        self.assertEqual(new_text, expected)

    def test_add_under_templates(self):
        """Test adding references section under templates in section."""
        page = pywikibot.Page(self.site, 'foo')
        bot = NoReferencesBot()
        bot.site = self.site
        page.text = '\n== Reference ==\n{{Překlad|en|Baz|123456}}'
        new_text = bot.addReferences(page.text)
        expected = page.text + '\n<references />\n'
        self.assertEqual(new_text, expected)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
