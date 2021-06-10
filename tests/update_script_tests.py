"""update_script.py tests."""
#
# (C) Pywikibot team, 2019-2021
#
# Distributed under the terms of the MIT license.
#
import unittest

import scripts.maintenance.update_script as us
from tests.aspects import TestCase


class Compat2CoreTests(TestCase):

    """Validate update_script script."""

    net = False

    def test_replacements(self):
        """Test update_script replacements."""
        for item in us.replacements:
            self.assertLength(item, 2)
            self.assertIsInstance(item[0], str)
            self.assertIsInstance(item[1], str)

    def test_warnings(self):
        """Test update_script warnings."""
        for item in us.warnings:
            self.assertLength(item, 2)
            self.assertIsInstance(item[0], str)
            self.assertIsInstance(item[1], str)

    def test_bot(self):
        """Test update_script bot."""
        bot = us.ConvertBot(warnonly=True)
        self.assertIsNone(bot.source)
        self.assertTrue(bot.warnonly)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
