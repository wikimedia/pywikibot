#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the tests package."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import pywikibot

from tests.aspects import unittest, TestCase
from tests.utils import allowed_failure


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
        pass


class TestPageAssert(TestCase):

    """Test page assertion methods."""

    family = 'wikipedia'
    code = 'en'

    dry = True

    @allowed_failure
    def test_assertPageTitlesEqual(self):
        """Test assertPageTitlesEqual shows the second page title and '...'."""
        pages = [pywikibot.Page(self.site, 'Foo'),
                 pywikibot.Page(self.site, 'Bar'),
                 pywikibot.Page(self.site, 'Baz')]
        self.assertPageTitlesEqual(pages,
                                   ['Foo'],
                                   self.site)


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
