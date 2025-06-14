#!/usr/bin/env python3
r"""This script runs commands on each entry in the API caches.

Syntax:

    python pwb.py cache [-password] [-delete] [-c "..."] [-o "..."] [dir ...]

If no directory are specified, it will detect the API caches.

If no command is specified, it will print the filename of all entries.
If only -delete is specified, it will delete all entries.

The following parameters are supported:

-delete           Delete each command filtered. If that option is set the
                  default output will be nothing.

-c                Filter command in python syntax. It must evaluate to True to
                  output anything.

-o                Output command which is output when the filter evaluated to
                  True. If it returns None it won't output anything.

Examples
--------

  Print the filename of any entry with 'wikidata' in the key:

    -c "wikidata" in entry._uniquedescriptionstr()

  Customised output if the site code is 'ar':

    -c entry.site.code == "ar"
    -o uniquedesc(entry)

  Or the state of the login:

    -c entry.site._loginstatus == LoginStatus.NOT_ATTEMPTED
    -o uniquedesc(entry)

  If the function only uses one parameter for the entry it can be omitted:

    -c has_password
    -o uniquedesc

Available filter commands:

    has_password(entry)
    is_logout(entry)
    empty_response(entry)
    not_accessed(entry)
    incorrect_hash(entry)
    older_than_one_day(entry)
    recent(entry)

There are helper functions which can be part of a command:

    older_than(entry, interval)
    newer_than(entry, interval)

Available output commands:

    uniquedesc(entry)
"""
#
# (C) Pywikibot team, 2014-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import datetime
import hashlib
import os
import pickle
import sys
from pathlib import Path
from random import sample

import pywikibot
from pywikibot.data import api

# The follow attributes are used by eval()
from pywikibot.login import LoginStatus  # noqa: F401
from pywikibot.page import User  # noqa: F401
from pywikibot.site import APISite, ClosedSite, DataSite  # noqa: F401
from pywikibot.tools import PYTHON_VERSION


class ParseError(Exception):

    """Error parsing."""


class CacheEntry(api.CachedRequest):

    """A Request cache entry."""

    def __init__(self, directory: str, filename: str) -> None:
        """Initializer."""
        self.directory = directory
        self.filename = filename

    def __str__(self) -> str:
        """Return string equivalent of object."""
        return self.filename

    def __repr__(self) -> str:
        """Representation of object."""
        return str(self._cachefile_path())

    def _create_file_name(self):
        """Filename of the cached entry."""
        return self.filename

    def _get_cache_dir(self) -> Path:
        """Directory of the cached entry.

        .. versionchanged:: 8.0
           return a `pathlib.Path` object.
        """
        return Path(self.directory)

    def _cachefile_path(self) -> Path:
        """Return cache file path.

        .. versionchanged:: 8.0
           return a `pathlib.Path` object.
        """
        return self._get_cache_dir() / self._create_file_name()

    def _load_cache(self) -> bool:
        """Load the cache entry."""
        with self._cachefile_path().open('rb') as f:
            self.key, self._data, self._cachetime = pickle.load(f)
        return True

    def parse_key(self):
        """Parse the key loaded from the cache entry."""
        # find the start of the first parameter
        start = self.key.index('(')
        # find the end of the first object
        end = self.key.index(')')

        if not end:
            raise ParseError(f'End of Site() keyword not found: {self.key}')

        if 'Site' not in self.key[0:start]:
            raise ParseError(
                f'Site() keyword not found at start of key: {self.key}')

        site = self.key[0:end + 1]
        if site[0:5] == 'Site(':
            site = 'APISite(' + site[5:]

        username = None
        login_status = None

        start = end + 1
        if self.key[start:start + 5] == 'User(':
            # The addition of user to the cache key used:
            #   repr(User)
            # which includes namespaces resulting in:
            #   User(User:<username>)
            # This also accepts User(<username>)
            if self.key[start:start + 10] == 'User(User:':
                start += 10
            else:
                start += 5

            end = self.key.index(')', start + 5)
            if not end:
                raise ParseError(
                    f'End of User() keyword not found: {self.key}')
            username = self.key[start:end]
        elif self.key[start:start + 12] == 'LoginStatus(':
            end = self.key.index(')', start + 12)
            if not end:
                raise ParseError(
                    f'End of LoginStatus() keyword not found: {self.key}')
            login_status = self.key[start:end + 1]
        # If the key does not contain User(..) or LoginStatus(..),
        # it must be the old key format which only contains Site and params
        elif self.key[start:start + 3] != "[('":
            raise ParseError(
                f'Keyword after Site not recognised: {self.key}...')

        start = end + 1

        params = self.key[start:]

        self._parsed_key = (site, username, login_status, params)
        return self._parsed_key

    def _rebuild(self) -> None:
        """Reconstruct the original Request from the key."""
        if hasattr(self, '_parsed_key'):
            (site, username, login_status, params) = self._parsed_key
        else:
            (site, username, login_status, params) = self.parse_key()
        if not site:
            raise ParseError('No Site')
        self.site = eval(site)
        if login_status:
            self.site._loginstatus = eval(login_status)
        if username:
            self.site._username = username
        if not params:
            raise ParseError('No request params')
        self._params = {}
        for key, value in eval(params):
            if isinstance(value, bytes):
                value = value.decode(self.site.encoding())
            self._params[key] = value.split('|')

    def _delete(self) -> None:
        """Delete the cache entry."""
        self._cachefile_path().unlink()


