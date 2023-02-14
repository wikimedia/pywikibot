#!/usr/bin/env python3
"""Bot tests for input_choice options."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

from pywikibot import bot, bot_choice
from pywikibot.bot_choice import ChoiceException, QuitKeyboardInterrupt
from tests.aspects import TestCase


message = bot.Option.formatted


class TestChoiceOptions(TestCase):

    """Test cases for input_choice Option."""

    TEST_RE = "'int' object has no attribute 'lower'"
    SEQ_EMPTY_RE = 'The sequence is empty.'
    net = False

    def test_formatted(self):
        """Test static method Option.formatted."""
        self.assertEqual(message('Question:', [], None), 'Question: ()')

    def test_output(self):
        """Test OutputOption."""
        option = bot_choice.OutputOption()
        self.assertFalse(option.stop)
        with self.assertRaisesRegex(NotImplementedError, ''):
            message('?', [option], None)

    def test_proxy_output(self):
        """Test OutputProxyOption."""
        option = bot_choice.OutputProxyOption('Test', 'T', None)
        self.assertFalse(option.stop)
        self.assertEqual(option.format(), '[t]est')

    def test_standard(self):
        """Test StandardOption."""
        option = bot.StandardOption('Test', 'T')
        self.assertTrue(option.stop)
        self.assertEqual(option.option, 'Test')
        self.assertEqual(option.shortcut, 't')
        self.assertEqual(option.shortcut, option.result(None))
        self.assertEqual(option.format(None), '[t]est')
        self.assertEqual(option.format(), '[t]est')
        self.assertEqual(option.format(default=None), '[t]est')
        self.assertEqual(option.format('t'), '[T]est')
        self.assertEqual(option.format(default='t'), '[T]est')
        self.assertTrue(option.test('Test'))
        self.assertTrue(option.test('t'))
        self.assertTrue(option.test('T'))
        self.assertFalse(option.test('?'))
        self.assertIs(option.handled('T'), option)
        self.assertIsNone(option.handled('?'))
        self.assertEqual(message('?', [option], None), '? ([t]est)')
        self.assertEqual(message('?', [option]), '? ([t]est)')
        self.assertEqual(message('?', [option], 't'), '? ([T]est)')
        self.assertEqual(message('?', [option], default='t'), '? ([T]est)')

    def test_Nested(self):
        """Test NestedOption."""
        standard = bot.StandardOption('Test', 'T')
        self.assertTrue(standard.stop)
        option = bot.NestedOption('Next', 'x', 'Nested:', [standard])
        self.assertFalse(option.stop)
        self.assertEqual(option.format('x'), 'Ne[X]t')
        self.assertEqual(option.format(), 'Ne[x]t')
        self.assertEqual(option._output, 'Nested: ([t]est)')
        self.assertEqual(message('?', [option], 't'), '? (Ne[x]t)')
        self.assertIs(standard.handled('t'), standard)
        self.assertIs(option.handled('x'), option)
        self.assertIs(option.handled('t'), standard)

    def test_Integer(self):
        """Test IntegerOption."""
        option = bot.IntegerOption(maximum=5, prefix='r')
        self.assertTrue(option.stop)
        self.assertEqual(option.format('2'), 'r<number> [1-5]')
        self.assertEqual(option.format('r2'), 'r<number> [1-[2]-5]')
        self.assertEqual(option.format(default='r2'), 'r<number> [1-[2]-5]')
        self.assertEqual(option.format(), 'r<number> [1-5]')
        self.assertEqual(message('?', [option], None), '? (r<number> [1-5])')
        self.assertEqual(message('?', [option], 'r3'),
                         '? (r<number> [1-[3]-5])')
        with self.assertRaisesRegex(AttributeError, self.TEST_RE):
            option.test(1)
        self.assertFalse(option.test('0'))
        self.assertFalse(option.test('r0'))
        self.assertFalse(option.test('r6'))
        self.assertIsNone(option.handled('r6'))
        for i in range(1, 6):
            self.assertTrue(option.test(f'r{i}'))
            self.assertEqual(option.handled(f'r{i}'), option)
            self.assertEqual(option.result(f'r{i}'), ('r', i))

    def test_List(self):
        """Test ListOption."""
        with self.assertRaisesRegex(
                ValueError,
                self.SEQ_EMPTY_RE):
            bot.ListOption([])
        options = ['foo', 'bar']
        option = bot.ListOption(options)
        self.assertTrue(option.stop)
        self.assertEqual(message('?', [option], None), '? (<number> [1-2])')
        self.assertEqual(message('?', [option]), '? (<number> [1-2])')
        self.assertEqual(message('?', [option], '2'), '? (<number> [1-[2]])')
        self.assertEqual(message('?', [option], default='2'),
                         '? (<number> [1-[2]])')
        options.pop()
        self.assertEqual(message('?', [option], None), '? (<number> [1])')
        self.assertEqual(message('?', [option], '1'), '? (<number> [[1]])')
        options.pop()
        with self.assertRaisesRegex(
                ValueError,
                self.SEQ_EMPTY_RE):
            option.format(None)
        with self.assertRaisesRegex(
                ValueError,
                self.SEQ_EMPTY_RE):
            option.format()
        self.assertFalse(option.test('0'))
        options += ['baz', 'quux', 'norf']
        self.assertEqual(message('?', [option], None), '? (<number> [1-3])')
        for prefix in ('', 'r', 'st'):
            option = bot.ListOption(options, prefix=prefix)
            self.assertEqual(message('?', [option]),
                             f'? ({prefix}<number> [1-3])')
            for i, elem in enumerate(options, 1):
                self.assertTrue(option.test(f'{prefix}{i}'))
                self.assertIs(option.handled('{}{}'
                                             .format(prefix, i)), option)
                self.assertEqual(option.result(f'{prefix}{i}'),
                                 (prefix, elem))
            self.assertFalse(option.test('{}{}'
                                         .format(prefix, len(options) + 1)))
            self.assertIsNone(option.handled('{}{}'.format(
                prefix, len(options) + 1)))

    def test_showing_list(self):
        """Test ShowingListOption."""
        with self.assertRaisesRegex(
                ValueError,
                self.SEQ_EMPTY_RE):
            bot.ShowingListOption([])
        options = ['foo', 'bar']
        option = bot.ShowingListOption(options)
        self.assertEqual(message('?', [option]), '? (<number> [1-2])')

    def test_multiple_choice_list(self):
        """Test MultipleChoiceList."""
        with self.assertRaisesRegex(
                ValueError,
                self.SEQ_EMPTY_RE):
            bot.MultipleChoiceList([])
        options = ['foo', 'bar']
        option = bot.MultipleChoiceList(options)
        self.assertTrue(option.stop)
        self.assertEqual(message('?', [option]), '? (<number> [1-2])')
        self.assertFalse(option.test(''))
        self.assertFalse(option.test('*'))
        self.assertFalse(option.test('0'))
        self.assertFalse(option.test('0,1'))
        self.assertTrue(option.test('1'))
        self.assertFalse(option.test('1,'))
        self.assertTrue(option.test('1,2'))
        self.assertTrue(option.test('2'))
        self.assertFalse(option.test('2,3'))
        self.assertFalse(option.test('3'))
        self.assertEqual(option.result('1'), ('', [options[0]]))
        self.assertEqual(option.result('1,2'), ('', [options[0], options[1]]))

    def test_showing_multiple_choice_list(self):
        """Test ShowingMultipleChoiceList."""
        with self.assertRaisesRegex(
                ValueError,
                self.SEQ_EMPTY_RE):
            bot.ShowingMultipleChoiceList([])
        options = ['foo', 'bar']
        option = bot.ShowingMultipleChoiceList(options)
        self.assertEqual(message('?', [option]), '? (<number> [1-2])')
        self.assertFalse(option.test('*'))
        self.assertTrue(option.test('1'))
        self.assertTrue(option.test('1,2'))
        self.assertTrue(option.test('2'))
        self.assertFalse(option.test('2,3'))
        self.assertEqual(option.result('2'), ('', [options[1]]))
        self.assertEqual(option.result('1,2'), ('', [options[0], options[1]]))

    def test_choice_excepton(self):
        """Test ChoiceException."""
        option = ChoiceException('Test', 'T')
        self.assertTrue(option.stop)
        self.assertEqual(option.result('*'), option)
        with self.assertRaises(ChoiceException):
            raise ChoiceException('Test', 'T')

    def test_quit_keyboard_interrupt(self):
        """Test QuitKeyboardInterrupt."""
        option = QuitKeyboardInterrupt()
        self.assertTrue(option.stop)
        self.assertEqual(option.result('*'), option)
        self.assertEqual(option.option, 'quit')
        self.assertEqual(option.shortcut, 'q')
        with self.assertRaises(QuitKeyboardInterrupt):
            raise QuitKeyboardInterrupt()


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
