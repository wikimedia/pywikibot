# -*- coding: utf-8  -*-
"""Tests for exceptions."""
#
# (C) Pywikibot team, 2014
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
        # Accessing from the main package should work fine.
        cls = pywikibot.UploadWarning
        self.assertNoDeprecation()
        e = cls('foo', 'bar')
        self.assertIsInstance(e, pywikibot.Error)
        self.assertNoDeprecation()

        self._reset_messages()

        # But it sholdnt be accessed from the exceptions module.
        cls = pywikibot.exceptions.UploadWarning

        self.assertOneDeprecationParts('pywikibot.exceptions.UploadWarning',
                                       'pywikibot.data.api.UploadWarning')

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


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