def process_entries(cache_path, func, use_accesstime: bool | None = None,
                    output_func=None, action_func=None, *,
                    tests: int | None = None) -> None:
    """Check the contents of the cache.

    This program tries to use file access times to determine whether
    cache files are being used. However file access times are not always
    usable. On many modern filesystems, they have been disabled. On Unix,
    check the filesystem mount options. You may need to remount with
    'strictatime'.

    .. versionchanged:: 9.0
       default cache path to 'apicache' without Python main version.

    :param use_accesstime: Whether access times should be used. `None`
        for detect, `False` for don't use and `True` for always use.
    :param tests: Only process a test sample of files
    """
    if not cache_path:
        cache_path = os.path.join(pywikibot.config.base_dir, 'apicache')

    if not os.path.exists(cache_path):
        pywikibot.error(f'{cache_path}: no such file or directory')
        return

    if os.path.isdir(cache_path):
        filenames = [os.path.join(cache_path, filename)
                     for filename in os.listdir(cache_path)]
    else:
        filenames = [cache_path]

    if tests:
        filenames = sample(filenames, min(len(filenames), tests))

    for filepath in filenames:
        filename = os.path.basename(filepath)
        cache_dir = os.path.dirname(filepath)
        if use_accesstime is not False:
            stinfo = os.stat(filepath)

        entry = CacheEntry(cache_dir, filename)

        # Deletion is chosen only, abbreviate this request
        if func is None and output_func is None \
           and action_func == CacheEntry._delete:
            action_func(entry)
            continue

        # Skip foreign python specific directory
        *_, version = cache_path.partition('-')
        if version and version[-1] != str(PYTHON_VERSION[0]):
            pywikibot.error(f"Skipping {cache_path} directory, can't read "
                            f'content with python {PYTHON_VERSION[0]}')
            continue

        try:
            entry._load_cache()
        except ValueError:
            pywikibot.error(f'Failed loading {entry._cachefile_path()}')
            pywikibot.exception()
            continue

        if use_accesstime is None:
            stinfo2 = os.stat(filepath)
            use_accesstime = stinfo.st_atime != stinfo2.st_atime

        if use_accesstime:
            # Reset access times to values before loading cache entry.
            os.utime(filepath, (stinfo.st_atime, stinfo.st_mtime))
            entry.stinfo = stinfo

        try:
            entry.parse_key()
        except ParseError as e:
            pywikibot.error(
                f'Problems parsing {entry.filename} with key {entry.key}')
            pywikibot.error(e)
            continue

        try:
            entry._rebuild()
        except Exception:
            pywikibot.error(f'Problems loading {entry.filename} with key '
                            f'{entry.key}, {entry._parsed_key!r}')
            pywikibot.exception()
            continue

        if func is None or func(entry):
            if output_func or action_func is None:
                output = entry if output_func is None else output_func(entry)
                if output is not None:
                    pywikibot.info(output)
            if action_func:
                action_func(entry)


