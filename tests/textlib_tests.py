# -*- coding: utf-8  -*-
#
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

try:
    import mwparserfromhell
except ImportError:
    mwparserfromhell = False
import codecs
import os

import pywikibot
import pywikibot.textlib as textlib
from pywikibot import config

from tests.aspects import unittest, TestCase

files = {}
dirname = os.path.join(os.path.dirname(__file__), "pages")

for f in ["enwiki_help_editing"]:
    files[f] = codecs.open(os.path.join(dirname, f + ".page"),
                           'r', 'utf-8').read()


class TestSectionFunctions(TestCase):

    net = False

    def setUp(self):
        self.catresult1 = ('[[Category:Cat1]]%(LS)s[[Category:Cat2]]%(LS)s'
                           % {'LS': config.LS})
        super(TestSectionFunctions, self).setUp()

    def contains(self, fn, sn):
        return textlib.does_text_contain_section(
            files[fn], sn)

    def assertContains(self, fn, sn, *args, **kwargs):
        self.assertEqual(self.contains(fn, sn), True, *args, **kwargs)

    def assertNotContains(self, fn, sn, *args, **kwargs):
        self.assertEqual(self.contains(fn, sn), False, *args, **kwargs)

    def testCurrentBehaviour(self):
        self.assertContains("enwiki_help_editing", u"Editing")

    def testExtractTemplates(self):
        if not (pywikibot.config.use_mwparserfromhell and mwparserfromhell):
            return  # We'll test the regex function in the test below
        func = textlib.extract_templates_and_params  # It's really long.
        self.assertEqual(func('{{a}}'), [('a', {})])
        self.assertEqual(func('{{a|b=c}}'), [('a', {'b': 'c'})])
        self.assertEqual(func('{{a|b|c=d}}'), [('a', {u'1': 'b', 'c': 'd'})])
        self.assertEqual(func('{{a|b={{c}}}}'), [(u'a', {u'b': u'{{c}}'}), ('c', {})])

    def testExtractTemplatesRegex(self):
        func = textlib.extract_templates_and_params_regex  # It's really long.
        self.assertEqual(func('{{a}}'), [('a', {})])
        self.assertEqual(func('{{a|b=c}}'), [('a', {'b': 'c'})])
        self.assertEqual(func('{{a|b|c=d}}'), [('a', {u'1': 'b', 'c': 'd'})])
        self.assertEqual(func('{{a|b={{c}}}}'), [('c', {}), (u'a', {u'b': u'{{c}}'})])

    def testSpacesInSection(self):
        self.assertContains("enwiki_help_editing", u"Minor_edits")
        self.assertNotContains("enwiki_help_editing", u"#Minor edits", "Incorrect, '#Minor edits' does not work")
        self.assertNotContains("enwiki_help_editing", u"Minor Edits", "section hashes are case-sensitive")
        self.assertNotContains("enwiki_help_editing", u"Minor_Edits", "section hashes are case-sensitive")

    @unittest.expectedFailure
    def testNonAlphabeticalCharactersInSection(self):
        self.assertContains("enwiki_help_editing", u"Talk_.28discussion.29_pages", "As used in the TOC")
        self.assertContains("enwiki_help_editing", u"Talk_(discussion)_pages", "Understood by mediawiki")

    def test_spaces_outside_section(self):
        self.assertContains("enwiki_help_editing", u"Naming and_moving")
        self.assertContains("enwiki_help_editing", u" Naming and_moving ")
        self.assertContains("enwiki_help_editing", u" Naming and_moving_")

    def test_link_in_section(self):
        # section is ==[[Wiki markup]]==
        self.assertContains("enwiki_help_editing", u"[[Wiki markup]]", "Link as section header")
        self.assertContains("enwiki_help_editing", u"[[:Wiki markup]]", "section header link with preleading colon")
        self.assertNotContains("enwiki_help_editing", u"Wiki markup", "section header must be a link")
        # section is ===[[:Help]]ful tips===
        self.assertContains("enwiki_help_editing", u"[[Help]]ful tips", "Containing link")
        self.assertContains("enwiki_help_editing", u"[[:Help]]ful tips", "Containing link with preleading colon")
        self.assertNotContains("enwiki_help_editing", u"Helpful tips", "section header must contain a link")


