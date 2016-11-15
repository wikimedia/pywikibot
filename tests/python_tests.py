#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests Python features."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import unicodedata
try:
    import unicodedata2
except ImportError:
    unicodedata2 = None

from pywikibot.tools import PYTHON_VERSION

from tests.aspects import TestCase, unittest
from tests.utils import expected_failure_if

# TODO:
# very old
# http://bugs.python.org/issue2517
#
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
# http://bugs.python.org/issue1678345


class PythonTestCase(TestCase):

    """Test Python bugs and features."""

    net = False

    @expected_failure_if((2, 7, 0) <= PYTHON_VERSION < (2, 7, 2) or
                         PYTHON_VERSION == (2, 6, 6))
    def test_issue_10254(self):
        """Test Python issue #10254."""
        # Python 2.6.6, 2.7.0 and 2.7.1 have a bug in this routine.
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