def _parse_command(command, name):
    """Parse command."""
    obj = globals().get(command)
    if callable(obj):
        return obj

    try:
        return eval('lambda entry: ' + command)
    except Exception as e:
        pywikibot.error(e)
        pywikibot.error(
            f'Cannot compile {name} command: {command}')
        return None


# Filter commands

def has_password(entry):
    """Entry has a password in the entry."""
    return entry if 'lgpassword' in entry._uniquedescriptionstr() else None


def is_logout(entry):
    """Entry is a logout entry."""
    return entry if not entry._data and 'logout' in entry.key else None


def empty_response(entry):
    """Entry has no data."""
    return entry if not entry._data and 'logout' not in entry.key else None


def not_accessed(entry):
    """Entry has never been accessed."""
    if not hasattr(entry, 'stinfo'):
        return None

    if entry.stinfo.st_atime <= entry.stinfo.st_mtime:
        return entry

    return None


def incorrect_hash(entry):
    """Incorrect hash."""
    if hashlib.sha256(entry.key.encode('utf-8')).hexdigest() != entry.filename:
        return entry
    return None


def older_than(entry, interval):
    """Find older entries."""
    if entry._cachetime.tzinfo is not None \
       and entry._cachetime + interval < pywikibot.Timestamp.nowutc():
        return entry

    # old apicache-py2/3 cache
    if entry._cachetime.tzinfo is None \
       and entry._cachetime + interval < pywikibot.Timestamp.utcnow():
        return entry

    return None


def newer_than(entry, interval):
    """Find newer entries."""
    if entry._cachetime.tzinfo is not None \
       and entry._cachetime + interval >= pywikibot.Timestamp.nowutc():
        return entry

    # old apicache-py2/3 cache
    if entry._cachetime.tzinfo is None \
       and entry._cachetime + interval >= pywikibot.Timestamp.utcnow():
        return entry

    return None


def older_than_one_day(entry):
    """Find more than one day old entries."""
    if older_than(entry, datetime.timedelta(days=1)):
        return entry
    return None


def recent(entry):
    """Find entries newer than on hour."""
    return entry if newer_than(entry, datetime.timedelta(hours=1)) else None


# Output commands

def uniquedesc(entry):
    """Return the unique description string."""
    return entry._uniquedescriptionstr()


def parameters(entry):
    """Return a pretty formatted parameters list."""
    lines = ''
    for key, items in sorted(entry._params.items()):
        lines += f"{key}={', '.join(items)}\n"
    return lines


def main() -> None:
    """Process command line arguments and invoke bot."""
    local_args = pywikibot.handle_args()
    cache_paths = None
    delete = False
    command = None
    output = None

    for arg in local_args:
        if command == '':
            command = arg
        elif output == '':
            output = arg
        elif arg == '-delete':
            delete = True
        elif arg == '-password':
            command = 'has_password(entry)'
        elif arg == '-c':
            if command:
                sys.exit('Only one command may be executed.')
            command = ''
        elif arg == '-o':
            if output:
                sys.exit('Only one output may be defined.')
            output = ''
        elif not cache_paths:
            cache_paths = [arg]
        else:
            cache_paths.append(arg)

    if not cache_paths:
        folders = ('apicache', 'apicache-py2', 'apicache-py3')
        cache_paths = list(folders)
        # Add tests folders
        cache_paths += [os.path.join('tests', f) for f in folders]

        # Also process the base directory, if it isn't the current directory
        if os.path.abspath(os.getcwd()) != pywikibot.config.base_dir:
            cache_paths += [
                os.path.join(pywikibot.config.base_dir, f) for f in folders]

        # Also process the user home cache, if it isn't the config directory
        userpath = os.path.expanduser(os.path.join('~', '.pywikibot'))
        if userpath != pywikibot.config.base_dir:
            cache_paths += [
                os.path.join(userpath, f) for f in folders]

    action_func = CacheEntry._delete if delete else None

    if output:
        output_func = _parse_command(output, 'output')
        if output_func is None:
            return
    else:
        output_func = None

    if command:
        filter_func = _parse_command(command, 'filter')
        if filter_func is None:
            return
    else:
        filter_func = None

    for cache_path in cache_paths:
        if len(cache_paths) > 1:
            pywikibot.info(f'Processing {cache_path}')
        process_entries(cache_path, filter_func, output_func=output_func,
                        action_func=action_func)


if __name__ == '__main__':
    main()
