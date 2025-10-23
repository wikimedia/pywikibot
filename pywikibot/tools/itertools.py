"""Iterator functions.

.. note:: ``pairwise()`` function introduced in Python 3.10 is backported
   in :mod:`backports`
"""
#
# (C) Pywikibot team, 2008-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import collections
import heapq
import itertools
from contextlib import suppress
from typing import Any

from pywikibot.backports import (
    Callable,
    Generator,
    Iterable,
    Iterator,
    batched,
)
from pywikibot.logging import debug
from pywikibot.tools import deprecated


__all__ = (
    'filter_unique',
    'intersect_generators',
    'islice_with_ellipsis',
    'itergroup',
    'roundrobin_generators',
    'union_generators',
)


@deprecated('backports.batched()', since='8.2.0')
def itergroup(iterable,
              size: int,
              strict: bool = False) -> Generator[list[Any], None, None]:
    """Make an iterator that returns lists of (up to) size items from iterable.

    Example:

    >>> i = itergroup(range(25), 10)
    >>> print(next(i))
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
    >>> print(next(i))
    [10, 11, 12, 13, 14, 15, 16, 17, 18, 19]
    >>> print(next(i))
    [20, 21, 22, 23, 24]
    >>> print(next(i))
    Traceback (most recent call last):
     ...
    StopIteration

    .. versionadded:: 7.6
       The *strict* parameter.
    .. deprecated:: 8.2
       Use :func:`backports.batched` instead.

    :param size: How many items of the iterable to get in one chunk
    :param strict: If True, raise a ValueError if length of iterable is
        not divisible by `size`.
    :raises ValueError: iterable is not divisible by size
    """
    for group in batched(iterable, size, strict=strict):
        yield list(group)


def islice_with_ellipsis(iterable, *args, marker: str = '…'):
    """Generator which yields the first n elements of the iterable.

    If more elements are available and marker is True, it returns an extra
    string marker as continuation mark.

    Function takes the
    and the additional keyword marker.

    :param iterable: the iterable to work on
    :type iterable: iterable
    :param args: same args as:
        - ``itertools.islice(iterable, stop)``
        - ``itertools.islice(iterable, start, stop[, step])``
    :param marker: element to yield if iterable still contains elements
        after showing the required number. Default value: '…'
    """
    s = slice(*args)
    _iterable = iter(iterable)
    yield from itertools.islice(_iterable, *args)
    if marker and s.stop is not None:
        with suppress(StopIteration):
            next(_iterable)
            yield marker


def union_generators(*iterables: Iterable[Any],
                     key: Callable[[Any], Any] | None = None,
                     reverse: bool = False) -> Iterator[Any]:
    """Generator of union of sorted iterables.

    Yield all items from the input iterables in sorted order, removing
    duplicates. The input iterables must already be sorted according to
    the same *key* and direction. For descending direction, *reverse*
    must be ``True``. The generator will yield each element only once,
    even if it appears in multiple iterables. This behaves similarly to:

        sorted(set(itertools.chain(*iterables)), key=key, reverse=reverse)

    but is memory-efficient since it processes items lazily.

    Sample:

    >>> list(union_generators([1, 2, 3, 4], [3, 4, 5], [2, 6]))
    [1, 2, 3, 4, 5, 6]
    >>> list(union_generators([4, 3, 2, 1], [5, 4, 3], [6, 2], reverse=True))
    [6, 5, 4, 3, 2, 1]

    .. versionadded:: 10.6

    .. note::
       All input iterables must be sorted consistently. *reverse* must
       be set to ``True`` only if the iterables are sorted in descending
       order. For simple concatenation without duplicate removal, use
       :pylib:`itertools.chain<itertools#itertools.chain>` instead.

    :param iterables: Sorted iterables to merge.
    :param key: Optional key function to compare elements. If ``None``,
        items are compared directly.
    :param reverse: Whether the input iterables are sorted in descending
        order.
    :return: Generator yielding all unique items in sorted order.
    """
    merged = heapq.merge(*iterables, key=key, reverse=reverse)
    return (list(group)[0] for _, group in itertools.groupby(merged, key=key))


