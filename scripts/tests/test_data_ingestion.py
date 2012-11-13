#!/usr/bin/python
# -*- coding: utf-8  -*-

"""Unit tests for data_ingestion.py"""
__version__ = '$Id: test_userlib.py 9043 2011-03-13 10:25:08Z xqt $'

import os
import unittest
import test_utils

import pywikibot

import data_ingestion

class TestPhoto(unittest.TestCase):
    def setUp(self):
        self.obj = data_ingestion.Photo(URL='http://upload.wikimedia.org/wikipedia/commons/f/fc/MP_sounds.png', 
                                        metadata={'description.en': '"Sounds" icon',
                                                  'source': 'http://commons.wikimedia.org/wiki/File:Sound-icon.svg',
                                                  'author': 'KDE artists | Silstor',
                                                  'license': 'LGPL',
                                                  'set': 'Crystal SVG icon set',
                                                  'name': 'Sound icon'}
                                        )

    def test_downloadPhoto(self):
        f = open(os.path.join(os.path.split(__file__)[0], 'data', 'MP_sounds.png'))
        self.assertEqual(f.read(), self.obj.downloadPhoto().read())

    def test_findDuplicateImages(self):
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
}}""")


class TestCSVReader(unittest.TestCase):
    def setUp(self):
        fileobj = open(os.path.join(os.path.split(__file__)[0], 'data', 'csv_ingestion.csv'))
        self.iterator = data_ingestion.CSVReader(fileobj, 'url')
        self.obj = self.iterator.next()

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
}}""")


if __name__ == "__main__":
    unittest.main()
