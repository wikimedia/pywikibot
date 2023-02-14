#!/usr/bin/env python3
"""Test textlib module."""
#
# (C) Pywikibot team, 2011-2023
#
# Distributed under the terms of the MIT license.
#
import codecs
import functools
import os
import re
import unittest
from collections import OrderedDict
from contextlib import suppress
from unittest import mock

import pywikibot
from pywikibot import textlib
from pywikibot.backports import nullcontext
from pywikibot.exceptions import UnknownSiteError
from pywikibot.site._interwikimap import _IWEntry
from pywikibot.textlib import MultiTemplateMatchBuilder, extract_sections
from pywikibot.tools import has_module
from tests.aspects import (
    DefaultDrySiteTestCase,
    SiteAttributeTestCase,
    TestCase,
    require_modules,
)


files = {}
dirname = os.path.join(os.path.dirname(__file__), 'pages')

for f in ['enwiki_help_editing']:
    with codecs.open(os.path.join(dirname, f + '.page'),
                     'r', 'utf-8') as content:
        files[f] = content.read()


class TestSectionFunctions(TestCase):

    """Test wikitext section handling function."""

    net = False

    def setUp(self):
        """Setup tests."""
        self.catresult1 = '[[Category:Cat1]]\n[[Category:Cat2]]\n'
        super().setUp()

    @staticmethod
    def contains(fn, sn):
        """Invoke does_text_contain_section()."""
        return textlib.does_text_contain_section(
            files[fn], sn)

    def assertContains(self, fn, sn, *args, **kwargs):
        """Test that files[fn] contains sn."""
        self.assertEqual(self.contains(fn, sn), True, *args, **kwargs)

    def assertNotContains(self, fn, sn, *args, **kwargs):
        """Test that files[fn] does not contain sn."""
        self.assertEqual(self.contains(fn, sn), False, *args, **kwargs)

    def testCurrentBehaviour(self):
        """Test that 'Editing' is found."""
        self.assertContains('enwiki_help_editing', 'Editing')

    def testSpacesInSection(self):
        """Test with spaces in section."""
        self.assertContains('enwiki_help_editing', 'Minor_edits')
        self.assertNotContains('enwiki_help_editing', '#Minor edits',
                               "Incorrect, '#Minor edits' does not work")
        self.assertNotContains('enwiki_help_editing', 'Minor Edits',
                               'section hashes are case-sensitive')
        self.assertNotContains('enwiki_help_editing', 'Minor_Edits',
                               'section hashes are case-sensitive')

    @unittest.expectedFailure  # TODO: T133276
    def test_encoded_chars_in_section(self):
        """Test encoded chars in section."""
        self.assertContains(
            'enwiki_help_editing', 'Talk_.28discussion.29_pages',
            'As used in the TOC')

    def test_underline_characters_in_section(self):
        """Test with underline chars in section."""
        self.assertContains('enwiki_help_editing', 'Talk_(discussion)_pages',
                            'Understood by mediawiki')

    def test_spaces_outside_section(self):
        """Test with spaces around section."""
        self.assertContains('enwiki_help_editing', 'Naming and_moving')
        self.assertContains('enwiki_help_editing', ' Naming and_moving ')
        self.assertContains('enwiki_help_editing', ' Naming and_moving_')

    def test_link_in_section(self):
        """Test with link inside section."""
        # section is ==[[Wiki markup]]==
        self.assertContains('enwiki_help_editing', '[[Wiki markup]]',
                            'Link as section header')
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

    def test_interwiki_format_Page(self):
        """Test formatting interwiki links using Page instances."""
        interwikis = {
            'de': pywikibot.Page(pywikibot.Link('de:German', self.site)),
            'fr': pywikibot.Page(pywikibot.Link('fr:French', self.site))
        }
        self.assertEqual('[[de:German]]\n[[fr:French]]\n',
                         textlib.interwikiFormat(interwikis, self.site))

    def test_interwiki_format_Link(self):
        """Test formatting interwiki links using Page instances."""
        interwikis = {
            'de': pywikibot.Link('de:German', self.site),
            'fr': pywikibot.Link('fr:French', self.site),
        }
        self.assertEqual('[[de:German]]\n[[fr:French]]\n',
                         textlib.interwikiFormat(interwikis, self.site))


class TestFormatCategory(DefaultDrySiteTestCase):

    """Test category formatting."""

    catresult = '[[Category:Cat1]]\n[[Category:Cat2]]\n'

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


class TestAddText(DefaultDrySiteTestCase):

    """Test add_text function."""

    def test_add_text(self):
        """Test adding text."""
        self.assertEqual(
            textlib.add_text('foo\n[[Category:Foo]]', 'bar', site=self.site),
            'foo\nbar\n\n[[Category:Foo]]'
        )


