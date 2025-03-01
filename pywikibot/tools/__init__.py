"""Miscellaneous helper functions (not wiki-dependent)."""
#
# (C) Pywikibot team, 2008-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import abc
import bz2
import gzip
import hashlib
import importlib.metadata
import ipaddress
import lzma
import os
import re
import stat
import subprocess
from contextlib import suppress
from functools import total_ordering, wraps
from types import TracebackType
from typing import Any
from warnings import catch_warnings, showwarning, warn

import packaging.version

import pywikibot  # T306760
from pywikibot.backports import PYTHON_VERSION, SPHINX_RUNNING, Callable
from pywikibot.tools._deprecate import (
    ModuleDeprecationWrapper,
    add_decorated_full_name,
    add_full_name,
    deprecate_arg,
    deprecate_positionals,
    deprecated,
    deprecated_args,
    get_wrapper_depth,
    issue_deprecation_warning,
    manage_wrapping,
    redirect_func,
    remove_last_args,
)
from pywikibot.tools._unidata import _first_upper_exception


__all__ = (
    # deprecating functions
    'ModuleDeprecationWrapper',
    'add_decorated_full_name',
    'add_full_name',
    'deprecate_arg',
    'deprecate_positionals',
    'deprecated',
    'deprecated_args',
    'get_wrapper_depth',
    'issue_deprecation_warning',
    'manage_wrapping',
    'redirect_func',
    'remove_last_args',

    # other tools
    'PYTHON_VERSION',
    'SPHINX_RUNNING',
    'as_filename',
    'is_ip_address',
    'is_ip_network',
    'has_module',
    'classproperty',
    'suppress_warnings',
    'ComparableMixin',
    'first_lower',
    'first_upper',
    'strtobool',
    'normalize_username',
    'MediaWikiVersion',
    'open_archive',
    'merge_unique_dicts',
    'file_mode_checker',
    'compute_file_hash',
    'cached',
)


def is_ip_address(value: str) -> bool:
    """Check if a value is a valid IPv4 or IPv6 address.

    .. versionadded:: 6.1
       Was renamed from ``is_IP()``.

    :param value: value to check
    """
    with suppress(ValueError):
        ipaddress.ip_address(value)
        return True

    return False


def is_ip_network(value: str) -> bool:
    """Check if a value is a valid range of IPv4 or IPv6 addresses.

    .. versionadded:: 9.0

    :param value: value to check
    """
    with suppress(ValueError):
        ipaddress.ip_network(value)
        return True

    return False


def has_module(module: str, version: str | None = None) -> bool:
    """Check if a module can be imported.

    .. versionadded:: 3.0

    .. versionchanged:: 6.1
       Dependency of distutils was dropped because the package will be
       removed with Python 3.12.
    """
    try:
        metadata_version = importlib.metadata.version(module)
    except importlib.metadata.PackageNotFoundError:
        return False
    if version:

        required_version = packaging.version.Version(version)
        module_version = packaging.version.Version(metadata_version)

        if module_version < required_version:
            warn(f'Module version {module_version} is lower than requested '
                 f'version {required_version}', ImportWarning)
            return False

    return True


class classproperty:  # noqa: N801

    """Descriptor class to access a class method as a property.

    This class may be used as a decorator::

        class Foo:

            _bar = 'baz'  # a class property

            @classproperty
            def bar(cls):  # a class property method
                return cls._bar

    Foo.bar gives 'baz'.

    .. versionadded:: 3.0
    """

    def __init__(self, cls_method) -> None:
        """Initializer: hold the class method and documentation."""
        self.method = cls_method
        self.__annotations__ = self.method.__annotations__
        doc = self.method.__doc__
        self.__doc__ = f':class:`classproperty<tools.classproperty>` {doc}'

        rtype = self.__annotations__.get('return')
        if rtype:
            lines = doc.splitlines()

            if len(lines) > 2 and PYTHON_VERSION < (3, 13):
                spaces = ' ' * re.search('[^ ]', lines[2]).start()
            else:
                spaces = ''

            self.__doc__ += f'\n\n{spaces}:rtype: {rtype}'

    def __get__(self, instance, owner):
        """Get the attribute of the owner class by its method."""
        if SPHINX_RUNNING:
            return self

        return self.method(owner)


