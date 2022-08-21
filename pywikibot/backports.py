"""This module contains backports to support older Python versions."""
#
# (C) Pywikibot team, 2014-2022
#
# Distributed under the terms of the MIT license.
#
import sys
from typing import Any


PYTHON_VERSION = sys.version_info[:3]

# functools.cache
if PYTHON_VERSION >= (3, 9):
    from functools import cache  # type: ignore[attr-defined]
else:
    from functools import lru_cache as _lru_cache
    cache = _lru_cache(None)


# context
if PYTHON_VERSION < (3, 7):

    class nullcontext:  # noqa: N801

        """Dummy context manager for Python 3.5/3.6 that does nothing."""

        def __init__(self, result: Any = None) -> None:  # noqa: D107
            self.result = result

        def __enter__(self) -> Any:
            return self.result

        def __exit__(self, *args: Any) -> None:
            pass
else:
    from contextlib import nullcontext  # type: ignore[misc]


# queue
if PYTHON_VERSION < (3, 7):
    from queue import Queue as SimpleQueue
else:
    from queue import SimpleQueue  # type: ignore[misc]


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
if PYTHON_VERSION >= (3, 9):
    removeprefix = str.removeprefix  # type: ignore[attr-defined]
    removesuffix = str.removesuffix  # type: ignore[attr-defined]
else:
    def removeprefix(string: str, prefix: str) -> str:  # skipcq: TYP-053
        """Remove prefix from a string or return a copy otherwise.

        .. versionadded:: 5.4
        """
        if string.startswith(prefix):
            return string[len(prefix):]
        return string

    def removesuffix(string: str, suffix: str) -> str:  # skipcq: TYP-053
        """Remove prefix from a string or return a copy otherwise.

        .. versionadded:: 5.4
        """
        if string.endswith(suffix):
            return string[:-len(suffix)]
        return string


# bpo-38200
if PYTHON_VERSION >= (3, 10):
    from itertools import pairwise
else:
    from itertools import tee

    def pairwise(iterable):
        """Return successive overlapping pairs taken from the input iterable.

        .. versionadded:: 7.6
        """
        a, b = tee(iterable)
        next(b, None)
        return zip(a, b)
