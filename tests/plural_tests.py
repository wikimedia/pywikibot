#!/usr/bin/env python3
"""Test plural module."""
#
# (C) Pywikibot team, 2015-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

from pywikibot import plural
from tests.aspects import MetaTestCaseClass, TestCase


class MetaPluralRulesTest(MetaTestCaseClass):

    """Metaclass to test each plural rule in separate tests."""

    def __new__(cls, name, bases, dct):
        """Create a new test case which tests all plural rules."""
        def create_test(rule):
            def test_static_rule(self):
                """Test a rule which is just one integer."""
                self.assertEqual(rule['nplurals'], 1)
                self.assertEqual(rule['plural'], 0)

            def test_callable_rule(self):
                """Test a rule which is callable."""
                # in theory a static rule could be also callable
                self.assertGreater(rule['nplurals'], 0)
                num_plurals = set()
                for num in range(self.max_num + 1):
                    index = rule['plural'](num)
                    self.assertLess(index, rule['nplurals'],
                                    msg='Plural for {} created an index {} '
                                        '(greater than {})'
                                        .format(num, index, rule['nplurals']))
                    num_plurals.add(index)
                self.assertCountEqual(num_plurals,
                                      list(range(rule['nplurals'])))

            # Don't already fail on creation
            if callable(rule.get('plural')):
                return test_callable_rule
            return test_static_rule

        for lang, rule in plural.plural_rules.items():
            cls.add_method(dct, 'test_{}'.format(lang.replace('-', '_')),
                           create_test(rule),
                           doc_suffix=f'for "{lang}"')
        return super().__new__(cls, name, bases, dct)


class TestPluralRules(TestCase, metaclass=MetaPluralRulesTest):

    """Test the consistency of the plural rules."""

    net = False
    # for callable plural rules it'll test up until this number, this number
    # must cause to create all plurals in all dynamic languages
    max_num = 1000


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
