#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Test Interwiki Graph functionality."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

from pywikibot import interwiki_graph

from tests.aspects import unittest, SiteAttributeTestCase
from tests.utils import DryPage


class TestWiktionaryGraph(SiteAttributeTestCase):

    """Tests for interwiki links to local sites."""

    sites = {
        'enwikt': {
            'family': 'wiktionary',
            'code': 'en',
        },
        'frwikt': {
            'family': 'wiktionary',
            'code': 'fr',
        },
        'plwikt': {
            'family': 'wiktionary',
            'code': 'pl',
        },
    }
    dry = True

    @classmethod
    def setUpClass(cls):
        """Setup test class."""
        if isinstance(interwiki_graph.pydot, ImportError):
            raise unittest.SkipTest('pydot not installed')
        super(TestWiktionaryGraph, cls).setUpClass()

        cls.pages = {
            'en': DryPage(cls.enwikt, 'origin'),
            'en2': DryPage(cls.enwikt, 'origin2'),
            'fr': DryPage(cls.frwikt, 'origin'),
            'pl': DryPage(cls.plwikt, 'origin'),
        }

    def test_simple_graph(self):
        """Test that GraphDrawer.createGraph does not raise exception."""
        data = interwiki_graph.Subject(self.pages['en'])

        data.found_in[self.pages['en']] = [self.pages['fr'], self.pages['pl']]
        data.found_in[self.pages['fr']] = [self.pages['en'], self.pages['pl']]
        data.found_in[self.pages['pl']] = [self.pages['en'], self.pages['fr']]

        drawer = interwiki_graph.GraphDrawer(data)

        drawer.createGraph()

    def test_octagon(self):
        """Test octagon nodes."""
        data = interwiki_graph.Subject(self.pages['en'])

        data.found_in[self.pages['en']] = [self.pages['fr'], self.pages['pl']]
        data.found_in[self.pages['en2']] = [self.pages['fr']]
        data.found_in[self.pages['fr']] = [self.pages['en'], self.pages['pl']]
        data.found_in[self.pages['pl']] = [self.pages['en'], self.pages['fr']]

        drawer = interwiki_graph.GraphDrawer(data)

        drawer.createGraph()

        nodes = drawer.graph.obj_dict['nodes']
        self.assertEqual(
            nodes['"pl:origin"'][0]['attributes']['shape'],
            'rectangle')

        self.assertEqual(
            nodes['"fr:origin"'][0]['attributes']['shape'],
            'rectangle')

        self.assertEqual(
            nodes['"en:origin"'][0]['attributes']['shape'],
            'octagon')


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
