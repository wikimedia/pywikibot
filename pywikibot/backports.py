"""This module contains backports to support older Python versions."""
#
# (C) Pywikibot team, 2014-2021
#
# Distributed under the terms of the MIT license.
#
from pywikibot.tools import PYTHON_VERSION


# functools.cache
if PYTHON_VERSION >= (3, 9):
    from functools import cache
else:
    from functools import lru_cache as _lru_cache
    cache = _lru_cache(None)


# context
if PYTHON_VERSION < (3, 7):

    class nullcontext:  # noqa: N801

        """Dummy context manager for Python 3.5/3.6 that does nothing."""

        def __init__(self, result=None):  # noqa: D107
            self.result = result

        def __enter__(self):
            return self.result

        def __exit__(self, *args):
            pass
else:
    from contextlib import nullcontext


# queue
if PYTHON_VERSION < (3, 7):
    from queue import Queue as SimpleQueue
else:
    from queue import SimpleQueue


# typing
if PYTHON_VERSION < (3, 5, 2):
    from typing import Dict as DefaultDict
elif PYTHON_VERSION < (3, 9):
    from typing import DefaultDict
else:
    from collections import defaultdict as DefaultDict  # noqa: N812


if PYTHON_VERSION < (3, 7, 2):
    from typing import Dict as OrderedDict
elif PYTHON_VERSION < (3, 9):
    from typing import OrderedDict
else:
    from collections import OrderedDict


if PYTHON_VERSION >= (3, 9):
    from collections.abc import Iterable, Sequence
    Dict = dict
    FrozenSet = frozenset
    List = list
    Set = set
    Tuple = tuple
else:
    from typing import Dict, FrozenSet, Iterable, List, Sequence, Set, Tuple


# PEP 616 string methods
if PYTHON_VERSION >= (3, 9):
    removeprefix = str.removeprefix
    removesuffix = str.removesuffix
else:
    def removeprefix(string: str, prefix: str) -> str:
        """Remove prefix from a string or return a copy otherwise.

        *New in version 5.4.*
        """
        if string.startswith(prefix):
            return string[len(prefix):]
        return string[:]

    def removesuffix(string: str, suffix: str) -> str:
        """Remove prefix from a string or return a copy otherwise.

        *New in version 5.4.*
        """
        if string.endswith(suffix):
            return string[:-len(suffix)]
        return string[:]
