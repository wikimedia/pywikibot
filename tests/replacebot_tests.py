#!/usr/bin/env python3
#
# (C) Pywikibot team, 2015-2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the replace script and ReplaceRobot class."""
from __future__ import annotations

import re
import unittest
from contextlib import suppress
from unittest.mock import MagicMock, call, patch

import pywikibot
from pywikibot import fixes
from scripts import replace
from tests import join_data_path
from tests.aspects import TestCase
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

    def setUp(self) -> None:
        """Replace the original bot class with a fake one."""
        class FakeReplaceBot(replace.ReplaceRobot):

            """A fake bot class for the minimal support."""

            changed_pages = -42  # show that weird number to show this was used

            def __init__(inner_self, *args, **kwargs) -> None:  # noqa: N805
                # Unpatch already here, as otherwise super calls will use
                # this class' super which is the class itself
                replace.ReplaceRobot = self._original_bot
                super().__init__(*args, **kwargs)
                self.bots.append(inner_self)

            def run(inner_self) -> None:  # noqa: N805
                """Nothing to do here."""
                inner_self.changed_pages = -47  # show that run was called

        def patched_login() -> None:
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

    def tearDown(self) -> None:
        """Bring back the old bot class."""
        replace.ReplaceRobot = self._original_bot
        replace.pywikibot.input = self._original_input
        replace.pywikibot.Site = self._original_site
        with empty_sites():
            super().tearDown()

    def _fake_input(self, message) -> str:
        """Cache the message and return static text "TESTRUN"."""
        self.inputs.append(message)
        return 'TESTRUN'

    @staticmethod
    def _run(*args):
        """Run the :py:obj:`replace.main` with the given args.

        It also adds -site and -page parameters:
            -page to not have an empty generator
            -site as it will use Site() otherwise
        """
        return replace.main(*args, '-site:wikipedia:test', '-page:TEST')

    def test_invalid_replacements(self) -> None:
        """Test invalid command line replacement configurations."""
        # old and new no longer need to be together but pairsfile must exist
        self._run('foo', '-pairsfile:/dev/null', 'bar')
        self.assertIn('Error loading /dev/null:',
                      pywikibot.bot.ui.pop_output()[0])

        # only old provided
        with empty_sites():
            self._run('foo')
            self.assertEqual([
                "Incomplete command line pattern replacement pair:\n['foo']",
            ], pywikibot.bot.ui.pop_output())

        # In the end no bots should've been created
        self.assertFalse(self.bots)

    def _test_replacement(self, replacement, clazz=replace.Replacement,
                          offset=0) -> None:
        """Test a replacement from the command line."""
        self.assertIsInstance(replacement, clazz)
        self.assertEqual(replacement.old, str(offset * 2 + 1))
        if not callable(replacement.new):
            self.assertEqual(replacement.new, str(offset * 2 + 2))

    def _test_fix_replacement(self, replacement,
                              length=1, offset=0, msg=False) -> None:
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

    def _apply(self, bot, expected, missing=None, title='Test page') -> None:
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

    def test_only_cmd(self) -> None:
        """Test command line replacements only."""
        bot = self._get_bot(True, '1', '2')
        self.assertLength(bot.replacements, 1)
        self._test_replacement(bot.replacements[0])

        self.assertEqual([
            'The summary message for the command line replacements will '
            'be something like: Bot: Automated text replacement  (-1 +2)',
        ], pywikibot.bot.ui.pop_output())

    def test_cmd_automatic(self) -> None:
        """Test command line replacements with automatic summary."""
        bot = self._get_bot(None, '1', '2', '-automaticsummary')
        self.assertLength(bot.replacements, 1)
        self._test_replacement(bot.replacements[0])
        self.assertEqual(self.inputs, [])

        self.assertEqual([
            'The summary message for the command line replacements will '
            'be something like: Bot: Automated text replacement  (-1 +2)',
        ], pywikibot.bot.ui.pop_output())

    def test_only_fix_global_message(self) -> None:
        """Test fixes replacements only."""
        bot = self._get_bot(None, '-fix:has-msg')
        self.assertLength(bot.replacements, 1)
        self._test_fix_replacement(bot.replacements[0])
        self.assertEqual([], pywikibot.bot.ui.pop_output())

    def test_only_fix_global_message_tw(self) -> None:
        """Test fixes replacements only."""
        bot = self._get_bot(None, '-fix:has-msg-tw')
        self.assertLength(bot.replacements, 1)
        self._test_fix_replacement(bot.replacements[0])
        self.assertEqual([], pywikibot.bot.ui.pop_output())

    def test_only_fix_no_message(self) -> None:
        """Test fixes replacements only."""
        bot = self._get_bot(True, '-fix:no-msg')
        self.assertLength(bot.replacements, 1)
        self._test_fix_replacement(bot.replacements[0])

        self.assertEqual([
            'The summary will not be used when the fix has one defined but '
            'the following fix(es) do(es) not have a summary defined: '
            '"no-msg" (all replacements)',
        ], pywikibot.bot.ui.pop_output())

    def test_only_fix_all_replacement_summary(self) -> None:
        """Test fixes replacements only."""
        bot = self._get_bot(None, '-fix:all-repl-msg')
        self.assertLength(bot.replacements, 1)
        self._test_fix_replacement(bot.replacements[0], msg=True)
        self.assertEqual([], pywikibot.bot.ui.pop_output())

    def test_only_fix_partial_replacement_summary(self) -> None:
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

    def test_only_fix_multiple(self) -> None:
        """Test fixes replacements only."""
        bot = self._get_bot(None, '-fix:has-msg-multiple')
        for offset, replacement in enumerate(bot.replacements):
            self._test_fix_replacement(replacement, 3, offset)
        self.assertLength(bot.replacements, 3)
        self.assertEqual([], pywikibot.bot.ui.pop_output())

    def test_cmd_and_fix(self) -> None:
        """Test command line and fix replacements together."""
        bot = self._get_bot(True, '1', '2', '-fix:has-msg')
        self.assertLength(bot.replacements, 2)
        self._test_replacement(bot.replacements[0])
        self._test_fix_replacement(bot.replacements[1])

        self.assertEqual([
            'The summary message for the command line replacements will be '
            'something like: Bot: Automated text replacement  (-1 +2)',
        ], pywikibot.bot.ui.pop_output())

    def test_except_title(self) -> None:
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

    def test_fix_callable(self) -> None:
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


