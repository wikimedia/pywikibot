"""Miscellaneous helper functions (not wiki-dependent)."""
#
# (C) Pywikibot team, 2008-2021
#
# Distributed under the terms of the MIT license.
#
import collections
import gzip
import hashlib
import ipaddress
import itertools
import os
import queue
import re
import stat
import subprocess
import sys
import threading
import time

from collections.abc import Container, Iterable, Iterator, Mapping, Sized
from contextlib import suppress
from functools import total_ordering, wraps
from importlib import import_module
from itertools import chain, zip_longest
from typing import Any, Optional
from warnings import catch_warnings, showwarning, warn

import pkg_resources

from pywikibot.logging import debug
from pywikibot.tools._deprecate import (  # noqa: F401
    add_decorated_full_name,
    add_full_name,
    deprecated,
    deprecate_arg,
    deprecated_args,
    get_wrapper_depth,
    issue_deprecation_warning,
    manage_wrapping,
    ModuleDeprecationWrapper,
    redirect_func,
    remove_last_args,
)

from pywikibot.tools._unidata import _first_upper_exception

pkg_Version = pkg_resources.packaging.version.Version  # noqa: N816

try:
    import bz2
except ImportError as bz2_import_error:
    try:
        import bz2file as bz2
        warn('package bz2 was not found; using bz2file', ImportWarning)
    except ImportError:
        warn('package bz2 and bz2file were not found', ImportWarning)
        bz2 = bz2_import_error

try:
    import lzma
except ImportError as lzma_import_error:
    lzma = lzma_import_error


PYTHON_VERSION = sys.version_info[:3]

_logger = 'tools'


def is_ip_address(value: str) -> bool:
    """Check if a value is a valid IPv4 or IPv6 address.

    :param value: value to check
    """
    with suppress(ValueError):
        ipaddress.ip_address(value)
        return True

    return False


def has_module(module, version=None):
    """Check if a module can be imported.

    *New in version 3.0.*
    """
    try:
        m = import_module(module)
    except ImportError:
        return False
    if version:
        if not hasattr(m, '__version__'):
            return False

        required_version = pkg_resources.parse_version(version)
        module_version = pkg_resources.parse_version(m.__version__)

        if module_version < required_version:
            warn('Module version {} is lower than requested version {}'
                 .format(module_version, required_version), ImportWarning)
            return False

    return True


def empty_iterator():
    # http://stackoverflow.com/a/13243870/473890
    """DEPRECATED. An iterator which does nothing."""
    return
    yield


class classproperty:  # noqa: N801

    """
    Descriptor class to access a class method as a property.

    This class may be used as a decorator::

        class Foo:

            _bar = 'baz'  # a class property

            @classproperty
            def bar(cls):  # a class property method
                return cls._bar

    Foo.bar gives 'baz'.
    """

    def __init__(self, cls_method):
        """Hold the class method."""
        self.method = cls_method
        self.__doc__ = self.method.__doc__

    def __get__(self, instance, owner):
        """Get the attribute of the owner class by its method."""
        return self.method(owner)


