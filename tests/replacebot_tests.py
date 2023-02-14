#!/usr/bin/env python3
"""Tests for the replace script and ReplaceRobot class."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

import pywikibot
from pywikibot import fixes
from scripts import replace
from tests import join_data_path
from tests.bot_tests import TWNBotTestCase
from tests.utils import empty_sites


# Load only the custom fixes
fixes.fixes.clear()
fixes._load_file(join_data_path('fixes.py'))


class TestReplacementsMain(TWNBotTestCase):

    """Test various calls of main()."""

    SUMMARY_CONFIRMATION = (
        'Press Enter to use this automatic message, or enter a '
        'description of the\nchanges your bot will make:')

    family = 'wikipedia'
    code = 'test'
    cached = False

    def setUp(self):
        """Replace the original bot class with a fake one."""
        class FakeReplaceBot(replace.ReplaceRobot):

            """A fake bot class for the minimal support."""

            changed_pages = -42  # show that weird number to show this was used

            def __init__(inner_self, *args, **kwargs):  # noqa: N805
                # Unpatch already here, as otherwise super calls will use
                # this class' super which is the class itself
                replace.ReplaceRobot = self._original_bot
                super().__init__(*args, **kwargs)
                self.bots.append(inner_self)

            def run(inner_self):  # noqa: N805
                """Nothing to do here."""
                inner_self.changed_pages = -47  # show that run was called

        def patched_login():
            """Do nothing."""

        def patched_site(*args, **kwargs):
            """Patching a Site instance replacing it's login."""
            site = self._original_site(*args, **kwargs)
            site.login = patched_login
            return site

        super().setUp()
        self._original_bot = replace.ReplaceRobot
        self._original_input = replace.pywikibot.input
        self._original_site = replace.pywikibot.Site
        self.bots = []
        self.inputs = []
        replace.ReplaceRobot = FakeReplaceBot
        replace.pywikibot.input = self._fake_input
        replace.pywikibot.Site = patched_site

        pywikibot.bot.ui.clear()

    def tearDown(self):
        """Bring back the old bot class."""
        replace.ReplaceRobot = self._original_bot
        replace.pywikibot.input = self._original_input
        replace.pywikibot.Site = self._original_site
        with empty_sites():
            super().tearDown()

    def _fake_input(self, message):
        """Cache the message and return static text "TESTRUN"."""
        self.inputs.append(message)
        return 'TESTRUN'

    def _run(self, *args):
        """Run the :py:obj:`replace.main` with the given args.

        It also adds -site and -page parameters:
            -page to not have an empty generator
            -site as it will use Site() otherwise
        """
        return replace.main(*(args + ('-site:wikipedia:test', '-page:TEST')))

    def test_invalid_replacements(self):
        """Test invalid command line replacement configurations."""
        # old and new no longer need to be together but pairsfile must exist
        self._run('foo', '-pairsfile:/dev/null', 'bar')
        self.assertIn('Error loading /dev/null:',
                      pywikibot.bot.ui.pop_output()[0])

        # only old provided
        with empty_sites():
            self._run('foo')
            self.assertEqual([
                'Incomplete command line pattern replacement pair.',
            ], pywikibot.bot.ui.pop_output())

        # In the end no bots should've been created
        self.assertFalse(self.bots)

    def _test_replacement(self, replacement, clazz=replace.Replacement,
                          offset=0):
        """Test a replacement from the command line."""
        self.assertIsInstance(replacement, clazz)
        self.assertEqual(replacement.old, str(offset * 2 + 1))
        if not callable(replacement.new):
            self.assertEqual(replacement.new, str(offset * 2 + 2))

    def _test_fix_replacement(self, replacement,
                              length=1, offset=0, msg=False):
        """Test a replacement from a fix."""
        assert length > offset
        self._test_replacement(replacement, replace.ReplacementListEntry,
                               offset)
        if msg:
            self.assertEqual(replacement.edit_summary,
                             f'M{offset + 1}')
        else:
            self.assertIs(replacement.edit_summary,
                          replacement.fix_set.edit_summary)
        self.assertIs(replacement.fix_set, replacement.container)
        self.assertIsInstance(replacement.fix_set, replace.ReplacementList)
        self.assertIsInstance(replacement.fix_set, list)
        self.assertIn(replacement, replacement.fix_set)
        self.assertIs(replacement, replacement.fix_set[offset])
        self.assertLength(replacement.fix_set, length)

    def _get_bot(self, only_confirmation, *args):
        """Run with arguments, assert and return one bot."""
        self._run(*args)
        self.assertLength(self.bots, 1)
        bot = self.bots[0]
        if only_confirmation is not None:
            self.assertIn(self.SUMMARY_CONFIRMATION, self.inputs)
            if only_confirmation is True:
                self.assertLength(self.inputs, 1)
        else:
            self.assertNotIn(self.SUMMARY_CONFIRMATION, self.inputs)
        self.assertEqual(bot.site, self.site)
        self.assertEqual(bot.changed_pages, -47)
        return bot

    def _apply(self, bot, expected, missing=None, title='Test page'):
        """Test applying a test change."""
        applied = set()
        if missing is True:
            required_applied = set()
        else:
            required_applied = set(bot.replacements)
            if missing:
                required_applied -= set(missing)
        # shouldn't be edited anyway
        page = pywikibot.Page(self.site, title)
        self.assertEqual(expected,
                         bot.apply_replacements('Hello 1', applied, page))
        self.assertEqual(applied, required_applied)

    def test_only_cmd(self):
        """Test command line replacements only."""
        bot = self._get_bot(True, '1', '2')
        self.assertLength(bot.replacements, 1)
        self._test_replacement(bot.replacements[0])

        self.assertEqual([
            'The summary message for the command line replacements will '
            'be something like: Bot: Automated text replacement  (-1 +2)',
        ], pywikibot.bot.ui.pop_output())

    def test_cmd_automatic(self):
        """Test command line replacements with automatic summary."""
        bot = self._get_bot(None, '1', '2', '-automaticsummary')
        self.assertLength(bot.replacements, 1)
        self._test_replacement(bot.replacements[0])
        self.assertEqual(self.inputs, [])

        self.assertEqual([
            'The summary message for the command line replacements will '
            'be something like: Bot: Automated text replacement  (-1 +2)',
        ], pywikibot.bot.ui.pop_output())

    def test_only_fix_global_message(self):
        """Test fixes replacements only."""
        bot = self._get_bot(None, '-fix:has-msg')
        self.assertLength(bot.replacements, 1)
        self._test_fix_replacement(bot.replacements[0])
        self.assertEqual([], pywikibot.bot.ui.pop_output())

    def test_only_fix_global_message_tw(self):
        """Test fixes replacements only."""
        bot = self._get_bot(None, '-fix:has-msg-tw')
        self.assertLength(bot.replacements, 1)
        self._test_fix_replacement(bot.replacements[0])
        self.assertEqual([], pywikibot.bot.ui.pop_output())

    def test_only_fix_no_message(self):
        """Test fixes replacements only."""
        bot = self._get_bot(True, '-fix:no-msg')
        self.assertLength(bot.replacements, 1)
        self._test_fix_replacement(bot.replacements[0])

        self.assertEqual([
            'The summary will not be used when the fix has one defined but '
            'the following fix(es) do(es) not have a summary defined: '
            '"no-msg" (all replacements)',
        ], pywikibot.bot.ui.pop_output())

    def test_only_fix_all_replacement_summary(self):
        """Test fixes replacements only."""
        bot = self._get_bot(None, '-fix:all-repl-msg')
        self.assertLength(bot.replacements, 1)
        self._test_fix_replacement(bot.replacements[0], msg=True)
        self.assertEqual([], pywikibot.bot.ui.pop_output())

    def test_only_fix_partial_replacement_summary(self):
        """Test fixes replacements only."""
        bot = self._get_bot(True, '-fix:partial-repl-msg')
        for offset, replacement in enumerate(bot.replacements):
            self._test_fix_replacement(replacement, 2, offset, offset == 0)
        self.assertLength(bot.replacements, 2)

        self.assertEqual([
            'The summary will not be used when the fix has one defined but '
            'the following fix(es) do(es) not have a summary defined: '
            '"partial-repl-msg" (replacement #2)',
        ], pywikibot.bot.ui.pop_output())

    def test_only_fix_multiple(self):
        """Test fixes replacements only."""
        bot = self._get_bot(None, '-fix:has-msg-multiple')
        for offset, replacement in enumerate(bot.replacements):
            self._test_fix_replacement(replacement, 3, offset)
        self.assertLength(bot.replacements, 3)
        self.assertEqual([], pywikibot.bot.ui.pop_output())

    def test_cmd_and_fix(self):
        """Test command line and fix replacements together."""
        bot = self._get_bot(True, '1', '2', '-fix:has-msg')
        self.assertLength(bot.replacements, 2)
        self._test_replacement(bot.replacements[0])
        self._test_fix_replacement(bot.replacements[1])

        self.assertEqual([
            'The summary message for the command line replacements will be '
            'something like: Bot: Automated text replacement  (-1 +2)',
        ], pywikibot.bot.ui.pop_output())

    def test_except_title(self):
        """Test excepting and requiring a title specific to fix."""
        bot = self._get_bot(True, '-fix:no-msg-title-exceptions')
        self.assertLength(bot.replacements, 1)
        self._test_fix_replacement(bot.replacements[0])
        self.assertIn('title', bot.replacements[0].exceptions)
        self.assertIn('require-title', bot.replacements[0].exceptions)

        self.assertEqual([
            'The summary will not be used when the fix has one defined but '
            'the following fix(es) do(es) not have a summary defined: '
            '"no-msg-title-exceptions" (all replacements)',
        ], pywikibot.bot.ui.pop_output())

        self._apply(bot, 'Hello 1', missing=True, title='Neither')
        self.assertEqual([
            'Skipping fix "no-msg-title-exceptions" on [[Neither]] because '
            'the title is on the exceptions list.',
        ], pywikibot.bot.ui.pop_output())

        self._apply(bot, 'Hello 2', title='Allowed')
        self.assertEqual([], pywikibot.bot.ui.pop_output())

        self._apply(bot, 'Hello 1', missing=True, title='Allowed Declined')
        self.assertEqual([
            'Skipping fix "no-msg-title-exceptions" on [[Allowed Declined]] '
            'because the title is on the exceptions list.'
        ], pywikibot.bot.ui.pop_output())

    def test_fix_callable(self):
        """Test fix replacements using a callable."""
        bot = self._get_bot(True, '-fix:no-msg-callable')
        self.assertLength(bot.replacements, 1)
        self._test_fix_replacement(bot.replacements[0])
        self.assertTrue(callable(bot.replacements[0].new))

        self.assertEqual([
            'The summary will not be used when the fix has one defined but '
            'the following fix(es) do(es) not have a summary defined: '
            '"no-msg-callable" (all replacements)',
        ], pywikibot.bot.ui.pop_output())


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
