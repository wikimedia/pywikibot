# -*- coding: utf-8  -*-
"""Tests for the replace script and ReplaceRobot class."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#
import os

from pywikibot import fixes

from scripts import replace

from tests import _data_dir
from tests.aspects import unittest, TestCase

# Load only the custom fixes
fixes.fixes.clear()
fixes._load_file(os.path.join(_data_dir, 'fixes.py'))


class TestReplacementsMain(TestCase):

    """Test various calls of main()."""

    SUMMARY_CONFIRMATION = (
        'Press Enter to use this automatic message, or enter a '
        'description of the\nchanges your bot will make:')

    family = 'test'
    code = 'test'

    def setUp(self):
        """Replace the original bot class with a fake one."""
        class FakeReplaceBot(object):

            """A fake bot class for the minimal support."""

            changed_pages = -42  # show that weird number to show this was used

            def __init__(inner_self, generator, replacements, exceptions={},
                         always=False, allowoverlap=False, recursive=False,
                         addedCat=None, sleep=None, summary='', site=None,
                         **kwargs):
                inner_self.replacements = replacements
                inner_self.site = site
                self.bots.append(inner_self)

            def run(inner_self):
                """Nothing to do here."""
                pass

        super(TestReplacementsMain, self).setUp()
        self._original_bot = replace.ReplaceRobot
        self._original_input = replace.pywikibot.input
        self.bots = []
        self.inputs = []
        replace.ReplaceRobot = FakeReplaceBot
        replace.pywikibot.input = self._fake_input

    def tearDown(self):
        """Bring back the old bot class."""
        replace.ReplaceRobot = self._original_bot
        replace.pywikibot.input = self._original_input
        super(TestReplacementsMain, self).tearDown()

    def _fake_input(self, message):
        """Cache the message and return static text "TESTRUN"."""
        self.inputs.append(message)
        return 'TESTRUN'

    def _run(self, *args):
        """Run the L{replace.main} with the given args and summary and page."""
        # -page to not have an empty generator
        # -lang and -family as it will use Site() otherwise
        return replace.main(*(args + ('-lang:test', '-family:test',
                                      '-page:TEST')))

    def test_invalid_replacements(self):
        """Test invalid command line replacement configurations."""
        # old and new need to be together
        self.assertFalse(self._run('foo', '-replacementfile:/dev/null', 'bar'))
        # only old provided
        self.assertFalse(self._run('foo'))

        # In the end no bots should've been created
        self.assertFalse(self.bots)

    def _test_replacement(self, replacement, clazz=replace.Replacement,
                          offset=0):
        """Test a replacement from the command line."""
        self.assertIsInstance(replacement, clazz)
        self.assertEqual(replacement.old, str(offset * 2 + 1))
        self.assertEqual(replacement.new, str(offset * 2 + 2))

    def _test_fix_replacement(self, replacement, length=1, offset=0):
        """Test a replacement from a fix."""
        assert length > offset
        self._test_replacement(replacement, replace.ReplacementListEntry,
                               offset)
        self.assertIsInstance(replacement.fix_set, replace.ReplacementList)
        self.assertIsInstance(replacement.fix_set, list)
        self.assertIn(replacement, replacement.fix_set)
        self.assertIs(replacement, replacement.fix_set[offset])
        self.assertEqual(len(replacement.fix_set), length)

    def _get_bot(self, only_confirmation, *args):
        """Run with arguments, assert and return one bot."""
        self.assertIsNone(self._run(*args))
        self.assertEqual(len(self.bots), 1)
        bot = self.bots[0]
        if only_confirmation is not None:
            self.assertIn(self.SUMMARY_CONFIRMATION, self.inputs)
            if only_confirmation is True:
                self.assertEqual(len(self.inputs), 1)
        else:
            self.assertNotIn(self.SUMMARY_CONFIRMATION, self.inputs)
        self.assertEqual(bot.site, self.site)
        return bot

    def test_only_cmd(self):
        """Test command line replacements only."""
        bot = self._get_bot(True, '1', '2')
        self.assertEqual(len(bot.replacements), 1)
        self._test_replacement(bot.replacements[0])

    def test_only_fix_global_message(self):
        """Test fixes replacements only."""
        bot = self._get_bot(True, '-fix:has-msg')
        self.assertEqual(len(bot.replacements), 1)
        self._test_fix_replacement(bot.replacements[0])

    def test_only_fix_global_message_tw(self):
        """Test fixes replacements only."""
        bot = self._get_bot(True, '-fix:has-msg-tw')
        self.assertEqual(len(bot.replacements), 1)
        self._test_fix_replacement(bot.replacements[0])

    def test_only_fix_no_message(self):
        """Test fixes replacements only."""
        bot = self._get_bot(True, '-fix:no-msg')
        self.assertEqual(len(bot.replacements), 1)
        self._test_fix_replacement(bot.replacements[0])

    def test_only_fix_multiple(self):
        """Test fixes replacements only."""
        bot = self._get_bot(True, '-fix:has-msg-multiple')
        for offset, replacement in enumerate(bot.replacements):
            self._test_fix_replacement(replacement, 3, offset)
        self.assertEqual(len(bot.replacements), 3)

    def test_cmd_and_fix(self):
        """Test command line and fix replacements together."""
        bot = self._get_bot(True, '1', '2', '-fix:has-msg')
        self.assertEqual(len(bot.replacements), 2)
        self._test_replacement(bot.replacements[0])
        self._test_fix_replacement(bot.replacements[1])


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