class suppress_warnings(catch_warnings):  # noqa: N801

    """A decorator/context manager that temporarily suppresses warnings.

    Those suppressed warnings that do not match the parameters will be raised
    shown upon exit.

    *New in vesion 3.0.*
    """

    def __init__(self, message='', category=Warning, filename=''):
        """Initialize the object.

        The parameter semantics are similar to those of
        `warnings.filterwarnings`.

        :param message: A string containing a regular expression that the start
            of the warning message must match. (case-insensitive)
        :type message: str
        :param category: A class (a subclass of Warning) of which the warning
            category must be a subclass in order to match.
        :type category: type
        :param filename: A string containing a regular expression that the
            start of the path to the warning module must match.
            (case-sensitive)
        :type filename: str
        """
        self.message_match = re.compile(message, re.I).match
        self.category = category
        self.filename_match = re.compile(filename).match
        super().__init__(record=True)

    def __enter__(self):
        """Catch all warnings and store them in `self.log`."""
        self.log = super().__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop logging warnings and show those that do not match to params."""
        super().__exit__(exc_type, exc_val, exc_tb)
        for warning in self.log:
            if (
                not issubclass(warning.category, self.category)
                or not self.message_match(str(warning.message))
                or not self.filename_match(warning.filename)
            ):
                showwarning(
                    warning.message, warning.category, warning.filename,
                    warning.lineno, warning.file, warning.line)

    def __call__(self, func):
        """Decorate func to suppress warnings."""
        @wraps(func)
        def suppressed_func(*args, **kwargs):
            with self:
                return func(*args, **kwargs)
        return suppressed_func


# From http://python3porting.com/preparing.html
class ComparableMixin:

    """Mixin class to allow comparing to other objects which are comparable."""

    def __lt__(self, other):
        """Compare if self is less than other."""
        return other > self._cmpkey()

    def __le__(self, other):
        """Compare if self is less equals other."""
        return other >= self._cmpkey()

    def __eq__(self, other):
        """Compare if self is equal to other."""
        return other == self._cmpkey()

    def __ge__(self, other):
        """Compare if self is greater equals other."""
        return other <= self._cmpkey()

    def __gt__(self, other):
        """Compare if self is greater than other."""
        return other < self._cmpkey()

    def __ne__(self, other):
        """Compare if self is not equal to other."""
        return other != self._cmpkey()


class DotReadableDict:

    """DEPRECATED. Lecacy class of Revision() and FileInfo().

    Provide: __getitem__() and __repr__().
    """

    def __getitem__(self, key):
        """Give access to class values by key.

        Revision class may also give access to its values by keys
        e.g. revid parameter may be assigned by revision['revid']
        as well as revision.revid. This makes formatting strings with
        % operator easier.

        """
        return getattr(self, key)

    def __repr__(self):
        """Return a more complete string representation."""
        return repr(self.__dict__)


class frozenmap(Mapping):  # noqa:  N801

    """DEPRECATED. Frozen mapping, preventing write after initialisation."""

    def __init__(self, data=(), **kwargs):
        """Initialize data in same ways like a dict."""
        self.__data = {}
        if isinstance(data, Mapping):
            for key in data:
                self.__data[key] = data[key]
        elif hasattr(data, 'keys'):
            for key in data.keys():
                self.__data[key] = data[key]
        else:
            for key, value in data:
                self.__data[key] = value
        for key, value in kwargs.items():
            self.__data[key] = value

    def __getitem__(self, key):
        return self.__data[key]

    def __iter__(self):
        return iter(self.__data)

    def __len__(self):
        return len(self.__data)

    def __repr__(self):
        return '{}({!r})'.format(self.__class__.__name__, self.__data)


# Collection is not provided with Python 3.5; use Container, Iterable, Sized
class SizedKeyCollection(Container, Iterable, Sized):

    """Structure to hold values where the key is given by the value itself.

    A stucture like a defaultdict but the key is given by the value
    itselfvand cannot be assigned directly. It returns the number of all
    items with len() but not the number of keys.

    Samples:

        >>> from pywikibot.tools import SizedKeyCollection
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

    *New in version 6.1.*
    """

    def __init__(self, keyattr: str):
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

    def append(self, value):
        """Add a value to the collection."""
        key = getattr(value, self.keyattr)
        if callable(key):
            key = key()
        if key not in self.data:
            self.data[key] = []
        self.data[key].append(value)
        self.size += 1

    def remove(self, value):
        """Remove a value from the container."""
        key = getattr(value, self.keyattr)
        if callable(key):
            key = key()
        with suppress(ValueError):
            self.data[key].remove(value)
            self.size -= 1

    def remove_key(self, key):
        """Remove all values for a given key."""
        with suppress(KeyError):
            self.size -= len(self.data[key])
            del self.data[key]

    def clear(self):
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


class LazyRegex:

    """
    DEPRECATED. Regex object that obtains and compiles the regex on usage.

    Instances behave like the object created using :py:obj:`re.compile`.
    """

    def __init__(self, pattern, flags=0):
        """
        Initializer.

        :param pattern: :py:obj:`re` regex pattern
        :type pattern: str or callable
        :param flags: :py:obj:`re.compile` flags
        :type flags: int
        """
        self.raw = pattern
        self.flags = flags
        super().__init__()

    @property
    def raw(self):
        """The raw property."""
        if callable(self._raw):
            self._raw = self._raw()

        return self._raw

    @raw.setter
    def raw(self, value):
        self._raw = value
        self._compiled = None

    @property
    def flags(self):
        """The flags property."""
        return self._flags

    @flags.setter
    def flags(self, value):
        self._flags = value
        self._compiled = None

    def __getattr__(self, attr):
        """Compile the regex and delegate all attribute to the regex."""
        if not self._raw:
            raise AttributeError('{}.raw not set'
                                 .format(self.__class__.__name__))

        if not self._compiled:
            self._compiled = re.compile(self.raw, self.flags)

        if hasattr(self._compiled, attr):
            return getattr(self._compiled, attr)

        raise AttributeError('{}: attr {} not recognised'
                             .format(self.__class__.__name__, attr))


class DeprecatedRegex(LazyRegex):

    """Regex object that issues a deprecation notice."""

    def __init__(self, pattern, flags=0, name=None, instead=None, since=None):
        """
        DEPRECATED. Deprecate a give regex.

        If name is None, the regex pattern will be used as part of
        the deprecation warning.

        :param name: name of the object that is deprecated
        :type name: str or None
        :param instead: if provided, will be used to specify the replacement
            of the deprecated name
        :type instead: str
        """
        super().__init__(pattern, flags)
        self._name = name or self.raw
        self._instead = instead
        self._since = since

    def __getattr__(self, attr):
        """Issue deprecation warning."""
        issue_deprecation_warning(self._name, self._instead, since=self._since)
        return super().__getattr__(attr)


def first_lower(string: str) -> str:
    """
    Return a string with the first character uncapitalized.

    Empty strings are supported. The original string is not changed.
    """
    return string[:1].lower() + string[1:]


def first_upper(string: str) -> str:
    """
    Return a string with the first character capitalized.

    Empty strings are supported. The original string is not changed.

    :note: MediaWiki doesn't capitalize some characters the same way as Python.
        This function tries to be close to MediaWiki's capitalize function in
        title.php. See T179115 and T200357.
    """
    first = string[:1]
    return (_first_upper_exception(first) or first.upper()) + string[1:]


def normalize_username(username) -> Optional[str]:
    """Normalize the username."""
    if not username:
        return None
    username = re.sub('[_ ]+', ' ', username).strip()
    return first_upper(username)


class Version(pkg_Version):

    """Version from pkg_resouce vendor package.

    This Version provides propreties of vendor package 20.4 shipped with
    setuptools 49.4.0.
    """

    def __init__(self, version):
        """Add additional properties of not provided by base class."""
        super().__init__(version)

    def __getattr__(self, name):
        """Provides propreties of vendor package 20.4."""
        if name in ('epoch', 'release', 'pre', ):
            return getattr(self._version, name)
        if name in ('post', 'dev'):
            attr = getattr(self._version, name)
            return attr[1] if attr else None
        if name == 'is_devrelease':
            return self.dev is not None

        parts = ('major', 'minor', 'micro')
        try:
            index = parts.index(name)
        except ValueError:
            raise AttributeError('{!r} object has to attribute {!r}'
                                 .format(type(self).__name__, name)) from None
        release = self.release
        return release[index] if len(release) >= index + 1 else 0


@total_ordering
class MediaWikiVersion:

    """
    Version object to allow comparing 'wmf' versions with normal ones.

    The version mainly consist of digits separated by periods. After that is a
    suffix which may only be 'wmf<number>', 'alpha', 'beta<number>' or
    '-rc.<number>' (the - and . are optional). They are considered from old to
    new in that order with a version number without suffix is considered the
    newest. This secondary difference is stored in an internal _dev_version
    attribute.

    Two versions are equal if their normal version and dev version are equal. A
    version is greater if the normal version or dev version is greater. For
    example:

        1.34 < 1.34.1 < 1.35wmf1 < 1.35alpha < 1.35beta1 < 1.35beta2
        < 1.35-rc-1 < 1.35-rc.2 < 1.35

    Any other suffixes are considered invalid.
    """

    MEDIAWIKI_VERSION = re.compile(
        r'(\d+(?:\.\d+)+)(-?wmf\.?(\d+)|alpha|beta(\d+)|-?rc\.?(\d+)|.*)?$')

    def __init__(self, version_str: str) -> None:
        """
        Initializer.

        :param version_str: version to parse
        """
        self._parse(version_str)

    def _parse(self, version_str: str) -> None:
        version_match = MediaWikiVersion.MEDIAWIKI_VERSION.match(version_str)

        if not version_match:
            raise ValueError('Invalid version number "{}"'.format(version_str))

        components = [int(n) for n in version_match.group(1).split('.')]

        # The _dev_version numbering scheme might change. E.g. if a stage
        # between 'alpha' and 'beta' is added, 'beta', 'rc' and stable releases
        # are reassigned (beta=3, rc=4, stable=5).

        if version_match.group(3):  # wmf version
            self._dev_version = (0, int(version_match.group(3)))
        elif version_match.group(4):
            self._dev_version = (2, int(version_match.group(4)))
        elif version_match.group(5):
            self._dev_version = (3, int(version_match.group(5)))
        elif version_match.group(2) in ('alpha', '-alpha'):
            self._dev_version = (1, )
        else:
            for handled in ('wmf', 'alpha', 'beta', 'rc'):
                # if any of those pops up here our parser has failed
                assert handled not in version_match.group(2), \
                    'Found "{}" in "{}"'.format(handled,
                                                version_match.group(2))
            if version_match.group(2):
                debug('Additional unused version part '
                      '"{}"'.format(version_match.group(2)),
                      _logger)
            self._dev_version = (4, )

        self.suffix = version_match.group(2) or ''
        self.version = tuple(components)

    @staticmethod
    def from_generator(generator: str) -> 'MediaWikiVersion':
        """Create instance from a site's generator attribute."""
        prefix = 'MediaWiki '

        if not generator.startswith(prefix):
            raise ValueError('Generator string ({!r}) must start with '
                             '"{}"'.format(generator, prefix))

        return MediaWikiVersion(generator[len(prefix):])

    def __str__(self) -> str:
        """Return version number with optional suffix."""
        return '.'.join(str(v) for v in self.version) + self.suffix

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, str):
            other = MediaWikiVersion(other)
        elif not isinstance(other, MediaWikiVersion):
            return False

        return self.version == other.version and \
            self._dev_version == other._dev_version

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, str):
            other = MediaWikiVersion(other)
        elif not isinstance(other, MediaWikiVersion):
            raise TypeError("Comparison between 'MediaWikiVersion' and '{}' "
                            'unsupported'.format(type(other).__name__))

        if self.version != other.version:
            return self.version < other.version
        else:
            return self._dev_version < other._dev_version


