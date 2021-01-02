# -*- coding: utf-8 -*-
"""This module contains backports to support older Python versions."""
#
# (C) Pywikibot team, 2020
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


# typing
if PYTHON_VERSION < (3, 5, 2):
    from typing import Dict as DefaultDict
elif PYTHON_VERSION < (3, 9):
    from typing import DefaultDict
else:
    from collections import defaultdict as DefaultDict  # noqa: N812

if PYTHON_VERSION >= (3, 9):
    from collections.abc import Iterable
    Dict = dict
    FrozenSet = frozenset
    List = list
    Set = set
    Tuple = tuple
else:
    from typing import Dict, FrozenSet, Iterable, List, Set, Tuple


# PEP 616 string methods
if PYTHON_VERSION >= (3, 9):
    removeprefix = str.removeprefix
    removesuffix = str.removesuffix
else:
    def removeprefix(string: str, prefix: str) -> str:
        """Remove prefix from a string or return a copy otherwise."""
        if string.startswith(prefix):
            return string[len(prefix):]
        return string[:]

    def removesuffix(string: str, suffix: str) -> str:
        """Remove prefix from a string or return a copy otherwise."""
        if string.endswith(suffix):
            return string[:-len(suffix)]
        return string[:]
