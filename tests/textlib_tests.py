# -*- coding: utf-8  -*-
#
# (C) Pywikipedia bot team, 2007
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: api_tests.py 8238 2010-06-02 13:50:48Z xqt $'

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