class TestCategoryRearrangement(DefaultDrySiteTestCase):

    """
    Ensure that sorting keys are not being lost.

    Tests .getCategoryLinks() and .replaceCategoryLinks(),
    with both a newline and an empty string as separators.
    """

    old = '[[Category:Cat1]]\n[[Category:Cat2|]]\n' \
          '[[Category:Cat1| ]]\n[[Category:Cat2|key]]'

    def test_standard_links(self):
        """Test getting and replacing categories."""
        cats = textlib.getCategoryLinks(self.old, site=self.site)
        new = textlib.replaceCategoryLinks(self.old, cats, site=self.site)
        self.assertEqual(self.old, new)

    def test_indentation(self):
        """Test indentation from previous block."""
        # Block of text
        old = 'Some text\n\n' + self.old
        cats = textlib.getCategoryLinks(old, site=self.site)
        new = textlib.replaceCategoryLinks(old, cats, site=self.site)
        self.assertEqual(old, new)

        # DEFAULTSORT
        old_ds = '{{DEFAULTSORT:key}}\n' + self.old
        cats_ds = textlib.getCategoryLinks(old_ds, site=self.site)
        new_ds = textlib.replaceCategoryLinks(old_ds, cats_ds, site=self.site)
        self.assertEqual(old_ds, new_ds)

    def test_in_place_replace(self):
        """Test in-place category change is reversible."""
        dummy = pywikibot.Category(self.site, 'foo')
        dummy.sortKey = 'bah'

        cats = textlib.getCategoryLinks(self.old, site=self.site)

        for count, cat in enumerate(textlib.getCategoryLinks(self.old,
                                                             site=self.site)):
            with self.subTest(category=cat):
                # Sanity checking
                temp = textlib.replaceCategoryInPlace(self.old, cat, dummy,
                                                      site=self.site)
                self.assertNotEqual(temp, self.old)
                new = textlib.replaceCategoryInPlace(temp, dummy, cat,
                                                     site=self.site)
                self.assertEqual(self.old, new)

        self.assertEqual(count, 3)

        # Testing removing categories
        temp = textlib.replaceCategoryInPlace(self.old, cats[0],
                                              None, site=self.site)
        self.assertNotEqual(temp, self.old)
        temp_cats = textlib.getCategoryLinks(temp, site=self.site)
        self.assertNotIn(cats[0], temp_cats)
        # First and third categories are the same
        self.assertEqual([cats[1], cats[3]], temp_cats)

        # Testing adding categories
        temp = textlib.replaceCategoryInPlace(
            self.old, cats[0], cats[1], site=self.site,
            add_only=True)
        self.assertNotEqual(temp, self.old)
        temp_cats = textlib.getCategoryLinks(temp, site=self.site)
        self.assertEqual([cats[0], cats[1], cats[1],
                          cats[2], cats[1], cats[3]], temp_cats)

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
        temp = textlib.replaceCategoryInPlace(self.old, cats[3],
                                              dummy, site=self.site)
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
            '[[Category:{{P1|Foo}}]]', self.site, expand_text=True),
            [pywikibot.page.Category(self.site, 'Foo')])
        self.assertEqual(textlib.getCategoryLinks(
            '[[Category:Foo{{!}}bar]][[Category:Wiki{{P2||pedia}}]]',
            self.site, expand_text=True),
            [pywikibot.page.Category(self.site, 'Foo', sort_key='bar'),
             pywikibot.page.Category(self.site, 'Wikipedia')])
        self.assertEqual(textlib.getCategoryLinks(
            '[[Category:Foo{{!}}and{{!}}bar]]', self.site, expand_text=True),
            [pywikibot.page.Category(self.site, 'Foo', sort_key='and|bar')])

        for pattern in ('[[Category:{{P1|Foo}}|bar]]',
                        '[[Category:{{P1|{{P2|L33t|Foo}}}}|bar]]',
                        '[[Category:Foo{{!}}bar]]'):
            with self.subTest(pattern=pattern):
                self.assertEqual(textlib.getCategoryLinks(
                    pattern, self.site, expand_text=True),
                    [pywikibot.page.Category(self.site, 'Foo',
                                             sort_key='bar')])

        with mock.patch.object(pywikibot, 'warning', autospec=True) as warn:
            textlib.getCategoryLinks('[[Category:nasty{{{!}}]]', self.site)
            warn.assert_called_once_with(
                'Invalid category title extracted: nasty{{{!}}')


