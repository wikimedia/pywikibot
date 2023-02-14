#!/usr/bin/env python3
"""upload.py script test."""
#
# (C) Pywikibot team, 2019-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

from scripts.upload import CHUNK_SIZE_REGEX, get_chunk_size
from tests.aspects import TestCase


def match(value: str = '') -> int:
    """Create a match object and call get_chunk_site.

    :param value: a chunk size value
    :return: chunk size in bytes
    """
    option = '-chunked'
    if value:
        option += ':' + value
    match = CHUNK_SIZE_REGEX.fullmatch(option)
    return get_chunk_size(match)


class TestUploadScript(TestCase):

    """Test cases for upload."""

    net = False

    def test_regex(self):
        """Test CHUNK_SIZE_REGEX and get_chunk_size function."""
        self.assertEqual(match(), 1024 ** 2)
        self.assertEqual(match('12345'), 12345)
        self.assertEqual(match('4567k'), 4567 * 1000)
        self.assertEqual(match('7890m'), 7890 * 10 ** 6)
        self.assertEqual(match('987ki'), 987 * 1024)
        self.assertEqual(match('654mi'), 654 * 1024 ** 2)
        self.assertEqual(match('3mike'), 0)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
