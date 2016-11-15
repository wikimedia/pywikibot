# -*- coding: utf-8 -*-
"""Tests for exceptions."""
#
# (C) Pywikibot team, 2014-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import pywikibot

from tests.aspects import unittest, DeprecationTestCase


class TestDeprecatedExceptions(DeprecationTestCase):

    """Test usage of deprecation in library code."""

    net = False

    def test_UploadWarning(self):
        """Test exceptions.UploadWarning is deprecated only."""
        # Accessing from the main package should be deprecated.
        cls = pywikibot.UploadWarning

        self.assertOneDeprecationParts('pywikibot.UploadWarning',
                                       'APISite.upload with a warning handler')

        e = cls('foo', 'bar')
        self.assertIsInstance(e, pywikibot.Error)
        self.assertNoDeprecation()

        self._reset_messages()

        # And it should not be accessed from the exceptions module either.
        # The first access loads the symbol
        cls = pywikibot.exceptions.UploadWarning

        self.assertOneDeprecationParts('pywikibot.exceptions.UploadWarning',
                                       'APISite.upload with a warning handler')

        e = cls('foo', 'bar')
        self.assertIsInstance(e, pywikibot.Error)
        self.assertNoDeprecation()

        # Check this again because the second time it should be cached
        cls = pywikibot.exceptions.UploadWarning

        self.assertOneDeprecationParts('pywikibot.exceptions.UploadWarning',
                                       'APISite.upload with a warning handler')

        e = cls('foo', 'bar')
        self.assertIsInstance(e, pywikibot.Error)
        self.assertNoDeprecation()

    def test_PageNotFound(self):
        """Test PageNotFound is deprecated from the package."""
        cls = pywikibot.PageNotFound
        self.assertOneDeprecation(
            'pywikibot.PageNotFound is deprecated, and no longer '
            'used by pywikibot; use http.fetch() instead.')

        e = cls('foo')
        self.assertIsInstance(e, pywikibot.Error)
        self.assertOneDeprecationParts(
            'pywikibot.exceptions.DeprecatedPageNotFoundError')

        cls = pywikibot.exceptions.PageNotFound

        self.assertOneDeprecation(
            'pywikibot.exceptions.PageNotFound is deprecated, and no longer '
            'used by pywikibot; use http.fetch() instead.')

        e = cls('foo')
        self.assertIsInstance(e, pywikibot.Error)
        self.assertOneDeprecationParts(
            'pywikibot.exceptions.DeprecatedPageNotFoundError')


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
