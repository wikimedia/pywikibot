# -*- coding: utf-8  -*-
"""
Site upload test.

These tests write to the wiki.
"""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

import os

import pywikibot

from tests import _images_dir
from tests.aspects import unittest, TestCase


class TestUpload(TestCase):

    """Test cases for upload."""

    write = True

    family = 'wikipedia'
    code = 'test'

    def test_png(self):
        """Test uploading a png using Site.upload."""
        page = pywikibot.FilePage(self.site, 'MP_sounds-pwb.png')
        local_filename = os.path.join(_images_dir, 'MP_sounds.png')
        self.site.upload(page, source_filename=local_filename,
                         comment='pywikibot test',
                         ignore_warnings=True)

    def test_png_chunked(self):
        """Test uploading a png in two chunks using Site.upload."""
        page = pywikibot.FilePage(self.site, 'MP_sounds-pwb-chunked.png')
        local_filename = os.path.join(_images_dir, 'MP_sounds.png')
        self.site.upload(page, source_filename=local_filename,
                         comment='pywikibot test',
                         ignore_warnings=True, chunk_size=1024)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