class TestTemplateParams(TestCase):

    """Test to verify that template params extraction works."""

    net = False

    def _common_results(self, func):
        """Common cases."""
        self.assertEqual(func('{{a}}'), [('a', OrderedDict())])
        self.assertEqual(func('{{ a}}'), [('a', OrderedDict())])
        self.assertEqual(func('{{a }}'), [('a', OrderedDict())])
        self.assertEqual(func('{{ a }}'), [('a', OrderedDict())])
        self.assertEqual(func('{{a|b=c}}'),
                         [('a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{a|b|c=d}}'),
                         [('a', OrderedDict((('1', 'b'), ('c', 'd'))))])
        self.assertEqual(func('{{a|b=c|f=g|d=e|1=}}'),
                         [('a', OrderedDict((('b', 'c'), ('f', 'g'),
                                             ('d', 'e'), ('1', ''))))])
        self.assertEqual(func('{{a|1=2|c=d}}'),
                         [('a', OrderedDict((('1', '2'), ('c', 'd'))))])
        self.assertEqual(func('{{a|c=d|1=2}}'),
                         [('a', OrderedDict((('c', 'd'), ('1', '2'))))])
        self.assertEqual(func('{{a|5=d|a=b}}'),
                         [('a', OrderedDict((('5', 'd'), ('a', 'b'))))])
        self.assertEqual(func('{{a|=2}}'),
                         [('a', OrderedDict((('', '2'), )))])
        self.assertEqual(func('{{a|}}'),
                         [('a', OrderedDict((('1', ''), )))])
        self.assertEqual(func('{{a|=|}}'),
                         [('a', OrderedDict((('', ''), ('1', ''))))])
        self.assertEqual(func('{{a||}}'),
                         [('a', OrderedDict((('1', ''), ('2', ''))))])
        self.assertEqual(func('{{a|b={{{1}}}}}'),
                         [('a', OrderedDict((('b', '{{{1}}}'), )))])
        self.assertEqual(func('{{a|b=<noinclude>{{{1}}}</noinclude>}}'),
                         [('a',
                           OrderedDict((('b',
                                         '<noinclude>{{{1}}}</noinclude>'),
                                        )))])
        self.assertEqual(func('{{Template:a|b=c}}'),
                         [('Template:a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{template:a|b=c}}'),
                         [('template:a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{:a|b=c}}'),
                         [(':a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{a|b={{{1}}}|c={{{2}}}}}'),
                         [('a', OrderedDict((('b', '{{{1}}}'),
                                             ('c', '{{{2}}}'))))])
        self.assertEqual(func('{{a|b=c}}{{d|e=f}}'),
                         [('a', OrderedDict((('b', 'c'), ))),
                          ('d', OrderedDict((('e', 'f'), )))])

        # initial '{' and '}' should be ignored as outer wikitext
        self.assertEqual(func('{{{a|b}}X}'),
                         [('a', OrderedDict((('1', 'b'), )))])

        # sf.net bug 1575: unclosed template
        self.assertEqual(func('{{a'), [])
        self.assertEqual(func('{{a}}{{foo|'), [('a', OrderedDict())])

    def _unstripped(self, func):
        """Common cases of unstripped results."""
        self.assertEqual(func('{{a|b=<!--{{{1}}}-->}}'),
                         [('a', OrderedDict((('b', '<!--{{{1}}}-->'), )))])

        self.assertEqual(func('{{a|  }}'),
                         [('a', OrderedDict((('1', '  '), )))])
        self.assertEqual(func('{{a| | }}'),
                         [('a', OrderedDict((('1', ' '), ('2', ' '))))])
        self.assertEqual(func('{{a| =|}}'),
                         [('a', OrderedDict(((' ', ''), ('1', ''))))])

        self.assertEqual(func('{{a| b=c}}'),
                         [('a', OrderedDict(((' b', 'c'), )))])
        self.assertEqual(func('{{a|b =c}}'),
                         [('a', OrderedDict((('b ', 'c'), )))])
        self.assertEqual(func('{{a|b= c}}'),
                         [('a', OrderedDict((('b', ' c'), )))])
        self.assertEqual(func('{{a|b=c }}'),
                         [('a', OrderedDict((('b', 'c '), )))])

        self.assertEqual(func('{{a| foo |2= bar }}'),
                         [('a', OrderedDict((('1', ' foo '),
                                             ('2', ' bar '))))])

        # The correct entry 'bar' is removed
        self.assertEqual(func('{{a| foo |2= bar | baz }}'),
                         [('a', OrderedDict((('1', ' foo '),
                                             ('2', ' baz '))))])
        # However whitespace prevents the correct item from being removed
        self.assertEqual(func('{{a| foo | 2 = bar | baz }}'),
                         [('a', OrderedDict((('1', ' foo '), (' 2 ', ' bar '),
                                             ('2', ' baz '))))])

    def _stripped(self, func):
        """Common cases of stripped results."""
        self.assertEqual(func('{{a|  }}'),
                         [('a', OrderedDict((('1', '  '), )))])
        self.assertEqual(func('{{a| | }}'),
                         [('a', OrderedDict((('1', ' '), ('2', ' '))))])
        self.assertEqual(func('{{a| =|}}'),
                         [('a', OrderedDict((('', ''), ('1', ''))))])

        self.assertEqual(func('{{a| b=c}}'),
                         [('a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{a|b =c}}'),
                         [('a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{a|b= c}}'),
                         [('a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{a|b=c }}'),
                         [('a', OrderedDict((('b', 'c'), )))])

        self.assertEqual(func('{{a| foo |2= bar }}'),
                         [('a', OrderedDict((('1', ' foo '), ('2', 'bar'))))])

        # 'bar' is always removed
        self.assertEqual(func('{{a| foo |2= bar | baz }}'),
                         [('a', OrderedDict((('1', ' foo '),
                                             ('2', ' baz '))))])
        self.assertEqual(func('{{a| foo | 2 = bar | baz }}'),
                         [('a', OrderedDict((('1', ' foo '),
                                             ('2', ' baz '))))])

    def _etp_regex_differs(self, func):
        """Common cases not handled the same by ETP_REGEX."""
        # inner {} should be treated as part of the value
        self.assertEqual(func('{{a|b={} }}'),
                         [('a', OrderedDict((('b', '{} '), )))])

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
                                                  ('2', 'd')])),
                               ('b', OrderedDict([('1', 'c')]))])

    def _mwpfh_passes(self, func):
        """Common cases failing with wikitextparser but passes with mwpfh.

        Probably the behaviour of regex or mwpfh is wrong.
        """
        failing = has_module('wikitextparser')
        patterns = [
            '{{subst:a|b=c}}',
            '{{safesubst:a|b=c}}',
            '{{msgnw:a|b=c}}',
            '{{subst::a|b=c}}'
        ]
        context = self.assertRaises(AssertionError) \
            if failing else nullcontext()

        for template in patterns:
            with self.subTest(template=template, failing=failing):
                name = template.strip('{}').split('|')[0]
                with context:
                    self.assertEqual(func(template),
                                     [(name, OrderedDict((('b', 'c'), )))])

    def test_extract_templates_params_mwpfh(self):
        """Test using mwparserfromhell."""
        func = textlib.extract_templates_and_params
        self._common_results(func)
        self._order_differs(func)
        self._unstripped(func)
        self._etp_regex_differs(func)
        self._mwpfh_passes(func)

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

    def test_extract_templates_params_parser_stripped(self):
        """Test using mwparserfromhell with stripping."""
        func = functools.partial(textlib.extract_templates_and_params,
                                 strip=True)

        self._common_results(func)
        self._order_differs(func)
        self._stripped(func)

    @require_modules('wikitextparser')
    def test_extract_templates_params_parser(self):
        """Test using wikitextparser."""
        func = textlib.extract_templates_and_params
        self._common_results(func)
        self._order_differs(func)
        self._unstripped(func)
        self._etp_regex_differs(func)
        self._mwpfh_passes(func)

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

    def test_extract_templates_params(self):
        """Test that the normal entry point works."""
        func = functools.partial(textlib.extract_templates_and_params,
                                 remove_disabled_parts=False, strip=False)

        self._common_results(func)
        self._unstripped(func)

        func = functools.partial(textlib.extract_templates_and_params,
                                 remove_disabled_parts=False, strip=True)
        self._common_results(func)
        self._stripped(func)

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
                         [('a', OrderedDict([('1', '{{b'),
                                             ('2', 'c}}}'),
                                             ('3', 'd')]))])

        # Safe fallback to handle arbitrary template levels
        # by merging top level templates together.
        # i.e. 'b' is not recognised as a template, and 'foo' is also
        # consumed as part of 'a'.
        self.assertEqual(func('{{a|{{c|{{d|{{e|}}}} }} }} foo {{b}}'),
                         [(None, OrderedDict())])

    def test_nested_template_regex_search(self):
        """Test NESTED_TEMPLATE_REGEX search."""
        func = textlib.NESTED_TEMPLATE_REGEX.search

        # Numerically named templates are rejected
        self.assertIsNone(func('{{1}}'))

        self.assertIsNone(func('{{#if:foo}}'))
        self.assertIsNone(func('{{{1}}}'))
        self.assertIsNone(func('{{{1|}}}'))
        self.assertIsNone(func('{{{15|a}}}'))
        self.assertIsNone(func('{{{1|{{{2|a}}} }}}'))

        self.assertIsNone(func('{{{1|{{2|a}} }}}'))

    def test_nested_template_regex_match(self):
        """Test NESTED_TEMPLATE_REGEX match."""
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
        patterns = '{{a|{{c|{{d|}} }} | foo  = bar }} foo {{bar}} baz', \
                   '{{a|\n{{c|{{d|}} }}\n| foo  = bar }} foo {{bar}} baz'
        for pattern in patterns:
            m = func(pattern)
            self.assertIsNotNone(m)
            self.assertIsNotNone(m[0])
            self.assertIsNone(m['name'])
            self.assertIsNone(m[1])
            self.assertIsNone(m['params'])
            self.assertIsNone(m[2])
            self.assertIsNotNone(m['unhandled_depth'])
            self.assertTrue(m[0].endswith('foo {{bar}}'))


class TestDisabledParts(DefaultDrySiteTestCase):

    """Test the removeDisabledParts function in textlib."""

    def test_remove_disabled_parts(self):
        """Test removeDisabledParts function."""
        tests = {
            'comment': '<!-- No comment yet -->',
            'link': '[[Target link]]',
            'source': '<source>foo := bar</source>',
            'template': '{{Infobox\n|foo = bar}}',
            'unknown': '<Unknown>This is an unknown pattern</unKnown>',
        }
        for test, pattern in tests.items():
            with self.subTest(test=test):
                self.assertEqual(
                    textlib.removeDisabledParts(pattern, tags=[test]), '')

    def test_remove_disabled_parts_include(self):
        """Test removeDisabledParts function with the include argument."""
        text = 'text <nowiki>tag</nowiki> text'
        self.assertEqual(
            textlib.removeDisabledParts(text, include=['nowiki']), text)

    def test_remove_disabled_parts_order(self):
        """Test the order of the replacements in removeDisabledParts."""
        text = 'text <ref>This is a reference.</ref> text'
        regex = re.compile('</?ref>')
        self.assertEqual(
            textlib.removeDisabledParts(text, tags=['ref', regex]),
            'text  text')
        self.assertEqual(
            textlib.removeDisabledParts(text, tags=[regex, 'ref']),
            'text This is a reference. text')


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
        super().setUpClass()
        # make APISite.interwiki work and prevent it from doing requests
        for site in cls.sites.values():
            mapping = {}
            for iw in cls.sites.values():
                mapping[iw['family']] = _IWEntry(True, 'invalid')
                mapping[iw['family']]._site = iw['site']
            mapping['bug'] = _IWEntry(False, 'invalid')
            mapping['bug']._site = UnknownSiteError('Not a wiki')
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
            if link.title.lower() == 'you':
                return False

            return None

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
                        '{}#{}'
                        .format(self._count, link.section), link.site)
                return pywikibot.Link(f'{self._count}', link.site)

            return None

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
        """Test a tuple as replacement removing the need for a piped link."""
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
                '[[File:Meh.png|thumb|Description of [[fancy]]]] '
                '[[Fancy]]...', ('File:Meh.png', 'File:Fancy.png'),
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
            textlib.replace_links('[[Target|Foo:]]', ('Target', 'Foo'),
                                  self.wp_site), '[[Foo|Foo:]]')

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
            textlib.replace_links(source_text, ('Foo', 'Bar#snafu'),
                                  self.wp_site),
            '[[Bar#bar|baz]]')
        self.assertEqual(
            textlib.replace_links(source_text,
                                  ('Foo', pywikibot.Page(self.wp_site,
                                                         'Bar#snafu')),
                                  self.wp_site),
            '[[Bar#bar|baz]]')
        self.assertEqual(
            textlib.replace_links(source_text,
                                  ('Foo', pywikibot.Link('Bar#snafu',
                                                         self.wp_site)),
                                  self.wp_site),
            '[[Bar#snafu]]')
        self.assertEqual(
            textlib.replace_links(source_text, ('Foo', 'Bar|foo'),
                                  self.wp_site), '[[Bar#bar|baz]]')
        self.assertEqual(
            textlib.replace_links(source_text,
                                  ('Foo', pywikibot.Page(self.wp_site,
                                                         'Bar|foo')),
                                  self.wp_site),
            '[[Bar#bar|baz]]')
        self.assertEqual(
            textlib.replace_links(source_text,
                                  ('Foo', pywikibot.Link('Bar|foo',
                                                         self.wp_site)),
                                  self.wp_site),
            '[[Bar|foo]]')
        self.assertEqual(
            textlib.replace_links(source_text, ('Foo', 'Bar#snafu|foo'),
                                  self.wp_site), '[[Bar#bar|baz]]')
        self.assertEqual(
            textlib.replace_links(source_text,
                                  ('Foo', pywikibot.Page(self.wp_site,
                                                         'Bar#snafu|foo')),
                                  self.wp_site),
            '[[Bar#bar|baz]]')
        self.assertEqual(
            textlib.replace_links(source_text,
                                  ('Foo', pywikibot.Link('Bar#snafu|foo',
                                                         self.wp_site)),
                                  self.wp_site),
            '[[Bar#snafu|foo]]')

    def test_replace_different_case(self):
        """Test that it uses piped links when the case is different."""
        source_text = '[[Foo|Bar]] and [[Foo|bar]]'
        self.assertEqual(
            textlib.replace_links(source_text, ('Foo', 'bar'),
                                  self.get_site('wp')),
            '[[Bar]] and [[bar]]')
        self.assertEqual(
            textlib.replace_links(source_text, ('Foo', 'bar'),
                                  self.get_site('wt')),
            '[[bar|Bar]] and [[bar]]')
        self.assertEqual(
            textlib.replace_links(source_text, ('Foo', 'Bar'),
                                  self.get_site('wt')),
            '[[Bar]] and [[Bar|bar]]')

    @unittest.expectedFailure
    def test_label_diff_namespace(self):
        """Test that it uses the old label when the new doesn't match."""
        # These tests require to get the actual part which is before the title
        # (interwiki and namespace prefixes) which could be then compared
        # case insensitive.
        tests = [
            ('[[Image:Foobar]]', '[[File:Foo|Image:Foobar]]'),
            ('[[en:File:Foobar]]', '[[File:Foo|en:File:Foobar]]'),
        ]
        for link, result in tests:
            with self.subTest(link=link):
                self.assertEqual(
                    textlib.replace_links(
                        link, ('File:Foobar', 'File:Foo'), self.wp_site),
                    result)

    def test_linktrails(self):
        """Test that the linktrails are used or applied."""
        self.assertEqual(
            textlib.replace_links('[[Foobar]]', ('Foobar', 'Foo'),
                                  self.wp_site),
            '[[Foo]]bar')
        self.assertEqual(
            textlib.replace_links('[[Talk:test]]s',
                                  ('Talk:Test', 'Talk:Tests'), self.wp_site),
            '[[Talk:tests]]')
        self.assertEqual(
            textlib.replace_links('[[Talk:test]]s',
                                  ('Talk:Test', 'Project:Tests'),
                                  self.wp_site),
            '[[Project:Tests|Talk:tests]]')

    def test_unicode_callback(self):
        """Test returning unicode in the callback."""
        def callback(link, text, groups, rng):
            self.assertEqual(link.site, self.wp_site)
            if link.title == 'World':
                # This must be a unicode instance not bytes
                return 'homewörlder'
            return None

        self.assertEqual(
            textlib.replace_links(self.text, callback, self.wp_site),
            'Hello homewörlder, [[how|are]] [[you#section|you]]? '
            'Are [[you]] a [[bug:1337]]?')

    def test_bytes_callback(self):
        """Test returning bytes in the callback."""
        def callback(link, text, groups, rng):
            self.assertEqual(link.site, self.wp_site)
            if link.title == 'World':
                # This must be a bytes instance not unicode
                return b'homeworlder'

            # 'World' is the first link and leads to ValueError
            return None  # pragma: no cover

        with self.assertRaisesRegex(ValueError,
                                    r'The result must be str and not bytes\.'):
            textlib.replace_links(self.text, callback, self.wp_site)

    def test_replace_interwiki_links(self):
        """Make sure interwiki links cannot be replaced."""
        link = '[[fr:how]]'
        self.assertEqual(
            textlib.replace_links(link, ('fr:how', 'de:are'), self.wp_site),
            link)
        self.assertEqual(
            textlib.replace_links(link, (':fr:how', ':de:are'), self.wp_site),
            link)
        self.assertEqual(
            textlib.replace_links(link, ('how', 'de:are'), self.wp_site),
            link)
        self.assertEqual(
            textlib.replace_links(link, ('de:how', 'de:are'), self.wp_site),
            link)


