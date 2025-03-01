"""Classes which can be used for threading."""
#
# (C) Pywikibot team, 2008-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import concurrent.futures as futures
import dataclasses
import importlib
import queue
import re
import threading
import time
from typing import Any

import pywikibot  # T306760
from pywikibot.tools import SPHINX_RUNNING


__all__ = (
    'BoundedPoolExecutor',
    'RLock',
    'ThreadedGenerator',
    'ThreadList',
)


class RLock:

    """Context manager which implements extended reentrant lock objects.

    This RLock is implicit derived from threading.RLock but provides a
    locked() method like in threading.Lock and a count attribute which
    gives the active recursion level of locks.

    Usage:

    >>> lock = RLock()
    >>> lock.acquire()
    True
    >>> with lock: print(lock.count)  # nested lock
    2
    >>> lock.locked()
    True
    >>> lock.release()
    >>> lock.locked()
    False

    .. versionadded:: 6.2
    """

    def __init__(self, *args, **kwargs) -> None:
        """Initializer."""
        self._lock = threading.RLock(*args, **kwargs)
        self._block = threading.Lock()

    def __enter__(self):
        """Acquire lock and call atenter."""
        return self._lock.__enter__()

    def __exit__(self, *exc):
        """Call atexit and release lock."""
        return self._lock.__exit__(*exc)

    def __getattr__(self, name):
        """Delegate attributes and methods to self._lock."""
        return getattr(self._lock, name)

    def __repr__(self) -> str:
        """Representation of tools.RLock instance."""
        return repr(self._lock).replace(
            '_thread.RLock',
            f'{self.__module__}.{type(self).__name__}'
        )

    @property
    def count(self):
        """Return number of acquired locks."""
        with self._block:
            counter = re.search(r'count=(\d+) ', repr(self))
            return int(counter[1])

    def locked(self):
        """Return true if the lock is acquired."""
        with self._block:
            status = repr(self).split(maxsplit=1)[0][1:]
            assert status in ('locked', 'unlocked')
            return status == 'locked'


class ThreadedGenerator(threading.Thread):

    """Look-ahead generator class.

    Runs a generator in a separate thread and queues the results; can
    be called like a regular generator.

    Subclasses should override self.generator, *not* self.run

    Important: the generator thread will stop itself if the generator's
    internal queue is exhausted; but, if the calling program does not use
    all the generated values, it must call the generator's stop() method to
    stop the background thread. Example usage:

    >>> gen = ThreadedGenerator(target=range, args=(20,))
    >>> try:
    ...     data = list(gen)
    ... finally:
    ...     gen.stop()
    >>> data
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19]

    .. versionadded:: 3.0
    """

    def __init__(self, group=None, target=None, name: str = 'GeneratorThread',
                 args=(), kwargs=None, qsize: int = 65536) -> None:
        """Initializer. Takes same keyword arguments as threading.Thread.

        target must be a generator function (or other callable that returns
        an iterable object).

        :param qsize: The size of the lookahead queue. The larger the qsize,
            the more values will be computed in advance of use (which can eat
            up memory and processor time).
        """
        if kwargs is None:
            kwargs = {}
        if target:
            self.generator = target
        if not hasattr(self, 'generator'):
            raise RuntimeError('No generator for ThreadedGenerator to run.')
        self.args, self.kwargs = args, kwargs
        super().__init__(group=group, name=name)
        self.queue = queue.Queue(qsize)
        self.finished = threading.Event()

    def __iter__(self):
        """Iterate results from the queue."""
        if not self.is_alive() and not self.finished.is_set():
            self.start()
        # if there is an item in the queue, yield it, otherwise wait
        while not self.finished.is_set():
            try:
                yield self.queue.get(True, 0.25)
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                self.stop()

    def stop(self) -> None:
        """Stop the background thread."""
        self.finished.set()

    def run(self) -> None:
        """Run the generator and store the results on the queue."""
        iterable = any(hasattr(self.generator, key)
                       for key in ('__iter__', '__getitem__'))
        if iterable and not self.args and not self.kwargs:
            self.__gen = self.generator
        else:
            self.__gen = self.generator(*self.args, **self.kwargs)
        for result in self.__gen:
            while True:
                if self.finished.is_set():
                    return
                try:
                    self.queue.put_nowait(result)
                except queue.Full:
                    time.sleep(0.25)
                    continue
                break
        # wait for queue to be emptied, then kill the thread
        while not self.finished.is_set() and not self.queue.empty():
            time.sleep(0.25)
        self.stop()