class suppress_warnings(catch_warnings):  # noqa: N801

    """A decorator/context manager that temporarily suppresses warnings.

    Those suppressed warnings that do not match the parameters will be
    raised shown upon exit.

    .. versionadded:: 3.0
    """

    def __init__(
        self,
        message: str = '',
        category=Warning,
        filename: str = ''
    ) -> None:
        """Initialize the object.

        The parameter semantics are similar to those of
        `warnings.filterwarnings`.

        :param message: A string containing a regular expression that
            the start of the warning message must match.
            (case-insensitive)
        :param category: A class (a subclass of Warning) of which the
            warning category must be a subclass in order to match.
        :type category: type
        :param filename: A string containing a regular expression that
            the start of the path to the warning module must match.
            (case-sensitive)
        """
        self.message_match = re.compile(message, re.IGNORECASE).match
        self.category = category
        self.filename_match = re.compile(filename).match
        super().__init__(record=True)

    def __enter__(self) -> None:
        """Catch all warnings and store them in `self.log`."""
        self.log = super().__enter__()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None
    ) -> None:
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
class ComparableMixin(abc.ABC):

    """Mixin class to allow comparing to other objects which are comparable.

    .. versionadded:: 3.0
    """

    @abc.abstractmethod
    def _cmpkey(self) -> Any:
        """Abstract method to return key for comparison of objects.

        This ensures that ``_cmpkey`` method is defined in subclass.

        .. versionadded:: 8.1.2
        """

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


def first_lower(string: str) -> str:
    """Return a string with the first character uncapitalized.

    Empty strings are supported. The original string is not changed.

    **Example**:

    >>> first_lower('Hello World')
    'hello World'

    .. versionadded:: 3.0
    """
    return string[:1].lower() + string[1:]


def first_upper(string: str) -> str:
    """Return a string with the first character capitalized.

    Empty strings are supported. The original string is not changed.

    **Example**:

    >>> first_upper('hello World')
    'Hello World'

    .. versionadded:: 3.0
    .. note:: MediaWiki doesn't capitalize some characters the same way
       as Python. This function tries to be close to MediaWiki's
       capitalize function in title.php. See :phab:`T179115` and
       :phab:`T200357`.
    """
    first = string[:1]
    return (_first_upper_exception(first) or first.upper()) + string[1:]


def as_filename(string: str, repl: str = '_') -> str:
    r"""Return a string with characters are valid for filenames.

    Replace characters that are not possible in file names on some
    systems, but still are valid in MediaWiki titles:

        - Unix: ``/``
        - MediaWiki: ``/:\\``
        - Windows: ``/:\\"?*``

    Spaces are possible on most systems, but are bad for URLs.

    **Example**:

    >>> as_filename('How are you?')
    'How_are_you_'
    >>> as_filename('Say: "Hello"')
    'Say___Hello_'
    >>> as_filename('foo*bar', '')
    'foobar'
    >>> as_filename('foo', 'bar')
    Traceback (most recent call last):
    ...
    ValueError: Invalid repl parameter 'bar'
    >>> as_filename('foo', '?')
    Traceback (most recent call last):
    ...
    ValueError: Invalid repl parameter '?'

    .. versionadded:: 8.0

    :param string: the string to be modified
    :param repl: the replacement character
    :raises ValueError: Invalid repl parameter
    """
    pattern = r':*?/\\" '
    if len(repl) > 1 or len(repl) == 1 and repl in pattern:
        raise ValueError(f'Invalid repl parameter {repl!r}')
    return re.sub(f'[{pattern}]', repl, string)


def strtobool(val: str) -> bool:
    """Convert a string representation of truth to True or False.

    This is a reimplementation of distutils.util.strtobool due to
    :pep:`632#Migration Advice`

    **Example**:

    >>> strtobool('yes')
    True
    >>> strtobool('Off')
    False
    >>> strtobool('aye')
    Traceback (most recent call last):
    ...
    ValueError: invalid truth value 'aye'

    .. versionadded:: 7.1

    :param val: True values are 'y', 'yes', 't', 'true', 'on', and '1';
        false values are 'n', 'no', 'f', 'false', 'off', and '0'.
    :raises ValueError: `val` is not a valid truth value
    """
    val = val.lower()
    if val in ('y', 'yes', 't', 'true', 'on', '1'):
        return True
    if val in ('n', 'no', 'f', 'false', 'off', '0'):
        return False
    raise ValueError(f'invalid truth value {val!r}')


def normalize_username(username) -> str | None:
    """Normalize the username.

    .. versionadded:: 3.0
    """
    if not username:
        return None
    username = re.sub('[_ ]+', ' ', username).strip()
    return first_upper(username)


