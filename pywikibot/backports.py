#
# (C) Pywikibot team, 2014-2026
#
# Distributed under the terms of the MIT license.
#
"""This module contains backports to support older Python versions.

.. caution:: This module is not part of the public pywikibot API.
   Breaking changes may be made at any time, and the module is not
   subject to deprecation requirements.

.. version-changed:: 10.0
   This module is 'private'.
"""
from __future__ import annotations

import re
import sys
from typing import TYPE_CHECKING, Any, Union

from pywikibot.tools import PYTHON_VERSION, SPHINX_RUNNING


if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterable


if PYTHON_VERSION < (3, 10) or SPHINX_RUNNING:
    from itertools import tee

    NoneType = type(None)

    # bpo-38200
    def pairwise(iterable):
        """Return successive overlapping pairs taken from the input iterable.

        .. seealso:: :python:`itertools.pairwise
           <library/itertools.html#itertools.pairwise>`,
           backported from Python 3.10.
        .. version-added:: 7.6
        .. version-removed:: 12.0
        """
        a, b = tee(iterable)
        next(b, None)
        return zip(a, b)

elif not TYPE_CHECKING:
    from itertools import pairwise  # noqa: F401
    from types import NoneType  # noqa: F401


# gh-98363
if PYTHON_VERSION < (3, 13) or SPHINX_RUNNING:
    def batched(iterable, n: int, *,
                strict: bool = False) -> Generator[tuple]:
        """Batch data from the *iterable* into tuples of length *n*.

        .. note:: The last batch may be shorter than *n* if *strict* is
           True or raise a ValueError otherwise.

        Example:

        >>> i = batched(range(25), 10)
        >>> print(next(i))
        (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)
        >>> print(next(i))
        (10, 11, 12, 13, 14, 15, 16, 17, 18, 19)
        >>> print(next(i))
        (20, 21, 22, 23, 24)
        >>> print(next(i))
        Traceback (most recent call last):
         ...
        StopIteration
        >>> list(batched('ABCD', 2))
        [('A', 'B'), ('C', 'D')]
        >>> list(batched('ABCD', 3, strict=False))
        [('A', 'B', 'C'), ('D',)]
        >>> list(batched('ABCD', 3, strict=True))
        Traceback (most recent call last):
         ...
        ValueError: batched(): incomplete batch

        .. seealso:: :python:`itertools.batched
           <library/itertools.html#itertools.batched>`,
           backported from Python 3.12.
        .. version-added:: 8.2
        .. version-changed:: 9.0
           Added *strict* option, backported from Python 3.13
        .. version-removed:: 15.0

        :param n: How many items of the iterable to get in one chunk
        :param strict: Raise a ValueError if the final batch is shorter
            than *n*.
        :raise ValueError: batched(): incomplete batch
        :raise TypeError: *n* cannot be interpreted as an integer
        """
        msg = 'batched(): incomplete batch'
        if PYTHON_VERSION < (3, 12):
            if not isinstance(n, int):
                raise TypeError(f'{type(n).__name__!r} object cannot be'
                                ' interpreted as an integer')
            group = []
            for item in iterable:
                group.append(item)
                if len(group) == n:
                    yield tuple(group)
                    group.clear()
            if group:
                if strict:
                    raise ValueError(msg)
                yield tuple(group)
        else:  # PYTHON_VERSION == (3, 12)
            if TYPE_CHECKING:
                _batched: Callable[[Iterable, int], Iterable]
            else:
                from itertools import batched as _batched

            for group in _batched(iterable, n):
                if strict and len(group) < n:
                    raise ValueError(msg)
                yield group

elif not TYPE_CHECKING:
    from itertools import batched


