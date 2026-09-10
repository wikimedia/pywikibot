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
    BrokenExecutor,
    Executor,
    Future,
    ProcessPoolExecutor,
    ThreadPoolExecutor,
)
from contextlib import suppress
from threading import Condition, Event, Thread
from unittest.mock import patch

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

    def test_producer_failure(self) -> None:
        """Test producer failures reach consumers after queued results."""
        values = (1, 2, 3)
        failure = ValueError('producer failed')

        def generate():
            yield from values
            raise failure

        self._check_failure(generate, values, failure)

    def test_target_failure(self) -> None:
        """Test failure while creating the iterable reaches the consumer."""
        failure = RuntimeError('target failed')

        def target():
            raise failure

        self._check_failure(target, (), failure)

    def _check_failure(self, target, values, failure) -> None:
        """Consume with a timeout so a broken producer cannot hang tests."""
        generator = ThreadedGenerator(target=target, qsize=1)
        received = []
        errors = []

        def consume() -> None:
            try:
                received.extend(generator)
            except type(failure) as e:
                errors.append(e)

        consumer = Thread(target=consume, daemon=True)
        consumer.start()
        try:
            consumer.join(3)
            self.assertFalse(consumer.is_alive())
            self.assertEqual(received, list(values))
            self.assertEqual(errors, [failure])
            self.assertIs(errors[0], failure)
        finally:
            generator.stop()
            consumer.join(3)
            generator.join(3)
        self.assertFalse(generator.is_alive())


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

    def test_submit_after_shutdown(self) -> None:
        """Test failed submissions after shutdown release their capacity."""
        for executor in (ThreadPoolExecutor, ProcessPoolExecutor):
            with self.subTest(executor=executor):
                pool = BoundedPoolExecutor(executor, max_bound=1,
                                           max_workers=1)
                pool.shutdown()
                with self.assertRaisesRegex(
                        RuntimeError,
                        'cannot schedule new futures after shutdown'):
                    pool.submit(pow, 2, 3)
                self.assertTrue(
                    pool._bound_semaphore.acquire(blocking=False)
                )
                pool._bound_semaphore.release()

    def test_submit_failure(self) -> None:
        """Test submission errors propagate and leave capacity reusable."""
        for error in (BrokenExecutor, RuntimeError, KeyboardInterrupt):
            with self.subTest(error=error), BoundedPoolExecutor(
                ThreadPoolExecutor, max_bound=1, max_workers=1
            ) as pool:
                failure = error('submission failed')
                with patch.object(ThreadPoolExecutor, 'submit',
                                  side_effect=failure):
                    with self.assertRaisesRegex(
                            error, 'submission failed') as caught:
                        pool.submit(pow, 2, 3)
                self.assertIs(caught.exception, failure)
                self.assertTrue(
                    pool._bound_semaphore.acquire(blocking=False)
                )
                pool._bound_semaphore.release()
                self.assertEqual(pool.submit(pow, 2, 3).result(timeout=5), 8)

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
