"""Collections datatypes."""
#
# (C) Pywikibot team, 2014-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import collections
from abc import ABC, abstractmethod
from collections.abc import Collection, Generator, Iterator, Mapping
from contextlib import suppress
from itertools import chain
from types import TracebackType
from typing import Any, NamedTuple

from pywikibot.backports import Generator as GeneratorType
from pywikibot.exceptions import ArgumentDeprecationWarning
from pywikibot.tools import (
    PYTHON_VERSION,
    deprecated_args,
    issue_deprecation_warning,
)


__all__ = (
    'CombinedError',
    'DequeGenerator',
    'EmptyDefault',
    'GeneratorWrapper',
    'RateLimit',
    'SizedKeyCollection',
    'EMPTY_DEFAULT',
)


class SizedKeyCollection(Collection):

    """Structure to hold values where the key is given by the value itself.

    A structure like a defaultdict but the key is given by the value
    itself and cannot be assigned directly. It returns the number of all
    items with len() but not the number of keys.

    Samples:

        >>> from pywikibot.tools.collections import SizedKeyCollection
        >>> data = SizedKeyCollection('title')
        >>> data.append('foo')
        >>> data.append('bar')
        >>> data.append('Foo')
        >>> list(data)
        ['foo', 'Foo', 'bar']
        >>> len(data)
        3
        >>> 'Foo' in data
        True
        >>> 'foo' in data
        False
        >>> data['Foo']
        ['foo', 'Foo']
        >>> list(data.keys())
        ['Foo', 'Bar']
        >>> data.remove_key('Foo')
        >>> list(data)
        ['bar']
        >>> data.clear()
        >>> list(data)
        []

    .. versionadded:: 6.1
    """

    def __init__(self, keyattr: str) -> None:
        """Initializer.

        :param keyattr: an attribute or method of the values to be hold
            with this collection which will be used as key.
        """
        self.keyattr = keyattr
        self.data: dict[Any, list[Any]] = {}
        self.size = 0

    def __contains__(self, key) -> bool:
        return key in self.data

    def __getattr__(self, key):
        """Delegate Mapping methods to self.data."""
        if key in ('keys', 'values', 'items'):
            return getattr(self.data, key)
        return super().__getattr__(key)

    def __getitem__(self, key) -> list:
        return self.data[key]

    def __iter__(self):
        """Iterate through all items of the tree."""
        yield from chain.from_iterable(self.data.values())

    def __len__(self) -> int:
        """Return the number of all values."""
        return self.size

    def __repr__(self) -> str:
        return str(self.data).replace('defaultdict', self.__class__.__name__)

    def append(self, value) -> None:
        """Add a value to the collection."""
        key = getattr(value, self.keyattr)
        if callable(key):
            key = key()
        if key not in self.data:
            self.data[key] = []
        self.data[key].append(value)
        self.size += 1

    def remove(self, value) -> None:
        """Remove a value from the container."""
        key = getattr(value, self.keyattr)
        if callable(key):
            key = key()
        with suppress(ValueError):
            self.data[key].remove(value)
            self.size -= 1

    def remove_key(self, key) -> None:
        """Remove all values for a given key."""
        with suppress(KeyError):
            self.size -= len(self.data[key])
            del self.data[key]

    def clear(self) -> None:
        """Remove all elements from SizedKeyCollection."""
        self.data.clear()  # defaultdict fails (T282865)
        self.size = 0

    def filter(self, key):
        """Iterate over items for a given key."""
        with suppress(KeyError):
            yield from self.data[key]

    def iter_values_len(self):
        """Yield key, len(values) pairs."""
        for key, values in self.data.items():
            yield key, len(values)


class CombinedError(KeyError, IndexError):

    """An error that gets caught by both KeyError and IndexError.

    .. versionadded:: 3.0
    """


class EmptyDefault(str, Mapping):

    """A default for a not existing siteinfo property.

    It should be chosen if there is no better default known. It acts like an
    empty collections, so it can be iterated through it safely if treated as a
    list, tuple, set or dictionary. It is also basically an empty string.

    Accessing a value via __getitem__ will result in a combined KeyError and
    IndexError.

    .. versionadded:: 3.0
    .. versionchanged:: 6.2
       ``empty_iterator()`` was removed in favour of ``iter()``.
    """

    def __init__(self) -> None:
        """Initialise the default as an empty string."""
        str.__init__(self)

    def __iter__(self):
        """An iterator which does nothing and drops the argument."""
        return iter(())

    def __getitem__(self, key):
        """Raise always a :py:obj:`CombinedError`."""
        raise CombinedError(key)


#:
EMPTY_DEFAULT = EmptyDefault()


class DequeGenerator(Iterator, collections.deque):

    """A generator that allows items to be added during generating.

    .. versionadded:: 3.0
    .. versionchanged:: 6.1
       Provide a representation string.
    """

    def __next__(self):
        """Iterator method."""
        if self:
            return self.popleft()
        raise StopIteration

    def __repr__(self) -> str:
        """Provide an object representation without clearing the content."""
        items = list(self)
        result = f'{self.__class__.__name__}({items})'
        self.extend(items)
        return result