class RLock:
    """Context manager which implements extended reentrant lock objects.

    This RLock is implicit derived from threading.RLock but provides a
    locked() method like in threading.Lock and a count attribute which
    gives the active recursion level of locks.

    Usage:

    >>> from pywikibot.tools import RLock
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

    *New in version 6.2*
    """

    def __init__(self, *args, **kwargs):
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

    def __repr__(self):
        """Representation of tools.RLock instance."""
        return repr(self._lock).replace(
            '_thread.RLock',
            '{cls.__module__}.{cls.__class__.__name__}'.format(cls=self))

    @property
    def count(self):
        """Return number of acquired locks."""
        with self._block:
            counter = re.search(r'count=(\d+) ', repr(self))
            return int(counter.group(1))

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

    """

    def __init__(self, group=None, target=None, name='GeneratorThread',
                 args=(), kwargs=None, qsize=65536):
        """Initializer. Takes same keyword arguments as threading.Thread.

        target must be a generator function (or other callable that returns
        an iterable object).

        :param qsize: The size of the lookahead queue. The larger the qsize,
            the more values will be computed in advance of use (which can eat
            up memory and processor time).
        :type qsize: int
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
        if not self.is_alive() and not self.finished.isSet():
            self.start()
        # if there is an item in the queue, yield it, otherwise wait
        while not self.finished.is_set():
            try:
                yield self.queue.get(True, 0.25)
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                self.stop()

    def stop(self):
        """Stop the background thread."""
        self.finished.set()

    def run(self):
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


