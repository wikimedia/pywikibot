#!/usr/bin/env python3
#
# (C) Pywikibot team, 2014-2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for threading tools."""
from __future__ import annotations

import unittest
from concurrent.futures import (
    Executor,
    Future,
    ProcessPoolExecutor,
    ThreadPoolExecutor,
)
from contextlib import suppress
from threading import Condition, Event, Thread

from pywikibot.tools import PYTHON_VERSION
from pywikibot.tools.threading import BoundedPoolExecutor, ThreadedGenerator
from tests.aspects import TestCase


class BasicThreadedGeneratorTestCase(TestCase):

    """ThreadedGenerator test cases."""

    net = False

    def test_run_from_iterable(self) -> None:
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

    def test_run_from_gen_function(self) -> None:
        """Test thread running with generator as target."""
        iterable = 'abcd'
        thd_gen = ThreadedGenerator(target=self.gen_func)
        thd_gen.start()
        self.assertEqual(list(thd_gen), list(iterable))


class BoundedThreadPoolTests(TestCase):

    """BoundedThreadPool test cases."""

    net = False

    def test_strings(self) -> None:
        """Test string and repr methods for executor strings."""
        executors = ['ThreadPoolExecutor', 'ProcessPoolExecutor']
        if PYTHON_VERSION >= (3, 14):
            executors.append('InterpreterPoolExecutor')

        for executor in executors:
            with self.subTest(executor=executor):
                pool = BoundedPoolExecutor(executor)
                self.assertEqual(str(pool), f'Bounded{executor}()')
                self.assertEqual(repr(pool),
                                 f'BoundedPoolExecutor({executor!r})')
                self.assertEqual(pool._bound_semaphore._initial_value,
                                 pool._max_workers)

    def test_class(self) -> None:
        """Test string and repr methods for an executor class."""
        executors = [ThreadPoolExecutor, ProcessPoolExecutor]
        if PYTHON_VERSION >= (3, 14):
            from concurrent.futures import InterpreterPoolExecutor
            executors.append(InterpreterPoolExecutor)

        for executor in executors:
            with self.subTest(executor=executor):
                pool = BoundedPoolExecutor(executor)
                self.assertEqual(str(pool), f'Bounded{executor.__name__}()')
                self.assertEqual(repr(pool),
                                 f'BoundedPoolExecutor({executor.__name__!r})')
                self.assertEqual(pool._bound_semaphore._initial_value,
                                 pool._max_workers)

    def _check_bound(self, bound: int) -> None:
        """Check executor operation for the given bound."""
        release = Event()
        submitted = Condition()
        futures = []

        def wait_for_release() -> None:
            release.wait()

        with BoundedPoolExecutor('ThreadPoolExecutor',
                                 max_bound=bound,
                                 max_workers=5) as pool:
            def submit_tasks() -> None:
                for _ in range(10):
                    future = pool.submit(wait_for_release)
                    with submitted:
                        futures.append(future)
                        submitted.notify_all()

            producer = Thread(target=submit_tasks)
            producer.start()
            try:
                with submitted:
                    reached_bound = submitted.wait_for(
                        lambda: len(futures) >= bound,
                        timeout=5,
                    )
                self.assertTrue(reached_bound)
                self.assertLength(futures, bound)
                self.assertFalse(
                    pool._bound_semaphore.acquire(blocking=False)
                )
            finally:
                release.set()

            producer.join(5)
            self.assertFalse(producer.is_alive())

        self.assertLength(futures, 10)
        for future in futures:
            self.assertIsInstance(future, Future)
            self.assertTrue(future.done())
            self.assertIsNone(future.result())

    def test_run(self) -> None:
        """Test examples for Executor during run."""
        for bound in (2, 5, 7):
            with self.subTest(bound=bound):
                self._check_bound(bound)

    def test_exceptions(self) -> None:
        """Test exceptions when creating a bounded executor."""
        with self.assertRaisesRegex(TypeError,
                                    r'issubclass\(\) arg 1 must be a class'):
            BoundedPoolExecutor(PYTHON_VERSION)
        with self.assertRaisesRegex(TypeError,
                                    'expected a real subclass of '
                                    r"'concurrent\.futures\.Executor'"):
            BoundedPoolExecutor(TestCase)
        with self.assertRaisesRegex(TypeError,
                                    'expected a real subclass of '
                                    r"'concurrent\.futures\.Executor'"):
            BoundedPoolExecutor(Future)
        with self.assertRaisesRegex(TypeError,
                                    'expected a real subclass of '
                                    r"'concurrent\.futures\.Executor'"):
            BoundedPoolExecutor(Executor)
        with self.assertRaisesRegex(
            TypeError,
            r'(duplicate base class |Cannot create a consistent method[\s\S]*)'
            "'?BoundedPoolExecutor'?"
        ):
            BoundedPoolExecutor(BoundedPoolExecutor)
        with self.assertRaisesRegex(ValueError, "Minimum 'max_bound' is 1"):
            BoundedPoolExecutor('ThreadPoolExecutor', 0)
        with self.assertRaisesRegex(ValueError, "Minimum 'max_bound' is 1"):
            BoundedPoolExecutor('ThreadPoolExecutor', max_bound=0)


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