class TestReplaceHelpers(TestCase):

    """Test helpers used by :func:`replace.main`."""

    net = False

    def setUp(self) -> None:
        """Clear output from previous helper tests."""
        super().setUp()
        pywikibot.bot.ui.clear()

    @patch.object(replace.pywikibot, 'handle_args',
                  side_effect=lambda args: args)
    def test_parse_args(self, handle_args) -> None:
        """Test parsing script-specific arguments."""
        generator_factory = MagicMock()
        generator_factory.handle_args.side_effect = lambda args: args

        options = replace._parse_args((
            '-regex', '-nocase', '-dotall', '-multiline', '-sleep:1.5',
            '-always', '-quiet', '-recursive', '-allowoverlap',
            '-addcat:Test', '-summary:summary', '-nopreload',
            '-xml:dump.xml', '-xmlstart:Start', '-mysqlquery:query',
            '-fix:no-msg', '-excepttitle:Skip', '1', '2',
        ), generator_factory)

        self.assertIsNotNone(options)
        self.assertEqual(options.bot_options, {
            'sleep': 1.5,
            'always': True,
            'quiet': True,
            'recursive': True,
            'allowoverlap': True,
            'addcat': 'Test',
        })
        self.assertEqual(options.replacement_args, ['1', '2'])
        self.assertEqual(options.fix_names, ['no-msg'])
        self.assertEqual(options.exceptions['title'], ['Skip'])
        self.assertEqual(options.edit_summary, 'summary')
        self.assertFalse(options.preload)
        self.assertTrue(options.regex)
        self.assertEqual(
            options.flags, re.IGNORECASE | re.DOTALL | re.MULTILINE)
        self.assertEqual(options.xml_filename, 'dump.xml')
        self.assertEqual(options.xml_start, 'Start')
        self.assertEqual(options.sql_query, 'query')
        handle_args.assert_called_once()

    def test_manual_summary_skips_translation(self) -> None:
        """Test that an explicit summary does not load i18n messages."""
        with patch.object(replace.i18n, 'twtranslate') as twtranslate:
            replacements, summary = replace._build_commandline_replacements(
                ['1', '2'], MagicMock(), 'summary')

        self.assertLength(replacements, 1)
        self.assertIsNone(summary)
        twtranslate.assert_not_called()

    def test_fix_exceptions_are_merged(self) -> None:
        """Test merging command-line and fix exceptions."""
        exceptions = {key: [] for key in replace.EXC_KEYS.values()}
        exceptions['title'].append('Command line')
        generator_factory = MagicMock()
        generator_factory.gens = []

        result = replace._load_fixes(
            ['no-msg-title-exceptions'], MagicMock(), generator_factory,
            exceptions)

        self.assertIsNotNone(result)
        replacements, missing_summaries = result
        self.assertLength(replacements, 1)
        self.assertEqual(set(exceptions['title']),
                         {'Command line', 'Declined'})
        self.assertEqual(exceptions['require-title'], ['Allowed'])
        self.assertEqual(missing_summaries, [
            '"no-msg-title-exceptions" (all replacements)',
        ])

    def test_fix_generator_precedence(self) -> None:
        """Test that a command-line generator suppresses fix generators."""
        fix = {'generator': '-page:Fix', 'replacements': [('1', '2')]}
        exceptions = {key: [] for key in replace.EXC_KEYS.values()}

        with patch.dict(fixes.fixes, {'with-generator': fix}):
            generator_factory = MagicMock()
            generator_factory.gens = [object()]
            replace._load_fixes(
                ['with-generator'], MagicMock(), generator_factory,
                exceptions)
            generator_factory.handle_arg.assert_not_called()

            generator_factory = MagicMock()
            generator_factory.gens = []
            replace._load_fixes(
                ['with-generator'], MagicMock(), generator_factory,
                exceptions)
            generator_factory.handle_arg.assert_called_once_with('-page:Fix')

    def test_build_generator(self) -> None:
        """Test XML, SQL, and combined generator construction."""
        generator_factory = MagicMock()
        generator_factory.getCombinedGenerator.side_effect = (
            lambda generator, preload: generator)
        replacements = [MagicMock()]
        exceptions = {key: [] for key in replace.EXC_KEYS.values()}
        xml_generator = object()
        sql_generator = object()

        with (
            patch.object(replace, 'XmlDumpReplacePageGenerator',
                         return_value=xml_generator) as xml,
            patch.object(replace, 'handle_sql',
                         return_value=sql_generator) as sql,
        ):
            result = replace._build_generator(
                generator_factory, replacements, exceptions, MagicMock(),
                xml_filename='dump.xml', xml_start='Start',
                sql_query='query', preload=False)
            self.assertIs(result, xml_generator)
            xml.assert_called_once()
            sql.assert_not_called()

            result = replace._build_generator(
                generator_factory, replacements, exceptions, MagicMock(),
                xml_filename=None, xml_start=None, sql_query='query',
                preload=True)
            self.assertIs(result, sql_generator)
            sql.assert_called_once_with(
                'query', replacements, exceptions['text-contains'])

            result = replace._build_generator(
                generator_factory, replacements, exceptions, MagicMock(),
                xml_filename=None, xml_start=None, sql_query=None,
                preload=True)
            self.assertIsNone(result)

        self.assertEqual(
            generator_factory.getCombinedGenerator.call_args_list, [
                call(xml_generator, preload=False),
                call(sql_generator, preload=True),
                call(None, preload=True),
            ])

    def test_pairs_file(self) -> None:
        """Test handle_pairsfile."""
        result = replace.handle_pairsfile('non existing file')
        self.assertIsNone(result)

        msg = pywikibot.bot.ui.pop_output()[0]
        self.assertIn('No such file or directory:', msg)
        self.assertIn('non existing file', msg)

        result = replace.handle_pairsfile('tests/data/pagelist-lines.txt')
        self.assertIsNone(result)
        self.assertIn('pagelist-lines.txt contains an incomplete pattern '
                      "replacement pair:\n['file', 'bracket', ",
                      pywikibot.bot.ui.pop_output()[0])

        # check file with and without BOM
        for variant in ('', ' BOM'):
            result = replace.handle_pairsfile(
                f'tests/data/pairsfile{variant}.txt')
            self.assertIsEmpty(pywikibot.bot.ui.pop_output())
            self.assertEqual(result, [
                'Category:Notice Board Quests',
                'Категория:Задания с Доски объявлений',
                'Windbluff Tower Key',
                'Ключ от Крепости Ветров'
            ])


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
