#!/usr/bin/env python3
"""Test cosmetic_changes module."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

from pywikibot import Page
from pywikibot.cosmetic_changes import CANCEL, CosmeticChangesToolkit
from pywikibot.site._namespace import NamespacesDict
from pywikibot.tools import has_module
from tests.aspects import TestCase


class TestCosmeticChanges(TestCase):

    """Test cosmetic changes methods."""

    family = 'wikipedia'
    code = 'de'

    @classmethod
    def setUpClass(cls):
        """Setup class for all tests."""
        super().setUpClass()
        cls.cct = CosmeticChangesToolkit(Page(cls.site, 'Test'))


class TestDryCosmeticChanges(TestCosmeticChanges):

    """Test cosmetic_changes not requiring a live wiki."""

    dry = True

    def test_fixSelfInterwiki(self):
        """Test fixSelfInterwiki method."""
        self.assertEqual('[[Foo bar]]',
                         self.cct.fixSelfInterwiki('[[de:Foo bar]]'))
        self.assertEqual('[[Foo bar]]',
                         self.cct.fixSelfInterwiki('[[:de: Foo bar]]'))
        self.assertEqual('[[Foo bar|Bar baz]]',
                         self.cct.fixSelfInterwiki('[[ de: Foo bar|Bar baz]]'))
        self.assertEqual('[[en:Foo bar]]',
                         self.cct.fixSelfInterwiki('[[en:Foo bar]]'))

    def test_standardizePageFooter(self):
        """Test standardizePageFooter method."""
        self.assertEqual('Foo\n{{any template}}\n\n[[Category:Foo]]',
                         self.cct.standardizePageFooter(
                             'Foo\n[[category:foo]]\n{{any template}}'))
        self.assertEqual('Foo\n\n[[Category:Test| ]]\n[[Category:Baz]]',
                         self.cct.standardizePageFooter(
                             'Foo\n\n[[category:baz]]\n[[category:test]]'))
        self.assertEqual('Foo\n\n[[Category:Foo]]\n\n{{Personendaten}}',
                         self.cct.standardizePageFooter(
                             'Foo\n[[category:foo]]\n{{Personendaten}}'))

    def test_resolveHtmlEntities(self):
        """Test resolveHtmlEntities method."""
        self.assertEqual(
            '&amp;#&nbsp;# #0#&#62;#x',
            self.cct.resolveHtmlEntities(
                '&amp;#&nbsp;#&#32;#&#48;#&#62;#&#120;'))
        self.assertEqual(
            '<syntaxhighlight>&#32;</syntaxhighlight>',
            self.cct.resolveHtmlEntities(
                '<syntaxhighlight>&#32;</syntaxhighlight>'))
        self.assertEqual(
            '<!-- &ndash; -->',
            self.cct.resolveHtmlEntities('<!-- &ndash; -->'))

    def test_removeUselessSpaces(self):
        """Test removeUselessSpaces method."""
        self.assertEqual('Foo bar',
                         self.cct.removeUselessSpaces('Foo  bar '))
        self.assertEqual('Foo bar',
                         self.cct.removeUselessSpaces('Foo  bar   '))
        self.assertEqual('Foo bar\nsna fu',
                         self.cct.removeUselessSpaces('Foo  bar \nsna  fu  '))
        # inside comments
        self.assertEqual('<!--Foo  bar -->',
                         self.cct.removeUselessSpaces('<!--Foo  bar -->'))
        # startspace
        self.assertEqual(' Foo  bar ',
                         self.cct.removeUselessSpaces(' Foo  bar '))
        # tab
        self.assertEqual('Fooooo bar',
                         self.cct.removeUselessSpaces('Fooooo bar\t'))

    def test_removeNonBreakingSpaceBeforePercent(self):
        """Test removeNonBreakingSpaceBeforePercent method."""
        self.assertEqual(
            '42 %', self.cct.removeNonBreakingSpaceBeforePercent('42&nbsp;%'))

    def test_cleanUpSectionHeaders(self):
        """Test cleanUpSectionHeaders method."""
        self.assertEqual('=== Header ===\n',
                         self.cct.cleanUpSectionHeaders('===Header===\n'))
        # tab
        self.assertEqual('=== Header ===\n',
                         self.cct.cleanUpSectionHeaders('===Header===\t\n'))
        # tabs inside
        self.assertEqual('=== Header ===\n',
                         self.cct.cleanUpSectionHeaders('===\tHeader\t===\n'))

    def test_putSpacesInLists(self):
        """Test putSpacesInLists method."""
        self.assertEqual('* Foo bar',
                         self.cct.putSpacesInLists('*Foo bar'))
        self.assertEqual('** Foo bar',
                         self.cct.putSpacesInLists('**Foo bar'))
        self.assertEqual('# Foo bar',
                         self.cct.putSpacesInLists('#Foo bar'))
        self.assertEqual('## Foo bar',
                         self.cct.putSpacesInLists('##Foo bar'))
        # right except the page is a redirect page
        self.assertEqual('# redirect',
                         self.cct.putSpacesInLists('#redirect'))
        self.assertEqual('#: Foo bar',
                         self.cct.putSpacesInLists('#:Foo bar'))
        self.assertEqual(':Foo bar',
                         self.cct.putSpacesInLists(':Foo bar'))
        self.assertEqual(':* Foo bar',
                         self.cct.putSpacesInLists(':*Foo bar'))

    def test_replaceDeprecatedTemplates(self):
        """Test replaceDeprecatedTemplates method."""
        self.assertEqual(
            '{{Belege fehlen}}'
            '{{Belege fehlen| }}'
            '{{Belege fehlen|foo}}'
            '{{Belege fehlen|foo}}',
            self.cct.replaceDeprecatedTemplates(
                '{{Quellen fehlen }}'
                '{{Quellen fehlen| }}'
                '{{Quellen fehlen|foo}}'
                '{{Quellen_fehlen|foo}}'
            ))

    def test_fixHtml(self):
        """Test fixHtml method."""
        self.assertEqual("'''Foo''' bar",
                         self.cct.fixHtml('<b>Foo</b> bar'))
        self.assertEqual("Foo '''bar'''",
                         self.cct.fixHtml('Foo <strong>bar</strong>'))
        self.assertEqual("''Foo'' bar",
                         self.cct.fixHtml('<i>Foo</i> bar'))
        self.assertEqual("Foo ''bar''",
                         self.cct.fixHtml('Foo <em>bar</em>'))
        self.assertEqual('\n----\n',
                         self.cct.fixHtml('\n<hr />\n'))
        self.assertEqual('\n=== Header ===\n',
                         self.cct.fixHtml('\n<h3>Header</h3>\n'))

    def test_fixReferences(self):
        """Test fixReferences method."""
        self.assertEqual('<ref name="Foo" />',
                         self.cct.fixReferences('<ref name= "Foo" />'))
        self.assertEqual('<ref name="Foo">bar</ref>',
                         self.cct.fixReferences('<ref name ="Foo">bar</ref>'))
        self.assertEqual('<ref name="Foo"/>',
                         self.cct.fixReferences('<ref name="Foo"></ref>'))
        self.assertEqual('',
                         self.cct.fixReferences('<ref />'))
        self.assertEqual('',
                         self.cct.fixReferences('<ref> \n</ref>'))

    def test_fixTypo(self):
        """Test fixTypo method."""
        self.assertEqual('42&nbsp;cm³',
                         self.cct.fixTypo('42 ccm'))
        self.assertEqual('42&nbsp;°C',
                         self.cct.fixTypo('42 ºC'))

    def test_fixArabicLetters(self):
        """Test fixArabicLetters."""
        text = '1234,كىي'
        # fixArabicLetters must not change text when site is not fa or ckb
        self.assertEqual(text, self.cct.fixArabicLetters(text))


class TestDryFixSyntaxSave(TestCosmeticChanges):

    """Test fixSyntaxSave not requiring a live wiki."""

    dry = True

    @classmethod
    def setUpClass(cls):
        """Setup class for all tests."""
        super().setUpClass()
        cls.cct.site._siteinfo._cache['general'] = (
            {'articlepath': '/wiki/$1'}, True)
        cls.cct.site._namespaces = NamespacesDict({
            6: ['Datei', 'File'],
            14: ['Kategorie', 'Category'],
        })

    def test_title_param(self):
        """Test fixing url with title parameter."""
        # necessary as the fixer needs the article path to fix it
        self.assertEqual(
            '[[Example|Page]]\n[[Example|Page]]\n[[Example|Page]]\n'
            '[[Example]]\n[[Example]]\n[[Example]]\n'
            '[https://de.wikipedia.org/w/index.php?title=Example&'
            'oldid=68181978 Page]\n'
            '[https://de.wikipedia.org/w/index.php?title=Example&'
            'oldid=68181978&diff=next Page]\n'
            '[https://en.wikipedia.org/w/index.php?title=Example]\n'
            '[https://de.wiktionary.org/w/index.php?title=Example]\n',
            self.cct.fixSyntaxSave(
                '[https://de.wikipedia.org/w/index.php?title=Example Page]\n'
                '[https://de.wikipedia.org/w/index.php?title=Example Page ]\n'
                '[https://de.wikipedia.org/w/index.php?title=Example  Page ]\n'
                '[https://de.wikipedia.org/w/index.php?title=Example]\n'
                '[https://de.wikipedia.org/w/index.php?title=Example ]\n'
                '[https://de.wikipedia.org/w/index.php?title=Example  ]\n'
                '[https://de.wikipedia.org/w/index.php?title=Example&'
                'oldid=68181978 Page]\n'
                '[https://de.wikipedia.org/w/index.php?title=Example&'
                'oldid=68181978&diff=next Page]\n'
                '[https://en.wikipedia.org/w/index.php?title=Example]\n'
                '[https://de.wiktionary.org/w/index.php?title=Example]\n'
            ))

    def test_fix_url(self):
        """Test fixing urls."""
        self.assertEqual(
            '[[Example]]\n[[Example]]\n[[Example]]\n'
            '[https://de.wikipedia.org/wiki/Example?oldid=68181978 Page]\n'
            '[https://de.wikipedia.org/wiki/Example?'
            'oldid=68181978&diff=next Page]\n'
            '[[Example]]\n[[Example]]\n[[Example]]\n'
            '[https://de.wikipedia.org/w/index.php/Example?'
            'oldid=68181978 Page]\n'
            '[https://de.wikipedia.org/w/index.php/Example?'
            'oldid=68181978&diff=next Page]\n'
            '[[&]]\n[[&]]\n',
            self.cct.fixSyntaxSave(
                '[https://de.wikipedia.org/wiki/Example]\n'
                '[https://de.wikipedia.org/wiki/Example ]\n'
                '[https://de.wikipedia.org/wiki/Example  ]\n'
                '[https://de.wikipedia.org/wiki/Example?oldid=68181978 Page]\n'
                '[https://de.wikipedia.org/wiki/Example?'
                'oldid=68181978&diff=next Page]\n'
                '[https://de.wikipedia.org/w/index.php/Example]\n'
                '[https://de.wikipedia.org/w/index.php/Example ]\n'
                '[https://de.wikipedia.org/w/index.php/Example  ]\n'
                '[https://de.wikipedia.org/w/index.php/Example?'
                'oldid=68181978 Page]\n'
                '[https://de.wikipedia.org/w/index.php/Example?'
                'oldid=68181978&diff=next Page]\n'
                '[https://de.wikipedia.org/wiki/&]\n'
                '[https://de.wikipedia.org/w/index.php/&]\n'
            ))

    def test_fix_brackets(self):
        """Test fixing brackets."""
        self.assertEqual(
            '[https://de.wikipedia.org]',
            self.cct.fixSyntaxSave('[[https://de.wikipedia.org]]'))

    def test_fix_missing_bracket(self):
        """Test fixing missing bracket."""
        self.assertEqual(
            '[https://de.wikipedia.org]',
            self.cct.fixSyntaxSave('[[https://de.wikipedia.org]'))

    def test_fix_link_text(self):
        """Test fixing link text."""
        self.assertEqual(
            '[https://de.wikipedia.org/w/api.php API]',
            self.cct.fixSyntaxSave('[https://de.wikipedia.org/w/api.php|API]'))

    def test_fix_files_and_categories(self):
        """Test files and categories fix."""
        self.assertEqual(
            '[[:Kategorie:Example]]\n'
            '[[:Category:Example|Description]]\n'
            '[[:Datei:Example.svg]]\n'
            '[[:File:Example.svg|Description]]\n'
            '[[:Category:Example]]\n'
            '[[:Kategorie:Example|Description]]\n'
            '[[:File:Example.svg]]\n'
            '[[:Datei:Example.svg|Description]]\n',
            self.cct.fixSyntaxSave(
                '[https://de.wikipedia.org/wiki/Kategorie:Example]\n'
                '[https://de.wikipedia.org/wiki/Category:Example '
                'Description]\n'
                '[https://de.wikipedia.org/wiki/Datei:Example.svg]\n'
                '[https://de.wikipedia.org/wiki/File:Example.svg '
                'Description]\n'
                '[[https://de.wikipedia.org/wiki/Category:Example]]\n'
                '[[https://de.wikipedia.org/wiki/Kategorie:Example '
                'Description]]\n'
                '[[https://de.wikipedia.org/wiki/File:Example.svg]]\n'
                '[[https://de.wikipedia.org/wiki/Datei:Example.svg '
                'Description]]\n'
            ))


class TestLiveCosmeticChanges(TestCosmeticChanges):

    """Test cosmetic_changes requiring a live wiki."""

    def test_removeEmptySections(self):
        """Test removeEmptySections method."""
        content = '\nSome content'
        # same level
        self.assertEqual(
            '\n==Bar==' + content,
            self.cct.removeEmptySections('\n== Foo ==\n\n==Bar==' + content))
        # different level
        self.assertEqual(
            '\n==Bar==' + content,
            self.cct.removeEmptySections('\n===Foo===\n\n==Bar==' + content))
        testcase = '\n==Foo==\n\n===Bar===' + content
        self.assertEqual(testcase, self.cct.removeEmptySections(testcase))
        # multiple empty sections
        self.assertEqual(
            '\n==Baz==' + content,
            self.cct.removeEmptySections('\n==Foo==\n==Bar==\n==Baz=='
                                         + content))
        # comment inside
        self.assertEqual(
            '\n==Bar==' + content,
            self.cct.removeEmptySections('\n==Foo==\n<!-- Baz -->\n==Bar=='
                                         + content))
        # comments and content between
        testcase = ('\n== Foo ==\n<!-- Baz -->\nBaz\n<!-- Foo -->\n== Bar =='
                    + content)
        self.assertEqual(testcase, self.cct.removeEmptySections(testcase))
        # inside comment
        testcase = '<!--\n==Foo==\n\n==Bar==\n-->' + content
        self.assertEqual(testcase, self.cct.removeEmptySections(testcase))
        testcase = '\n==Foo==\n<!--\n==Bar==\n-->' + content
        self.assertEqual(testcase, self.cct.removeEmptySections(testcase))
        testcase = '<!--\n==Foo==\n-->\n==Bar==' + content
        self.assertEqual(testcase, self.cct.removeEmptySections(testcase))
        # empty list item
        self.assertEqual(
            '\n==Baz==' + content,
            self.cct.removeEmptySections('\n==Foo==\n*\n==Bar==\n#\n==Baz=='
                                         + content))
        self.assertEqual(
            '\n==Baz==' + content,
            self.cct.removeEmptySections('\n==Foo==\n* <!--item-->\n==Baz=='
                                         + content))
        testcase = '\n==Foo==\n* item\n==Bar==' + content
        self.assertEqual(testcase, self.cct.removeEmptySections(testcase))
        # empty first section
        self.assertEqual(
            '==Bar==' + content,
            self.cct.removeEmptySections('==Foo==\n==Bar==' + content))
        # empty last section
        self.assertEqual(
            '\n[[Category:Baz]]',
            self.cct.removeEmptySections('\n==Bar==\n[[Category:Baz]]'))
        # complicated
        self.assertEqual(
            '\n[[Category:Baz]]',
            self.cct.removeEmptySections('\n==Bar==\n* <!--item-->'
                                         '\n[[Category:Baz]]'))
        self.assertEqual(
            '\n[[cs:Foo]]\n[[Category:Baz]]',
            self.cct.removeEmptySections('\n==Bar==\n[[cs:Foo]]'
                                         '\n[[Category:Baz]]'))

    def test_remove_empty_sections_interlanguage_links(self):
        """Test removeEmptySections with edge cases of language links."""
        # When removing language links, do not remove the \n after them,
        # otherwise the sections won't be detected correctly.
        text = 'text [[:en:link]]\n=== title1 ===\ncontent1'
        self.assertEqual(text, self.cct.removeEmptySections(text))
        self.assertEqual(
            't [[en:link]]\n=== 1 ===\nc',
            self.cct.removeEmptySections('t [[en:link]]\n=== 1 ===\nc'))
        # Treat sections that only contain language links as empty sections.
        self.assertEqual(
            't\n[[en:link]]',
            self.cct.removeEmptySections('t\n=== 1 ===\n[[en:link]]'))

    def test_remove_empty_sections_with_heading_comments(self):
        """Test removeEmptySections with comments in the section headings."""
        self.assertEqual(
            '==2==<!--c--> <!--\n-->\nt',
            self.cct.removeEmptySections('==1==\n==2==<!--c--> <!--\n-->\nt'))
        self.assertEqual(
            '==2== <!--c-->\nt',
            self.cct.removeEmptySections('==1==\n==2== <!--c-->\nt'))
        self.assertEqual(
            '==2<!--\n-->==\nt',
            self.cct.removeEmptySections('==1==\n==2<!--\n-->==\nt'))

    def test_translate_and_capitalize_namespaces(self):
        """Test translateAndCapitalizeNamespaces method."""
        self.assertEqual(
            '[[Wikipedia:Test]], [[Wikipedia:Test]], [[Datei:Test]]',
            self.cct.translateAndCapitalizeNamespaces(
                '[[Project:Test]], [[wikipedia:Test]], [[Image:Test]]'))

    def test_translate_magic_words(self):
        """Test translateMagicWords method."""
        self.assertEqual(
            '[[File:Foo.bar|mini]]',
            self.cct.translateMagicWords('[[File:Foo.bar|thumb]]'))
        self.assertEqual(
            '[[File:Foo.bar|mini]]',
            self.cct.translateMagicWords('[[File:Foo.bar|miniatur]]'))
        # test local namespace
        self.assertEqual(
            '[[Datei:Foo.bar|mini]]',
            self.cct.translateMagicWords('[[Datei:Foo.bar|thumb]]'))
        # test multiple magic words
        self.assertEqual(
            '[[File:Foo.bar|links|mini]]',
            self.cct.translateMagicWords('[[File:Foo.bar|left|thumb]]'))
        # test magic words at the end
        self.assertEqual(
            '[[File:Foo.bar|250px|links]]',
            self.cct.translateMagicWords('[[File:Foo.bar|250px|left]]'))
        # test touching unstripped parts and stripping magic words
        self.assertEqual(
            '[[File:Foo.bar|links| 250px]]',
            self.cct.translateMagicWords('[[File:Foo.bar| left | 250px]]'))
        # test magic word with a caption
        self.assertEqual(
            '[[File:Foo.bar|250px|zentriert|Bar]]',
            self.cct.translateMagicWords('[[File:Foo.bar|250px|center|Bar]]'))

    @unittest.expectedFailure
    def test_translateMagicWords_fail(self):
        """
        Test translateMagicWords method.

        The current implementation doesn't check whether the magic word is
        inside a template.
        """
        self.assertEqual(
            '[[File:Foo.bar|{{Baz|thumb|foo}}]]',
            self.cct.translateMagicWords('[[File:Foo.bar|{{Baz|thumb|foo}}]]'))

    def test_cleanUpLinks_pipes(self):
        """Test cleanUpLinks method."""
        self.assertEqual('[[No|no change]]',
                         self.cct.cleanUpLinks('[[no|no change]]'))
        self.assertEqual('[[title]]',
                         self.cct.cleanUpLinks('[[title|title]]'))
        self.assertEqual('[[title]]',
                         self.cct.cleanUpLinks('[[Title|title]]'))
        self.assertEqual('[[sand]]box',
                         self.cct.cleanUpLinks('[[sand|sandbox]]'))
        self.assertEqual('[[sand]]box',
                         self.cct.cleanUpLinks('[[sand|sand]]box'))
        self.assertEqual('[[Sand|demospace]]',
                         self.cct.cleanUpLinks('[[sand|demo]]space'))
        self.assertEqual('[[ß|Eszett]]',
                         self.cct.cleanUpLinks('[[ß|Eszett]]'))
        self.assertEqual('[[Title]]',
                         self.cct.cleanUpLinks('[[title|Title]]'))
        self.assertEqual('[[Sand]]box',
                         self.cct.cleanUpLinks('[[sand|Sandbox]]'))
        self.assertEqual('[[sand]]box',
                         self.cct.cleanUpLinks('[[Sand|sandbox]]'))
        self.assertEqual('[[Sand]]box',
                         self.cct.cleanUpLinks('[[sand|Sand]]box'))
        self.assertEqual('[[sand]]box',
                         self.cct.cleanUpLinks('[[Sand|sand]]box'))

    @unittest.expectedFailure
    def test_cleanup_links(self):
        """Test cleanUpLinks method.

        This method fails for the given samples from library. Either
        the method has to be changed or the examples must be fixed.
        """
        tests = [
            ('text [[title]] text', 'text[[ title ]]text'),
            ('text [[title|name]] text', 'text[[ title | name ]]text'),
            ('text[[title|name]]text', 'text[[ title |name]]text'),
            ('text [[title|name]]text', 'text[[title| name]]text'),
        ]
        for result, text in tests:
            with self.subTest(text=text):
                self.assertEqual(self.cct.cleanUpLinks(text), result)

    def test_replace_deprecated_templates(self):
        """Test replaceDeprecatedTemplates method."""
        self.assertEqual('{{Belege fehlen}}',
                         self.cct.replaceDeprecatedTemplates('{{Belege}}'))
        self.assertEqual(
            '{{Belege fehlen|Test}}',
            self.cct.replaceDeprecatedTemplates('{{Quelle|Test}}'))


class TestCosmeticChangesPersian(TestCosmeticChanges):

    """Test cosmetic changes methods in Persian Wikipedia."""

    family = 'wikipedia'
    code = 'fa'

    def test_fix_arabic_letters_comma(self):
        """Test fixArabicLetters comma replacements."""
        self.assertEqual(self.cct.fixArabicLetters(','), '،')
        self.assertEqual(self.cct.fixArabicLetters('A,b,ا,۴,'),
                         'A,b،ا،۴،')

    def test_fix_arabic_letters_comma_skip(self):
        """Test fixArabicLetters Latin comma not replaced."""
        self.assertEqual(self.cct.fixArabicLetters('a", b'), 'a", b')
        self.assertEqual(self.cct.fixArabicLetters('a, "b'), 'a, "b')
        self.assertEqual(self.cct.fixArabicLetters('a", "b'), 'a", "b')
        # spaces are not required
        self.assertEqual(self.cct.fixArabicLetters('a",b'), 'a",b')
        self.assertEqual(self.cct.fixArabicLetters('a,"b'), 'a,"b')
        self.assertEqual(self.cct.fixArabicLetters('a","b'), 'a","b')
        # quotes are a 'non-Farsi' character; additional non-Farsi not needed
        self.assertEqual(self.cct.fixArabicLetters('",b'), '",b')
        self.assertEqual(self.cct.fixArabicLetters('a,"'), 'a,"')
        self.assertEqual(self.cct.fixArabicLetters('","'), '","')

        # A single quotation is a 'non-Farsi' character
        self.assertEqual(self.cct.fixArabicLetters("',b"), "',b")
        self.assertEqual(self.cct.fixArabicLetters("a,'"), "a,'")
        self.assertEqual(self.cct.fixArabicLetters("','"), "','")

        # A space is a 'non-Farsi' character
        self.assertEqual(self.cct.fixArabicLetters('a", ۴'), 'a", ۴')
        self.assertEqual(self.cct.fixArabicLetters(' , '), ' , ')

    def test_fix_arabic_letters_letters(self):
        """Test fixArabicLetters letter replacements."""
        self.assertEqual(self.cct.fixArabicLetters('ك'),
                         'ک')
        self.assertEqual(self.cct.fixArabicLetters('ي'),
                         'ی')
        self.assertEqual(self.cct.fixArabicLetters('ى'),
                         'ی')
        self.assertEqual(self.cct.fixArabicLetters('كي'),
                         'کی')

        # Once numbering fixes are enabled we can add tests.


class TestCosmeticChangesISBN(TestCosmeticChanges):

    """Test CosmeticChanges ISBN fix."""

    dry = True

    ISBN_DIGITERROR_RE = 'ISBN [0-9]+ is not [0-9]+ digits long'
    ISBN_INVALIDERROR_RE = 'Invalid ISBN found'
    ISBN_CHECKSUMERROR_RE = 'ISBN checksum of [0-9]+ is incorrect'
    ISBN_INVALIDCHECKERROR_RE = 'checksum or check digit is invalid'
    ISBN_INVALIDCHARERROR_RE = 'ISBN [0-9a-zA-Z]+ contains invalid characters'
    ISBN_INVALIDLENGTHERROR_RE = 'The number has an invalid length'

    @classmethod
    def setUpClass(cls):
        """Skip tests if isbn libraries are missing."""
        if not has_module('stdnum', version='1.18'):
            raise unittest.SkipTest('python-stdnum is not available.')
        super().setUpClass()

    def test_valid_isbn(self):
        """Test ISBN."""
        text = self.cct.fix_ISBN(' ISBN 097522980x ')
        self.assertEqual(text, ' ISBN 0-9752298-0-X ')

        text = self.cct.fix_ISBN(' ISBN 9780975229804 ')
        self.assertEqual(text, ' ISBN 978-0-9752298-0-4 ')

        text = self.cct.fix_ISBN(' ISBN 9783955390631 ')
        self.assertEqual(text, ' ISBN 978-3-95539-063-1 ')

        text = self.cct.fix_ISBN(' ISBN 9791091447034 ')
        self.assertEqual(text, ' ISBN 979-10-91447-03-4 ')

    def test_invalid_isbn(self):
        """Test that it'll fail when the ISBN is invalid."""
        from stdnum.exceptions import ValidationError

        # Invalid characters
        with self.assertRaisesRegex(
                ValidationError,
                '|'.join((self.ISBN_DIGITERROR_RE,
                          self.ISBN_INVALIDERROR_RE,
                          self.ISBN_INVALIDLENGTHERROR_RE))):
            self.cct.fix_ISBN('ISBN 0975229LOL')
        # Invalid checksum
        with self.assertRaisesRegex(
                ValidationError,
                '|'.join((self.ISBN_CHECKSUMERROR_RE,
                          self.ISBN_INVALIDERROR_RE,
                          self.ISBN_INVALIDLENGTHERROR_RE,
                          self.ISBN_INVALIDCHECKERROR_RE))):
            self.cct.fix_ISBN('ISBN 0975229801')
        # Invalid length
        with self.assertRaisesRegex(
                ValidationError,
                '|'.join((self.ISBN_DIGITERROR_RE,
                          self.ISBN_INVALIDERROR_RE,
                          self.ISBN_INVALIDLENGTHERROR_RE))):
            self.cct.fix_ISBN('ISBN 09752298')
        # X in the middle
        with self.assertRaisesRegex(
            ValidationError,
            '|'.join((self.ISBN_INVALIDCHARERROR_RE,
                      self.ISBN_INVALIDERROR_RE,
                      self.ISBN_INVALIDLENGTHERROR_RE))):
            self.cct.fix_ISBN('ISBN 09752X9801')

    def test_ignore_invalid_isbn(self):
        """Test fixing ISBN numbers with an invalid ISBN."""
        safe_ignore = self.cct.ignore
        self.cct.ignore = CANCEL.MATCH
        text = self.cct.fix_ISBN(' ISBN 0975229LOL ISBN 9780975229804 ')
        self.assertEqual(text, ' ISBN 0975229LOL ISBN 978-0-9752298-0-4 ')
        self.cct.ignore = safe_ignore


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