class TestFormatFunctions(TestCase):

    family = 'wikipedia'
    code = 'en'

    cached = True

    @classmethod
    def setUpClass(cls):
        super(TestFormatFunctions, cls).setUpClass()
        cls.site = cls.get_site()
        cls.catresult = ('[[Category:Cat1]]%(LS)s[[Category:Cat2]]%(LS)s'
                          % {'LS': config.LS})

    def test_interwiki_format(self):
        interwikis = {
            'de': pywikibot.Page(pywikibot.Link('de:German', self.site)),
            'fr': pywikibot.Page(pywikibot.Link('fr:French', self.site))
        }
        self.assertEqual('[[de:German]]%(LS)s[[fr:French]]%(LS)s'
                         % {'LS': config.LS},
                         textlib.interwikiFormat(interwikis, self.site))

    def test_category_format_raw(self):
        self.assertEqual(self.catresult,
                         textlib.categoryFormat(['[[Category:Cat1]]',
                                                 '[[Category:Cat2]]'],
                                                self.site))

    def test_category_format_bare(self):
        self.assertEqual(self.catresult,
                         textlib.categoryFormat(['Cat1', 'Cat2'], self.site))

    def test_category_format_Category(self):
        data = [pywikibot.Category(self.site, 'Cat1'),
                pywikibot.Category(self.site, 'Cat2')]
        self.assertEqual(self.catresult,
                         textlib.categoryFormat(data, self.site))

    def test_category_format_Page(self):
        data = [pywikibot.Page(self.site, 'Category:Cat1'),
                pywikibot.Page(self.site, 'Category:Cat2')]
        self.assertEqual(self.catresult,
                         textlib.categoryFormat(data, self.site))


class TestCategoryRearrangement(TestCase):

    """
    Tests to ensure that sorting keys are not being lost when
    using .getCategoryLinks() and .replaceCategoryLinks(),
    with both a newline and an empty string as separators.
    """

    family = 'wikipedia'
    code = 'en'

    cached = True

    @classmethod
    def setUpClass(cls):
        super(TestCategoryRearrangement, cls).setUpClass()
        cls.site = cls.get_site()
        cls.old = ('[[Category:Cat1]]%(LS)s[[Category:Cat2|]]%(LS)s'
                   '[[Category:Cat1| ]]%(LS)s[[Category:Cat2|key]]'
                   % {'LS': config.LS})
        cls.cats = textlib.getCategoryLinks(cls.old, site=cls.site)

    def test_standard_links(self):
        new = textlib.replaceCategoryLinks(self.old, self.cats, site=self.site)
        self.assertEqual(self.old, new)

    def test_adjoining_links(self):
        old = self.old.replace(config.LS, '')
        cats = textlib.getCategoryLinks(old, site=self.site)
        self.assertEqual(self.cats, cats)
        sep = config.LS
        config.line_separator = ''  # use an empty separator temporarily
        new = textlib.replaceCategoryLinks(old, cats, site=self.site)
        self.assertEqual(old, new)
        config.line_separator = sep  # restore the default separator


class TestTemplatesInCategory(TestCase):

    """Tests to verify that templates in category links are handled."""

    family = 'wikipedia'
    code = 'en'

    cached = True

    def test_templates(self):
        self.site = self.get_site()
        self.assertEqual(textlib.getCategoryLinks(
            '[[Category:{{P1|Foo}}]]', self.site),
            [pywikibot.page.Category(self.site, 'Foo')])
        self.assertEqual(textlib.getCategoryLinks(
            '[[Category:{{P1|Foo}}|bar]]', self.site),
            [pywikibot.page.Category(self.site, 'Foo', sortKey='bar')])
        self.assertEqual(textlib.getCategoryLinks(
            '[[Category:{{P1|{{P2|L33t|Foo}}}}|bar]]', self.site),
            [pywikibot.page.Category(self.site, 'Foo', sortKey='bar')])
        self.assertEqual(textlib.getCategoryLinks(
            '[[Category:Foo{{!}}bar]]', self.site),
            [pywikibot.page.Category(self.site, 'Foo', sortKey='bar')])
        self.assertEqual(textlib.getCategoryLinks(
            '[[Category:Foo{{!}}bar]][[Category:Wiki{{P2||pedia}}]]',
            self.site),
            [pywikibot.page.Category(self.site, 'Foo', sortKey='bar'),
             pywikibot.page.Category(self.site, 'Wikipedia')])
        self.assertEqual(textlib.getCategoryLinks(
            '[[Category:Foo{{!}}and{{!}}bar]]', self.site),
            [pywikibot.page.Category(self.site, 'Foo', sortKey='and|bar')])
        self.assertRaises(pywikibot.InvalidTitle, textlib.getCategoryLinks,
                          '[[Category:nasty{{{!}}]]', self.site)

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
