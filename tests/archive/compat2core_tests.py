"""compat2core.py tests."""
#
# (C) Pywikibot team, 2019-2021
#
# Distributed under the terms of the MIT license.
#
import unittest

import scripts.maintenance.compat2core as c2c
from tests.aspects import TestCase


class Compat2CoreTests(TestCase):

    """Validate compat2core script."""

    net = False

    def test_replacements(self):
        """Test compat2core replacements."""
        for item in c2c.replacements:
            self.assertLength(item, 2)
            self.assertIsInstance(item[0], str)
            self.assertIsInstance(item[1], str)

    def test_warnings(self):
        """Test compat2core warnings."""
        for item in c2c.warnings:
            self.assertLength(item, 2)
            self.assertIsInstance(item[0], str)
            self.assertIsInstance(item[1], str)

    def test_bot(self):
        """Test compat2core bot."""
        bot = c2c.ConvertBot(warnonly=True)
        self.assertIsNone(bot.source)
        self.assertTrue(bot.warnonly)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