class GeneratorWrapper(ABC, Generator):

    """A Generator base class which wraps the internal `generator` property.

    This generator iterator also has :python:`generator.close()
    <reference/expressions.html#generator.close>` mixin method and it can
    be used as Iterable and Iterator as well.

    .. versionadded:: 7.6

    Example:

    >>> class Gen(GeneratorWrapper):
    ...     @property
    ...     def generator(self):
    ...         return (c for c in 'Pywikibot')
    >>> gen = Gen()
    >>> next(gen)  # can be used as Iterator ...
    'P'
    >>> next(gen)
    'y'
    >>> ''.join(c for c in gen)  # ... or as Iterable
    'wikibot'
    >>> next(gen)  # the generator is exhausted ...
    Traceback (most recent call last):
        ...
    StopIteration
    >>> gen.restart()  # ... but can be restarted
    >>> next(gen) + next(gen)
    'Py'
    >>> gen.close()  # the generator may be closed
    >>> next(gen)
    Traceback (most recent call last):
        ...
    StopIteration
    >>> gen.restart()  # restart a closed generator
    >>> # also send() and throw() works
    >>> gen.send(None) + gen.send(None)
    'Py'
    >>> gen.throw(RuntimeError('Foo'))
    Traceback (most recent call last):
        ...
    RuntimeError: Foo

    .. seealso:: :pep:`342`
    """

    @property
    @abstractmethod
    def generator(self) -> GeneratorType[Any, Any, Any]:
        """Abstract generator property."""
        yield from ()

    def send(self, value: Any) -> Any:
        """Return next yielded value from generator or raise StopIteration.

        The `value` parameter is ignored yet; usually it should be ``None``.
        If the wrapped generator property exits without yielding another
        value this method raises `StopIteration`. The send method works
        like the `next` function with a GeneratorWrapper instance as
        parameter.

        Refer :python:`generator.send()
        <reference/expressions.html#generator.send>` for its usage.

        :raises TypeError: generator property is not a generator
        """
        if not isinstance(self.generator, GeneratorType):
            raise TypeError('generator property is not a generator but '
                            f'{type(self.generator).__name__}')
        if not hasattr(self, '_started_gen'):
            # start the generator
            self._started_gen = self.generator
        return next(self._started_gen)

    @deprecated_args(val='value', tb='traceback')  # since 10.7.0
    def throw(self,
              typ: BaseException | type[BaseException] | None = None,
              value: Any = None,
              traceback: TracebackType | None = None) -> None:
        """Raise an exception inside the wrapped generator.

        Refer :python:`generator.throw()
        <reference/expressions.html#generator.throw>` for various
        parameter usage.

        .. versionchanged:: 10.7
           The *val* and *tb* parameters were renamed to *value* and
           *traceback*.
        .. deprecated:: 10.7
           The ``(type, value, traceback)`` signature is deprecated; use
           single-arg signature ``throw(value)`` instead.

        :raises RuntimeError: No generator started
        :raises TypeError: Invalid type for *typ* argument
        """
        if not hasattr(self, '_started_gen'):
            raise RuntimeError('No generator was started')

        # New-style (single exception instance) with keyword argument
        if typ is None and traceback is None and isinstance(value,
                                                            BaseException):
            self._started_gen.throw(value)
            return

        if PYTHON_VERSION > (3, 8) and not (value is None
                                            and traceback is None):
            # Old-style (type, value, traceback) signature
            issue_deprecation_warning(
                'The (type, value, traceback) signature of throw()',
                'the single-arg signature',
                warning_class=ArgumentDeprecationWarning,
                since='10.7.0'
            )
            self._started_gen.throw(typ, value, traceback)
            return

        # New-style (single exception instance)
        self._started_gen.throw(typ)

    def restart(self) -> None:
        """Restart the generator."""
        with suppress(AttributeError):
            del self._started_gen


class RateLimit(NamedTuple):

    """A namedtuple which can hold rate limit content.

    This class is used by :meth:`APISite.ratelimit()
    <pywikibot.site._apisite.APISite.ratelimit>`.

    .. note:: :meth:`delay` and :meth:`ratio` properties cannot be
       sliced or used with tuple indices. They must be used as
       attributes.

    >>> limit = RateLimit('user', 500, 10)
    >>> limit
    RateLimit(group='user', hits=500, seconds=10)
    >>> limit.delay
    0.02
    >>> limit.ratio
    50.0
    >>> limit._fields
    ('group', 'hits', 'seconds')
    >>> limit._asdict()  # doctest: +SKIP
    {'group': 'user', 'hits': 500, 'seconds': 10}
    >>> limit[0]
    'user'
    >>> limit[-1]
    10
    >>> user, hits, seconds = limit
    >>> hits, seconds
    (500, 10)
    >>> newlimit = limit._replace(seconds=0)
    >>> newlimit.delay
    0.0
    >>> newlimit.ratio
    inf

    .. versionadded:: 9.0
    """

    group: str = 'unknown'
    hits: int = 50
    seconds: int = 0

    @property
    def delay(self) -> float:
        """Calculate a delay value which is the inverse of :meth:`ratio`."""
        return self.seconds / self.hits

    @property
    def ratio(self) -> float:
        """Calculate a ratio how many hits can be done within one second."""
        return self.hits / self.seconds if self.seconds != 0 else float('inf')
