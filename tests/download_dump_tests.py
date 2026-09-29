#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the download_dump script."""
from __future__ import annotations

import unittest
from http import HTTPStatus
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

from scripts import download_dump
from tests.aspects import TestCase


class DownloadDumpMainTestCase(TestCase):

    """Test :func:`download_dump.main`."""

    net = False

    @patch.object(download_dump.pywikibot, 'input',
                  return_value='prompted-path')
    @patch.object(download_dump.pywikibot, 'handle_args',
                  side_effect=lambda args: args)
    def test_empty_storepath_prompts(self, _, input_mock) -> None:
        """Test that an empty store path prompts for a value."""
        download_dump.main('-storepath:')

        input_mock.assert_called_once_with('Enter the store path: ')


class DownloadDumpBotTestCase(TestCase):

    """Test :class:`download_dump.DownloadDumpBot`."""

    net = False

    @patch.object(download_dump.DownloadDumpBot, 'get_dump_name',
                  return_value=None)
    @patch.object(download_dump, 'fetch')
    def test_download_without_content_length(
        self, fetch_mock, get_dump_name_mock,
    ) -> None:
        """Test downloading a response without a content length."""
        response = MagicMock()
        response.__enter__.return_value = response
        response.status_code = HTTPStatus.OK
        response.headers = {}
        response.iter_content.return_value = [b'first', b'second']
        fetch_mock.return_value = response

        with TemporaryDirectory() as directory:
            bot = download_dump.DownloadDumpBot(
                wikiname='enwiki', filename='pages.xml.bz2',
                storepath=directory, dumpdate='latest')
            bot.run()

            path = Path(directory) / 'enwiki-latest-pages.xml.bz2'
            self.assertEqual(path.read_bytes(), b'firstsecond')

        response.__exit__.assert_called_once()


if __name__ == '__main__':
    unittest.main()
