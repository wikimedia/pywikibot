#!/usr/bin/env python3
"""Tests for threading tools."""
#
# (C) Pywikibot team, 2014-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

from pywikibot.tools.threading import ThreadedGenerator
from tests.aspects import TestCase


class BasicThreadedGeneratorTestCase(TestCase):

    """ThreadedGenerator test cases."""

    net = False

    def test_run_from_iterable(self):
        """Test thread running with iterable target."""
        iterable = 'abcd'
        thd_gen = ThreadedGenerator(target=iterable)
        thd_gen.start()
        self.assertEqual(list(thd_gen), list(iterable))

    @staticmethod
    def gen_func():
        """Helper method for generator test."""
        iterable = 'abcd'
        yield from iterable

    def test_run_from_gen_function(self):
        """Test thread running with generator as target."""
        iterable = 'abcd'
        thd_gen = ThreadedGenerator(target=self.gen_func)
        thd_gen.start()
        self.assertEqual(list(thd_gen), list(iterable))


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
