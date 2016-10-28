# -*- coding: utf-8 -*-
"""Test plural module."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

from pywikibot import plural

from tests.aspects import (
    unittest, TestCase, MetaTestCaseClass,
)
from tests.utils import add_metaclass


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
                                    msg='Plural for {0} created an index {1} '
                                        '(greater than {2})'.format(num, index,
                                                                    rule['nplurals']))
                    num_plurals.add(index)
                self.assertCountEqual(num_plurals, list(range(rule['nplurals'])))

            # Don't already fail on creation
            if callable(rule.get('plural')):
                return test_callable_rule
            else:
                return test_static_rule

        for lang, rule in plural.plural_rules.items():
            cls.add_method(dct, 'test_{0}'.format(lang), create_test(rule),
                           doc_suffix='for "{0}"'.format(lang))
        return super(MetaPluralRulesTest, cls).__new__(cls, name, bases, dct)


@add_metaclass
class TestPluralRules(TestCase):

    """Test the consistency of the plural rules."""

    __metaclass__ = MetaPluralRulesTest

    net = False
    # for callable plural rules it'll test up until this number, this number
    # must cause to create all plurals in all dynamic languages
    max_num = 1000


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
