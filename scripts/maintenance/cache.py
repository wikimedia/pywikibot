#!/usr/bin/python
# -*- coding: utf-8  -*-
r"""
This script runs commands on each entry in the API caches.

Syntax: cache.py [-password] [-delete] [-c '...'] [dir ...]

If no directory are specified, it will detect the API caches.

If no command is specified, it will print the filename of all entries.
If only -delete is specified, it will delete all entries.

The option '-c' must be followed by a command in python syntax.

Example commands:
  Print the filename of any entry with 'wikidata' in the key:

    entry if "wikidata" in entry._uniquedescriptionstr() else None

  Customised output if the site code is 'ar':

    entry.site.code == "ar" and print("%s" % entry._uniquedescriptionstr())

  Or the state of the login
    entry.site._loginstatus == LoginStatus.NOT_ATTEMPTED and \
print("%s" % entry._uniquedescriptionstr())

  These functions can be used as a command:
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
"""
#
# (C) Pywikibot team, 2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import print_function, unicode_literals
__version__ = '$Id$'
#

import os
import datetime
import pickle
import hashlib
import pywikibot
from pywikibot.data import api

from pywikibot.site import APISite, DataSite, LoginStatus  # noqa
from pywikibot.page import User  # noqa


class ParseError(Exception):

    """Error parsing."""


class CacheEntry(api.CachedRequest):

    """A Request cache entry."""

    def __init__(self, directory, filename):
        """Constructor."""
        self.directory = directory
        self.filename = filename

    def __str__(self):
        return self.filename

    def __repr__(self):
        return self._cachefile_path()

    def _create_file_name(self):
        """Filename of the cached entry."""
        return self.filename

    def _get_cache_dir(self):
        """Directory of the cached entry."""
        return self.directory

    def _cachefile_path(self):
        return os.path.join(self._get_cache_dir(),
                            self._create_file_name())

    def _load_cache(self):
        """Load the cache entry."""
        with open(self._cachefile_path(), 'rb') as f:
            self.key, self._data, self._cachetime = pickle.load(f)
        return True

    def parse_key(self):
        """Parse the key loaded from the cache entry."""
        # find the start of the first parameter
        start = self.key.index('(')
        # find the end of the first object
        end = self.key.index(')')

        if not end:
            raise ParseError('End of Site() keyword not found: %s' % self.key)

        if 'Site' not in self.key[0:start]:
            raise ParseError('Site() keyword not found at start of key: %s'
                             % self.key)

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
                raise ParseError('End of User() keyword not found: %s'
                                 % self.key)
            username = self.key[start:end]
        elif self.key[start:start + 12] == 'LoginStatus(':
            end = self.key.index(')', start + 12)
            if not end:
                raise ParseError('End of LoginStatus() keyword not found: %s'
                                 % self.key)
            login_status = self.key[start:end + 1]
        # If the key does not contain User(..) or LoginStatus(..),
        # it must be the old key format which only contains Site and params
        elif self.key[start:start + 3] != "[('":
            raise ParseError('Keyword after Site not recognised: %s...'
                             % self.key)

        start = end + 1

        params = self.key[start:]

        self._parsed_key = (site, username, login_status, params)
        return self._parsed_key

    def _rebuild(self):
        """Reconstruct the original Request from the key."""
        if hasattr(self, '_parsed_key'):
            (site, username, login_status, params) = self._parsed_key
        else:
            (site, username, login_status, params) = self.parse_key()
        if not site:
            raise ParseError('No Site')
        self.site = eval(site)
        if login_status:
            self.site._loginstatus = eval('LoginStatus.%s'
                                          % login_status[12:-1])
        if username:
            self.site._username = [username, username]
        if not params:
            raise ParseError('No request params')
        self._params = dict(eval(params))

    def _delete(self):
        """Delete the cache entry."""
        os.remove(self._cachefile_path())


