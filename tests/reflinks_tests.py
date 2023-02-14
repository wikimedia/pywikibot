#!/usr/bin/env python3
"""Tests for reflinks script."""
#
# (C) Pywikibot team, 2014-2022
#
# Distributed under the terms of the MIT license.
#
import unittest

from scripts.reflinks import ReferencesRobot, XmlDumpPageGenerator, main
from tests import join_xml_data_path
from tests.aspects import ScriptMainTestCase, TestCase
from tests.utils import empty_sites


class TestXMLPageGenerator(TestCase):

    """Test XML Page generator."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    def test_non_bare_ref_urls(self):
        """Test pages without bare references are not processed."""
        gen = XmlDumpPageGenerator(
            filename=join_xml_data_path('article-pear-0.10.xml'),
            start='Pear',
            namespaces=[0, 1],
            site=self.site)
        pages = list(gen)
        self.assertIsEmpty(pages)

    def test_simple_bare_refs(self):
        """Test simple bare references with several namespaces options."""
        namespace_variants = (None, [], [0, 1], ['0', '1'])

        filename = join_xml_data_path('dummy-reflinks.xml')
        for namespaces in namespace_variants:
            with self.subTest(namespaces=namespaces):
                gen = XmlDumpPageGenerator(filename=filename,
                                           start='Fake page',
                                           namespaces=namespaces,
                                           site=self.site)
                pages = list(gen)
                self.assertPageTitlesEqual(pages, ('Fake page',
                                                   'Talk:Fake page'),
                                           site=self.site)

    def test_namespace_names(self):
        """Test namespaces with namespace names."""
        gen = XmlDumpPageGenerator(
            filename=join_xml_data_path('dummy-reflinks.xml'),
            start='Fake page',
            namespaces=['Talk'],
            site=self.site)
        pages = list(gen)
        self.assertPageTitlesEqual(pages, ['Talk:Fake page'], site=self.site)

    def test_start_variants(self):
        """Test with several page title options."""
        start_variants = (
            None,  # None
            'Fake',  # prefix
            'Fake_page',  # underscore
        )

        filename = join_xml_data_path('dummy-reflinks.xml')
        for start in start_variants:
            with self.subTest(start=start):
                gen = XmlDumpPageGenerator(filename=filename,
                                           start=start,
                                           namespaces=[0, 1],
                                           site=self.site)
                pages = list(gen)
                self.assertPageTitlesEqual(pages, ('Fake page',
                                                   'Talk:Fake page'),
                                           site=self.site)


class TestReferencesBotConstructor(ScriptMainTestCase):

    """
    Test reflinks with run() removed.

    These tests can't verify the order of the pages in the XML
    as the constructor is given a preloading generator.
    See APISite.preloadpages for details.
    """

    family = 'wikipedia'
    code = 'en'

    def setUp(self):
        """Set up the script by patching the bot class."""
        super().setUp()
        self._original_constructor = ReferencesRobot.__init__
        self._original_run = ReferencesRobot.run
        ReferencesRobot.__init__ = dummy_constructor
        ReferencesRobot.run = lambda self: None

    def tearDown(self):
        """Tear down the test by undoing the bot class patch."""
        ReferencesRobot.__init__ = self._original_constructor
        ReferencesRobot.run = self._original_run
        with empty_sites():
            super().tearDown()

    def test_xml_simple(self):
        """Test the generator without any narrowing."""
        main('-xml:' + join_xml_data_path('dummy-reflinks.xml'))
        gen = self.constructor_kwargs['generator']
        self.assertPageTitlesCountEqual(gen, ['Fake page', 'Talk:Fake page'],
                                        site=self.get_site())

    def test_xml_one_namespace(self):
        """Test the generator using one namespace id."""
        main('-xml:' + join_xml_data_path('dummy-reflinks.xml'),
             '-namespace:1')
        gen = self.constructor_kwargs['generator']
        pages = list(gen)
        self.assertPageTitlesEqual(pages, ['Talk:Fake page'],
                                   site=self.get_site())

    def test_xml_multiple_namespace_ids(self):
        """Test the generator using multiple separate namespaces parameters."""
        main('-xml:' + join_xml_data_path('dummy-reflinks.xml'),
             '-namespace:0', '-namespace:1', '-xmlstart:Fake page')
        gen = self.constructor_kwargs['generator']
        self.assertPageTitlesCountEqual(gen, ['Fake page', 'Talk:Fake page'],
                                        site=self.get_site())

    def test_xml_multiple_namespace_ids_2(self):
        """Test the generator using multiple namespaces in one parameter."""
        main('-xml:' + join_xml_data_path('dummy-reflinks.xml'),
             '-namespace:0,1', '-xmlstart:Fake page')
        gen = self.constructor_kwargs['generator']
        self.assertPageTitlesCountEqual(gen, ['Fake page', 'Talk:Fake page'],
                                        site=self.get_site())

    def test_xml_start_variants(self):
        """Test the generator using variants of start page."""
        start_variants = (
            '-xmlstart:Fake page',  # title
            '-xmlstart:Fake_page',  # underscore
            '-xmlstart:Fake',  # prefix
        )

        filename = '-xml:' + join_xml_data_path('dummy-reflinks.xml')
        for start in start_variants:
            with self.subTest(xmlstart=start), empty_sites():
                main(filename, '-namespace:1', start)
                gen = self.constructor_kwargs['generator']
                pages = list(gen)
                self.assertPageTitlesEqual(pages, ['Talk:Fake page'],
                                           site=self.site)

    def test_xml_namespace_name(self):
        """Test the generator using a namespace name."""
        main('-xml:' + join_xml_data_path('dummy-reflinks.xml'),
             '-namespace:Talk', '-xmlstart:Fake page')
        gen = self.constructor_kwargs['generator']
        pages = list(gen)
        self.assertPageTitlesEqual(pages, ['Talk:Fake page'],
                                   site=self.get_site())


def dummy_constructor(self, *args, **kwargs):
    """A constructor faking the actual constructor."""
    TestReferencesBotConstructor.constructor_args = args
    TestReferencesBotConstructor.constructor_kwargs = kwargs


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
