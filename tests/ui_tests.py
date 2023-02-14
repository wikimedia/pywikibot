#!/usr/bin/env python3
"""Tests for the user interface."""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import io
import logging
import os
import unittest
from contextlib import redirect_stdout, suppress
from unittest.mock import patch

import pywikibot
from pywikibot.bot import (
    CRITICAL,
    DEBUG,
    ERROR,
    INFO,
    INPUT,
    STDOUT,
    VERBOSE,
    WARNING,
)
from pywikibot.userinterfaces import (
    terminal_interface_base,
    terminal_interface_unix,
    terminal_interface_win32,
)
from pywikibot.userinterfaces.transliteration import NON_LATIN_DIGITS, _trans
from tests.aspects import TestCase, TestCaseBase


logger = logging.getLogger('pywiki')
loggingcontext = {'caller_name': 'ui_tests',
                  'caller_file': 'ui_tests',
                  'caller_line': 0,
                  'newline': '\n'}


class UITestCase(TestCaseBase):

    """UI tests."""

    net = False

    def setUp(self):
        """Setup test.

        Here we patch standard input, output, and errors, essentially
        redirecting to `StringIO` streams.
        """
        super().setUp()
        self.stdout_patcher = patch('sys.stdout', new_callable=io.StringIO)
        self.strout = self.stdout_patcher.start()
        self.stderr_patcher = patch('sys.stderr', new_callable=io.StringIO)
        self.strerr = self.stderr_patcher.start()
        self.stdin_patcher = patch('sys.stdin', new_callable=io.StringIO)
        self.strin = self.stdin_patcher.start()

        pywikibot.bot.set_interface('terminal')

        self.org_input = pywikibot.bot.ui._raw_input
        pywikibot.bot.ui._raw_input = self._patched_input

        pywikibot.config.colorized_output = True
        pywikibot.config.transliterate = False
        pywikibot.ui.transliteration_target = None
        pywikibot.ui.encoding = 'utf-8'

    def tearDown(self):
        """Cleanup test."""
        super().tearDown()

        self.stdout_patcher.stop()
        self.stderr_patcher.stop()
        self.stdin_patcher.stop()

        pywikibot.bot.ui._raw_input = self.org_input
        pywikibot.bot.set_interface('buffer')

    def _patched_input(self):
        return self.strin.readline().strip()


class ExceptionTestError(Exception):

    """Test exception."""


class TestTerminalOutput(UITestCase):

    """Terminal output tests."""

    tests = [
        ('debug', DEBUG, '', ''),
        ('verbose', VERBOSE, '', ''),
        ('info', INFO, '', 'info\n'),
        ('stdout', STDOUT, 'stdout\n', ''),
        ('input', INPUT, '', 'input\n'),
        ('WARNING', WARNING, '', 'WARNING: WARNING\n'),
        ('ERROR', ERROR, '', 'ERROR: ERROR\n'),
        ('CRITICAL', CRITICAL, '', 'CRITICAL: CRITICAL\n'),
    ]

    def test_outputlevels_logging(self):
        """Test logger with output levels."""
        for text, level, out, err in self.tests:
            with self.subTest(test=text):
                logger.log(level, text, extra=loggingcontext)
                self.assertEqual(self.strout.getvalue(), out)
                self.assertEqual(self.strerr.getvalue(), err)

                # reset terminal files
                for stream in [self.strout, self.strerr, self.strin]:
                    stream.truncate(0)
                    stream.seek(0)

    def test_output(self):
        pywikibot.info('output')
        self.assertEqual(self.strout.getvalue(), '')
        self.assertEqual(self.strerr.getvalue(), 'output\n')

    def test_stdout(self):
        pywikibot.stdout('output')
        self.assertEqual(self.strout.getvalue(), 'output\n')
        self.assertEqual(self.strerr.getvalue(), '')

    def test_warning(self):
        pywikibot.warning('warning')
        self.assertEqual(self.strout.getvalue(), '')
        self.assertEqual(self.strerr.getvalue(), 'WARNING: warning\n')

    def test_error(self):
        pywikibot.error('error')
        self.assertEqual(self.strout.getvalue(), '')
        self.assertEqual(self.strerr.getvalue(), 'ERROR: error\n')

    def test_log(self):
        pywikibot.log('log')
        self.assertEqual(self.strout.getvalue(), '')
        self.assertEqual(self.strerr.getvalue(), '')

    def test_critical(self):
        pywikibot.critical('critical')
        self.assertEqual(self.strout.getvalue(), '')
        self.assertEqual(self.strerr.getvalue(), 'CRITICAL: critical\n')

    def test_debug(self):
        pywikibot.debug('debug', layer='test')
        self.assertEqual(self.strout.getvalue(), '')
        self.assertEqual(self.strerr.getvalue(), '')

    def test_exception(self):
        try:
            raise ExceptionTestError('Testing Exception')
        except ExceptionTestError:
            pywikibot.error('exception', exc_info=False)
        self.assertEqual(self.strout.getvalue(), '')
        self.assertEqual(self.strerr.getvalue(),
                         'ERROR: exception\n')

    def test_exception_empty(self):
        try:
            raise ExceptionTestError('Testing Exception')
        except ExceptionTestError:
            pywikibot.exception(exc_info=False)
        self.assertEqual(self.strout.getvalue(), '')
        self.assertEqual(self.strerr.getvalue(),
                         'ERROR: Testing Exception (ExceptionTestError)\n')

    def test_exception_tb(self):
        try:
            raise ExceptionTestError('Testing Exception')
        except ExceptionTestError:
            pywikibot.exception()
        self.assertEqual(self.strout.getvalue(), '')
        stderrlines = self.strerr.getvalue().split('\n')
        self.assertEqual(stderrlines[0],
                         'ERROR: Testing Exception')
        self.assertEqual(stderrlines[1], 'Traceback (most recent call last):')
        self.assertEqual(stderrlines[3],
                         "    raise ExceptionTestError('Testing Exception')")

        end_str = ': Testing Exception'
        self.assertTrue(stderrlines[-1].endswith(end_str),
                        '\n{!r} does not end with {!r}'
                        .format(stderrlines[-1], end_str))


