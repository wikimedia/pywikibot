# -*- coding: utf-8  -*-
"""Tests for threading tools."""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'


from tests.aspects import TestCase
from pywikibot.tools import ThreadedGenerator


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
