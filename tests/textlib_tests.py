# -*- coding: utf-8  -*-
"""Test textlib module."""
#
# (C) Pywikibot team, 2011-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import codecs
import functools
import os
import re

import pywikibot
import pywikibot.textlib as textlib

from pywikibot import config, UnknownSite
from pywikibot.site import _IWEntry
from pywikibot.tools import OrderedDict

from tests.aspects import (
    unittest, require_modules, TestCase, DefaultDrySiteTestCase,
)

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
        self.assertNotContains('enwiki_help_editing', '#Minor edits',
                               "Incorrect, '#Minor edits' does not work")
        self.assertNotContains('enwiki_help_editing', 'Minor Edits',
                               'section hashes are case-sensitive')
        self.assertNotContains('enwiki_help_editing', 'Minor_Edits',
                               'section hashes are case-sensitive')

    @unittest.expectedFailure
    def testNonAlphabeticalCharactersInSection(self):
        self.assertContains('enwiki_help_editing', 'Talk_.28discussion.29_pages',
                            'As used in the TOC')
        self.assertContains('enwiki_help_editing', 'Talk_(discussion)_pages',
                            'Understood by mediawiki')

    def test_spaces_outside_section(self):
        self.assertContains("enwiki_help_editing", u"Naming and_moving")
        self.assertContains("enwiki_help_editing", u" Naming and_moving ")
        self.assertContains("enwiki_help_editing", u" Naming and_moving_")

    def test_link_in_section(self):
        # section is ==[[Wiki markup]]==
        self.assertContains("enwiki_help_editing", u"[[Wiki markup]]", "Link as section header")
        self.assertContains('enwiki_help_editing', '[[:Wiki markup]]',
                            'section header link with preleading colon')
        self.assertNotContains('enwiki_help_editing', 'Wiki markup',
                               'section header must be a link')
        # section is ===[[:Help]]ful tips===
        self.assertContains('enwiki_help_editing', '[[Help]]ful tips',
                            'Containing link')
        self.assertContains('enwiki_help_editing', '[[:Help]]ful tips',
                            'Containing link with preleading colon')
        self.assertNotContains('enwiki_help_editing', 'Helpful tips',
                               'section header must contain a link')