class TestTerminalInput(UITestCase):

    """Terminal input tests."""

    input_choice_output = 'question ([A]nswer 1, a[n]swer 2, an[s]wer 3): '

    def testInput(self):
        self.strin.write('input to read\n')
        self.strin.seek(0)
        returned = pywikibot.input('question')

        self.assertEqual(self.strout.getvalue(), '')
        self.assertEqual(self.strerr.getvalue(), 'question: ')
        self.assertIsInstance(returned, str)
        self.assertEqual(returned, 'input to read')

    def test_input_yn(self):
        self.strin.write('\n')
        self.strin.seek(0)
        returned = pywikibot.input_yn('question', False, automatic_quit=False)

        self.assertEqual(self.strout.getvalue(), '')
        self.assertEqual(self.strerr.getvalue(), 'question ([y]es, [N]o): ')
        self.assertFalse(returned)

    def _call_input_choice(self):
        rv = pywikibot.input_choice(
            'question',
            (('answer 1', 'A'),
             ('answer 2', 'N'),
             ('answer 3', 'S')),
            'A',
            automatic_quit=False)

        self.assertEqual(self.strout.getvalue(), '')
        self.assertIsInstance(rv, str)
        return rv

    def testInputChoiceDefault(self):
        self.strin.write('\n')
        self.strin.seek(0)
        returned = self._call_input_choice()

        self.assertEqual(returned, 'a')

    def testInputChoiceCapital(self):
        self.strin.write('N\n')
        self.strin.seek(0)
        returned = self._call_input_choice()

        self.assertEqual(self.strerr.getvalue(), self.input_choice_output)
        self.assertEqual(returned, 'n')

    def testInputChoiceNonCapital(self):
        self.strin.write('n\n')
        self.strin.seek(0)
        returned = self._call_input_choice()

        self.assertEqual(self.strerr.getvalue(), self.input_choice_output)
        self.assertEqual(returned, 'n')

    def testInputChoiceIncorrectAnswer(self):
        self.strin.write('X\nN\n')
        self.strin.seek(0)
        returned = self._call_input_choice()

        self.assertEqual(self.strerr.getvalue(), self.input_choice_output * 2)
        self.assertEqual(returned, 'n')

    def test_input_list_choice(self):
        """Test input_list_choice function."""
        options = ('answer 1', 'answer 2', 'answer 3')
        rv = pywikibot.bot.input_list_choice('question', options, '2')

        self.assertEqual(self.strout.getvalue(), '')
        self.assertEqual(
            self.strerr.getvalue(),
            ''.join(f'{num}: {items}\n'
                    for num, items in enumerate(options, start=1))
            + 'question (default: 2): ')
        self.assertEqual(rv, 'answer 2')


