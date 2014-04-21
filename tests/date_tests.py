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

    def testMapEntry(self):
        """Tests the validity of the pywikibot.date format maps."""
        for formatName in date.formats:
            step = 1
            if formatName in date.decadeFormats:
                step = 10
            predicate, start, stop = date.formatLimits[formatName]

            for code, convFunc in date.formats[formatName].items():
                for value in range(start, stop, step):
                    self.assertTrue(
                        predicate(value),
                        "date.formats['%(formatName)s']['%(code)s']:\n"
                        "invalid value %(value)d" % locals())

                    newValue = convFunc(convFunc(value))
                    self.assertEqual(
                        newValue, value,
                        "date.formats['%(formatName)s']['%(code)s']:\n"
                        "value %(newValue)d does not match %(value)s"
                        % locals())


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
