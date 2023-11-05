"""This module contains backports to support older Python versions."""
#
# (C) Pywikibot team, 2014-2023
#
# Distributed under the terms of the MIT license.
#
import sys
from typing import Any


PYTHON_VERSION = sys.version_info[:3]
SPHINX_RUNNING = 'sphinx' in sys.modules

# functools.cache
if PYTHON_VERSION >= (3, 9):
    from functools import cache  # type: ignore[attr-defined]
else:
    from functools import lru_cache as _lru_cache
    cache = _lru_cache(None)


# context
if PYTHON_VERSION < (3, 7) or SPHINX_RUNNING:

    class nullcontext:  # noqa: N801

        """Context manager that does no additional processing.

        .. seealso:: :python:`contextlib.nullcontext
           <library/contextlib.html#contextlib.nullcontext>`,
           backported from Python 3.7.
        """

        def __init__(self, enter_result: Any = None) -> None:  # noqa: D107
            self.enter_result = enter_result

        def __enter__(self) -> Any:
            return self.enter_result

        def __exit__(self, *excinfo: Any) -> None:
            pass
else:
    from contextlib import nullcontext  # type: ignore[assignment]


# queue
if PYTHON_VERSION < (3, 7):
    from queue import Queue as SimpleQueue
else:
    from queue import SimpleQueue  # type: ignore[assignment]


# typing
if PYTHON_VERSION < (3, 9):
    from typing import DefaultDict  # type: ignore[misc]
else:
    from collections import (  # type: ignore[misc] # noqa: N812
        defaultdict as DefaultDict,
    )


if PYTHON_VERSION < (3, 7, 2):
    from typing import Dict as OrderedDict
elif PYTHON_VERSION < (3, 9):
    from typing import OrderedDict
else:
    from collections import OrderedDict

if PYTHON_VERSION < (3, 9):
    from typing import (
        Container,
        Counter,
        Dict,
        FrozenSet,
        Generator,
        Iterable,
        Iterator,
        List,
        Mapping,
        Match,
        Pattern,
        Sequence,
        Set,
        Tuple,
        Type,
    )
else:
    from collections.abc import (
        Container,
        Generator,
        Iterable,
        Iterator,
        Mapping,
        Sequence,
    )
    from collections import Counter
    from re import Match, Pattern
    Dict = dict  # type: ignore[misc]
    FrozenSet = frozenset  # type: ignore[misc]
    List = list  # type: ignore[misc]
    Set = set  # type: ignore[misc]
    Tuple = tuple  # type: ignore[assignment]
    Type = type


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


# bpo-38200
if PYTHON_VERSION < (3, 10) or SPHINX_RUNNING:
    from itertools import tee

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


# gh-98363
if PYTHON_VERSION < (3, 12) or SPHINX_RUNNING:
    def batched(iterable, n: int) -> Generator[tuple, None, None]:
        """Batch data from the *iterable* into tuples of length *n*.

        .. note:: The last batch may be shorter than *n*.

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

        .. seealso:: :python:`itertools.batched
           <library/itertools.html#itertools.batched>`,
           backported from Python 3.12.
        .. versionadded:: 8.2

        :param n: How many items of the iterable to get in one chunk
        """
        group = []
        for item in iterable:
            group.append(item)
            if len(group) == n:
                yield tuple(group)
                group.clear()
        if group:
            yield tuple(group)
else:
    from itertools import batched  # type: ignore[no-redef]