class TestReplaceLinksNonDry(TestCase):
    """Test the replace_links function in textlib non-dry."""

    family = 'wikipedia'
    code = 'en'

    cached = True

    def test_replace_interlanguage_links(self):
        """Test replacing interlanguage links."""
        link = '[[:fr:how]]'
        self.assertEqual(
            textlib.replace_links(link, (':fr:how', ':de:are'),
                                  self.site),
            '[[:de:Are|fr:how]]')
        self.assertEqual(
            textlib.replace_links(link, ('fr:how', 'de:are'),
                                  self.site),
            '[[:de:Are|fr:how]]')
        self.assertEqual(
            textlib.replace_links(link, ('how', ':de:are'),
                                  self.site),
            link)
        self.assertEqual(
            textlib.replace_links(link, (':de:how', ':de:are'),
                                  self.site),
            link)


class TestDigitsConversion(TestCase):

    """Test to verify that local digits are correctly being handled."""

    net = False

    def test_to_local(self):
        """Test converting Latin digits to local digits."""
        self.assertEqual(textlib.to_local_digits(299792458, 'en'), '299792458')
        self.assertEqual(
            textlib.to_local_digits(299792458, 'fa'), '۲۹۹۷۹۲۴۵۸')
        self.assertEqual(
            textlib.to_local_digits(
                '299792458 flash', 'fa'), '۲۹۹۷۹۲۴۵۸ flash')
        self.assertEqual(
            textlib.to_local_digits('299792458', 'km'), '២៩៩៧៩២៤៥៨')

    def test_to_latin(self):
        """Test converting local digits to Latin digits."""
        self.assertEqual(textlib.to_latin_digits('299792458'), '299792458')
        self.assertEqual(
            textlib.to_latin_digits('۲۹۹۷۹۲۴۵۸', 'fa'), '299792458')
        self.assertEqual(
            textlib.to_latin_digits('۲۹۹۷۹۲۴۵۸ flash'), '299792458 flash')
        self.assertEqual(
            textlib.to_latin_digits('២៩៩៧៩២៤៥៨', 'km'), '299792458')
        self.assertEqual(
            textlib.to_latin_digits('២៩៩៧៩២៤៥៨'), '299792458')
        self.assertEqual(
            textlib.to_latin_digits('២៩៩៧៩២៤៥៨', ['km', 'en']), '299792458')
        self.assertEqual(
            textlib.to_latin_digits('២៩៩៧៩២៤៥៨', ['en']), '២៩៩៧៩២៤៥៨')


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
        # This is different from re.sub() as re.sub() doesn't
        # allow None groups
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
        # test regex with lookbehind.
        self.assertEqual(
            textlib.replaceExcept('A behindB C', r'(?<=behind)\w',
                                  r'Z', [], site=self.site),
            'A behindZ C')
        # test regex with lookbehind and groups.
        self.assertEqual(
            textlib.replaceExcept('A behindB C D', r'(?<=behind)\w( )',
                                  r'\g<1>Z', [], site=self.site),
            'A behind ZC D')
        # test regex with lookahead.
        self.assertEqual(
            textlib.replaceExcept('A Bahead C', r'\w(?=ahead)',
                                  r'Z', [], site=self.site),
            'A Zahead C')
        # test regex with lookahead and groups.
        self.assertEqual(
            textlib.replaceExcept('A Bahead C D', r'( )\w(?=ahead)',
                                  r'Z\g<1>', [], site=self.site),
            'AZ ahead C D')

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
        self.assertEqual(textlib.replaceExcept('1\n= 1 =\n', '1', ' \n= 1 =\n',
                                               ['header'],
                                               allowoverlap=True,
                                               site=self.site),
                         ' \n= 1 =\n\n= 1 =\n')

    def test_replace_exception(self):
        """Test replacing not inside a specific regex."""
        self.assertEqual(textlib.replaceExcept('123x123', '123', '000', [],
                                               site=self.site),
                         '000x000')
        self.assertEqual(textlib.replaceExcept('123x123', '123', '000',
                                               [re.compile(r'\w123')],
                                               site=self.site),
                         '000x123')
        self.assertEqual(
            textlib.replaceExcept(
                '1\n= 1 =\n', '1', 'verylongreplacement', ['header'],
                site=self.site),
            'verylongreplacement\n= 1 =\n')

    def test_replace_tags(self):
        """Test replacing not inside various tags."""
        self.assertEqual(textlib.replaceExcept('A <!-- x --> B', 'x', 'y',
                                               ['comment'], site=self.site),
                         'A <!-- x --> B')
        self.assertEqual(textlib.replaceExcept('\n==x==\n', 'x', 'y',
                                               ['header'], site=self.site),
                         '\n==x==\n')
        self.assertEqual(textlib.replaceExcept('\n<!--'
                                               '\ncomment-->==x==<!--comment'
                                               '\n-->\n', 'x', 'y',
                                               ['header'], site=self.site),
                         '\n<!--\ncomment-->==x==<!--comment\n-->\n')
        self.assertEqual(textlib.replaceExcept('<pre>x</pre>', 'x', 'y',
                                               ['pre'], site=self.site),
                         '<pre>x</pre>')
        self.assertEqual(textlib.replaceExcept('<nowiki   >x</nowiki    >x',
                                               'x', 'y', ['nowiki'],
                                               site=self.site),
                         '<nowiki   >x</nowiki    >y')  # T191559
        self.assertEqual(textlib.replaceExcept('<source lang="xml">x</source>',
                                               'x', 'y', ['source'],
                                               site=self.site),
                         '<source lang="xml">x</source>')
        self.assertEqual(
            textlib.replaceExcept('<syntaxhighlight>x</syntaxhighlight>',
                                  'x', 'y', ['source'], site=self.site),
            '<syntaxhighlight>x</syntaxhighlight>')
        self.assertEqual(
            textlib.replaceExcept(
                '<syntaxhighlight lang="xml">x</syntaxhighlight>',
                'x', 'y', ['source'], site=self.site),
            '<syntaxhighlight lang="xml">x</syntaxhighlight>')
        self.assertEqual(
            textlib.replaceExcept('<source>x</source>',
                                  'x', 'y', ['syntaxhighlight'],
                                  site=self.site),
            '<source>x</source>')
        self.assertEqual(textlib.replaceExcept('<includeonly>x</includeonly>',
                                               'x', 'y', ['includeonly'],
                                               site=self.site),
                         '<includeonly>x</includeonly>')
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
        self.assertEqual(textlib.replaceExcept(':xA ', 'x', 'y',
                                               ['startcolon'], site=self.site),
                         ':xA ')
        self.assertEqual(textlib.replaceExcept('<table>x</table>', 'x', 'y',
                                               ['table'], site=self.site),
                         '<table>x</table>')
        self.assertEqual(textlib.replaceExcept('x [http://www.sample.com x]',
                                               'x', 'y', ['hyperlink'],
                                               site=self.site),
                         'y [http://www.sample.com y]')
        self.assertEqual(textlib.replaceExcept(
            'x http://www.sample.com/x.html', 'x', 'y',
            ['hyperlink'], site=self.site), 'y http://www.sample.com/x.html')
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
        self.assertEqual(
            textlib.replaceExcept(
                '<ref name=etwa /> not_in_ref <ref> in_ref </ref>',
                'not_in_ref', 'text', ['ref'], site=self.site),
            '<ref name=etwa /> text <ref> in_ref </ref>')
        self.assertEqual(
            textlib.replaceExcept(
                '<ab> content </a>', 'content', 'text', ['a'], site=self.site),
            '<ab> text </a>')

    def test_replace_with_count(self):
        """Test replacing with count argument."""
        self.assertEqual(textlib.replaceExcept('x [[x]] x x', 'x', 'y', [],
                                               site=self.site),
                         'y [[y]] y y')
        self.assertEqual(textlib.replaceExcept('x [[x]] x x', 'x', 'y', [],
                                               site=self.site, count=5),
                         'y [[y]] y y')
        self.assertEqual(textlib.replaceExcept('x [[x]] x x', 'x', 'y', [],
                                               site=self.site, count=2),
                         'y [[y]] x x')
        self.assertEqual(textlib.replaceExcept(
            'x [[x]] x x', 'x', 'y', ['link'], site=self.site, count=2),
            'y [[x]] y x')

    def test_replace_tag_category(self):
        """Test replacing not inside category links."""
        for ns_name in self.site.namespaces[14]:
            self.assertEqual(textlib.replaceExcept(f'[[{ns_name}:x]]',
                                                   'x', 'y', ['category'],
                                                   site=self.site),
                             f'[[{ns_name}:x]]')

    def test_replace_tag_file(self):
        """Test replacing not inside file links."""
        for ns_name in self.site.namespaces[6]:
            self.assertEqual(textlib.replaceExcept(f'[[{ns_name}:x]]',
                                                   'x', 'y', ['file'],
                                                   site=self.site),
                             f'[[{ns_name}:x]]')

        self.assertEqual(
            textlib.replaceExcept(
                '[[File:x|foo]]',
                'x', 'y', ['file'], site=self.site),
            '[[File:x|foo]]')

        self.assertEqual(
            textlib.replaceExcept(
                '[[File:x|]]',
                'x', 'y', ['file'], site=self.site),
            '[[File:x|]]')

        self.assertEqual(
            textlib.replaceExcept(
                '[[File:x|foo|bar x]] x',
                'x', 'y', ['file'], site=self.site),
            '[[File:x|foo|bar x]] y')

        self.assertEqual(
            textlib.replaceExcept(
                '[[File:x|]][[File:x|foo]]',
                'x', 'y', ['file'], site=self.site),
            '[[File:x|]][[File:x|foo]]')

        self.assertEqual(
            textlib.replaceExcept(
                '[[NonFile:x]]',
                'x', 'y', ['file'], site=self.site),
            '[[NonFile:y]]')

        self.assertEqual(
            textlib.replaceExcept(
                '[[File:]]',
                'File:', 'NonFile:', ['file'], site=self.site),
            '[[File:]]')

        self.assertEqual(
            textlib.replaceExcept(
                '[[File:x|[[foo]].]]',
                'x', 'y', ['file'], site=self.site),
            '[[File:x|[[foo]].]]')

        # ensure only links inside file are captured
        self.assertEqual(
            textlib.replaceExcept(
                '[[File:a|[[foo]].x]][[x]]',
                'x', 'y', ['file'], site=self.site),
            '[[File:a|[[foo]].x]][[y]]')

        self.assertEqual(
            textlib.replaceExcept(
                '[[File:a|[[foo]][[bar]].x]][[x]]',
                'x', 'y', ['file'], site=self.site),
            '[[File:a|[[foo]][[bar]].x]][[y]]')

        self.assertEqual(
            textlib.replaceExcept(
                '[[File:a|[[foo]][[bar]].x]][[x]]',
                'x', 'y', ['file'], site=self.site),
            '[[File:a|[[foo]][[bar]].x]][[y]]')

        # Correctly handle single brackets in the text.
        self.assertEqual(
            textlib.replaceExcept(
                '[[File:a|[[foo]] [bar].x]][[x]]',
                'x', 'y', ['file'], site=self.site),
            '[[File:a|[[foo]] [bar].x]][[y]]')

        self.assertEqual(
            textlib.replaceExcept(
                '[[File:a|[bar] [[foo]] .x]][[x]]',
                'x', 'y', ['file'], site=self.site),
            '[[File:a|[bar] [[foo]] .x]][[y]]')

    def test_replace_tag_file_invalid(self):
        """Test replacing not inside file links with invalid titles."""
        # Correctly handle [ and ] inside wikilinks inside file link
        # even though these are an invalid title.
        self.assertEqual(
            textlib.replaceExcept(
                '[[File:a|[[foo]] [[bar [invalid] ]].x]][[x]]',
                'x', 'y', ['file'], site=self.site),
            '[[File:a|[[foo]] [[bar [invalid] ]].x]][[y]]')

        self.assertEqual(
            textlib.replaceExcept(
                '[[File:a|[[foo]] [[bar [invalid ]].x]][[x]]',
                'x', 'y', ['file'], site=self.site),
            '[[File:a|[[foo]] [[bar [invalid ]].x]][[y]]')

    @unittest.expectedFailure
    def test_replace_tag_file_failure(self):
        """Test showing limits of the file link regex."""
        # When the double brackets are unbalanced, the regex
        # does not correctly detect the end of the file link.
        self.assertEqual(
            textlib.replaceExcept(
                '[[File:a|[[foo]] [[bar [[invalid ]].x]][[x]]',
                'x', 'y', ['file'], site=self.site),
            '[[File:a|[[foo]] [[bar [invalid] ]].x]][[y]]')

    def test_replace_tags_interwiki(self):
        """Test replacing not inside interwiki links."""
        if ('es' not in self.site.family.langs
                or 'ey' in self.site.family.langs):
            raise unittest.SkipTest("family {} doesn't have languages"
                                    .format(self.site))

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
        # Don't use a valid reference number in the original string,
        # in case it tries to apply that as a reference.
        self.assertEqual(textlib.replaceExcept(r'\42', r'^(.*)$', r'X\1X',
                                               [], site=self.site),
                         r'X\42X')
        self.assertEqual(textlib.replaceExcept(
            r'\g<bar>', r'^(?P<foo>.*)$', r'X\g<foo>X', [], site=self.site),
            r'X\g<bar>X')


