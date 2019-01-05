# -*- coding: utf-8 -*-
"""
UploadRobot test.

These tests write to the wiki.
"""
#
# (C) Pywikibot team, 2014-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import os

from pywikibot.specialbots import UploadRobot

from tests import join_images_path
from tests.aspects import unittest, TestCase


class TestUploadbot(TestCase):

    """Test cases for upload."""

    write = True

    family = 'wikipedia'
    code = 'test'

    params = dict(  # noqa: C408
        description='pywikibot upload.py script test',
        keepFilename=True,
        aborts=set(),
        ignoreWarning=True,
    )

    def test_png_list(self):
        """Test uploading a list of pngs using upload.py."""
        image_list = []
        for directory_info in os.walk(join_images_path()):
            for dir_file in directory_info[2]:
                image_list.append(os.path.join(directory_info[0], dir_file))
        bot = UploadRobot(url=image_list, targetSite=self.get_site(),
                          **self.params)
        bot.run()

    def test_png(self):
        """Test uploading a png using upload.py."""
        bot = UploadRobot(
            url=[join_images_path('MP_sounds.png')],
            targetSite=self.get_site(), **self.params)
        bot.run()

    def test_png_url(self):
        """Test uploading a png from url using upload.py."""
        link = 'https://upload.wikimedia.org/'
        link += 'wikipedia/commons/f/fc/MP_sounds.png'
        bot = UploadRobot(url=[link], targetSite=self.get_site(),
                          **self.params)
        bot.run()


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
