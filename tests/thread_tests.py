"""Tests for threading tools."""
#
# (C) Pywikibot team, 2014-2021
#
# Distributed under the terms of the MIT license.
#
import unittest
from collections import Counter
from contextlib import suppress

from pywikibot.tools import ThreadedGenerator, intersect_generators
from tests.aspects import TestCase


class BasicThreadedGeneratorTestCase(TestCase):

    """ThreadedGenerator test cases."""

    net = False

    def test_run_from_iterable(self):
        """Test thread running with iterable target."""
        iterable = 'abcd'
        thd_gen = ThreadedGenerator(target=iterable)
        thd_gen.start()
        self.assertEqual(list(thd_gen), list(iterable))

    @staticmethod
    def gen_func():
        """Helper method for generator test."""
        iterable = 'abcd'
        yield from iterable

    def test_run_from_gen_function(self):
        """Test thread running with generator as target."""
        iterable = 'abcd'
        thd_gen = ThreadedGenerator(target=self.gen_func)
        thd_gen.start()
        self.assertEqual(list(thd_gen), list(iterable))


class GeneratorIntersectTestCase(TestCase):

    """Base class for intersect_generators test cases."""

    def assertEqualItertools(self, gens):
        """Assert intersect_generators result is same as set intersection."""
        # If they are a generator, we need to convert to a list
        # first otherwise the generator is empty the second time.
        datasets = [list(gen) for gen in gens]
        set_result = set(datasets[0]).intersection(*datasets[1:])
        result = list(intersect_generators(datasets))

        self.assertCountEqual(set(result), result)
        self.assertCountEqual(result, set_result)

    def assertEqualItertoolsWithDuplicates(self, gens):
        """Assert intersect_generators result equals Counter intersection."""
        # If they are a generator, we need to convert to a list
        # first otherwise the generator is empty the second time.
        datasets = [list(gen) for gen in gens]
        counter_result = Counter(datasets[0])
        for dataset in datasets[1:]:
            counter_result = counter_result & Counter(dataset)
        counter_result = list(counter_result.elements())
        result = list(intersect_generators(datasets, allow_duplicates=True))
        self.assertCountEqual(counter_result, result)


class BasicGeneratorIntersectTestCase(GeneratorIntersectTestCase):

    """Disconnected intersect_generators test cases."""

    net = False

    def test_intersect_basic(self):
        """Test basic intersect without duplicates."""
        self.assertEqualItertools(['abc', 'db', 'ba'])

    def test_intersect_with_dups(self):
        """Test basic intersect with duplicates."""
        self.assertEqualItertools(['aabc', 'dddb', 'baa'])

    def test_intersect_with_accepted_dups(self):
        """Test intersect with duplicates accepted."""
        self.assertEqualItertoolsWithDuplicates(['abc', 'db', 'ba'])
        self.assertEqualItertoolsWithDuplicates(['aabc', 'dddb', 'baa'])
        self.assertEqualItertoolsWithDuplicates(['abb', 'bb'])
        self.assertEqualItertoolsWithDuplicates(['bb', 'abb'])
        self.assertEqualItertoolsWithDuplicates(['abbcd', 'abcba'])
        self.assertEqualItertoolsWithDuplicates(['abcba', 'abbcd'])


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
