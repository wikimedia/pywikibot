#!/usr/bin/env python3
"""
UploadRobot test.

These tests write to the wiki.
"""
#
# (C) Pywikibot team, 2014-2022
#
# Distributed under the terms of the MIT license.
#
import os
import unittest
from contextlib import suppress

from pywikibot.specialbots import UploadRobot
from tests import join_images_path
from tests.aspects import DefaultSiteTestCase, TestCase


class TestUploadbot(TestCase):

    """Test cases for upload."""

    write = True

    family = 'wikipedia'
    code = 'test'

    params = dict(  # noqa: C408
        description='pywikibot upload.py script test',
        keep_filename=True,
        aborts=set(),
        ignore_warning=True,
    )

    def test_png_list(self):
        """Test uploading a list of pngs using upload.py."""
        image_list = []
        for directory_info in os.walk(join_images_path()):
            for dir_file in directory_info[2]:
                image_list.append(os.path.join(directory_info[0], dir_file))
        bot = UploadRobot(url=image_list, target_site=self.get_site(),
                          **self.params)
        bot.run()

    def test_png(self):
        """Test uploading a png using upload.py."""
        bot = UploadRobot(
            url=[join_images_path('MP_sounds.png')],
            target_site=self.get_site(), **self.params)
        bot.run()

    def test_png_url(self):
        """Test uploading a png from url using upload.py."""
        link = 'https://upload.wikimedia.org/'
        link += 'wikipedia/commons/f/fc/MP_sounds.png'
        bot = UploadRobot(url=[link], target_site=self.get_site(),
                          **self.params)
        bot.run()


class TestDryUploadbot(DefaultSiteTestCase):

    """Dry tests UploadRobot."""

    net = False

    params = dict(  # noqa: C408
        description='pywikibot upload.py script test',
        keep_filename=True,
        aborts=set(),
        ignore_warning=True,
    )

    def test_png_file(self):
        """Test UploadRobot attributes and methods."""
        bot = UploadRobot(url=['test.png'], target_site=self.site,
                          **self.params)
        self.assertEqual(bot.description, self.params['description'])
        self.assertTrue(bot._handle_warning('any warning'))  # ignore_warning
        self.assertTrue(bot.ignore_on_warn('any warning'))  # ignore_warning
        self.assertFalse(bot.abort_on_warn('any warning'))  # aborts


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
