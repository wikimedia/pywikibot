#!/usr/bin/python
"""Tests for the tests package."""
#
# (C) Pywikibot team, 2014-2021
#
# Distributed under the terms of the MIT license.
import unittest
from contextlib import suppress

from tests.aspects import TestCase


class HttpServerProblemTestCase(TestCase):

    """Test HTTP status 502 causes this test class to be skipped."""

    sites = {
        '502': {
            'hostname': 'http://httpbin.org/status/502',
        }
    }

    def test_502(self):
        """Test a HTTP 502 response using http://httpbin.org/status/502."""
        self.fail('The test framework should skip this test.')


class TestLengthAssert(TestCase):

    """Test length assertion methods."""

    net = False

    seq1 = ('foo', 'bar', 'baz')
    seq2 = 'foo'

    def test_assert_is_empty(self):
        """Test assertIsEmpty method."""
        self.assertIsEmpty([])
        self.assertIsEmpty('')

    @unittest.expectedFailure
    def test_assert_is_empty_fail(self):
        """Test assertIsEmpty method failing."""
        self.assertIsEmpty(self.seq1)
        self.assertIsEmpty(self.seq2)

    def test_assert_is_not_empty(self):
        """Test assertIsNotEmpty method."""
        self.assertIsNotEmpty(self.seq1)
        self.assertIsNotEmpty(self.seq2)

    @unittest.expectedFailure
    def test_assert_is_not_empty_fail(self):
        """Test assertIsNotEmpty method."""
        self.assertIsNotEmpty([])
        self.assertIsNotEmpty('')

    def test_assert_length(self):
        """Test assertIsNotEmpty method."""
        self.assertLength([], 0)
        self.assertLength(self.seq1, 3)
        self.assertLength(self.seq1, self.seq2)

    @unittest.expectedFailure
    def test_assert_length_fail(self):
        """Test assertIsNotEmpty method."""
        self.assertLength([], 1)
        self.assertLength(self.seq1, 0)
        self.assertLength(None, self.seq)


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
