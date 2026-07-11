#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the exceptions module."""
from __future__ import annotations

import unittest
from contextlib import suppress

import pywikibot
from pywikibot.exceptions import ApiTimeoutError, Error, MaxlagTimeoutError
from tests.aspects import DeprecationTestCase, TestCase


class TestApiTimeoutError(TestCase):

    """Test ApiTimeoutError exceptions."""

    net = False

    def test_hierarchy(self) -> None:
        """Test inheritance hierarchy."""
        self.assertTrue(issubclass(ApiTimeoutError, Error))
        self.assertTrue(issubclass(MaxlagTimeoutError, ApiTimeoutError))

    def test_raise_catch(self) -> None:
        """Test raising and catching ApiTimeoutError."""
        with self.assertRaises(ApiTimeoutError):
            raise ApiTimeoutError('Test timeout')

        with self.assertRaises(ApiTimeoutError):
            raise MaxlagTimeoutError('Test maxlag timeout')


class TestTimeoutErrorDeprecation(DeprecationTestCase):

    """Test deprecation of TimeoutError alias."""

    net = False

    def test_deprecation(self) -> None:
        """Test that accessing TimeoutError triggers a deprecation warning."""
        # Accessing the deprecated attribute
        exc_class = pywikibot.exceptions.TimeoutError
        self.assertIs(exc_class, ApiTimeoutError)
        self.assertOneDeprecationParts(
            'pywikibot.exceptions.TimeoutError',
            'pywikibot.exceptions.ApiTimeoutError'
        )

    def test_raise_catch_deprecated(self) -> None:
        """Test raising and catching using the deprecated alias."""
        # Reset any messages from previous tests
        self._reset_messages()

        # Catch ApiTimeoutError using the TimeoutError alias
        try:
            raise ApiTimeoutError('Test raise')
        except pywikibot.exceptions.TimeoutError:
            pass

        self.assertOneDeprecationParts(
            'pywikibot.exceptions.TimeoutError',
            'pywikibot.exceptions.ApiTimeoutError'
        )


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
