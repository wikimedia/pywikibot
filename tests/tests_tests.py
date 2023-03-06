#!/usr/bin/env python3
"""Tests for the tests package."""
#
# (C) Pywikibot team, 2014-2023
#
# Distributed under the terms of the MIT license.
import unittest
from contextlib import suppress

from tests import utils
from tests.aspects import TestCase


class HttpServerProblemTestCase(TestCase):

    """Test HTTP status 502 causes this test class to be skipped."""

    sites = {
        '502': {
            'hostname': 'http://httpbin.org/status/502',
        }
    }

    def test_502(self):
        """Test that framework is skipping this test due to HTTP status 502."""
        self.fail("The test framework should skip this test but it hasn't.")


class TestLengthAssertion(TestCase):

    """Test length assertion methods.

    ``@unittest.expectedFailure`` is used to test the failure of a test;
    this is intentional. If the decorated test passes unexpectedly the
    test will fail.
    """

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
        """Test that assertIsNotEmpty method may fail."""
        self.assertIsNotEmpty([])
        self.assertIsNotEmpty('')

    def test_assert_length(self):
        """Test assertLength method."""
        self.assertLength([], 0)
        self.assertLength(self.seq1, 3)
        self.assertLength(self.seq1, self.seq2)

    @unittest.expectedFailure
    def test_assert_length_fail(self):
        """Test that assertLength method is failing."""
        self.assertLength([], 1)
        self.assertLength(self.seq1, 0)
        self.assertLength(None, self.seq)


class UtilsTests(TestCase):

    """Tests for tests.utils."""

    net = False
    pattern = 'Hello World'

    def test_fixed_generator(self):
        """Test utils.fixed_generator."""
        gen = utils.fixed_generator(self.pattern)
        self.assertEqual(list(gen(1, 'foo', bar='baz')), list(self.pattern))

    def test_entered_loop(self):
        """Test utils.entered_loop."""
        self.assertTrue(utils.entered_loop(self.pattern))
        self.assertFalse(utils.entered_loop(''))


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
