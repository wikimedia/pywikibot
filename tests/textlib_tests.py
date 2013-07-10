# -*- coding: utf-8  -*-
#
# (C) Pywikipedia bot team, 2007
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: api_tests.py 8238 2010-06-02 13:50:48Z xqt $'

try:
    import mwparserfromhell
except ImportError:
    mwparserfromhell = False
import unittest
import codecs
import os

import pywikibot
import pywikibot.textlib as textlib

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

    @unittest.expectedFailure
    def testSpacesInSection(self):
        self.assertContains("enwiki_help_editing", u"Minor_edits")
        self.assertNotContains("enwiki_help_editing", u"Minor edits", "Incorrect, '#Minor edits' does not work")
        self.assertNotContains("enwiki_help_editing", u"Minor Edits", "section hashes are case-sensitive")
        self.assertNotContains("enwiki_help_editing", u"Minor_Edits", "section hashes are case-sensitive")

    @unittest.expectedFailure
    def testNonAlphabeticalCharactersInSection(self):
        self.assertContains("enwiki_help_editing", u"Talk_.28discussion.29_pages", "As used in the TOC")
        self.assertContains("enwiki_help_editing", u"Talk_(discussion)_pages", "Understood by mediawiki")

if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
