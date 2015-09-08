# -*- coding: utf-8  -*-
"""Test cosmetic_changes module."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot.cosmetic_changes import CosmeticChangesToolkit

from tests.aspects import unittest, TestCase


class TestCosmeticChanges(TestCase):

    """Test cosmetic changes methods."""

    family = 'wikipedia'
    code = 'de'

    @classmethod
    def setUpClass(cls):
        """Setup class for all tests."""
        super(TestCosmeticChanges, cls).setUpClass()
        cls.cct = CosmeticChangesToolkit(cls.site, namespace=0,
                                         pageTitle='Test')

    def test_fixSelfInterwiki(self):
        """Test fixSelfInterwiki method."""
        self.assertEqual('[[Foo bar]]',
                         self.cct.fixSelfInterwiki('[[de:Foo bar]]'))
        self.assertEqual('[[en:Foo bar]]',
                         self.cct.fixSelfInterwiki('[[en:Foo bar]]'))

    def test_translateAndCapitalizeNamespaces(self):
        """Test translateAndCapitalizeNamespaces method."""
        self.assertEqual(
            '[[Wikipedia:Test]], [[Wikipedia:Test]], [[Datei:Test]]',
            self.cct.translateAndCapitalizeNamespaces(
                '[[Project:Test]], [[wikipedia:Test]], [[Image:Test]]'))

    def test_translateMagicWords(self):
        """Test translateMagicWords method."""
        self.assertEqual(
            '[[File:Foo.bar|mini]]',
            self.cct.translateMagicWords('[[File:Foo.bar|thumb]]'))
        self.assertEqual(
            '[[File:Foo.bar|mini]]',
            self.cct.translateMagicWords('[[File:Foo.bar|miniatur]]'))

    def test_cleanUpLinks_pipes(self):
        """Test cleanUpLinks method."""
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

    @unittest.expectedFailure
    def test_cleanUpLinks_pipes_fail(self):
        """Test cleanUpLinks method."""
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
    def test_cleanUpLinks(self):
        """
        Test cleanUpLinks method.

        This method fails for the given samples from library. Either the method
        has to be changed or the examples must be fixed.
        """
        self.assertEqual('text [[title]] text',
                         self.cct.cleanUpLinks('text[[ title ]]text'))
        self.assertEqual('text [[title|name]] text',
                         self.cct.cleanUpLinks('text[[ title | name ]]text'))
        self.assertEqual('text[[title|name]]text',
                         self.cct.cleanUpLinks('text[[ title |name]]text'))
        self.assertEqual('text [[title|name]]text',
                         self.cct.cleanUpLinks('text[[title| name]]text'))

    def test_resolveHtmlEntities(self):
        """Test resolveHtmlEntities method."""
        self.assertEqual(
            '&amp;#&nbsp;# #0#&#62;#x',
            self.cct.resolveHtmlEntities('&amp;#&nbsp;#&#32;#&#48;#&#62;#&#120;'))

    def test_removeUselessSpaces(self):
        """Test removeUselessSpaces method."""
        self.assertEqual('Foo bar',
                         self.cct.removeUselessSpaces('Foo  bar '))
        # inside comments
        self.assertEqual('<!--Foo  bar -->',
                         self.cct.removeUselessSpaces('<!--Foo  bar -->'))
        # startspace
        self.assertEqual(' Foo  bar ',
                         self.cct.removeUselessSpaces(' Foo  bar '))

    def test_removeNonBreakingSpaceBeforePercent(self):
        """Test removeNonBreakingSpaceBeforePercent method."""
        self.assertEqual(
            '42 %', self.cct.removeNonBreakingSpaceBeforePercent('42&nbsp;%'))

    def test_cleanUpSectionHeaders(self):
        """Test cleanUpSectionHeaders method."""
        self.assertEqual('=== Header ===\n',
                         self.cct.cleanUpSectionHeaders('===Header===\n'))

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
        self.assertEqual('{{Belege fehlen}}',
                         self.cct.replaceDeprecatedTemplates('{{Belege}}'))
        self.assertEqual('{{Belege fehlen|Test}}',
                         self.cct.replaceDeprecatedTemplates('{{Quelle|Test}}'))

    def test_fixSyntaxSave(self):
        """Test fixSyntaxSave method."""
        self.assertEqual(
            '[https://de.wikipedia.org]',
            self.cct.fixSyntaxSave('[[https://de.wikipedia.org]]'))
        self.assertEqual(
            '[https://de.wikipedia.org]',
            self.cct.fixSyntaxSave('[[https://de.wikipedia.org]'))
        self.assertEqual(
            '[https://de.wikipedia.org/w/api.php API]',
            self.cct.fixSyntaxSave('[https://de.wikipedia.org/w/api.php|API]'))

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


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
