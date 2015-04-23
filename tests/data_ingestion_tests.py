#!/usr/bin/python
# -*- coding: utf-8  -*-
"""Unit tests for data_ingestion.py script."""
from __future__ import unicode_literals

__version__ = '$Id$'

import os
from tests import _data_dir
from tests import _images_dir
from tests.aspects import unittest, TestCase, ScriptMainTestCase
from scripts import data_ingestion


class TestPhoto(TestCase):

    """Test Photo class."""

    sites = {
        'wm-upload': {
            'hostname': 'upload.wikimedia.org',
        },
        'commons': {
            'family': 'commons',
            'code': 'commons',
        },
    }

    def setUp(self):
        super(TestPhoto, self).setUp()
        self.obj = data_ingestion.Photo(URL='http://upload.wikimedia.org/wikipedia/commons/f/fc/MP_sounds.png',
                                        metadata={'description.en': '"Sounds" icon',
                                                  'source': 'http://commons.wikimedia.org/wiki/File:Sound-icon.svg',
                                                  'author': 'KDE artists | Silstor',
                                                  'license': 'LGPL',
                                                  'set': 'Crystal SVG icon set',
                                                  'name': 'Sound icon'},
                                        site=self.get_site('commons'))

    def test_downloadPhoto(self):
        """Test download from http://upload.wikimedia.org/."""
        with open(os.path.join(_images_dir, 'MP_sounds.png'), 'rb') as f:
            self.assertEqual(f.read(), self.obj.downloadPhoto().read())

    def test_findDuplicateImages(self):
        """Test finding duplicates on Wikimedia Commons."""
        duplicates = self.obj.findDuplicateImages()
        self.assertIn('MP sounds.png', [dup.replace("_", " ") for dup in duplicates])

    def test_getTitle(self):
        self.assertEqual(self.obj.getTitle("%(name)s - %(set)s.%(_ext)s"), "Sound icon - Crystal SVG icon set.png")

    def test_getDescription(self):
        self.assertEqual(self.obj.getDescription('CrystalTemplate'),
"""{{CrystalTemplate
|author=KDE artists {{!}} Silstor
|description.en="Sounds" icon
|license=LGPL
|name=Sound icon
|set=Crystal SVG icon set
|source=http://commons.wikimedia.org/wiki/File:Sound-icon.svg
}}""")  # noqa


class TestCSVReader(TestCase):

    """Test CSVReader class."""

    family = 'commons'
    code = 'commons'

    def setUp(self):
        super(TestCSVReader, self).setUp()
        with open(os.path.join(_data_dir, 'csv_ingestion.csv')) as fileobj:
            self.iterator = data_ingestion.CSVReader(fileobj, 'url',
                                                     site=self.get_site())
            self.obj = next(self.iterator)

    def test_PhotoURL(self):
        self.assertEqual(self.obj.URL, 'http://upload.wikimedia.org/wikipedia/commons/f/fc/MP_sounds.png')

    def test_getTitle(self):
        self.assertEqual(self.obj.getTitle("%(name)s - %(set)s.%(_ext)s"), "Sound icon - Crystal SVG icon set.png")

    def test_getDescription(self):
        self.assertEqual(self.obj.getDescription('CrystalTemplate'),
"""{{CrystalTemplate
|author=KDE artists {{!}} Silstor
|description.en="Sounds" icon
|license=LGPL
|name=Sound icon
|set=Crystal SVG icon set
|source=http://commons.wikimedia.org/wiki/File:Sound-icon.svg
|url=http://upload.wikimedia.org/wikipedia/commons/f/fc/MP_sounds.png
}}""")  # noqa


class TestDataIngestionBot(ScriptMainTestCase):

    """Test TestDataIngestionBot class."""

    family = 'test'
    code = 'test'

    def test_existing_file(self):
        """Test uploading a file that already exists."""
        data_ingestion.main(
            '-csvdir:tests/data',
            '-page:User:John_Vandenberg/data_ingestion_test_template')


if __name__ == "__main__":
    unittest.main()
