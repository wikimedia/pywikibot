# -*- coding: utf-8  -*-
"""Tests for reflinks script."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import os

from scripts.reflinks import XmlDumpPageGenerator, ReferencesRobot, main

from tests import _data_dir
from tests.aspects import unittest, TestCase, ScriptMainTestCase

_xml_data_dir = os.path.join(_data_dir, 'xml')


class TestXMLPageGenerator(TestCase):

    """Test XML Page generator."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    def test_non_bare_ref_urls(self):
        """Test pages without bare references are not processed."""
        gen = XmlDumpPageGenerator(
            xmlFilename=os.path.join(_xml_data_dir, 'article-pear-0.10.xml'),
            xmlStart=u'Pear',
            namespaces=[0, 1],
            site=self.get_site())
        pages = list(gen)
        self.assertEqual(len(pages), 0)

    def test_simple_bare_refs(self):
        """Test simple bare references in multiple namespaces."""
        gen = XmlDumpPageGenerator(
            xmlFilename=os.path.join(_xml_data_dir, 'dummy-reflinks.xml'),
            xmlStart=u'Fake page',
            namespaces=[0, 1],
            site=self.get_site())
        pages = list(gen)
        self.assertPagelistTitles(pages, (u'Fake page', u'Talk:Fake page'),
                                  site=self.get_site())

    def test_namespace_empty_list(self):
        """Test namespaces=[] processes all namespaces."""
        gen = XmlDumpPageGenerator(
            xmlFilename=os.path.join(_xml_data_dir, 'dummy-reflinks.xml'),
            xmlStart=u'Fake page',
            namespaces=[],
            site=self.get_site())
        pages = list(gen)
        self.assertPagelistTitles(pages, (u'Fake page', u'Talk:Fake page'),
                                  site=self.get_site())

    @unittest.expectedFailure
    def test_namespace_None(self):
        """Test namespaces=None processes all namespaces."""
        gen = XmlDumpPageGenerator(
            xmlFilename=os.path.join(_xml_data_dir, 'dummy-reflinks.xml'),
            xmlStart=u'Fake page',
            namespaces=None,
            site=self.get_site())
        pages = list(gen)
        self.assertPagelistTitles(pages, (u'Fake page', u'Talk:Fake page'),
                                  site=self.get_site())

    @unittest.expectedFailure
    def test_namespace_string_ids(self):
        """Test namespaces with ids as string."""
        gen = XmlDumpPageGenerator(
            xmlFilename=os.path.join(_xml_data_dir, 'dummy-reflinks.xml'),
            xmlStart=u'Fake page',
            namespaces=["0", "1"],
            site=self.get_site())
        pages = list(gen)
        self.assertPagelistTitles(pages, (u'Fake page', u'Talk:Fake page'),
                                  site=self.get_site())

    def test_namespace_names(self):
        """Test namespaces with namespace names."""
        gen = XmlDumpPageGenerator(
            xmlFilename=os.path.join(_xml_data_dir, 'dummy-reflinks.xml'),
            xmlStart=u'Fake page',
            namespaces=["Talk"],
            site=self.get_site())
        pages = list(gen)
        self.assertPagelistTitles(pages, (u'Talk:Fake page', ),
                                  site=self.get_site())

    @unittest.expectedFailure
    def test_start_with_underscore(self):
        """Test with underscore in start page title."""
        gen = XmlDumpPageGenerator(
            xmlFilename=os.path.join(_xml_data_dir, 'dummy-reflinks.xml'),
            xmlStart=u'Fake_page',
            namespaces=[0, 1],
            site=self.get_site())
        pages = list(gen)
        self.assertPagelistTitles(pages, (u'Fake page', u'Talk:Fake page'),
                                  site=self.get_site())

    def test_without_start(self):
        """Test without a start page title."""
        gen = XmlDumpPageGenerator(
            xmlFilename=os.path.join(_xml_data_dir, 'dummy-reflinks.xml'),
            xmlStart=None,
            namespaces=[0, 1],
            site=self.get_site())
        pages = list(gen)
        self.assertPagelistTitles(pages, (u'Fake page', u'Talk:Fake page'),
                                  site=self.get_site())

    @unittest.expectedFailure
    def test_start_prefix(self):
        """Test with a prefix as a start page title."""
        gen = XmlDumpPageGenerator(
            xmlFilename=os.path.join(_xml_data_dir, 'dummy-reflinks.xml'),
            xmlStart='Fake',
            namespaces=[0, 1],
            site=self.get_site())
        pages = list(gen)
        self.assertPagelistTitles(pages, (u'Fake page', u'Talk:Fake page'),
                                  site=self.get_site())