@unittest.skipUnless(os.name == 'posix', 'requires Unix console')
class TestTerminalOutputColorUnix(UITestCase):

    """Terminal output color tests."""

    str1 = 'text <<lightpurple>>light purple text<<default>> text'

    def testOutputColorizedText(self):
        pywikibot.info(self.str1)
        self.assertEqual(self.strout.getvalue(), '')
        self.assertEqual(
            self.strerr.getvalue(),
            'text \x1b[95mlight purple text\x1b[0m text\n')

    def testOutputNoncolorizedText(self):
        pywikibot.config.colorized_output = False
        pywikibot.info(self.str1)
        self.assertEqual(self.strout.getvalue(), '')
        self.assertEqual(
            self.strerr.getvalue(),
            'text light purple text text ***\n')

    str2 = ('normal text <<lightpurple>> light purple '
            '<<lightblue>> light blue <<previous>> light purple '
            '<<default>> normal text')

    def testOutputColorCascade_incorrect(self):
        """Test incorrect behavior of testOutputColorCascade."""
        pywikibot.info(self.str2)
        self.assertEqual(self.strout.getvalue(), '')
        self.assertEqual(
            self.strerr.getvalue(),
            'normal text \x1b[95m light purple '
            '\x1b[94m light blue \x1b[95m light purple '
            '\x1b[0m normal text\n')


@unittest.skipUnless(os.name == 'posix', 'requires Unix console')
class TestTerminalUnicodeUnix(UITestCase):

    """Terminal output tests for Unix."""

    def testOutputUnicodeText(self):
        pywikibot.info('Заглавная_страница')
        self.assertEqual(self.strout.getvalue(), '')
        self.assertEqual(self.strerr.getvalue(), 'Заглавная_страница\n')

    def testInputUnicodeText(self):
        self.strin.write('Заглавная_страница\n')
        self.strin.seek(0)

        returned = pywikibot.input('Википедию? ')

        self.assertEqual(self.strout.getvalue(), '')
        self.assertEqual(
            self.strerr.getvalue(), 'Википедию? ')

        self.assertIsInstance(returned, str)
        self.assertEqual(returned, 'Заглавная_страница')


@unittest.skipUnless(os.name == 'posix', 'requires Unix console')
class TestTransliterationUnix(UITestCase):

    """Terminal output transliteration tests."""

    def testOutputTransliteratedUnicodeText(self):
        pywikibot.bot.ui.encoding = 'latin-1'
        pywikibot.config.transliterate = True
        pywikibot.info('abcd АБГД αβγδ あいうえお')
        self.assertEqual(self.strout.getvalue(), '')
        self.assertEqual(
            self.strerr.getvalue(),
            'abcd \x1b[93mA\x1b[0m\x1b[93mB\x1b[0m\x1b[93mG\x1b[0m'
            '\x1b[93mD\x1b[0m \x1b[93ma\x1b[0m\x1b[93mb\x1b[0m\x1b[93mg'
            '\x1b[0m\x1b[93md\x1b[0m \x1b[93ma\x1b[0m\x1b[93mi\x1b[0m'
            '\x1b[93mu\x1b[0m\x1b[93me\x1b[0m\x1b[93mo\x1b[0m\n')


class TestTransliterationTable(TestCase):

    """Test transliteration table."""

    net = False

    def test_latin_digits(self):
        """Test that non latin digits are in transliteration table."""
        for lang, digits in NON_LATIN_DIGITS.items():
            with self.subTest(lang=lang):
                for char in digits:
                    self.assertIn(char, _trans,
                                  '{!r} not in transliteration table'
                                  .format(char))

    def test_transliteration_table(self):
        """Test transliteration table consistency."""
        for k, v in _trans.items():
            with self.subTest():
                self.assertNotEqual(k, v)


