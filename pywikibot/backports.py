"""This module contains backports to support older Python versions.

.. caution:: This module is not part of the public pywikibot API.
   Breaking changes may be made at any time, and the module is not
   subject to deprecation requirements.

.. versionchanged:: 10.0
   This module is 'private'.
"""
#
# (C) Pywikibot team, 2014-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import sys
from typing import Any


# Placed here to omit circular import in tools
PYTHON_VERSION = sys.version_info[:3]
SPHINX_RUNNING = 'sphinx' in sys.modules

# functools.cache
if PYTHON_VERSION >= (3, 9):
    from functools import cache  # type: ignore[attr-defined]
else:
    from functools import lru_cache as _lru_cache
    cache = _lru_cache(None)


# typing
if PYTHON_VERSION < (3, 9):
    from typing import DefaultDict  # type: ignore[misc]
else:
    from collections import (  # type: ignore[misc] # noqa: N812
        defaultdict as DefaultDict,
    )


if PYTHON_VERSION < (3, 9):
    from typing import OrderedDict
else:
    from collections import OrderedDict

if PYTHON_VERSION < (3, 9):
    from typing import (
        Container,
        Counter,
        Dict,
        Generator,
        Iterable,
        Iterator,
        Mapping,
        Match,
        Pattern,
        Sequence,
    )
else:
    from collections import Counter
    from collections.abc import (
        Container,
        Generator,
        Iterable,
        Iterator,
        Mapping,
        Sequence,
    )
    from re import Match, Pattern
    Dict = dict  # type: ignore[misc]


if PYTHON_VERSION < (3, 9, 2):
    from typing import Callable
else:
    from collections.abc import Callable


# PEP 616 string methods
if PYTHON_VERSION < (3, 9) or SPHINX_RUNNING:
    def removeprefix(string: str, prefix: str) -> str:  # skipcq: TYP-053
        """Remove prefix from a string or return a copy otherwise.

        >>> removeprefix('TestHook', 'Test')
        'Hook'
        >>> removeprefix('BaseTestCase', 'Test')
        'BaseTestCase'

        .. seealso:: :python:`str.removeprefix
           <library/stdtypes.html#str.removeprefix>`,
           backported from Python 3.9.
        .. versionadded:: 5.4
        """
        if string.startswith(prefix):
            return string[len(prefix):]
        return string

    def removesuffix(string: str, suffix: str) -> str:  # skipcq: TYP-053
        """Remove suffix from a string or return a copy otherwise.

        >>> removesuffix('MiscTests', 'Tests')
        'Misc'
        >>> removesuffix('TmpDirMixin', 'Tests')
        'TmpDirMixin'

        .. seealso:: :python:`str.removesuffix
           <library/stdtypes.html#str.removesuffix>`,
           backported from Python 3.9.
        .. versionadded:: 5.4
        """
        if string.endswith(suffix):
            return string[:-len(suffix)]
        return string
else:
    removeprefix = str.removeprefix  # type: ignore[assignment]
    removesuffix = str.removesuffix  # type: ignore[assignment]


if PYTHON_VERSION < (3, 10) or SPHINX_RUNNING:
    from itertools import tee

    NoneType = type(None)

    # bpo-38200
    def pairwise(iterable):
        """Return successive overlapping pairs taken from the input iterable.

        .. seealso:: :python:`itertools.pairwise
           <library/itertools.html#itertools.pairwise>`,
           backported from Python 3.10.
        .. versionadded:: 7.6
        """
        a, b = tee(iterable)
        next(b, None)
        return zip(a, b)
else:
    from itertools import pairwise  # type: ignore[no-redef]
    from types import NoneType


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
        .. versionadded:: 8.2
        .. versionchanged:: 9.0
           Added *strict* option, backported from Python 3.13

        :param n: How many items of the iterable to get in one chunk
        :param strict: raise a ValueError if the final batch is shorter
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
            from itertools import batched as _batched
            for group in _batched(iterable, n):
                if strict and len(group) < n:
                    raise ValueError(msg)
                yield group
else:
    from itertools import batched  # type: ignore[no-redef]
