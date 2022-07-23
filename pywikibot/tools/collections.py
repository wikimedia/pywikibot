"""Collections datatypes."""
#
# (C) Pywikibot team, 2014-2022
#
# Distributed under the terms of the MIT license.
#
import collections
from collections.abc import Container, Iterable, Iterator, Mapping, Sized
from contextlib import suppress
from itertools import chain


__all__ = (
    'CombinedError',
    'DequeGenerator',
    'EmptyDefault',
    'SizedKeyCollection',
    'EMPTY_DEFAULT',
)


# Collection is not provided with Python 3.5; use Container, Iterable, Sized
class SizedKeyCollection(Container, Iterable, Sized):

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
        self.clear()

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
        self.data = {}  # defaultdict fails (T282865)
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

    """
    A default for a not existing siteinfo property.

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
        result = '{}({})'.format(self.__class__.__name__, items)
        self.extend(items)
        return result