@total_ordering
class MediaWikiVersion:

    """Version object to allow comparing 'wmf' versions with normal ones.

    The version mainly consist of digits separated by periods. After
    that is a suffix which may only be 'wmf<number>', 'alpha',
    'beta<number>' or '-rc.<number>' (the - and . are optional). They
    are considered from old to new in that order with a version number
    without suffix is considered the newest. This secondary difference
    is stored in an internal _dev_version attribute.

    Two versions are equal if their normal version and dev version are
    equal. A version is greater if the normal version or dev version is
    greater. For example::

        1.34 < 1.34.1 < 1.35wmf1 < 1.35alpha < 1.35beta1 < 1.35beta2
        < 1.35-rc-1 < 1.35-rc.2 < 1.35

    Any other suffixes are considered invalid.

    .. versionadded:: 3.0

    .. versionchanged:: 6.1
       Dependency of distutils was dropped because the package will be
       removed with Python 3.12.
    """

    MEDIAWIKI_VERSION = re.compile(
        r'(\d+(?:\.\d+)+)(-?wmf\.?(\d+)|alpha|beta(\d+)|-?rc\.?(\d+)|.*)?')

    def __init__(self, version_str: str) -> None:
        """Initializer.

        :param version_str: version to parse
        """
        self._parse(version_str)

    def _parse(self, version_str: str) -> None:
        version_match = MediaWikiVersion.MEDIAWIKI_VERSION.fullmatch(
            version_str)

        if not version_match:
            raise ValueError(f'Invalid version number "{version_str}"')

        components = [int(n) for n in version_match[1].split('.')]

        # The _dev_version numbering scheme might change. E.g. if a stage
        # between 'alpha' and 'beta' is added, 'beta', 'rc' and stable releases
        # are reassigned (beta=3, rc=4, stable=5).

        if version_match[3]:  # wmf version
            self._dev_version = (0, int(version_match[3]))
        elif version_match[4]:
            self._dev_version = (2, int(version_match[4]))
        elif version_match[5]:
            self._dev_version = (3, int(version_match[5]))
        elif version_match[2] in ('alpha', '-alpha'):
            self._dev_version = (1, )
        else:
            for handled in ('wmf', 'alpha', 'beta', 'rc'):
                # if any of those pops up here our parser has failed
                assert handled not in version_match[2], \
                    f'Found "{handled}" in "{version_match[2]}"'
            if version_match[2]:
                pywikibot.logging.debug(
                    'Additional unused version part {version_match[2]!r}')
            self._dev_version = (4, )

        self.suffix = version_match[2] or ''
        self.version = tuple(components)

    @staticmethod
    def from_generator(generator: str) -> MediaWikiVersion:
        """Create instance from a site's generator attribute."""
        prefix = 'MediaWiki '

        if not generator.startswith(prefix):
            raise ValueError(f'Generator string ({generator!r}) must start '
                             f'with "{prefix}"')

        return MediaWikiVersion(generator[len(prefix):])

    def __str__(self) -> str:
        """Return version number with optional suffix."""
        return '.'.join(str(v) for v in self.version) + self.suffix

    def __repr__(self) -> str:
        """Return version number representation, mainly used by tests.

        .. versionadded:: 10.0

        """
        return f"'{self}'"

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
            raise TypeError(f"Comparison between 'MediaWikiVersion' and "
                            f"'{type(other).__name__}' unsupported")

        if self.version != other.version:
            return self.version < other.version
        return self._dev_version < other._dev_version


def open_archive(filename: str, mode: str = 'rb', use_extension: bool = True):
    """Open a file and uncompress it if needed.

    This function supports bzip2, gzip, 7zip, lzma, and xz as
    compression containers. It uses the packages available in the
    standard library for bzip2, gzip, lzma, and xz so they are always
    available. 7zip is only available when a 7za program is available
    and only supports reading from it.

    The compression is either selected via the magic number or file
    ending.

    .. versionadded:: 3.0

    :param filename: The filename.
    :param use_extension: Use the file extension instead of the magic
        number to determine the type of compression (default True). Must
        be True when writing or appending.
    :param mode: The mode in which the file should be opened. It may
        either be 'r', 'rb', 'a', 'ab', 'w' or 'wb'. All modes open the
        file in binary mode. It defaults to 'rb'.
    :raises ValueError: When 7za is not available or the opening mode is
        unknown or it tries to write a 7z archive.
    :raises FileNotFoundError: When the filename doesn't exist and it
        tries to read from it or it tries to determine the compression
        algorithm.
    :raises OSError: When it's not a 7z archive but the file extension
        is 7z. It is also raised by bz2 when its content is invalid.
        gzip does not immediately raise that error but only on reading
        it.
    :raises lzma.LZMAError: When error occurs during compression or
        decompression or when initializing the state with lzma or xz.
    :return: A file-like object returning the uncompressed data in
        binary mode.
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
        raise ValueError(f'Invalid mode: "{mode}"')

    if use_extension:
        # if '.' not in filename, it'll be 1 character long but otherwise
        # contain the period
        extension = filename[filename.rfind('.'):][1:]
    else:
        if mode != 'rb':
            raise ValueError('Magic number detection only when reading')
        with open(filename, 'rb') as f:
            magic_number = f.read(8)

        for pattern, ext in extension_map.items():
            if magic_number.startswith(pattern):
                extension = ext
                break
        else:
            extension = ''

    if extension == 'bz2':
        binary = bz2.BZ2File(filename, mode)

    elif extension == 'gz':
        binary = gzip.open(filename, mode)

    elif extension == '7z':
        if mode != 'rb':
            raise NotImplementedError('It is not possible to write a 7z file.')

        try:
            process = subprocess.Popen(['7za', 'e', '-bd', '-so', filename],
                                       stdout=subprocess.PIPE,
                                       stderr=subprocess.PIPE,
                                       bufsize=65535)
        except OSError:
            raise ValueError(
                f'7za is not installed or cannot uncompress "{filename}"')

        stderr = process.stderr.read()
        process.stderr.close()
        if stderr != b'':
            process.stdout.close()
            raise OSError(
                f'Unexpected STDERR output from 7za {stderr}')
        binary = process.stdout

    elif extension in ('lzma', 'xz'):
        lzma_fmts = {'lzma': lzma.FORMAT_ALONE, 'xz': lzma.FORMAT_XZ}
        binary = lzma.open(filename, mode, format=lzma_fmts[extension])

    else:  # assume it's an uncompressed file
        binary = open(filename, 'rb')

    return binary


def merge_unique_dicts(*args, **kwargs):
    """Return a merged dict and make sure that the original keys are unique.

    The positional arguments are the dictionaries to be merged. It is
    also possible to define an additional dict using the keyword
    arguments.

    .. versionadded:: 3.0
    """
    args = [*list(args), dict(kwargs)]
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


def file_mode_checker(
    filename: str,
    mode: int = 0o600,
    quiet: bool = False,
    create: bool = False
):
    """Check file mode and update it, if needed.

    .. versionadded:: 3.0

    :param filename: filename path
    :param mode: requested file mode
    :param quiet: warn about file mode change if False.
    :param create: create the file if it does not exist already
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