class TestMultiTemplateMatchBuilder(DefaultDrySiteTestCase):

    """Test MultiTemplateMatchBuilder."""

    @classmethod
    def setUpClass(cls):
        """Cache namespace 10 (Template) case sensitivity."""
        super().setUpClass()
        cls._template_not_case_sensitive = (
            cls.get_site().namespaces.TEMPLATE.case != 'case-sensitive')

    def test_no_match(self):
        """Test text without any desired templates."""
        string = 'The quick brown fox'
        builder = MultiTemplateMatchBuilder(self.site)
        self.assertIsNone(re.search(builder.pattern('quick'), string))

    def test_match(self):
        """Test text with one match without parameters."""
        string = 'The {{quick}} brown fox'
        builder = MultiTemplateMatchBuilder(self.site)
        self.assertIsNotNone(re.search(builder.pattern('quick'), string))
        self.assertEqual(bool(re.search(builder.pattern('Quick'), string)),
                         self._template_not_case_sensitive)

    def test_match_with_params(self):
        """Test text with one match with parameters."""
        string = 'The {{quick|brown}} fox'
        builder = MultiTemplateMatchBuilder(self.site)
        self.assertIsNotNone(re.search(builder.pattern('quick'), string))
        self.assertEqual(bool(re.search(builder.pattern('Quick'), string)),
                         self._template_not_case_sensitive)

    def test_match_msg(self):
        """Test text with {{msg:..}}."""
        string = 'The {{msg:quick}} brown fox'
        builder = MultiTemplateMatchBuilder(self.site)
        self.assertIsNotNone(re.search(builder.pattern('quick'), string))
        self.assertEqual(bool(re.search(builder.pattern('Quick'), string)),
                         self._template_not_case_sensitive)

    def test_match_template_prefix(self):
        """Test pages with {{template:..}}."""
        string = 'The {{%s:%s}} brown fox'
        template = 'template'
        builder = MultiTemplateMatchBuilder(self.site)
        if self._template_not_case_sensitive:
            quick_list = ('quick', 'Quick')
        else:
            quick_list = ('quick', )

        for t in (template.upper(), template.lower(), template.title()):
            for q in quick_list:
                self.assertIsNotNone(re.search(builder.pattern('quick'),
                                               string % (t, q)))
                self.assertEqual(bool(re.search(builder.pattern('Quick'),
                                                string % (t, q))),
                                 self._template_not_case_sensitive)