def itergroup(iterable, size: int):
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
    """
    group = []
    for item in iterable:
        group.append(item)
        if len(group) == size:
            yield group
            group = []
    if group:
        yield group


def islice_with_ellipsis(iterable, *args, marker='…'):
    """
    Generator which yields the first n elements of the iterable.

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
    :type marker: str
    """
    s = slice(*args)
    _iterable = iter(iterable)
    yield from itertools.islice(_iterable, *args)
    if marker and s.stop is not None:
        with suppress(StopIteration):
            next(_iterable)
            yield marker


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

    _logger = 'threadlist'

    def __init__(self, limit=128, wait_time=2, *args):
        """Initializer.

        :param limit: the number of simultaneous threads
        :type limit: int
        :param wait_time: how long to wait if active threads exceeds limit
        :type wait_time: int or float
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
        debug("thread {} ('{}') started".format(len(self), type(thd)),
              self._logger)

    def stop_all(self):
        """Stop all threads the pool."""
        if self:
            debug('EARLY QUIT: Threads: {}'.format(len(self)), self._logger)
        for thd in self:
            thd.stop()
            debug('EARLY QUIT: Queue size left in {}: {}'
                  .format(thd, thd.queue.qsize()), self._logger)


def intersect_generators(*iterables, allow_duplicates: bool = False):
    """Intersect generators listed in iterables.

    Yield items only if they are yielded by all generators of iterables.
    Threads (via ThreadedGenerator) are used in order to run generators
    in parallel, so that items can be yielded before generators are
    exhausted.

    Threads are stopped when they are either exhausted or Ctrl-C is pressed.
    Quitting before all generators are finished is attempted if
    there is no more chance of finding an item in all queues.

    Sample:

    >>> iterables = 'mississippi', 'missouri'
    >>> list(intersect_generators(*iterables))
    ['m', 'i', 's']
    >>> list(intersect_generators(*iterables, allow_duplicates=True))
    ['m', 'i', 's', 's', 'i']

    :param iterables: page generators
    :param allow_duplicates: optional keyword argument to allow duplicates
        if present in all generators
    """
    # 'allow_duplicates' must be given as keyword argument
    if iterables and iterables[-1] in (True, False):
        allow_duplicates = iterables[-1]
        iterables = iterables[:-1]
        issue_deprecation_warning("'allow_duplicates' as positional argument",
                                  'keyword argument "allow_duplicates={}"'
                                  .format(allow_duplicates),
                                  since='6.4.0')

    # iterables must not be given as tuple or list
    if len(iterables) == 1 and isinstance(iterables[0], (list, tuple)):
        iterables = iterables[0]
        issue_deprecation_warning("'iterables' as list type",
                                  "consecutive iterables or use '*' to unpack",
                                  since='6.4.0')

    if not iterables:
        return

    if len(iterables) == 1:
        yield from iterables[0]
        return

    # If any generator is empty, no pages are going to be returned
    for source in iterables:
        if not source:
            debug('At least one generator ({!r}) is empty and execution was '
                  'skipped immediately.'.format(source), 'intersect')
            return

    # Item is cached to check that it is found n_gen
    # times before being yielded.
    cache = collections.defaultdict(collections.Counter)
    n_gen = len(iterables)

    # Class to keep track of alive threads.
    # Start new threads and remove completed threads.
    thrlist = ThreadList()

    for source in iterables:
        threaded_gen = ThreadedGenerator(name=repr(source), target=source)
        threaded_gen.daemon = True
        thrlist.append(threaded_gen)

    ones = collections.Counter(thrlist)
    seen = {}

    while True:
        # Get items from queues in a round-robin way.
        for t in thrlist:
            try:
                # TODO: evaluate if True and timeout is necessary.
                item = t.queue.get(True, 0.1)

                if not allow_duplicates and hash(item) in seen:
                    continue

                # Cache entry is a Counter of ThreadedGenerator objects.
                cache[item].update([t])
                if len(cache[item]) == n_gen:
                    if allow_duplicates:
                        yield item
                        # Remove item from cache if possible.
                        if all(el == 1 for el in cache[item].values()):
                            cache.pop(item)
                        else:
                            cache[item] -= ones
                    else:
                        yield item
                        cache.pop(item)
                        seen[hash(item)] = True

                active = thrlist.active_count()
                max_cache = n_gen
                if cache.values():
                    max_cache = max(len(v) for v in cache.values())
                # No. of active threads is not enough to reach n_gen.
                # We can quit even if some thread is still active.
                # There could be an item in all generators which has not yet
                # appeared from any generator. Only when we have lost one
                # generator, then we can bail out early based on seen items.
                if active < n_gen and n_gen - max_cache > active:
                    thrlist.stop_all()
                    return
            except queue.Empty:
                pass
            except KeyboardInterrupt:
                thrlist.stop_all()
            # All threads are done.
            if thrlist.active_count() == 0:
                return