# TODO: add tests for background colors.
class FakeUITest(TestCase):

    """Test case to allow doing uncolorized general UI tests."""

    net = False

    expected = 'Hello world you! ***'
    expect_color = False
    ui_class = terminal_interface_base.UI

    def setUp(self):
        """Create dummy instances for the test and patch encounter_color."""
        super().setUp()
        self.ui_obj = self.ui_class()
        # Write to sys.stdout stream, which we'll redirect to the stream below
        self.redirect = io.StringIO()
        self._orig_encounter_color = self.ui_obj.encounter_color
        self.ui_obj.encounter_color = self._encounter_color
        self._index = 0

    def tearDown(self):
        """Unpatch the encounter_color method."""
        self.ui_obj.encounter_color = self._orig_encounter_color
        super().tearDown()
        self.assertEqual(self._index,
                         len(self._colors) if self.expect_color else 0)

    def _encounter_color(self, color, target_stream):
        """Patched encounter_color method."""
        raise AssertionError(
            'This method should not be invoked')  # pragma: no cover

    def test_no_color(self):
        """Test a string without any colors."""
        self._colors = ()
        with redirect_stdout(self.redirect) as f:
            self.ui_obj._print('Hello world you!', self.ui_obj.stdout)
        self.assertEqual(f.getvalue(), 'Hello world you!')

    def test_one_color(self):
        """Test a string using one color."""
        self._colors = (('red', 6), ('default', 10))
        with redirect_stdout(self.redirect) as f:
            self.ui_obj._print('Hello <<red>>world you!', self.ui_obj.stdout)
        self.assertEqual(f.getvalue(), self.expected)

    def test_flat_color(self):
        """Test using colors with defaulting in between."""
        self._colors = (('red', 6), ('default', 6), ('yellow', 3),
                        ('default', 1))
        with redirect_stdout(self.redirect) as f:
            self.ui_obj._print(
                'Hello <<red>>world <<default>>you<<yellow>>!',
                self.ui_obj.stdout)
        self.assertEqual(f.getvalue(), self.expected)

    def test_stack_with_pop_color(self):
        """Test using stacked colors and just popping the latest color."""
        self._colors = (('red', 6), ('yellow', 6), ('red', 3), ('default', 1))
        with redirect_stdout(self.redirect) as f:
            self.ui_obj._print(
                'Hello <<red>>world <<yellow>>you<<previous>>!',
                self.ui_obj.stdout)
        self.assertEqual(f.getvalue(), self.expected)

    def test_stack_implicit_color(self):
        """Test using stacked colors without popping any."""
        self._colors = (('red', 6), ('yellow', 6), ('default', 4))
        with redirect_stdout(self.redirect) as f:
            self.ui_obj._print('Hello <<red>>world <<yellow>>you!',
                               self.ui_obj.stdout)
        self.assertEqual(f.getvalue(), self.expected)

    def test_one_color_newline(self):
        """Test with trailing new line and one color."""
        self._colors = (('red', 6), ('default', 11))
        with redirect_stdout(self.redirect) as f:
            self.ui_obj._print('Hello <<red>>world you!\n',
                               self.ui_obj.stdout)
        self.assertEqual(f.getvalue(), self.expected + '\n')


class FakeUIColorizedTestBase(TestCase):

    """Base class for test cases requiring that colorized output is active."""

    net = False

    expect_color = True
    expected = 'Hello world you!'

    def setUp(self):
        """Force colorized_output to True."""
        super().setUp()
        self._old_config = pywikibot.config.colorized_output
        pywikibot.config.colorized_output = True

    def tearDown(self):
        """Undo colorized_output configuration."""
        pywikibot.config.colorized_output = self._old_config
        super().tearDown()

    def _encounter_color(self, color, target_stream):
        """Verify that the written data, color and stream are correct."""
        self.assertIs(target_stream, self.ui_obj.stdout)
        expected_color = self._colors[self._index][0]
        self._index += 1
        self.assertEqual(color, expected_color)
        self.assertLength(self.redirect.getvalue(),
                          sum(e[1] for e in self._colors[:self._index]))


class FakeUnixTest(FakeUIColorizedTestBase, FakeUITest):

    """Test case to allow doing colorized Unix tests in any environment."""

    ui_class = terminal_interface_unix.UnixUI


class FakeWin32Test(FakeUIColorizedTestBase, FakeUITest):

    """
    Test case to allow doing colorized Win32 tests in any environment.

    This only patches the ctypes import in the terminal_interface_win32
    module. As the Win32CtypesUI is using the std-streams from another
    import these will be unpatched.
    """

    ui_class = terminal_interface_win32.Win32UI

    def setUp(self):
        """Patch the ctypes import and initialize a stream and UI instance."""
        super().setUp()
        self.ui_obj.stdout.isatty = lambda: self.expect_color


class FakeWin32UncolorizedTest(FakeWin32Test):

    """Test case to allow doing uncolorized Win32 tests in any environment."""

    expected = 'Hello world you! ***'
    expect_color = False


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