# gh-115942, gh-134323
if PYTHON_VERSION < (3, 14) or SPHINX_RUNNING:
    import threading as _threading

    from pywikibot.tools import deprecated, issue_deprecation_warning

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

        .. version-added:: 6.2
        .. version-changed:: 10.2
           moved from :mod:`tools.threading` to :mod:`backports`.
        .. version-deprecated:: 10.2
           Passing any arguments is deprecated; a TypeError will be
           raised with Pywikibot 13.0.
        .. version-removed:: 16.0
        .. note:: Passing any arguments has no effect and has been
           deprecated since Python 3.14 and was removed in Python 3.15.
        """

        def __init__(self, *args, **kwargs) -> None:
            """Initializer."""
            if args or kwargs:
                issue_deprecation_warning('Passing arguments to RLock',
                                          since='10.2.0')
            self._lock = _threading.RLock()
            self._block = _threading.Lock()

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
        @deprecated(since='10.2.0')
        def count(self):
            """Return number of acquired locks.

            .. version-deprecated:: 10.2
            """
            with self._block:
                counter = re.search(r'count=(\d+) ', repr(self))
                return int(counter[1])

        def locked(self):
            """Return true if the lock is acquired."""
            with self._block:
                status = repr(self).split(maxsplit=1)[0][1:]
                assert status in ('locked', 'unlocked')
                return status == 'locked'

else:
    from threading import RLock  # type: ignore[assignment]


if PYTHON_VERSION < (3, 15) or SPHINX_RUNNING:

    class sentinel:  # noqa: N801

        """Implementation of a unique sentinel object.

        Usage:

        >>> MISSING = sentinel('MISSING')
        >>> MISSING
        MISSING
        >>> MISSING = sentinel('MISSING', repr="'MISSING'")
        >>> MISSING
        'MISSING'
        >>> import copy
        >>> value = copy.copy(MISSING)
        >>> value is MISSING
        True

        .. version-added:: 11.6
        .. version-removed:: 17.0
        .. seealso::
           - :pylib:`sentinel<functions#sentinel>` backported
             from Python 3.15.
           - :pep:`661`

        :param name: Name of the sentinel object; it should be the name
            of the variable to which the sentinel shall be assigned.
        :param repr: Representation returned by :func:`repr`.
        :raises TypeError: If *name* is not a string or subclassing is
            attempted.
        :raises AttributeError: If an attribute other than ``__module__``
            is assigned.
        """

        if TYPE_CHECKING:
            __name__: str
            _repr: str
            __module__: str

        def __init__(self, name: str, /, *, repr: str | None = None) -> None:
            """Initializer."""
            if not isinstance(name, str):
                raise TypeError(f'sentinel name must be a string, '
                                f'not {type(name).__name__}')
            object.__setattr__(self, '__name__', name)
            object.__setattr__(self, '_repr',
                               repr if repr is not None else name)
            object.__setattr__(
                self,
                '__module__',
                self._get_module_name()
            )

        def __init_subclass__(cls):
            """Prevent subclassing of sentinel objects.

            :raises TypeError: Always, as sentinel objects cannot be
                subclassed.
            """
            raise TypeError(
                "type 'sentinel' is not an acceptable base type")

        def __repr__(self) -> str:
            """Return the representation of the sentinel."""
            return self._repr

        def __reduce__(self) -> str:
            """Return the name used to restore the sentinel object.

            The returned name is resolved in the original module during
            unpickling.

            :return: The sentinel name.
            """
            return self.__name__

        def __copy__(self) -> sentinel:
            """Return the same instance when shallow-copied."""
            return self

        def __deepcopy__(self, memo: dict[int, Any]) -> sentinel:
            """Return the same instance when deep-copied.

            :param memo: Deep-copy memo dictionary.

            :return: The sentinel instance itself.
            """
            return self

        def __setattr__(self, attr: str, value: object) -> None:
            """Prevent modification of sentinel attributes.

             Sentinel objects are immutable after initialization. The
            ``__module__`` attribute is excluded to support pickle
            compatibility.

            :param attr: Attribute name.
            :param value: Attribute value.
            :raises AttributeError: If an attribute other than
                ``__module__`` is assigned.
            """
            if attr == '__module__':
                object.__setattr__(self, attr, value)
                return

            raise AttributeError(
                "'sentinel' object has no attribute assignment")

        @staticmethod
        def _get_module_name(depth: int = 1, default: str = '__main__') -> str:
            """Return the module name of a caller frame."""
            d = depth + 1
            if PYTHON_VERSION >= (3, 12):
                return (
                    sys._getframemodulename(d)  # type: ignore[attr-defined]
                    or default
                )

            return sys._getframe(d).f_globals.get('__name__', default)

        if PYTHON_VERSION >= (3, 10):
            def __or__(self, other: object) -> Any:
                return Union[self, other]

            def __ror__(self, other: object) -> Any:
                return Union[other, self]

else:
    from builtins import sentinel  # type: ignore[no-redef, attr-defined]