class TestGetLanguageLinks(SiteAttributeTestCase):

    """Test :py:obj:`textlib.getLanguageLinks` function."""

    sites = {
        'enwp': {
            'family': 'wikipedia',
            'code': 'en',
        },
        'dewp': {
            'family': 'wikipedia',
            'code': 'de',
        },
        'commons': {
            'family': 'commons',
            'code': 'commons',
        },
    }

    example_text = ('[[en:Site]] [[de:Site|Piped]] [[commons:Site]] '
                    '[[baden:Site]] [[fr:{{PAGENAME}}]]')

    @classmethod
    def setUpClass(cls):
        """Define set of valid targets for the example text."""
        super().setUpClass()
        cls.sites_set = {cls.enwp, cls.dewp}

    def test_getLanguageLinks(self, key):
        """Test if the function returns the correct titles and sites."""
        with mock.patch('pywikibot.info') as m:
            lang_links = textlib.getLanguageLinks(self.example_text,
                                                  self.site)
        m.assert_called_once_with(
            '[getLanguageLinks] Text contains invalid interwiki link '
            '[[fr:{{PAGENAME}}]].')
        self.assertEqual({page.title() for page in lang_links.values()},
                         {'Site'})
        self.assertEqual(set(lang_links), self.sites_set - {self.site})


