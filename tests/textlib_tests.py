# -*- coding: utf-8  -*-
"""Test textlib module."""
#
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import codecs
import os
import re

import pywikibot
import pywikibot.textlib as textlib

from pywikibot import config
from pywikibot.tools import OrderedDict

from tests.aspects import unittest, TestCase, DefaultDrySiteTestCase

files = {}
dirname = os.path.join(os.path.dirname(__file__), "pages")

for f in ["enwiki_help_editing"]:
    with codecs.open(os.path.join(dirname, f + ".page"),
                     'r', 'utf-8') as content:
        files[f] = content.read()


class TestSectionFunctions(TestCase):

    """Test wikitext section handling function."""

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


class TestFormatInterwiki(TestCase):

    """Test format functions."""

    family = 'wikipedia'
    code = 'en'

    cached = True

    def test_interwiki_format(self):
        interwikis = {
            'de': pywikibot.Page(pywikibot.Link('de:German', self.site)),
            'fr': pywikibot.Page(pywikibot.Link('fr:French', self.site))
        }
        self.assertEqual('[[de:German]]%(LS)s[[fr:French]]%(LS)s'
                         % {'LS': config.LS},
                         textlib.interwikiFormat(interwikis, self.site))


class TestFormatCategory(DefaultDrySiteTestCase):

    """Test category formatting."""

    dry = True

    catresult = ('[[Category:Cat1]]%(LS)s[[Category:Cat2]]%(LS)s'
                 % {'LS': config.LS})

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


class TestCategoryRearrangement(DefaultDrySiteTestCase):

    """
    Ensure that sorting keys are not being lost.

    Tests .getCategoryLinks() and .replaceCategoryLinks(),
    with both a newline and an empty string as separators.
    """

    dry = True

    old = ('[[Category:Cat1]]%(LS)s[[Category:Cat2|]]%(LS)s'
           '[[Category:Cat1| ]]%(LS)s[[Category:Cat2|key]]'
           % {'LS': config.LS})

    def test_standard_links(self):
        cats = textlib.getCategoryLinks(self.old, site=self.site)
        new = textlib.replaceCategoryLinks(self.old, cats, site=self.site)
        self.assertEqual(self.old, new)

    def test_adjoining_links(self):
        cats_std = textlib.getCategoryLinks(self.old, site=self.site)
        old = self.old.replace(config.LS, '')
        cats = textlib.getCategoryLinks(old, site=self.site)
        self.assertEqual(cats_std, cats)
        sep = config.LS
        config.line_separator = ''  # use an empty separator temporarily
        new = textlib.replaceCategoryLinks(old, cats, site=self.site)
        # Restore the default separator.
        config.line_separator = sep
        self.assertEqual(old, new)

    def test_in_place_replace(self):
        """Test in-place category change is reversible."""
        dummy = pywikibot.Category(self.site, 'foo')
        dummy.sortKey = 'bah'

        cats = textlib.getCategoryLinks(self.old, site=self.site)

        # Sanity checking
        temp = textlib.replaceCategoryInPlace(self.old, cats[0], dummy, site=self.site)
        self.assertNotEqual(temp, self.old)
        new = textlib.replaceCategoryInPlace(temp, dummy, cats[0], site=self.site)
        self.assertEqual(self.old, new)

        temp = textlib.replaceCategoryInPlace(self.old, cats[1], dummy, site=self.site)
        self.assertNotEqual(temp, self.old)
        new = textlib.replaceCategoryInPlace(temp, dummy, cats[1], site=self.site)
        self.assertEqual(self.old, new)

        temp = textlib.replaceCategoryInPlace(self.old, cats[2], dummy, site=self.site)
        self.assertNotEqual(temp, self.old)
        new = textlib.replaceCategoryInPlace(temp, dummy, cats[2], site=self.site)
        self.assertEqual(self.old, new)

        temp = textlib.replaceCategoryInPlace(self.old, cats[3], dummy, site=self.site)
        self.assertNotEqual(temp, self.old)
        new = textlib.replaceCategoryInPlace(temp, dummy, cats[3], site=self.site)
        self.assertEqual(self.old, new)

        new_cats = textlib.getCategoryLinks(new, site=self.site)
        self.assertEqual(cats, new_cats)

    def test_in_place_retain_sort(self):
        """Test in-place category change does not alter the sortkey."""
        # sort key should be retained when the new cat sortKey is None
        dummy = pywikibot.Category(self.site, 'foo')
        self.assertIsNone(dummy.sortKey)

        cats = textlib.getCategoryLinks(self.old, site=self.site)

        self.assertEqual(cats[3].sortKey, 'key')
        orig_sortkey = cats[3].sortKey
        temp = textlib.replaceCategoryInPlace(self.old, cats[3], dummy, site=self.site)
        self.assertNotEqual(self.old, temp)
        new_dummy = textlib.getCategoryLinks(temp, site=self.site)[3]
        self.assertIsNotNone(new_dummy.sortKey)
        self.assertEqual(orig_sortkey, new_dummy.sortKey)


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