@dataclasses.dataclass(repr=False, eq=False)
class ThreadList(list):

    """A simple threadpool class to limit the number of simultaneous threads.

    Any threading.Thread object can be added to the pool using the
    :meth:`append` method. If the maximum number of simultaneous threads
    has not been reached, the Thread object will be started immediately;
    if not, the append() call will block until the thread is able to
    start.

    Example:

    .. code-block:: python

       pool = ThreadList(limit=10)
       def work():
           time.sleep(1)

       for x in range(20):
           pool.append(threading.Thread(target=work))

    .. versionchanged:: 10.0
       the unintentional and undocumented *args* parameter was removed.

    .. seealso:: :class:`BoundedPoolExecutor`

    :param limit: the number of simultaneous threads
    :param wait_time: how long to wait if active threads exceeds limit
    """

    limit: int = 128  #: :meta private:
    wait_time: float = 2.0  #: :meta private:

    def active_count(self) -> int:
        """Return the number of alive threads and delete all non-alive ones."""
        cnt = 0
        for item in self[:]:
            if item.is_alive():
                cnt += 1
            else:
                self.remove(item)
        return cnt

    def append(self, thd: threading.Thread) -> None:
        """Add a thread to the pool and start it.

        :param thd: the Thread to be appended to the ThreadList.
        """
        if not isinstance(thd, threading.Thread):
            raise TypeError(f"Cannot append '{type(thd)}' to ThreadList")

        while self.active_count() >= self.limit:
            time.sleep(self.wait_time)

        super().append(thd)
        thd.start()
        pywikibot.logging.debug(f"thread {len(self)} ('{type(thd)}') started")


class BoundedPoolExecutor(futures.Executor):

    """A bounded Executor which limits prefetched Futures.

    BoundedThreadPoolExecutor behaves like other executors derived from
    :pylib:`concurrent.futures.Executor
    <concurrent.futures.html#concurrent.futures.Executor>` but will
    block further items on :meth:`submit` calls to be added to workers
    queue if the *max_bound* limit is reached.

    .. versionadded:: 10.0

    .. seealso::
       - :pylib:`concurrent.futures.html#executor-objects`
       - :class:`ThreadList`

    :param executor: One of the executors found in ``concurrent.futures``.
        The parameter may be given as class type or its name.
    :param max_bound: the maximum number of items in the workers queue.
        If not given or None, the number is set to *max_workers*.
    :param args: Any positional argument for the given *executor*
    :param kwargs: Any keyword argument for the given *executor*
    :raises AttributeError: given *executor* is not found in
        concurrent.futures.
    :raises TypeError: given *executor* is not a class or not a real
        subclass of concurrent.futures.Executor.
    :raises ValueError: minimum *max_bound* is 1.
    """

    def __new__(
        cls,
        executor: futures.Executor | str,
        /,
        max_bound: int | None = None,
        *args: Any,
        **kwargs: Any
    ) -> BoundedPoolExecutor:
        """Create a new BoundedPoolExecutor subclass.

        The class inherits from :class:`BoundedPoolExecutor` and the
        given *executor*. The class name is composed of "Bounded" and
        the name of the *executor*.
        """
        module = 'concurrent.futures'
        if isinstance(executor, str):
            base = getattr(
                importlib.import_module(module), executor)
        else:
            base = executor

        if base is futures.Executor or not issubclass(base, futures.Executor):
            raise TypeError(
                f'expected a real subclass of {module + ".Executor"!r} or the '
                f'class name for executor parameter, not {base.__name__!r}'
            )
        new = type('Bounded' + base.__name__, (cls, base), {})
        return super().__new__(new)

    def __init__(self, executor, /, max_bound=None, *args, **kwargs) -> None:
        """Initializer."""
        if max_bound is not None and max_bound < 1:
            raise ValueError("Minimum 'max_bound' is 1")

        super().__init__(*args, **kwargs)
        self._bound_semaphore = threading.BoundedSemaphore(
            max_bound or self._max_workers)

    def submit(self, fn, /, *args, **kwargs) -> futures.Future:
        """Schedules callable *fn* to be executed as ``fn(*args, **kwargs)``.

        .. code-block:: python

           with BoundedPoolExecutor('ThreadPoolExecutor',
                                     max_bound=5,
                                     max_workers=1) as executor:
               future = executor.submit(pow, 323, 1235)
               print(future.result())

        """
        self._bound_semaphore.acquire()

        try:
            f = super().submit(fn, *args, **kwargs)
        except futures.BrokenExecutor:
            self._bound_semaphore.release()
            raise

        f.add_done_callback(lambda _f: self._bound_semaphore.release())
        return f

    if not SPHINX_RUNNING:
        submit.__doc__ = futures.Executor.submit.__doc__

    def _bound(self, sep: str = '') -> str:
        """Helper method for str and repr."""
        if not hasattr(self, '_bound_semaphore'):
            # class is not fully initialized
            return ''

        bound = self._bound_semaphore._initial_value
        return '' if bound == self._max_workers else f'{sep}{bound}'

    def __str__(self):
        """String of current BoundedPoolExecutor type.

        Includes *max_bound* if necessary.
        """
        return f'{type(self).__name__}({self._bound()})'

    def __repr__(self):
        """Representation string of BoundedPoolExecutor.

        Includes the *executor* and *max_bound* if necessary.
        """
        base, executor = type(self).__bases__
        return f'{base.__name__}({executor.__name__!r}{self._bound(", ")})'