def process_entries(cache_path, func, use_accesstime=None):
    """
    Check the contents of the cache.

    This program tries to use file access times to determine
    whether cache files are being used.
    However file access times are not always usable.
    On many modern filesystems, they have been disabled.
    On unix, check the filesystem mount options.  You may
    need to remount with 'strictatime'.

    @param use_accesstime: Whether access times should be used.
    @type use_accesstime: bool tristate:
         - None  = detect
         - False = dont use
         - True  = always use
    """
    if not cache_path:
        cache_path = os.path.join(pywikibot.config2.base_dir, 'apicache')

    if not os.path.exists(cache_path):
        pywikibot.error('%s: no such file or directory' % cache_path)
        return

    if os.path.isdir(cache_path):
        filenames = [os.path.join(cache_path, filename)
                     for filename in os.listdir(cache_path)]
    else:
        filenames = [cache_path]

    for filepath in filenames:
        filename = os.path.basename(filepath)
        cache_dir = os.path.dirname(filepath)
        if use_accesstime is not False:
            stinfo = os.stat(filepath)

        entry = CacheEntry(cache_dir, filename)
        try:
            entry._load_cache()
        except ValueError as e:
            print('Failed loading %s' % entry._cachefile_path())
            pywikibot.exception(e, tb=True)
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
        except ParseError:
            pywikibot.error(u'Problems parsing %s with key %s'
                            % (entry.filename, entry.key))
            pywikibot.exception()
            continue

        try:
            entry._rebuild()
        except Exception as e:
            pywikibot.error(u'Problems loading %s with key %s, %r'
                            % (entry.filename, entry.key, entry._parsed_key))
            pywikibot.exception(e, tb=True)
            continue

        func(entry)


def has_password(entry):
    """Entry has a password in the entry."""
    if 'lgpassword' in entry._uniquedescriptionstr():
        return entry


def is_logout(entry):
    """Entry is a logout entry."""
    if not entry._data and 'logout' in entry.key:
        return entry


def empty_response(entry):
    """Entry has no data."""
    if not entry._data and 'logout' not in entry.key:
        return entry


def not_accessed(entry):
    """Entry has never been accessed."""
    if not hasattr(entry, 'stinfo'):
        return

    if entry.stinfo.st_atime <= entry.stinfo.st_mtime:
        return entry


def incorrect_hash(entry):
    if hashlib.sha256(entry.key.encode('utf-8')).hexdigest() != entry.filename:
        return entry


def older_than(entry, interval):
    if entry._cachetime + interval < datetime.datetime.now():
        return entry


def newer_than(entry, interval):
    if entry._cachetime + interval >= datetime.datetime.now():
        return entry


def older_than_one_day(entry):
    if older_than(entry, datetime.timedelta(days=1)):
        return entry


def recent(entry):
    if newer_than(entry, datetime.timedelta(hours=1)):
        return entry


def main():
    local_args = pywikibot.handleArgs()
    cache_paths = None
    delete = False
    command = None

    for arg in local_args:
        if command == '':
            command = arg
        elif arg == '-delete':
            delete = True
        elif arg == '-password':
            command = 'has_password(entry)'
        elif arg == '-c':
            if command:
                pywikibot.error('Only one command may be executed.')
                exit(1)
            command = ''
        else:
            if not cache_paths:
                cache_paths = [arg]
            else:
                cache_paths.append(arg)

    func = None

    if not cache_paths:
        cache_paths = ['apicache', 'tests/apicache']

        # Also process the base directory, if it isnt the current directory
        if os.path.abspath(os.getcwd()) != pywikibot.config2.base_dir:
            cache_paths += [
                os.path.join(pywikibot.config2.base_dir, 'apicache')]

        # Also process the user home cache, if it isnt the config directory
        if os.path.expanduser('~/.pywikibot') != pywikibot.config2.base_dir:
            cache_paths += [
                os.path.join(os.path.expanduser('~/.pywikibot'), 'apicache')]

    if delete:
        action_func = lambda entry: entry._delete()
    else:
        action_func = lambda entry: pywikibot.output(entry)

    if command:
        try:
            command_func = eval('lambda entry: ' + command)
        except:
            pywikibot.exception()
            pywikibot.error(u'Can not compile command: %s' % command)
            exit(1)

        func = lambda entry: command_func(entry) and action_func(entry)
    else:
        func = action_func

    for cache_path in cache_paths:
        if len(cache_paths) > 1:
            pywikibot.output(u'Processing %s' % cache_path)
        process_entries(cache_path, func)

if __name__ == '__main__':
    main()
