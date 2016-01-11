#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests Python features."""
#
# (C) Pywikibot team, 2015-2018
#
# Distributed under the terms of the MIT license.
from __future__ import absolute_import, unicode_literals

import unicodedata
try:
    import unicodedata2
except ImportError:
    unicodedata2 = None

from tests.aspects import TestCase, unittest

# TODO:
# unicode
# http://sourceforge.net/p/pywikipediabot/bugs/1246/
# http://bugs.python.org/issue10254
#
# ip
# http://bugs.python.org/issue22282
#
# http://bugs.python.org/issue7559
#
# diff
# http://bugs.python.org/issue2142
# http://bugs.python.org/issue11747
# http://sourceforge.net/p/pywikipediabot/bugs/509/
# https://phabricator.wikimedia.org/T57329
# http://bugs.python.org/issue1528074


class PythonTestCase(TestCase):

    """Test Python bugs and features."""

    net = False

    def test_issue_10254(self):
        """Test Python issue #10254."""
        # Python 2.7.0 and 2.7.1 have a bug in this routine.
        # See T102461 and http://bugs.python.org/issue10254
        text = 'Li̍t-sṳ́'
        self.assertEqual(text, unicodedata.normalize('NFC', text))

    @unittest.skipIf(not unicodedata2, 'unicodedata2 not found')
    def test_issue_10254_unicodedata2(self):
        """Test Python issue #10254 is avoided with unicodedata2 package."""
        text = 'Li̍t-sṳ́'
        self.assertEqual(text, unicodedata2.normalize('NFC', text))


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
