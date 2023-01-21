"""Classes which can be used for threading."""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import queue
import re
import threading
import time

import pywikibot  # T306760


__all__ = (
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
            '{cls.__module__}.{cls.__class__.__name__}'.format(cls=self))

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


class ThreadList(list):

    """A simple threadpool class to limit the number of simultaneous threads.

    Any threading.Thread object can be added to the pool using the append()
    method. If the maximum number of simultaneous threads has not been reached,
    the Thread object will be started immediately; if not, the append() call
    will block until the thread is able to start.

    >>> pool = ThreadList(limit=10)
    >>> def work():
    ...     time.sleep(1)
    ...
    >>> for x in range(20):
    ...     pool.append(threading.Thread(target=work))
    ...

    """

    def __init__(self, limit: int = 128, wait_time: float = 2, *args) -> None:
        """Initializer.

        :param limit: the number of simultaneous threads
        :param wait_time: how long to wait if active threads exceeds limit
        """
        self.limit = limit
        self.wait_time = wait_time
        super().__init__(*args)
        for item in self:
            if not isinstance(item, threading.Thread):
                raise TypeError("Cannot add '{}' to ThreadList"
                                .format(type(item)))

    def active_count(self):
        """Return the number of alive threads and delete all non-alive ones."""
        cnt = 0
        for item in self[:]:
            if item.is_alive():
                cnt += 1
            else:
                self.remove(item)
        return cnt

    def append(self, thd):
        """Add a thread to the pool and start it."""
        if not isinstance(thd, threading.Thread):
            raise TypeError("Cannot append '{}' to ThreadList"
                            .format(type(thd)))

        while self.active_count() >= self.limit:
            time.sleep(self.wait_time)

        super().append(thd)
        thd.start()
        pywikibot.logging.debug("thread {} ('{}') started"
                                .format(len(self), type(thd)))