def compute_file_hash(filename: str | os.PathLike,
                      sha: str | Callable[[], Any] = 'sha1',
                      bytes_to_read: int | None = None) -> str:
    """Compute file hash.

    Result is expressed as hexdigest().

    .. versionadded:: 3.0
    .. versionchanged:: 8.2
       *sha* may be  also a hash constructor, or a callable that returns
       a hash object.


    :param filename: filename path
    :param sha: hash algorithm available with hashlib: ``sha1()``,
        ``sha224()``, ``sha256()``, ``sha384()``, ``sha512()``,
        ``blake2b()``, and ``blake2s()``. Additional algorithms like
        ``md5()``, ``sha3_224()``, ``sha3_256()``, ``sha3_384()``,
        ``sha3_512()``, ``shake_128()`` and ``shake_256()`` may also be
        available. *sha* must either be a hash algorithm name as a str
        like ``'sha1'`` (default), a hash constructor like
        ``hashlib.sha1``, or a callable that returns a hash object like
        ``lambda: hashlib.sha1()``.
    :param bytes_to_read: only the first bytes_to_read will be
        considered; if file size is smaller, the whole file will be
        considered.
    """
    with open(filename, 'rb') as f:
        if PYTHON_VERSION < (3, 11) or bytes_to_read is not None:
            digest = sha() if callable(sha) else hashlib.new(sha)
            size = os.path.getsize(filename)
            bytes_to_read = min(bytes_to_read or size, size)
            step = 1 << 20
            while bytes_to_read > 0:
                read_bytes = f.read(min(bytes_to_read, step))
                assert read_bytes  # make sure we actually read bytes
                bytes_to_read -= len(read_bytes)
                digest.update(read_bytes)
        else:
            digest = hashlib.file_digest(f, sha)

    return digest.hexdigest()


def cached(*arg: Callable) -> Any:
    """Decorator to cache information of an object.

    The wrapper adds an attribute to the instance which holds the result
    of the decorated method. The attribute's name is the method name
    with preleading underscore.

    Usage::

        @cached
        def this_method(self)

        @cached
        def that_method(self, force=False)

    No parameter may be used with this decorator. Only a force parameter
    may be used with the decorated method. All other parameters are
    discarded and lead to a TypeError.

    .. note:: A property must be decorated on top of the property method
       below other decorators. This decorator must not be used with
       functions.
    .. versionadded:: 7.3

    :raises TypeError: decorator must be used without arguments
    """
    fn = arg and arg[0]
    if not callable(fn):
        raise TypeError(
            '"cached" decorator must be used without arguments.') from None

    @wraps(fn)
    def wrapper(obj: object, *, force=False) -> Any:
        cache_name = '_' + fn.__name__
        if force:
            with suppress(AttributeError):
                delattr(obj, cache_name)
        try:
            return getattr(obj, cache_name)
        except AttributeError:
            val = fn(obj)
            setattr(obj, cache_name, val)
            return val

    return wrapper
