#!/usr/bin/env python3
#
# (C) Pywikibot team, 2014-2026
#
# Distributed under the terms of the MIT license.
#
"""UploadRobot test.

These tests write to the wiki.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from contextlib import suppress
from pathlib import Path
from unittest import mock

import requests

from pywikibot.exceptions import APIError
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

    def test_png_list(self) -> None:
        """Test uploading a list of pngs using upload.py."""
        image_list = []
        for directory_info in os.walk(join_images_path()):
            image_list += [os.path.join(directory_info[0], dir_file)
                           for dir_file in directory_info[2]]

        bot = UploadRobot(url=image_list, target_site=self.get_site(),
                          **self.params)
        bot.run()

    def test_png(self) -> None:
        """Test uploading a png using upload.py."""
        bot = UploadRobot(
            url=[join_images_path('MP_sounds.png')],
            target_site=self.get_site(), **self.params)
        bot.run()

    def test_png_url(self) -> None:
        """Test uploading a png from url using upload.py."""
        link = 'https://upload.wikimedia.org/'
        link += 'wikipedia/commons/f/fc/MP_sounds.png'
        bot = UploadRobot(url=[link], target_site=self.get_site(),
                          **self.params)
        bot.run()


class TestDryUploadbot(DefaultSiteTestCase):

    """Dry tests UploadRobot."""

    net = False

    def test_png_file(self) -> None:
        """Test UploadRobot attributes and methods."""
        params = {
            'description': 'pywikibot upload.py script test',
            'keep_filename': True,
            'aborts': set(),
            'ignore_warning': True,
        }
        bot = UploadRobot(url=['test.png'], target_site=self.site, **params)
        self.assertEqual(bot.description, params['description'])
        self.assertTrue(bot._handle_warning('any warning'))  # ignore_warning
        self.assertTrue(bot.ignore_on_warn('any warning'))  # ignore_warning
        self.assertFalse(bot.abort_on_warn('any warning'))  # aborts
        self.assertIsNone(bot.post_processor)


class TestUploadbotTempFiles(TestCase):

    """Dry tests for UploadRobot temporary files."""

    net = False

    def test_download_failure_removes_partial_file(self) -> None:
        """Test that a failed download removes its partial file."""
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.headers = {
            'Content-Type': 'image/png',
            'Content-Length': '10',
        }

        def chunks():
            yield b'partial'
            raise requests.Timeout('Download timed out')

        response.iter_content.return_value = chunks()
        bot = UploadRobot(
            url=['mahveo.png'], target_site=mock.Mock(), always=False)

        with tempfile.TemporaryDirectory() as directory:
            temp_fd, tempname = tempfile.mkstemp(dir=directory)
            with (
                mock.patch('pywikibot.specialbots._upload.tempfile.mkstemp',
                           return_value=(temp_fd, tempname)),
                mock.patch('pywikibot.specialbots._upload.http.fetch',
                           return_value=response),
                self.assertRaises(requests.Timeout),
            ):
                bot.read_file_content('https://yo.wikipedia.org/mahveo.png')

            self.assertFalse(Path(tempname).exists())

        response.__exit__.assert_called_once()

    def test_downloaded_file_cleanup(self) -> None:
        """Test that downloaded files are removed after an upload attempt."""
        file_url = 'https://yo.wikipedia.org/mahveo.png'
        cases = (
            (True, 'mahveo.png'),
            (False, None),
            (APIError('mahveo', 'Upload failed'), None),
        )

        for outcome, expected in cases:
            with self.subTest(outcome=outcome), \
                    tempfile.TemporaryDirectory() as directory:
                temp_path = Path(directory) / 'download'
                temp_path.write_bytes(b'content')
                site = mock.Mock()
                site.has_right.return_value = False
                imagepage = mock.Mock()

                def upload(source, *, expected_path=temp_path,
                           upload_outcome=outcome, **kwargs):
                    self.assertEqual(source, str(expected_path))
                    self.assertTrue(expected_path.exists())
                    if isinstance(upload_outcome, Exception):
                        raise upload_outcome
                    return upload_outcome

                imagepage.upload.side_effect = upload
                bot = UploadRobot(
                    url=[file_url], target_site=site, always=False)
                with (
                    mock.patch.object(bot, 'process_filename',
                                      return_value='mahveo.png'),
                    mock.patch.object(bot, 'read_file_content',
                                      return_value=str(temp_path)),
                    mock.patch('pywikibot.FilePage', return_value=imagepage),
                    mock.patch('pywikibot.exception'),
                ):
                    result = bot.upload_file(file_url)

                self.assertEqual(result, expected)
                self.assertFalse(temp_path.exists())

    def test_local_file_is_preserved(self) -> None:
        """Test that a caller-owned local file is not removed."""
        site = mock.Mock()
        imagepage = mock.Mock()
        imagepage.upload.return_value = True

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'mahveo.png'
            path.write_bytes(b'content')
            bot = UploadRobot(
                url=[str(path)], target_site=site, always=False)
            with (
                mock.patch.object(bot, 'process_filename',
                                  return_value='mahveo.png'),
                mock.patch('pywikibot.FilePage', return_value=imagepage),
            ):
                result = bot.upload_file(str(path))

            self.assertEqual(result, 'mahveo.png')
            self.assertTrue(path.exists())

    def test_downloaded_file_cleanup_after_retry(self) -> None:
        """Test cleanup after falling back from URL to file upload."""
        file_url = 'https://yo.wikipedia.org/mahveo.png'
        site = mock.Mock()
        site.has_right.return_value = True
        imagepage = mock.Mock()

        with tempfile.TemporaryDirectory() as directory:
            temp_path = Path(directory) / 'download'
            temp_path.write_bytes(b'content')

            def upload(source, **kwargs):
                if source == file_url:
                    raise APIError('copyuploadbaddomain', 'Bad domain')
                self.assertEqual(source, str(temp_path))
                self.assertTrue(temp_path.exists())
                return True

            imagepage.upload.side_effect = upload
            bot = UploadRobot(
                url=[file_url], target_site=site, always=False)
            with (
                mock.patch.object(bot, 'process_filename',
                                  return_value='mahveo.png'),
                mock.patch.object(bot, 'read_file_content',
                                  return_value=str(temp_path)) as download,
                mock.patch('pywikibot.FilePage', return_value=imagepage),
            ):
                result = bot.upload_file(file_url)

            self.assertEqual(result, 'mahveo.png')
            download.assert_called_once_with(file_url)
            self.assertFalse(temp_path.exists())


class TestUploadbotCounter(TestCase):

    """Dry tests for UploadRobot counters."""

    net = False

    def test_upload_counter(self) -> None:
        """Test that a successful upload is counted once."""
        bot = UploadRobot(
            url=['test.png'], target_site=mock.Mock(), always=False)

        with (
            mock.patch.object(bot, 'skip_run', return_value=False),
            mock.patch.object(bot, 'process_filename',
                              return_value='test.png'),
            mock.patch.object(bot, 'exit'),
            mock.patch('pywikibot.FilePage') as file_page,
        ):
            file_page.return_value.upload.return_value = True
            bot.run()

        self.assertEqual(bot.counter['read'], 1)
        self.assertEqual(bot.counter['upload'], 1)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