class TestReferencesBotConstructor(ScriptMainTestCase):

    """
    Test reflinks with run() removed.

    These tests cant verify the order of the pages in the XML
    as the constructor is given a preloading generator.
    See APISite.preloadpages for details.
    """

    family = 'wikipedia'
    code = 'en'

    def setUp(self):
        super(TestReferencesBotConstructor, self).setUp()
        self._original_constructor = ReferencesRobot.__init__
        self._original_run = ReferencesRobot.run
        ReferencesRobot.__init__ = dummy_constructor
        ReferencesRobot.run = lambda self: None

    def tearDown(self):
        ReferencesRobot.__init__ = self._original_constructor
        ReferencesRobot.run = self._original_run
        super(TestReferencesBotConstructor, self).tearDown()

    def test_xml_simple(self):
        main('-xml:' + os.path.join(_xml_data_dir, 'dummy-reflinks.xml'))
        gen = self.constructor_args[0]
        self.assertPageTitlesCountEqual(gen, [u'Fake page', u'Talk:Fake page'],
                                        site=self.get_site())

    def test_xml_one_namespace(self):
        main('-xml:' + os.path.join(_xml_data_dir, 'dummy-reflinks.xml'),
             '-namespace:1')
        gen = self.constructor_args[0]
        pages = list(gen)
        self.assertPagelistTitles(pages, [u'Talk:Fake page'],
                                  site=self.get_site())

    def test_xml_multiple_namespace_ids(self):
        main('-xml:' + os.path.join(_xml_data_dir, 'dummy-reflinks.xml'),
             '-namespace:0', '-namespace:1', '-xmlstart:Fake page')
        gen = self.constructor_args[0]
        self.assertPageTitlesCountEqual(gen, [u'Fake page', u'Talk:Fake page'],
                                        site=self.get_site())

    @unittest.expectedFailure
    def test_xml_multiple_namespace_ids_2(self):
        main('-xml:' + os.path.join(_xml_data_dir, 'dummy-reflinks.xml'),
             '-namespace:0,1', '-xmlstart:Fake page')
        gen = self.constructor_args[0]
        self.assertPageTitlesCountEqual(gen, [u'Fake page', u'Talk:Fake page'],
                                        site=self.get_site())

    @unittest.expectedFailure
    def test_xml_start_prefix(self):
        main('-xml:' + os.path.join(_xml_data_dir, 'dummy-reflinks.xml'),
             '-namespace:1', '-xmlstart:Fake')
        gen = self.constructor_args[0]
        pages = list(gen)
        self.assertPagelistTitles(pages, [u'Talk:Fake page'],
                                  site=self.get_site())

    @unittest.expectedFailure
    def test_xml_start_underscore(self):
        main('-xml:' + os.path.join(_xml_data_dir, 'dummy-reflinks.xml'),
             '-namespace:1', '-xmlstart:Fake_page')
        gen = self.constructor_args[0]
        pages = list(gen)
        self.assertPagelistTitles(pages, [u'Talk:Fake page'],
                                  site=self.get_site())

    def test_xml_namespace_name(self):
        main('-xml:' + os.path.join(_xml_data_dir, 'dummy-reflinks.xml'),
             '-namespace:Talk', '-xmlstart:Fake page')
        gen = self.constructor_args[0]
        pages = list(gen)
        self.assertPagelistTitles(pages, [u'Talk:Fake page'],
                                  site=self.get_site())


def dummy_constructor(self, *args, **kwargs):
    TestReferencesBotConstructor.constructor_args = args
    TestReferencesBotConstructor.constructor_kwargs = kwargs


if __name__ == "__main__":
    unittest.main()
