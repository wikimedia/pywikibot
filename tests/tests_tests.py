#!/usr/bin/env python3
"""Tests for the tests package."""
#
# (C) Pywikibot team, 2014-2025
#
# Distributed under the terms of the MIT license.
from __future__ import annotations

import unittest
from contextlib import suppress

from tests import utils
from tests.aspects import DefaultSiteTestCase, TestCase, require_version


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


class TestRequireVersionDry(DefaultSiteTestCase):

    """Test require_version decorator."""

    dry = True

    @require_version('')
    def method(self):
        """Test method for decorator."""

    def test_require_version(self):
        """Test require_version for DrySite."""
        with self.assertRaisesRegex(
            TypeError,
                f'{type(self).__name__}.site must be a BaseSite not DrySite'):
            self.method()


class TestRequireVersion(DefaultSiteTestCase):

    """Test require_version decorator."""

    @require_version('')
    def method_with_params(self, key):
        """Test method for decorated methods with unsupported arguments."""

    def method_failing(self):
        """Test method for decorator with invalid parameter."""
        self.assertTrue(False, 'should never happen')

    @require_version('>=1.31')
    def method_succeed(self):
        """Test that decorator passes."""
        self.assertTrue(False, 'intentional fail for method_succeed test')

    @require_version('<1.31')
    def method_fail(self):
        """Test that decorator skips."""
        self.assertTrue(False, 'intentional fail for test')

    def test_unsupported_methods(self):
        """Test require_version with unsupported methods."""
        with self.assertRaisesRegex(
                TypeError, "Test method 'method_with_params' has parameters"):
            self.method_with_params('42')
        with self.assertRaisesRegex(
                TypeError, "Test method 'method_with_params' has parameters"):
            self.method_with_params(key='42')
        with self.assertRaisesRegex(ValueError,
                                    'There is no valid operator given '):
            self.method_with_params()

    def test_version_needed(self):
        """Test for invalid decorator parameters."""
        with self.assertRaisesRegex(ValueError,
                                    'There is no valid operator given '):
            require_version('foo')(self.method_failing)(self)
        with self.assertRaisesRegex(ValueError,
                                    'first operand foo should not be set'):
            require_version('foo>bar')(self.method_failing)(self)
        with self.assertRaisesRegex(ValueError, 'Invalid version number'):
            require_version('>bar')(self.method_failing)(self)
        with self.assertRaisesRegex(unittest.SkipTest,
                                    r'MediaWiki < v1\.31 required'):
            require_version('<1.31')(self.method_failing)(self)
        with self.assertRaisesRegex(
                unittest.SkipTest,
                r'MediaWiki < v1\.31 required to run this test'):
            require_version('<1.31',
                            'run this test')(self.method_failing)(self)

    def test_decorator(self):
        """Test that decorator passes or skips."""
        with self.assertRaisesRegex(
            AssertionError,
                'intentional fail for method_succeed test'):
            self.method_succeed()
        with self.assertRaisesRegex(unittest.SkipTest,
                                    r'MediaWiki < v1\.31 required'):
            self.method_fail()


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

    @utils.expected_failure_if(True)
    def test_expected_failure_true(self):
        """Test expected_failure_if decorator if condition is True."""
        self.assertTrue(False)

    @utils.expected_failure_if(False)
    def test_expected_failure_false(self):
        """Test expected_failure_if decorator if condition is False."""
        self.assertTrue(True)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
