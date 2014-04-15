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
from collections import OrderedDict

import pywikibot
import pywikibot.textlib as textlib

from utils import unittest

files = {}
dirname = os.path.join(os.path.dirname(__file__), "pages")

for f in ["enwiki_help_editing"]:
    files[f] = codecs.open(os.path.join(dirname, f + ".page"), 'r', 'utf-8').read()


class TestSectionFunctions(unittest.TestCase):
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
        self.assertEqual(func('{{a}}'), [('a', OrderedDict())])
        self.assertEqual(func('{{a|b=c}}'), [('a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{a|b|c=d}}'), [('a', OrderedDict((('1', 'b'), ('c', 'd'))))])
        self.assertEqual(func('{{a|b={{c}}}}'), [('c', {}), ('a', OrderedDict((('b', '{{c}}'), )))])
        self.assertEqual(func('{{a|b=c|f=g|d=e|1=}}'), [('a', OrderedDict((('b', 'c'), ('f', 'g'), ('d', 'e'), ('1', ''))))])

    def testExtractTemplatesRegex(self):
        func = textlib.extract_templates_and_params_regex  # It's really long.
        self.assertEqual(func('{{a}}'), [('a', OrderedDict())])
        self.assertEqual(func('{{a|b=c}}'), [('a', OrderedDict((('b', 'c'), )))])
        self.assertEqual(func('{{a|b|c=d}}'), [('a', OrderedDict((('1', 'b'), ('c', 'd'))))])
        self.assertEqual(func('{{a|b={{c}}}}'), [('c', {}), ('a', OrderedDict((('b', '{{c}}'), )))])
        self.assertEqual(func('{{a|b=c|f=g|d=e|1=}}'), [('a', OrderedDict((('b', 'c'), ('f', 'g'), ('d', 'e'), ('1', ''))))])

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


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
