# -*- coding: utf-8  -*-
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

from tests.utils import unittest
from pywikibot import date


class TestDate(unittest.TestCase):
    """Test cases for date library"""

    def __init__(self, formatname):
        super(TestDate, self).__init__()
        self.formatname = formatname

    def testMapEntry(self, formatname):
        """The test ported from date.py"""
        step = 1
        if formatname in date.decadeFormats:
            step = 10
        predicate, start, stop = date.formatLimits[formatname]

        for code, convFunc in date.formats[formatname].items():
            for value in range(start, stop, step):
                self.assertTrue(
                    predicate(value),
                    "date.formats['%(formatname)s']['%(code)s']:\n"
                    "invalid value %(value)d" % locals())

                newValue = convFunc(convFunc(value))
                self.assertEqual(
                    newValue, value,
                    "date.formats['%(formatname)s']['%(code)s']:\n"
                    "value %(newValue)d does not match %(value)s"
                    % locals())

    def runTest(self):
        """method called by unittest"""
        self.testMapEntry(self.formatname)


def suite():
    """Setup the test suite and register all test to different instances"""
    suite = unittest.TestSuite()
    suite.addTests(TestDate(formatname) for formatname in date.formats)
    return suite


if __name__ == '__main__':
    try:
        unittest.TextTestRunner().run(suite())
    except SystemExit:
        pass