class TestFormatInterwiki(TestCase):

    """Test format functions."""

    family = 'wikipedia'
    code = 'en'

    cached = True

    def test_interwiki_format(self):
        """Test formatting interwiki links using Page instances."""
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
        """Test formatting categories as strings formatted as links."""
        self.assertEqual(self.catresult,
                         textlib.categoryFormat(['[[Category:Cat1]]',
                                                 '[[Category:Cat2]]'],
                                                self.site))

    def test_category_format_bare(self):
        """Test formatting categories as strings."""
        self.assertEqual(self.catresult,
                         textlib.categoryFormat(['Cat1', 'Cat2'], self.site))

    def test_category_format_Category(self):
        """Test formatting categories as Category instances."""
        data = [pywikibot.Category(self.site, 'Cat1'),
                pywikibot.Category(self.site, 'Cat2')]
        self.assertEqual(self.catresult,
                         textlib.categoryFormat(data, self.site))

    def test_category_format_Page(self):
        """Test formatting categories as Page instances."""
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
        """Test getting and replacing categories."""
        cats = textlib.getCategoryLinks(self.old, site=self.site)
        new = textlib.replaceCategoryLinks(self.old, cats, site=self.site)
        self.assertEqual(self.old, new)

    def test_adjoining_links(self):
        """Test getting and replacing adjacent categories."""
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
        """Test normal templates inside category links."""
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

    def _common_results(self, func):
        """Common cases."""
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

        self.assertEqual(func('{{a|}}'), [('a', OrderedDict((('1', ''), )))])
        self.assertEqual(func('{{a|=|}}'), [('a', OrderedDict((('', ''), ('1', ''))))])
        self.assertEqual(func('{{a||}}'), [('a', OrderedDict((('1', ''), ('2', ''))))])

        self.assertEqual(func('{{a|b={{{1}}}}}'), [('a', OrderedDict((('b', '{{{1}}}'), )))])
        self.assertEqual(func('{{a|b=<noinclude>{{{1}}}</noinclude>}}'),
                         [('a', OrderedDict((('b', '<noinclude>{{{1}}}</noinclude>'), )))])
        self.assertEqual(func('{{subst:a|b=c}}'), [('subst:a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{safesubst:a|b=c}}'),
                         [('safesubst:a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{msgnw:a|b=c}}'), [('msgnw:a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{Template:a|b=c}}'), [('Template:a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{template:a|b=c}}'), [('template:a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{:a|b=c}}'), [(':a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{subst::a|b=c}}'), [('subst::a', OrderedDict((('b', 'c'), )))])

        self.assertEqual(func('{{a|b={{{1}}}|c={{{2}}}}}'),
                         [('a', OrderedDict((('b', '{{{1}}}'), ('c', '{{{2}}}'))))])
        self.assertEqual(func('{{a|b=c}}{{d|e=f}}'),
                         [('a', OrderedDict((('b', 'c'), ))),
                          ('d', OrderedDict((('e', 'f'), )))])

        self.assertEqual(func('{{a|b=<!--{{{1}}}-->}}'),
                         [('a', OrderedDict((('b', '<!--{{{1}}}-->'), )))])

        # initial '{' and '}' should be ignored as outer wikitext
        self.assertEqual(func('{{{a|b}}X}'),
                         [('a', OrderedDict((('1', 'b'), )))])

        # sf.net bug 1575: unclosed template
        self.assertEqual(func('{{a'), [])
        self.assertEqual(func('{{a}}{{foo|'), [('a', OrderedDict())])

    def _etp_regex_differs(self, func):
        """Common cases not handled the same by ETP_REGEX."""
        self.assertEqual(func('{{a| b=c}}'), [('a', OrderedDict(((' b', 'c'), )))])
        self.assertEqual(func('{{a|b =c}}'), [('a', OrderedDict((('b ', 'c'), )))])
        self.assertEqual(func('{{a|b= c}}'), [('a', OrderedDict((('b', ' c'), )))])
        self.assertEqual(func('{{a|b=c }}'), [('a', OrderedDict((('b', 'c '), )))])

        # inner {} should be treated as part of the value
        self.assertEqual(func('{{a|b={} }}'), [('a', OrderedDict((('b', '{} '), )))])

    def _order_differs(self, func):
        """Common cases where the order of templates differs."""
        self.assertCountEqual(func('{{a|b={{c}}}}'),
                              [('a', OrderedDict((('b', '{{c}}'), ))),
                               ('c', OrderedDict())])

        self.assertCountEqual(func('{{a|{{c|d}}}}'),
                              [('c', OrderedDict((('1', 'd'), ))),
                               ('a', OrderedDict([('1', '{{c|d}}')]))])

        # inner '}' after {{b|c}} should be treated as wikitext
        self.assertCountEqual(func('{{a|{{b|c}}}|d}}'),
                              [('a', OrderedDict([('1', '{{b|c}}}'),
                                                  ('2', u'd')])),
                               ('b', OrderedDict([('1', 'c')]))])

    @require_modules('mwparserfromhell')
    def test_extract_templates_params_mwpfh(self):
        """Test using mwparserfromhell."""
        func = textlib.extract_templates_and_params_mwpfh
        self._common_results(func)
        self._order_differs(func)
        self._etp_regex_differs(func)

        self.assertCountEqual(func('{{a|{{c|{{d}}}}}}'),
                              [('c', OrderedDict((('1', '{{d}}'), ))),
                               ('a', OrderedDict([('1', '{{c|{{d}}}}')])),
                               ('d', OrderedDict())
                               ])

        self.assertCountEqual(func('{{a|{{c|{{d|}}}}}}'),
                              [('c', OrderedDict((('1', '{{d|}}'), ))),
                               ('a', OrderedDict([('1', '{{c|{{d|}}}}')])),
                               ('d', OrderedDict([('1', '')]))
                               ])

    def test_extract_templates_params_regex(self):
        """Test using many complex regexes."""
        func = functools.partial(textlib.extract_templates_and_params_regex,
                                 remove_disabled_parts=False)
        self._common_results(func)
        self._order_differs(func)

        self.assertEqual(func('{{a|b={} }}'), [])  # FIXME: {} is normal text

        self.assertEqual(func('{{a| b=c}}'), [('a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{a|b =c}}'), [('a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{a|b= c}}'), [('a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{a|b=c }}'), [('a', OrderedDict((('b', 'c'), )))])

        func = textlib.extract_templates_and_params_regex
        self.assertEqual(func('{{a|b=<!--{{{1}}}-->}}'),
                         [('a', OrderedDict((('b', ''), )))])

        # Identical to mwpfh
        self.assertCountEqual(func('{{a|{{c|{{d}}}}}}'),
                              [('c', OrderedDict((('1', '{{d}}'), ))),
                               ('a', OrderedDict([('1', '{{c|{{d}}}}')])),
                               ('d', OrderedDict())
                               ])

        # However fails to correctly handle three levels of balanced brackets
        # with empty parameters
        self.assertCountEqual(func('{{a|{{c|{{d|}}}}}}'),
                              [('c', OrderedDict((('1', '{{d|}}}'), ))),
                               ('d', OrderedDict([('1', '}')]))
                               ])

    def test_extract_templates_params(self):
        """Test that the normal entry point works."""
        self._common_results(
            textlib.extract_templates_and_params)

    def test_template_simple_regex(self):
        """Test using simple regex."""
        func = textlib.extract_templates_and_params_regex_simple
        self._common_results(func)
        self._etp_regex_differs(func)

        # The simple regex copies the whitespace of mwpfh, but does
        # not have additional entries for nested templates.
        self.assertEqual(func('{{a| b={{c}}}}'),
                         [('a', OrderedDict(((' b', '{{c}}'), )))])
        self.assertEqual(func('{{a|b={{c}}}}'),
                         [('a', OrderedDict((('b', '{{c}}'), )))])
        self.assertEqual(func('{{a|b= {{c}}}}'),
                         [('a', OrderedDict((('b', ' {{c}}'), )))])
        self.assertEqual(func('{{a|b={{c}} }}'),
                         [('a', OrderedDict((('b', '{{c}} '), )))])

        # These three are from _order_differs, and while the first works
        self.assertEqual(func('{{a|{{c}} }}'),
                         [('a', OrderedDict((('1', '{{c}} '), )))])

        # an inner '|' causes extract_template_and_params_regex_simple to
        # split arguments incorrectly in the next two cases.
        self.assertEqual(func('{{a|{{c|d}} }}'),
                         [('a', OrderedDict([('1', '{{c'),
                                             ('2', 'd}} ')]))])

        self.assertEqual(func('{{a|{{b|c}}}|d}}'),
                         [(u'a', OrderedDict([('1', u'{{b'),
                                              ('2', u'c}}}'),
                                              ('3', u'd')]))])

        # Safe fallback to handle arbitary template levels
        # by merging top level templates together.
        # i.e. 'b' is not recognised as a template, and 'foo' is also
        # consumed as part of 'a'.
        self.assertEqual(func('{{a|{{c|{{d|{{e|}}}} }} }} foo {{b}}'),
                         [(None, OrderedDict())])

    def test_regexes(self):
        """_ETP_REGEX, NESTED_TEMPLATE_REGEX and TEMP_REGEX tests."""
        func = textlib._ETP_REGEX.search

        self.assertIsNotNone(func('{{{1}}}'))
        self.assertIsNotNone(func('{{a|b={{{1}}} }}'))
        self.assertIsNotNone(func('{{a|b={{c}} }}'))
        self.assertIsNotNone(func('{{a|b={{c}} }}'))
        self.assertIsNotNone(func('{{a|b={{c|d=1}} }}'))

        self.assertIsNotNone(func('{{a|{{c}} }}'))
        self.assertIsNotNone(func('{{a|{{c|d}} }}'))

        func = textlib._ETP_REGEX.match

        self.assertIsNone(func('{{{1}}}'))

        self.assertIsNotNone(func('{{#if:foo}}'))
        self.assertIsNotNone(func('{{foo:}}'))

        self.assertIsNotNone(func('{{CURRENTYEAR}}'))
        self.assertIsNotNone(func('{{1}}'))

        self.assertIsNone(func('{{a|b={{CURRENTYEAR}} }}'))
        self.assertIsNone(func('{{a|b={{{1}}} }}'))
        self.assertIsNone(func('{{a|b={{c}} }}'))
        self.assertIsNone(func('{{a|b={{c|d=1}} }}'))
        self.assertIsNone(func('{{a|b={} }}'))
        self.assertIsNone(func('{{:a|b={{c|d=1}} }}'))

        self.assertIsNone(func('{{a|{{c}} }}'))
        self.assertIsNone(func('{{a|{{c|d}} }}'))

        func = textlib.TEMP_REGEX.search

        self.assertIsNotNone(func('{{{1}}}'))
        self.assertIsNotNone(func('{{a|b={{c}} }}'))
        self.assertIsNotNone(func('{{a|b={{c|d=1}} }}'))
        self.assertIsNotNone(func('{{a|{{c}} }}'))
        self.assertIsNotNone(func('{{a|{{c|d}} }}'))

        func = textlib.TEMP_REGEX.match

        self.assertIsNotNone(func('{{#if:foo}}'))
        self.assertIsNotNone(func('{{foo:}}'))

        self.assertIsNotNone(func('{{CURRENTYEAR}}'))
        self.assertIsNotNone(func('{{1}}'))

        self.assertIsNotNone(func('{{a|b={{CURRENTYEAR}} }}'))
        self.assertIsNotNone(func('{{a|b={{{1}}} }}'))

        self.assertIsNone(func('{{a|b={{c}} }}'))
        self.assertIsNone(func('{{a|b={{c|d=1}} }}'))
        self.assertIsNotNone(func('{{a|b={} }}'))
        self.assertIsNone(func('{{:a|b={{c|d=1}} }}'))

        self.assertIsNone(func('{{a|{{c}} }}'))
        self.assertIsNone(func('{{a|{{c|d}} }}'))

        func = textlib.NESTED_TEMPLATE_REGEX.search

        # Numerically named templates are rejected
        self.assertIsNone(func('{{1}}'))

        self.assertIsNone(func('{{#if:foo}}'))
        self.assertIsNone(func('{{{1}}}'))
        self.assertIsNone(func('{{{1|}}}'))
        self.assertIsNone(func('{{{15|a}}}'))
        self.assertIsNone(func('{{{1|{{{2|a}}} }}}'))

        self.assertIsNone(func('{{{1|{{2|a}} }}}'))

        func = textlib.NESTED_TEMPLATE_REGEX.match

        self.assertIsNotNone(func('{{CURRENTYEAR}}'))
        self.assertIsNotNone(func('{{foo:bar}}'))
        self.assertIsNone(func('{{1}}'))

        self.assertIsNotNone(func('{{a|b={{CURRENTYEAR}} }}'))
        self.assertIsNotNone(func('{{a|b={{{1}}} }}'))
        self.assertIsNotNone(func('{{a|b={{c}} }}'))
        self.assertIsNotNone(func('{{a|b={{c|d=1}} }}'))
        self.assertIsNotNone(func('{{a|b={} }}'))
        self.assertIsNotNone(func('{{:a|b={{c|d=1}} }}'))

        self.assertIsNotNone(func('{{a|{{c}} }}'))
        self.assertIsNotNone(func('{{a|{{c|d}} }}'))

        # All templates are captured when template depth is greater than 2
        m = func('{{a|{{c|{{d|}} }} | foo  = bar }} foo {{bar}} baz')
        self.assertIsNotNone(m)
        self.assertIsNotNone(m.group(0))
        self.assertIsNone(m.group('name'))
        self.assertIsNone(m.group(1))
        self.assertIsNone(m.group('params'))
        self.assertIsNone(m.group(2))
        self.assertIsNotNone(m.group('unhandled_depth'))
        self.assertTrue(m.group(0).endswith('foo {{bar}}'))


class TestReplaceLinks(TestCase):

    """Test the replace_links function in textlib."""

    sites = {
        'wt': {
            'family': 'wiktionary',
            'code': 'en',
        },
        'wp': {
            'family': 'wikipedia',
            'code': 'en',
        }
    }

    dry = True

    text = ('Hello [[World]], [[how|are]] [[you#section|you]]? Are [[you]] a '
            '[[bug:1337]]?')

    @classmethod
    def setUpClass(cls):
        """Create a fake interwiki cache."""
        super(TestReplaceLinks, cls).setUpClass()
        # make APISite.interwiki work and prevent it from doing requests
        for site in cls.sites.values():
            mapping = {}
            for iw in cls.sites.values():
                mapping[iw['family']] = _IWEntry(True, 'invalid')
                mapping[iw['family']]._site = iw['site']
            mapping['bug'] = _IWEntry(False, 'invalid')
            mapping['bug']._site = UnknownSite('Not a wiki')
            mapping['en'] = _IWEntry(True, 'invalid')
            mapping['en']._site = site['site']
            site['site']._interwikimap._map = mapping
            site['site']._interwikimap._site = None  # prevent it from loading
        cls.wp_site = cls.get_site('wp')

    def test_replacements_function(self):
        """Test a dynamic function as the replacements."""
        def callback(link, text, groups, rng):
            self.assertEqual(link.site, self.wp_site)
            if link.title == 'World':
                return pywikibot.Link('Homeworld', link.site)
            elif link.title.lower() == 'you':
                return False
        self.assertEqual(
            textlib.replace_links(self.text, callback, self.wp_site),
            'Hello [[Homeworld]], [[how|are]] you? Are you a [[bug:1337]]?')

    def test_replacements_once(self):
        """Test dynamic replacement."""
        def callback(link, text, groups, rng):
            if link.title.lower() == 'you':
                self._count += 1
                if link.section:
                    return pywikibot.Link(
                        '{0}#{1}'.format(self._count, link.section), link.site)
                else:
                    return pywikibot.Link('{0}'.format(self._count), link.site)
        self._count = 0  # buffer number of found instances
        self.assertEqual(
            textlib.replace_links(self.text, callback, self.wp_site),
            'Hello [[World]], [[how|are]] [[1#section]]? Are [[2]] a '
            '[[bug:1337]]?')
        del self._count

    def test_unlink_all(self):
        """Test unlinking."""
        def callback(link, text, groups, rng):
            self.assertEqual(link.site, self.wp_site)
            return False
        self.assertEqual(
            textlib.replace_links(self.text, callback, self.wp_site),
            'Hello World, are you? Are you a [[bug:1337]]?')

    def test_unlink_some(self):
        """Test unlinking only some links."""
        self.assertEqual(
            textlib.replace_links(self.text, ('World', False), self.wp_site),
            'Hello World, [[how|are]] [[you#section|you]]? Are [[you]] a '
            '[[bug:1337]]?')
        self.assertEqual(
            textlib.replace_links('[[User:Namespace|Label]]\n'
                                  '[[User:Namespace#Section|Labelz]]\n'
                                  '[[Nothing]]',
                                  ('User:Namespace', False),
                                  self.wp_site),
            'Label\nLabelz\n[[Nothing]]')

    def test_replace_neighbour(self):
        """Test that it replaces two neighbouring links."""
        self.assertEqual(
            textlib.replace_links('[[A]][[A]][[C]]',
                                  ('A', 'B'),
                                  self.wp_site),
            '[[B|A]][[B|A]][[C]]')

    def test_replacements_simplify(self):
        """Test a tuple as a replacement removing the need for a piped link."""
        self.assertEqual(
            textlib.replace_links(self.text,
                                  ('how', 'are'),
                                  self.wp_site),
            'Hello [[World]], [[are]] [[you#section|you]]? Are [[you]] a '
            '[[bug:1337]]?')

    def test_replace_file(self):
        """Test that it respects the namespace."""
        self.assertEqual(
            textlib.replace_links(
                '[[File:Meh.png|thumb|Description of [[fancy]]]] [[Fancy]]...',
                ('File:Meh.png', 'File:Fancy.png'),
                self.wp_site),
            '[[File:Fancy.png|thumb|Description of [[fancy]]]] [[Fancy]]...')

    def test_replace_strings(self):
        """Test if strings can be used."""
        self.assertEqual(
            textlib.replace_links(self.text, ('how', 'are'), self.wp_site),
            'Hello [[World]], [[are]] [[you#section|you]]? Are [[you]] a '
            '[[bug:1337]]?')

    def test_replace_invalid_link_text(self):
        """Test that it doesn't pipe a link when it's an invalid link."""
        self.assertEqual(
            textlib.replace_links('[[Target|Foo:]]', ('Target', 'Foo'), self.wp_site),
            '[[Foo|Foo:]]')

    def test_replace_modes(self):
        """Test replacing with or without label and section."""
        source_text = '[[Foo#bar|baz]]'
        self.assertEqual(
            textlib.replace_links(source_text, ('Foo', 'Bar'), self.wp_site),
            '[[Bar#bar|baz]]')
        self.assertEqual(
            textlib.replace_links(source_text,
                                  ('Foo', pywikibot.Page(self.wp_site, 'Bar')),
                                  self.wp_site),
            '[[Bar#bar|baz]]')
        self.assertEqual(
            textlib.replace_links(source_text,
                                  ('Foo', pywikibot.Link('Bar', self.wp_site)),
                                  self.wp_site),
            '[[Bar]]')
        self.assertEqual(
            textlib.replace_links(source_text, ('Foo', 'Bar#snafu'), self.wp_site),
            '[[Bar#bar|baz]]')
        self.assertEqual(
            textlib.replace_links(source_text,
                                  ('Foo', pywikibot.Page(self.wp_site, 'Bar#snafu')),
                                  self.wp_site),
            '[[Bar#bar|baz]]')
        self.assertEqual(
            textlib.replace_links(source_text,
                                  ('Foo', pywikibot.Link('Bar#snafu', self.wp_site)),
                                  self.wp_site),
            '[[Bar#snafu]]')
        self.assertEqual(
            textlib.replace_links(source_text, ('Foo', 'Bar|foo'), self.wp_site),
            '[[Bar#bar|baz]]')
        self.assertEqual(
            textlib.replace_links(source_text,
                                  ('Foo', pywikibot.Page(self.wp_site, 'Bar|foo')),
                                  self.wp_site),
            '[[Bar#bar|baz]]')
        self.assertEqual(
            textlib.replace_links(source_text,
                                  ('Foo', pywikibot.Link('Bar|foo', self.wp_site)),
                                  self.wp_site),
            '[[Bar|foo]]')
        self.assertEqual(
            textlib.replace_links(source_text, ('Foo', 'Bar#snafu|foo'), self.wp_site),
            '[[Bar#bar|baz]]')
        self.assertEqual(
            textlib.replace_links(source_text,
                                  ('Foo', pywikibot.Page(self.wp_site, 'Bar#snafu|foo')),
                                  self.wp_site),
            '[[Bar#bar|baz]]')
        self.assertEqual(
            textlib.replace_links(source_text,
                                  ('Foo', pywikibot.Link('Bar#snafu|foo', self.wp_site)),
                                  self.wp_site),
            '[[Bar#snafu|foo]]')

    def test_replace_different_case(self):
        """Test that it uses piped links when the case is different."""
        source_text = '[[Foo|Bar]] and [[Foo|bar]]'
        self.assertEqual(
            textlib.replace_links(source_text, ('Foo', 'bar'), self.get_site('wp')),
            '[[Bar]] and [[bar]]')
        self.assertEqual(
            textlib.replace_links(source_text, ('Foo', 'bar'), self.get_site('wt')),
            '[[bar|Bar]] and [[bar]]')
        self.assertEqual(
            textlib.replace_links(source_text, ('Foo', 'Bar'), self.get_site('wt')),
            '[[Bar]] and [[Bar|bar]]')

    @unittest.expectedFailure
    def test_label_diff_namespace(self):
        """Test that it uses the old label when the new doesn't match."""
        # These tests require to get the actual part which is before the title
        # (interwiki and namespace prefixes) which could be then compared
        # case insensitive.
        self.assertEqual(
            textlib.replace_links('[[Image:Foobar]]', ('File:Foobar', 'File:Foo'), self.wp_site),
            '[[File:Foo|Image:Foobar]]')
        self.assertEqual(
            textlib.replace_links('[[en:File:Foobar]]', ('File:Foobar', 'File:Foo'), self.wp_site),
            '[[File:Foo|en:File:Foobar]]')

    def test_linktrails(self):
        """Test that the linktrails are used or applied."""
        self.assertEqual(
            textlib.replace_links('[[Foobar]]', ('Foobar', 'Foo'), self.wp_site),
            '[[Foo]]bar')
        self.assertEqual(
            textlib.replace_links('[[Talk:test]]s', ('Talk:Test', 'Talk:Tests'), self.wp_site),
            '[[Talk:tests]]')
        self.assertEqual(
            textlib.replace_links('[[Talk:test]]s', ('Talk:Test', 'Project:Tests'), self.wp_site),
            '[[Project:Tests|Talk:tests]]')

    def test_unicode_callback(self):
        """Test returning unicode in the callback."""
        def callback(link, text, groups, rng):
            self.assertEqual(link.site, self.wp_site)
            if link.title == 'World':
                # This must be a unicode instance not bytes
                return 'homewörlder'
        self.assertEqual(
            textlib.replace_links(self.text, callback, self.wp_site),
            'Hello homewörlder, [[how|are]] [[you#section|you]]? Are [[you]] a '
            '[[bug:1337]]?')

    def test_bytes_callback(self):
        """Test returning bytes in the callback."""
        def callback(link, text, groups, rng):
            self.assertEqual(link.site, self.wp_site)
            if link.title == 'World':
                # This must be a bytes instance not unicode
                return b'homeworlder'
        self.assertRaisesRegex(
            ValueError, r'unicode \(str.*bytes \(str',
            textlib.replace_links, self.text, callback, self.wp_site)


class TestLocalDigits(TestCase):

    """Test to verify that local digits are correctly being handled."""

    net = False

    def test_to_local(self):
        """Test converting Arabic digits to local digits."""
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
        """Test replacing when the old text does not match."""
        self.assertEqual(textlib.replaceExcept('12345678', 'x', 'y', [],
                                               site=self.site),
                         '12345678')

    def test_simple_replace(self):
        """Test replacing without regex."""
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
        """Test replacing with a regex."""
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
        """Test replacing with different case sensitivity."""
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
        """Test replacing with a marker."""
        self.assertEqual(textlib.replaceExcept('AxyxB', 'x', 'y', [],
                                               marker='.',
                                               site=self.site),
                         'Ayyy.B')
        self.assertEqual(textlib.replaceExcept('AxyxB', '1', 'y', [],
                                               marker='.',
                                               site=self.site),
                         'AxyxB.')

    def test_overlapping_replace(self):
        """Test replacing with and without overlap."""
        self.assertEqual(textlib.replaceExcept('1111', '11', '21', [],
                                               allowoverlap=False,
                                               site=self.site),
                         '2121')
        self.assertEqual(textlib.replaceExcept('1111', '11', '21', [],
                                               allowoverlap=True,
                                               site=self.site),
                         '2221')

    def test_replace_exception(self):
        """Test replacing not inside a specific regex."""
        self.assertEqual(textlib.replaceExcept('123x123', '123', '000', [],
                                               site=self.site),
                         '000x000')
        self.assertEqual(textlib.replaceExcept('123x123', '123', '000',
                                               [re.compile(r'\w123')],
                                               site=self.site),
                         '000x123')

    def test_replace_tags(self):
        """Test replacing not inside various tags."""
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
        """Test replacing not inside interwiki links."""
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
        """Test replacing not inside templates."""
        template_sample = (r'a {{templatename '
                           r'    | accessdate={{Fecha|1993}} '
                           r'    |atitle=The [[real title]] }}')
        self.assertEqual(textlib.replaceExcept(template_sample, 'a', 'X',
                                               ['template'], site=self.site),
                         'X' + template_sample[1:])

        template_sample = (r'a {{templatename '
                           r'    | 1={{a}}2{{a}} '
                           r'    | 2={{a}}1{{a}} }}')
        self.assertEqual(textlib.replaceExcept(template_sample, 'a', 'X',
                                               ['template'], site=self.site),
                         'X' + template_sample[1:])

        template_sample = (r'a {{templatename '
                           r'    | 1={{{a}}}2{{{a}}} '
                           r'    | 2={{{a}}}1{{{a}}} }}')
        self.assertEqual(textlib.replaceExcept(template_sample, 'a', 'X',
                                               ['template'], site=self.site),
                         'X' + template_sample[1:])

        # sf.net bug 1575: unclosed template
        template_sample = template_sample[:-2]
        self.assertEqual(textlib.replaceExcept(template_sample, 'a', 'X',
                                               ['template'], site=self.site),
                         'X' + template_sample[1:])

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