def intersect_generators(*iterables, allow_duplicates: bool = False):
    """Generator of intersect iterables.

    Yield items only if they are yielded by all iterables. zip_longest
    is used to retrieve items from all iterables in parallel, so that
    items can be yielded before iterables are exhausted.

    Generator is stopped when all iterables are exhausted. Quitting
    before all iterables are finished is attempted if there is no more
    chance of finding an item in all of them.

    Sample:

    >>> iterables = 'mississippi', 'missouri'
    >>> list(intersect_generators(*iterables))
    ['m', 'i', 's']
    >>> list(intersect_generators(*iterables, allow_duplicates=True))
    ['m', 'i', 's', 's', 'i']


    .. versionadded:: 3.0

    .. versionchanged:: 5.0
       Avoid duplicates (:phab:`T263947`).

    .. versionchanged:: 6.4
       ``genlist`` was renamed to ``iterables``; consecutive iterables
       are to be used as iterables parameters or '*' to unpack a list

    .. versionchanged:: 7.0
       Reimplemented without threads which is up to 10'000 times faster

    .. versionchanged:: 9.0
       Iterable elements may consist of lists or tuples
       ``allow_duplicates`` is a keyword-only argument

    :param iterables: page generators
    :param allow_duplicates: optional keyword argument to allow duplicates
        if present in all generators
    """
    if not iterables:
        return

    if len(iterables) == 1:
        yield from iterables[0]
        return

    # If any iterable is empty, no pages are going to be returned
    for source in iterables:
        if not source:
            debug(f'At least one iterable ({source!r}) is empty and execution'
                  ' was skipped immediately.')
            return

    # Item is cached to check that it is found n_gen times
    # before being yielded.
    cache = collections.defaultdict(collections.Counter)
    n_gen = len(iterables)

    ones = collections.Counter(range(n_gen))
    active_iterables = set(range(n_gen))
    seen = set()

    # Get items from iterables in a round-robin way.
    sentinel = object()
    for items in itertools.zip_longest(*iterables, fillvalue=sentinel):
        for index, item in enumerate(items):

            if item is sentinel:
                active_iterables.discard(index)
                continue

            if not allow_duplicates and hash(item) in seen:
                continue

            # Each cache entry is a Counter of iterables' index
            cache[item][index] += 1

            if len(cache[item]) == n_gen:
                yield item

                # Remove item from cache if possible or decrease Counter entry
                if not allow_duplicates:
                    del cache[item]
                    seen.add(hash(item))
                elif cache[item] == ones:
                    del cache[item]
                else:
                    cache[item] -= ones

        # We can quit if an iterable is exceeded and cached iterables is
        # a subset of active iterables.
        if len(active_iterables) < n_gen:
            cached_iterables = set(
                itertools.chain.from_iterable(v.keys()
                                              for v in cache.values()))
            if cached_iterables <= active_iterables:
                return


def roundrobin_generators(*iterables) -> Generator[Any, None, None]:
    """Yield simultaneous from each iterable.

    Sample:

    >>> tuple(roundrobin_generators('ABC', range(5)))
    ('A', 0, 'B', 1, 'C', 2, 3, 4)

    .. versionadded:: 3.0
    .. versionchanged:: 6.4
       A sentinel variable is used to determine the end of an iterable
       instead of None.

    :param iterables: any iterable to combine in roundrobin way
    :type iterables: iterable
    :return: the combined generator of iterables
    :rtype: generator
    """
    sentinel = object()
    return (item
            for item in itertools.chain.from_iterable(
                itertools.zip_longest(*iterables, fillvalue=sentinel))
            if item is not sentinel)


def filter_unique(iterable, container=None, key=None, add=None):
    """Yield unique items from an iterable, omitting duplicates.

    By default, to provide uniqueness, it puts the generated items into a
    set created as a local variable. It only yields items which are not
    already present in the local set.

    For large collections, this is not memory efficient, as a strong reference
    to every item is kept in a local set which cannot be cleared.

    Also, the local set can't be re-used when chaining unique operations on
    multiple generators.

    To avoid these issues, it is advisable for the caller to provide their own
    container and set the key parameter to be the function
    :py:obj:`hash`, or use a :py:obj:`weakref` as the key.

    The container can be any object that supports __contains__.
    If the container is a set or dict, the method add or __setitem__ will be
    used automatically. Any other method may be provided explicitly using the
    add parameter.

    Beware that key=id is only useful for cases where id() is not unique.

    .. warning:: This is not thread safe.

    .. versionadded:: 3.0

    :param iterable: the source iterable
    :type iterable: collections.abc.Iterable
    :param container: storage of seen items
    :type container: type
    :param key: function to convert the item to a key
    :type key: callable
    :param add: function to add an item to the container
    :type add: callable
    """
    if container is None:
        container = set()

    if not add:
        if hasattr(container, 'add'):
            def container_add(x) -> None:
                container.add(key(x) if key else x)

            add = container_add
        else:
            def container_setitem(x) -> None:
                container.__setitem__(key(x) if key else x,
                                      True)

            add = container_setitem

    for item in iterable:
        try:
            if (key(item) if key else item) not in container:
                add(item)
                yield item
        except StopIteration:
            return