class TestExtractSections(DefaultDrySiteTestCase):

    """Test the extract_sections function."""

    def _extract_sections_tests(self, result, header, sections, footer):
        """Test extract_sections function."""
        self.assertIsInstance(result, tuple)
        self.assertIsInstance(result.sections, list)
        self.assertEqual(result, (header, sections, footer))
        self.assertEqual(result.header, header)
        self.assertEqual(result.sections, sections)
        self.assertEqual(result.footer, footer)
        if result.sections:
            for section in sections:
                self.assertIsInstance(section, tuple)
                self.assertLength(section, 2)

    def test_no_sections_no_footer(self):
        """Test for text having no sections or footer."""
        text = 'text'
        result = extract_sections(text, self.site)
        self._extract_sections_tests(result, text, [], '')

    def test_no_sections_with_footer(self):
        """Test for text having footer but no section."""
        text = 'text\n\n[[Category:A]]'
        result = extract_sections(text, self.site)
        self._extract_sections_tests(result, 'text\n\n', [], '[[Category:A]]')

    def test_with_section_no_footer(self):
        """Test for text having sections but no footer."""
        text = ('text\n\n'
                '==title==\n'
                'content')
        result = extract_sections(text, self.site)
        self._extract_sections_tests(
            result, 'text\n\n', [('==title==', '\ncontent')], '')

    def test_with_section_with_footer(self):
        """Test for text having sections and footer."""
        text = ('text\n\n'
                '==title==\n'
                'content\n'
                '[[Category:A]]\n')
        result = extract_sections(text, self.site)
        self._extract_sections_tests(
            result,
            'text\n\n', [('==title==', '\ncontent\n')], '[[Category:A]]\n')

    def test_with_h1_and_h2_sections(self):
        """Test for text having h1 and h2 sections."""
        text = ('text\n\n'
                '=first level=\n'
                'foo\n'
                '==title==\n'
                'bar')
        result = extract_sections(text, self.site)
        self._extract_sections_tests(
            result,
            'text\n\n',
            [('=first level=', '\nfoo\n'), ('==title==', '\nbar')],
            '')

    def test_with_h4_and_h2_sections(self):
        """Test for text having h4 and h2 sections."""
        text = ('text\n\n'
                '====title====\n'
                '==title 2==\n'
                'content')
        result = extract_sections(text, self.site)
        self._extract_sections_tests(
            result,
            'text\n\n',
            [('====title====', '\n'), ('==title 2==', '\ncontent')],
            '')

    def test_long_comment(self):
        r"""Test for text having a long expanse of white space.

        This is to catch certain regex issues caused by patterns like
        r'(\s+)*$' (as found in older versions of extract_section).
        They may not halt.

        c.f.
        https://www.regular-expressions.info/catastrophic.html
        """
        text = '<!--                                         -->'
        result = extract_sections(text, self.site)
        self._extract_sections_tests(result, text, [], '')


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