class TestTemplateParams(TestCase):

    """Test to verify that template params extraction works."""

    net = False

    def _extract_templates_params(self, func):
        self.assertEqual(func('{{a}}'), [('a', OrderedDict())])
        self.assertEqual(func('{{ a}}'), [('a', OrderedDict())])
        self.assertEqual(func('{{a }}'), [('a', OrderedDict())])
        self.assertEqual(func('{{ a }}'), [('a', OrderedDict())])
        self.assertEqual(func('{{a|b=c}}'), [('a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{a|b|c=d}}'), [('a', OrderedDict((('1', 'b'), ('c', 'd'))))])
        self.assertEqual(func('{{a|b=c|f=g|d=e|1=}}'),
                         [('a', OrderedDict((('b', 'c'), ('f', 'g'), ('d', 'e'), ('1', ''))))])
        self.assertEqual(func('{{a|1=2|c=d}}'), [('a', OrderedDict((('1', '2'), ('c', 'd'))))])
        self.assertEqual(func('{{a|c=d|1=2}}'), [('a', OrderedDict((('c', 'd'), ('1', '2'))))])
        self.assertEqual(func('{{a|5=d|a=b}}'), [('a', OrderedDict((('5', 'd'), ('a', 'b'))))])
        self.assertEqual(func('{{a|=2}}'), [('a', OrderedDict((('', '2'), )))])
        self.assertEqual(func('{{a|=|}}'), [('a', OrderedDict((('', ''), ('1', ''))))])
        self.assertEqual(func('{{a||}}'), [('a', OrderedDict((('1', ''), ('2', ''))))])
        self.assertEqual(func('{{a|b={{{1}}}}}'), [('a', OrderedDict((('b', '{{{1}}}'), )))])
        self.assertEqual(func('{{a|b=<noinclude>{{{1}}}</noinclude>}}'),
                         [('a', OrderedDict((('b', '<noinclude>{{{1}}}</noinclude>'), )))])
        self.assertEqual(func('{{subst:a|b=c}}'), [('subst:a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{safesubst:a|b=c}}'), [('safesubst:a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{msgnw:a|b=c}}'), [('msgnw:a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{Template:a|b=c}}'), [('Template:a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{template:a|b=c}}'), [('template:a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{:a|b=c}}'), [(':a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{subst::a|b=c}}'), [('subst::a', OrderedDict((('b', 'c'), )))])

    def test_extract_templates_params_mwpfh(self):
        try:
            import mwparserfromhell  # noqa
        except ImportError:
            raise unittest.SkipTest('mwparserfromhell not available')

        func = textlib.extract_templates_and_params_mwpfh
        self._extract_templates_params(func)

        self.assertEqual(func('{{a|}}'), [('a', OrderedDict((('1', ''), )))])

        self.assertEqual(func('{{a| b=c}}'), [('a', OrderedDict(((' b', 'c'), )))])
        self.assertEqual(func('{{a|b =c}}'), [('a', OrderedDict((('b ', 'c'), )))])
        self.assertEqual(func('{{a|b= c}}'), [('a', OrderedDict((('b', ' c'), )))])
        self.assertEqual(func('{{a|b=c }}'), [('a', OrderedDict((('b', 'c '), )))])

        self.assertEqual(func('{{a| b={{c}}}}'), [('a', OrderedDict(((' b', '{{c}}'), ))), ('c', OrderedDict())])
        self.assertEqual(func('{{a|b={{c}}}}'), [('a', OrderedDict((('b', '{{c}}'), ))), ('c', OrderedDict())])
        self.assertEqual(func('{{a|b= {{c}}}}'), [('a', OrderedDict((('b', ' {{c}}'), ))), ('c', OrderedDict())])
        self.assertEqual(func('{{a|b={{c}} }}'), [('a', OrderedDict((('b', '{{c}} '), ))), ('c', OrderedDict())])

        self.assertEqual(func('{{a|b=<!--{{{1}}}-->}}'), [('a', OrderedDict((('b', '<!--{{{1}}}-->'), )))])

    def test_extract_templates_params_regex(self):
        func = textlib.extract_templates_and_params_regex
        self._extract_templates_params(func)

        self.assertEqual(func('{{a|}}'), [])  # FIXME: this is a bug

        self.assertEqual(func('{{a| b=c}}'), [('a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{a|b =c}}'), [('a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{a|b= c}}'), [('a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{a|b=c }}'), [('a', OrderedDict((('b', 'c'), )))])

        self.assertEqual(func('{{a| b={{c}}}}'), [('c', OrderedDict()), ('a', OrderedDict((('b', '{{c}}'), )))])
        self.assertEqual(func('{{a|b={{c}}}}'), [('c', OrderedDict()), ('a', OrderedDict((('b', '{{c}}'), )))])
        self.assertEqual(func('{{a|b= {{c}}}}'), [('c', OrderedDict()), ('a', OrderedDict((('b', '{{c}}'), )))])
        self.assertEqual(func('{{a|b={{c}} }}'), [('c', OrderedDict()), ('a', OrderedDict((('b', '{{c}}'), )))])

        self.assertEqual(func('{{a|b=<!--{{{1}}}-->}}'), [('a', OrderedDict((('b', ''), )))])

    def test_extract_templates_params(self):
        self._extract_templates_params(
            textlib.extract_templates_and_params)


class TestLocalDigits(TestCase):

    """Test to verify that local digits are correctly being handled."""

    net = False

    def test_to_local(self):
        self.assertEqual(textlib.to_local_digits(299792458, 'en'), 299792458)
        self.assertEqual(
            textlib.to_local_digits(299792458, 'fa'), u"۲۹۹۷۹۲۴۵۸")
        self.assertEqual(
            textlib.to_local_digits(
                u"299792458 flash", 'fa'), u"۲۹۹۷۹۲۴۵۸ flash")
        self.assertEqual(
            textlib.to_local_digits(
                "299792458", 'km'), u"២៩៩៧៩២៤៥៨")


class TestReplaceExcept(DefaultDrySiteTestCase):

    """Test to verify the replacements with exceptions are done correctly."""

    def test_no_replace(self):
        self.assertEqual(textlib.replaceExcept('12345678', 'x', 'y', [],
                                               site=self.site),
                         '12345678')

    def test_simple_replace(self):
        self.assertEqual(textlib.replaceExcept('AxB', 'x', 'y', [],
                                               site=self.site),
                         'AyB')
        self.assertEqual(textlib.replaceExcept('AxxB', 'x', 'y', [],
                                               site=self.site),
                         'AyyB')
        self.assertEqual(textlib.replaceExcept('AxyxB', 'x', 'y', [],
                                               site=self.site),
                         'AyyyB')

    def test_regex_replace(self):
        self.assertEqual(textlib.replaceExcept('A123B', r'\d', r'x', [],
                                               site=self.site),
                         'AxxxB')
        self.assertEqual(textlib.replaceExcept('A123B', r'\d+', r'x', [],
                                               site=self.site),
                         'AxB')
        self.assertEqual(textlib.replaceExcept('A123B',
                                               r'A(\d)2(\d)B', r'A\1x\2B', [],
                                               site=self.site),
                         'A1x3B')
        self.assertEqual(
            textlib.replaceExcept('', r'(a?)', r'\1B', [], site=self.site),
            'B')
        self.assertEqual(
            textlib.replaceExcept('abc', r'x*', r'-', [], site=self.site),
            '-a-b-c-')
        # This is different from re.sub() as re.sub() doesn't allow None groups
        self.assertEqual(
            textlib.replaceExcept('', r'(a)?', r'\1\1', [], site=self.site),
            '')
        self.assertEqual(
            textlib.replaceExcept('A123B', r'A(\d)2(\d)B', r'A\g<1>x\g<2>B',
                                  [], site=self.site),
            'A1x3B')
        self.assertEqual(
            textlib.replaceExcept('A123B', r'A(?P<a>\d)2(?P<b>\d)B',
                                  r'A\g<a>x\g<b>B', [], site=self.site),
            'A1x3B')
        self.assertEqual(
            textlib.replaceExcept('A123B', r'A(?P<a>\d)2(\d)B',
                                  r'A\g<a>x\g<2>B', [], site=self.site),
            'A1x3B')
        self.assertEqual(
            textlib.replaceExcept('A123B', r'A(?P<a>\d)2(\d)B',
                                  r'A\g<a>x\2B', [], site=self.site),
            'A1x3B')

    def test_case_sensitive(self):
        self.assertEqual(textlib.replaceExcept('AxB', 'x', 'y', [],
                                               caseInsensitive=False,
                                               site=self.site),
                         'AyB')
        self.assertEqual(textlib.replaceExcept('AxB', 'X', 'y', [],
                                               caseInsensitive=False,
                                               site=self.site),
                         'AxB')
        self.assertEqual(textlib.replaceExcept('AxB', 'x', 'y', [],
                                               caseInsensitive=True,
                                               site=self.site),
                         'AyB')
        self.assertEqual(textlib.replaceExcept('AxB', 'X', 'y', [],
                                               caseInsensitive=True,
                                               site=self.site),
                         'AyB')

    def test_replace_with_marker(self):
        self.assertEqual(textlib.replaceExcept('AxyxB', 'x', 'y', [],
                                               marker='.',
                                               site=self.site),
                         'Ayyy.B')
        self.assertEqual(textlib.replaceExcept('AxyxB', '1', 'y', [],
                                               marker='.',
                                               site=self.site),
                         'AxyxB.')

    def test_overlapping_replace(self):
        self.assertEqual(textlib.replaceExcept('1111', '11', '21', [],
                                               allowoverlap=False,
                                               site=self.site),
                         '2121')
        self.assertEqual(textlib.replaceExcept('1111', '11', '21', [],
                                               allowoverlap=True,
                                               site=self.site),
                         '2221')

    def test_replace_exception(self):
        self.assertEqual(textlib.replaceExcept('123x123', '123', '000', [],
                                               site=self.site),
                         '000x000')
        self.assertEqual(textlib.replaceExcept('123x123', '123', '000',
                                               [re.compile(r'\w123')],
                                               site=self.site),
                         '000x123')

    def test_replace_tags(self):
        self.assertEqual(textlib.replaceExcept('A <!-- x --> B', 'x', 'y',
                                               ['comment'], site=self.site),
                         'A <!-- x --> B')
        self.assertEqual(textlib.replaceExcept('\n==x==\n', 'x', 'y',
                                               ['header'], site=self.site),
                         '\n==x==\n')
        self.assertEqual(textlib.replaceExcept('<pre>x</pre>', 'x', 'y',
                                               ['pre'], site=self.site),
                         '<pre>x</pre>')
        self.assertEqual(textlib.replaceExcept('<source lang="xml">x</source>',
                                               'x', 'y', ['source'],
                                               site=self.site),
                         '<source lang="xml">x</source>')
        self.assertEqual(textlib.replaceExcept('<syntaxhighlight lang="xml">x</syntaxhighlight>',
                                               'x', 'y', ['source'],
                                               site=self.site),
                         '<syntaxhighlight lang="xml">x</syntaxhighlight>')
        self.assertEqual(textlib.replaceExcept('<ref>x</ref>', 'x', 'y',
                                               ['ref'], site=self.site),
                         '<ref>x</ref>')
        self.assertEqual(textlib.replaceExcept('<ref name="x">A</ref>',
                                               'x', 'y',
                                               ['ref'], site=self.site),
                         '<ref name="x">A</ref>')
        self.assertEqual(textlib.replaceExcept(' xA ', 'x', 'y',
                                               ['startspace'], site=self.site),
                         ' xA ')
        self.assertEqual(textlib.replaceExcept('<table>x</table>', 'x', 'y',
                                               ['table'], site=self.site),
                         '<table>x</table>')
        self.assertEqual(textlib.replaceExcept('x [http://www.sample.com x]',
                                               'x', 'y', ['hyperlink'],
                                               site=self.site),
                         'y [http://www.sample.com y]')
        self.assertEqual(textlib.replaceExcept('x http://www.sample.com/x.html',
                                               'x', 'y',
                                               ['hyperlink'], site=self.site),
                         'y http://www.sample.com/x.html')
        self.assertEqual(textlib.replaceExcept('<gallery>x</gallery>',
                                               'x', 'y', ['gallery'],
                                               site=self.site),
                         '<gallery>x</gallery>')
        self.assertEqual(textlib.replaceExcept('[[x]]', 'x', 'y', ['link'],
                                               site=self.site),
                         '[[x]]')
        self.assertEqual(textlib.replaceExcept('{{#property:p171}}', '1', '2',
                                               ['property'], site=self.site),
                         '{{#property:p171}}')
        self.assertEqual(textlib.replaceExcept('{{#invoke:x}}', 'x', 'y',
                                               ['invoke'], site=self.site),
                         '{{#invoke:x}}')
        for ns_name in self.site.namespaces[14]:
            self.assertEqual(textlib.replaceExcept('[[%s:x]]' % ns_name,
                                                   'x', 'y', ['category'],
                                                   site=self.site),
                             '[[%s:x]]' % ns_name)
        for ns_name in self.site.namespaces[6]:
            self.assertEqual(textlib.replaceExcept('[[%s:x]]' % ns_name,
                                                   'x', 'y', ['file'],
                                                   site=self.site),
                             '[[%s:x]]' % ns_name)

    def test_replace_tags_interwiki(self):
        if 'es' not in self.site.family.langs or 'ey' in self.site.family.langs:
            raise unittest.SkipTest('family %s doesnt have languages'
                                    % self.site)

        self.assertEqual(textlib.replaceExcept('[[es:s]]', 's', 't',
                                               ['interwiki'], site=self.site),
                         '[[es:s]]')  # "es" is a valid interwiki code
        self.assertEqual(textlib.replaceExcept('[[ex:x]]', 'x', 'y',
                                               ['interwiki'], site=self.site),
                         '[[ey:y]]')  # "ex" is not a valid interwiki code

    def test_replace_template(self):
        template_sample = r'{{templatename | url= | accessdate={{Fecha|1993}} |atitle=The [[real title]] }}'
        self.assertEqual(textlib.replaceExcept(template_sample, 'a', 'X',
                                               ['template'], site=self.site),
                         template_sample)

    def test_replace_source_reference(self):
        """Test replacing in text which contains back references."""
        # Don't use a valid reference number in the original string, in case it
        # tries to apply that as a reference.
        self.assertEqual(textlib.replaceExcept(r'\42', r'^(.*)$', r'X\1X',
                                               [], site=self.site),
                         r'X\42X')
        self.assertEqual(textlib.replaceExcept(r'\g<bar>', r'^(?P<foo>.*)$',
                                               r'X\g<foo>X', [], site=self.site),
                         r'X\g<bar>X')


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
