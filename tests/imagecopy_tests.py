# -*- coding: utf-8 -*-
"""Tests for imagecopy script."""
#
# (C) Pywikibot team, 2018
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import re

from scripts.imagecopy import pageTextPost

from tests.aspects import TestCase
from tests import join_data_path


class CommonsHelperMethodTest(TestCase):
    """Test CommonsHelper methods in imagecopy."""

    hostname = 'https://tools.wmflabs.org/commonshelper/'

    def test_pageTextPost(self):
        """Test scripts.imagecopy.pageTextPost() method."""
        parameters_dict = {
            'language': b'id',
            'image': b'Ahmad Syaikhu Wakil Walikota Bekasi.jpg',
            'newname': b'Ahmad Syaikhu Wakil Walikota Bekasi.jpg',
            'project': b'wikipedia',
            'username': '',
            'commonsense': '1',
            'remove_categories': '1',
            'ignorewarnings': '1',
            'doit': 'Uitvoeren'}

        commons_helper = pageTextPost('', parameters_dict)
        # Extract the CommonsHelper description from the html
        commons_helper = (
            re.compile(
                "<textarea .+ name='wpUploadDescription'>(.+)</textarea>",
                re.DOTALL | re.M).findall(commons_helper)[0])
        with open(join_data_path('commonsHelper_description.txt')) as f:
            self.assertEqual(f.read(), commons_helper)