def roundrobin_generators(*iterables):
    """Yield simultaneous from each iterable.

    Sample:

    >>> tuple(roundrobin_generators('ABC', range(5)))
    ('A', 0, 'B', 1, 'C', 2, 3, 4)

    *New in version 3.0.*

    :param iterables: any iterable to combine in roundrobin way
    :type iterables: iterable
    :return: the combined generator of iterables
    :rtype: generator
    """
    sentinel = object()
    return (item
            for item in itertools.chain.from_iterable(
                zip_longest(*iterables, fillvalue=sentinel))
            if item is not sentinel)


def filter_unique(iterable, container=None, key=None, add=None):
    """
    Yield unique items from an iterable, omitting duplicates.

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

    Note: This is not thread safe.

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
            def container_add(x):
                container.add(key(x) if key else x)

            add = container_add
        else:
            def container_setitem(x):
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


class CombinedError(KeyError, IndexError):

    """An error that gets caught by both KeyError and IndexError."""


class EmptyDefault(str, Mapping):

    """
    A default for a not existing siteinfo property.

    It should be chosen if there is no better default known. It acts like an
    empty collections, so it can be iterated through it safely if treated as a
    list, tuple, set or dictionary. It is also basically an empty string.

    Accessing a value via __getitem__ will result in a combined KeyError and
    IndexError.
    """

    def __init__(self):
        """Initialise the default as an empty string."""
        str.__init__(self)

    def __iter__(self):
        """An iterator which does nothing and drops the argument."""
        return iter(())

    def __getitem__(self, key):
        """Raise always a :py:obj:`CombinedError`."""
        raise CombinedError(key)


EMPTY_DEFAULT = EmptyDefault()


class SelfCallMixin:

    """
    Return self when called.

    When '_own_desc' is defined it'll also issue a deprecation warning using
    issue_deprecation_warning('Calling ' + _own_desc, 'it directly').
    """

    def __call__(self):
        """Do nothing and just return itself."""
        issue_deprecation_warning('Referencing this attribute like a function',
                                  'it directly', since='20210420')

        return self


class SelfCallDict(SelfCallMixin, dict):

    """Dict with SelfCallMixin."""


class SelfCallString(SelfCallMixin, str):

    """String with SelfCallMixin."""


class DequeGenerator(Iterator, collections.deque):

    """A generator that allows items to be added during generating."""

    def __next__(self):
        """Iterator method."""
        if self:
            return self.popleft()
        raise StopIteration

    def __repr__(self):
        """Provide an object representation without clearing the content."""
        items = list(self)
        result = '{}({})'.format(self.__class__.__name__, items)
        self.extend(items)
        return result


def open_archive(filename, mode='rb', use_extension=True):
    """
    Open a file and uncompress it if needed.

    This function supports bzip2, gzip, 7zip, lzma, and xz as compression
    containers. It uses the packages available in the standard library for
    bzip2, gzip, lzma, and xz so they are always available. 7zip is only
    available when a 7za program is available and only supports reading
    from it.

    The compression is either selected via the magic number or file ending.

    :param filename: The filename.
    :type filename: str
    :param use_extension: Use the file extension instead of the magic number
        to determine the type of compression (default True). Must be True when
        writing or appending.
    :type use_extension: bool
    :param mode: The mode in which the file should be opened. It may either be
        'r', 'rb', 'a', 'ab', 'w' or 'wb'. All modes open the file in binary
        mode. It defaults to 'rb'.
    :type mode: str
    :raises ValueError: When 7za is not available or the opening mode is
        unknown or it tries to write a 7z archive.
    :raises FileNotFoundError: When the filename doesn't exist and it tries
        to read from it or it tries to determine the compression algorithm.
    :raises OSError: When it's not a 7z archive but the file extension is 7z.
        It is also raised by bz2 when its content is invalid. gzip does not
        immediately raise that error but only on reading it.
    :raises lzma.LZMAError: When error occurs during compression or
        decompression or when initializing the state with lzma or xz.
    :raises ImportError: When file is compressed with bz2 but neither bz2 nor
        bz2file is importable, or when file is compressed with lzma or xz but
        lzma is not importable.
    :return: A file-like object returning the uncompressed data in binary mode.
    :rtype: file-like object
    """
    # extension_map maps magic_number to extension.
    # Unfortunately, legacy LZMA container has no magic number
    extension_map = {
        b'BZh': 'bz2',
        b'\x1F\x8B\x08': 'gz',
        b"7z\xBC\xAF'\x1C": '7z',
        b'\xFD7zXZ\x00': 'xz',
    }

    if mode in ('r', 'a', 'w'):
        mode += 'b'
    elif mode not in ('rb', 'ab', 'wb'):
        raise ValueError('Invalid mode: "{}"'.format(mode))

    if use_extension:
        # if '.' not in filename, it'll be 1 character long but otherwise
        # contain the period
        extension = filename[filename.rfind('.'):][1:]
    else:
        if mode != 'rb':
            raise ValueError('Magic number detection only when reading')
        with open(filename, 'rb') as f:
            magic_number = f.read(8)

        for pattern in extension_map:
            if magic_number.startswith(pattern):
                extension = extension_map[pattern]
                break
        else:
            extension = ''

    if extension == 'bz2':
        if isinstance(bz2, ImportError):
            raise bz2
        return bz2.BZ2File(filename, mode)

    if extension == 'gz':
        return gzip.open(filename, mode)

    if extension == '7z':
        if mode != 'rb':
            raise NotImplementedError('It is not possible to write a 7z file.')

        try:
            process = subprocess.Popen(['7za', 'e', '-bd', '-so', filename],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       bufsize=65535)
        except OSError:
            raise ValueError('7za is not installed or cannot '
                             'uncompress "{}"'.format(filename))
        else:
            stderr = process.stderr.read()
            process.stderr.close()
            if stderr != b'':
                process.stdout.close()
                raise OSError(
                    'Unexpected STDERR output from 7za {}'.format(stderr))
            return process.stdout

    if extension in ('lzma', 'xz'):
        if isinstance(lzma, ImportError):
            raise lzma
        lzma_fmts = {'lzma': lzma.FORMAT_ALONE, 'xz': lzma.FORMAT_XZ}
        return lzma.open(filename, mode, format=lzma_fmts[extension])

    # assume it's an uncompressed file
    return open(filename, 'rb')


def merge_unique_dicts(*args, **kwargs):
    """
    Return a merged dict and make sure that the original dicts keys are unique.

    The positional arguments are the dictionaries to be merged. It is also
    possible to define an additional dict using the keyword arguments.
    """
    args = list(args) + [dict(kwargs)]
    conflicts = set()
    result = {}
    for arg in args:
        conflicts |= set(arg.keys()) & set(result.keys())
        result.update(arg)
    if conflicts:
        raise ValueError('Multiple dicts contain the same keys: {}'
                         .format(', '.join(sorted(str(key)
                                                  for key in conflicts))))
    return result


def file_mode_checker(filename: str, mode=0o600, quiet=False, create=False):
    """Check file mode and update it, if needed.

    :param filename: filename path
    :param mode: requested file mode
    :type mode: int
    :param quiet: warn about file mode change if False.
    :type quiet: bool
    :param create: create the file if it does not exist already
    :type create: bool
    :raise IOError: The file does not exist and `create` is False.
    """
    try:
        st_mode = os.stat(filename).st_mode
    except OSError:  # file does not exist
        if not create:
            raise
        os.close(os.open(filename, os.O_CREAT | os.O_EXCL, mode))
        return

    warn_str = 'File {0} had {1:o} mode; converted to {2:o} mode.'
    if stat.S_ISREG(st_mode) and (st_mode - stat.S_IFREG != mode):
        os.chmod(filename, mode)
        # re-read and check changes
        if os.stat(filename).st_mode != st_mode and not quiet:
            warn(warn_str.format(filename, st_mode - stat.S_IFREG, mode))


def compute_file_hash(filename: str, sha='sha1', bytes_to_read=None):
    """Compute file hash.

    Result is expressed as hexdigest().

    :param filename: filename path
    :param sha: hashing function among the following in hashlib:
        md5(), sha1(), sha224(), sha256(), sha384(), and sha512()
        function name shall be passed as string, e.g. 'sha1'.
    :type sha: str
    :param bytes_to_read: only the first bytes_to_read will be considered;
        if file size is smaller, the whole file will be considered.
    :type bytes_to_read: None or int

    """
    size = os.path.getsize(filename)
    if bytes_to_read is None:
        bytes_to_read = size
    else:
        bytes_to_read = min(bytes_to_read, size)
    step = 1 << 20

    shas = ['md5', 'sha1', 'sha224', 'sha256', 'sha384', 'sha512']
    assert sha in shas
    sha = getattr(hashlib, sha)()  # sha instance

    with open(filename, 'rb') as f:
        while bytes_to_read > 0:
            read_bytes = f.read(min(bytes_to_read, step))
            assert read_bytes  # make sure we actually read bytes
            bytes_to_read -= len(read_bytes)
            sha.update(read_bytes)
    return sha.hexdigest()

# deprecated parts ############################################################


@deprecated('bot_choice.Option and its subclasses', since='20181217')
def concat_options(message, line_length, options):
    """DEPRECATED. Concatenate options."""
    indent = len(message) + 2
    line_length -= indent
    option_msg = ''
    option_line = ''
    for option in options:
        if option_line:
            option_line += ', '
        # +1 for ','
        if len(option_line) + len(option) + 1 > line_length:
            if option_msg:
                option_msg += '\n' + ' ' * indent
            option_msg += option_line[:-1]  # remove space
            option_line = ''
        option_line += option
    if option_line:
        if option_msg:
            option_msg += '\n' + ' ' * indent
        option_msg += option_line
    return '{} ({}):'.format(message, option_msg)


wrapper = ModuleDeprecationWrapper(__name__)
wrapper.add_deprecated_attr('empty_iterator', replacement_name='iter(())',
                            since='20220422')
wrapper.add_deprecated_attr('DotReadableDict', replacement_name='',
                            since='20210416')
wrapper.add_deprecated_attr('frozenmap',
                            replacement_name='types.MappingProxyType',
                            since='20210415')
wrapper.add_deprecated_attr('LazyRegex', replacement_name='',
                            since='20210418')
wrapper.add_deprecated_attr('DeprecatedRegex', replacement_name='',
                            since='20210418')


is_IP = redirect_func(is_ip_address, old_name='is_IP',  # noqa N816
                      since='20210418')
