# -*- coding: utf-8  -*-
"""Tests for threading tools."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'

from tests.aspects import unittest, TestCase
from pywikibot.tools import ThreadedGenerator, intersect_generators


class BasicThreadedGeneratorTestCase(TestCase):

    """ThreadedGenerator test cases."""

    net = False

    def test_run_from_iterable(self):
        iterable = 'abcd'
        thd_gen = ThreadedGenerator(target=iterable)
        thd_gen.start()
        self.assertEqual(list(thd_gen), list(iterable))

    def gen_func(self):
        iterable = 'abcd'
        for i in iterable:
            yield i

    def test_run_from_gen_function(self):
        iterable = 'abcd'
        thd_gen = ThreadedGenerator(target=self.gen_func)
        thd_gen.start()
        self.assertEqual(list(thd_gen), list(iterable))


class GeneratorIntersectTestCase(TestCase):

    """Base class for intersect_generators test cases."""

    def assertEqualItertools(self, gens):
        # If they are a generator, we need to convert to a list
        # first otherwise the generator is empty the second time.
        datasets = [list(gen) for gen in gens]

        set_result = set(datasets[0]).intersection(*datasets[1:])

        result = list(intersect_generators(datasets))

        self.assertCountEqual(set(result), result)

        self.assertCountEqual(result, set_result)


class BasicGeneratorIntersectTestCase(GeneratorIntersectTestCase):

    """Disconnected intersect_generators test cases."""

    net = False

    def test_intersect_basic(self):
        self.assertEqualItertools(['abc', 'db', 'ba'])

    def test_intersect_with_dups(self):
        self.assertEqualItertools(['aabc', 'dddb', 'baa'])


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
