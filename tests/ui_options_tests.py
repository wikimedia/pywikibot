# -*- coding: utf-8 -*-
"""Bot tests for input_choice options."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#
from pywikibot import bot, bot_choice

from tests.aspects import unittest, TestCase

message = bot.Option.formatted


class TestChoiceOptions(TestCase):

    """Test cases for input_choice Option."""

    TEST_RE = '\'int\' object has no attribute \'lower\''
    SEQ_EMPTY_RE = 'The sequence is empty.'
    net = False

    def test_formatted(self):
        """Test static method Option.formatted."""
        self.assertEqual(message('Question:', [], None), 'Question: ()')

    def test_output(self):
        """Test OutputOption."""
        option = bot_choice.OutputOption()
        with self.assertRaisesRegex(NotImplementedError, ''):
            message('?', [option], None)

    def test_standard(self):
        """Test StandardOption."""
        option = bot.StandardOption('Test', 'T')
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
        option = bot.NestedOption('Next', 'x', 'Nested:', [standard])
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
        self.assertEqual(option.format('2'), 'r<number> [1-5]')
        self.assertEqual(option.format('r2'), 'r<number> [1-[2]-5]')
        self.assertEqual(option.format(default='r2'), 'r<number> [1-[2]-5]')
        self.assertEqual(option.format(), 'r<number> [1-5]')
        self.assertEqual(message('?', [option], None), '? (r<number> [1-5])')
        self.assertEqual(message('?', [option], 'r3'), '? (r<number> [1-[3]-5])')
        self.assertRaisesRegex(AttributeError, self.TEST_RE, option.test, 1)
        self.assertFalse(option.test('0'))
        self.assertFalse(option.test('r0'))
        self.assertFalse(option.test('r6'))
        self.assertIsNone(option.handled('r6'))
        for i in range(1, 6):
            self.assertTrue(option.test('r%d' % i))
            self.assertEqual(option.handled('r%d' % i), option)
            self.assertEqual(option.result('r%d' % i), ('r', i))

    def test_List(self):
        """Test ListOption."""
        self.assertRaisesRegex(ValueError, self.SEQ_EMPTY_RE, bot.ListOption, [])
        options = ['foo', 'bar']
        option = bot.ListOption(options)
        self.assertEqual(message('?', [option], None), '? (<number> [1-2])')
        self.assertEqual(message('?', [option]), '? (<number> [1-2])')
        self.assertEqual(message('?', [option], '2'), '? (<number> [1-[2]])')
        self.assertEqual(message('?', [option], default='2'),
                         '? (<number> [1-[2]])')
        options.pop()
        self.assertEqual(message('?', [option], None), '? (<number> [1])')
        self.assertEqual(message('?', [option], '1'), '? (<number> [[1]])')
        options.pop()
        self.assertRaisesRegex(ValueError, self.SEQ_EMPTY_RE, option.format, None)
        self.assertRaisesRegex(ValueError, self.SEQ_EMPTY_RE, option.format)
        self.assertFalse(option.test('0'))
        options += ['baz', 'quux', 'norf']
        self.assertEqual(message('?', [option], None), '? (<number> [1-3])')
        for prefix in ('', 'r', 'st'):
            option = bot.ListOption(options, prefix=prefix)
            self.assertEqual(message('?', [option]),
                             '? (%s<number> [1-3])' % prefix)
            for i, elem in enumerate(options, 1):
                self.assertTrue(option.test('%s%d' % (prefix, i)))
                self.assertIs(option.handled('%s%d' % (prefix, i)), option)
                self.assertEqual(option.result('%s%d' % (prefix, i)),
                                 (prefix, elem))
            self.assertFalse(option.test('%s%d' % (prefix, len(options) + 1)))
            self.assertIsNone(option.handled('%s%d'
                                             % (prefix, len(options) + 1)))


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
