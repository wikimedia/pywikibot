#!/usr/bin/env python3
"""Tests for mysql module."""
#
# (C) Pywikibot team, 2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress
from types import GeneratorType

from tests.aspects import TestCase, require_modules


@require_modules('pymysql')
class TestMySQL(TestCase):

    """Test data.mysql."""

    net = False

    def test_mysql(self):
        """Test data.mysql.mysql_query function."""
        from pywikibot.data.mysql import mysql_query
        result = mysql_query('test')
        self.assertIsInstance(result, GeneratorType)
        self.assertEqual(next(result), 'test')


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
