#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Wrapper around djvulibre to access djvu files properties and content."""
#
# (C) Pywikibot team, 2015-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

from collections import Counter
import os
import re
import subprocess

import pywikibot

from pywikibot.tools import (
    deprecated, deprecated_args,
    StringTypes,
    UnicodeType,
)


def _call_cmd(args, lib='djvulibre'):
    """
    Tiny wrapper around subprocess.Popen().

    @param args: same as Popen()
    @type args: typing.Sequence[string]

    @param library: library to be logged in logging messages
    @type library: str

    @param log: log process output; errors are always logged.
    @type library: bool


    @return: returns a tuple (res, stdoutdata), where
        res is True if dp.returncode != 0 else False
    """
    if not isinstance(args, StringTypes):
        # upcast if any param in sequence args is not in StringTypes
        args = [str(a) if not isinstance(a, StringTypes) else a for a in args]
        cmd = ' '.join(args)
    else:
        cmd = args

    dp = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdoutdata, stderrdata = dp.communicate()

    if dp.returncode != 0:
        pywikibot.error('{0} error; {1}'.format(lib, cmd))
        pywikibot.error('{0}'.format(stderrdata))
        return (False, stdoutdata)

    pywikibot.log('SUCCESS: {0} (PID: {1})'.format(cmd, dp.pid))

    return (True, stdoutdata)


class DjVuFile(object):

    """Wrapper around djvulibre to access djvu files properties and content.

    Perform file existence checks.

    Control characters in djvu text-layer are converted for convenience
    (see http://djvu.sourceforge.net/doc/man/djvused.html for control chars
    details).

    """

    @deprecated_args(file_djvu='file')
    def __init__(self, file):
        """
        Initializer.

        @param file: filename (including path) to djvu file
        @type file: str
        """
        self._filename = file
        filename = os.path.expanduser(file)
        filename = os.path.abspath(filename)
        # Check file exists and has read permissions.
        with open(filename):
            self.file = filename
        self.dirname = os.path.dirname(filename)

        # pattern for parsing of djvudump output.
        self._pat_form = re.compile(
            r' *?FORM:DJVU *?\[\d+\] *?(?P<id>{[^\}]*?})? *?\[P(?P<n>\d+)\]')
        self._pat_info = re.compile(
            r'DjVu.*?(?P<size>\d+x\d+).*?(?P<dpi>\d+) dpi')

    def __repr__(self):
        """Return a more complete string representation."""
        filename = self._filename
        if not isinstance(filename, str):
            filename = self._filename.encode('utf-8')
        return str("{0}.{1}('{2}')").format(self.__module__,
                                            self.__class__.__name__,
                                            filename)

    def __str__(self):
        """Return a string representation."""
        filename = self._filename
        if not isinstance(filename, str):
            filename = self._filename.encode('utf-8')
        return str("{0}('{1}')").format(self.__class__.__name__, filename)

    def __unicode__(self):
        """Return a unicode representation."""
        _str = self.__str__()
        if not isinstance(_str, UnicodeType):
            _str = _str.decode('utf-8')
        return _str

    @property
    @deprecated('DjVuFile.file', since='2010222', future_warning=True)
    def file_djvu(self):
        """Deprecated file_djvu instance variable."""
        return self.file

    def check_cache(fn):
        """Decorator to check if cache shall be cleared."""
        cache = ['_page_count', '_has_text', '_page_info']

        def wrapper(obj, *args, **kwargs):
            force = kwargs.get('force', False)
            if force:
                for el in cache:
                    obj.__dict__.pop(el, None)
            _res = fn(obj, *args, **kwargs)
            return _res
        return wrapper

    def check_page_number(fn):
        """Decorator to check if page number is valid.

        @raises ValueError
        """
        def wrapper(obj, *args, **kwargs):
            n = args[0]
            force = kwargs.get('force', False)
            if not (1 <= n <= obj.number_of_images(force=force)):
                raise ValueError('Page %d not in file %s [%d-%d]'
                                 % (n, obj.file, n, obj.number_of_images()))
            _res = fn(obj, *args, **kwargs)
            return _res
        return wrapper

    @check_cache
    def number_of_images(self, force=False):
        """
        Return the number of images in the djvu file.

        @param force: if True, refresh the cached data
        @type force: bool
        """
        if not hasattr(self, '_page_count'):
            res, stdoutdata = _call_cmd(['djvused', '-e', 'n', self.file])
            if not res:
                return False
            self._page_count = int(stdoutdata)
        return self._page_count

    @check_page_number
    def page_info(self, n, force=False):
        """
        Return a tuple (id, (size, dpi)) for page n of djvu file.

        @param force: if True, refresh the cached data
        @type force: bool
        """
        if not hasattr(self, '_page_info') or force:
            self._get_page_info(force=force)
        return self._page_info[n]

    @check_cache
    def _get_page_info(self, force=False):
        """
        Return a dict of tuples (id, (size, dpi)) for all pages of djvu file.

        @param force: if True, refresh the cached data
        @type force: bool
        """
        if not hasattr(self, '_page_info'):
            self._page_info = {}

            res, stdoutdata = _call_cmd(['djvudump', self.file])
            if not res:
                return False

            has_text = False
            for line in stdoutdata.decode('utf-8').split('\n'):
                if 'TXTz' in line:
                    has_text = True

                if 'FORM:DJVU' in line:
                    m = self._pat_form.search(line)
                    if m:
                        key, id = int(m.group('n')), m.group('id')
                    else:
                        # If djvu doc has only one page,
                        # FORM:DJVU line in djvudump has no id
                        key, id = 1, ''

                if 'INFO' in line:
                    m = self._pat_info.search(line)
                    if m:
                        size, dpi = m.group('size'), int(m.group('dpi'))
                    else:
                        size, dpi = None, None
                else:
                    continue

                self._page_info[key] = (id, (size, dpi))
            self._has_text = has_text
        return self._page_info

    def get_most_common_info(self):
        """Return most common size and dpi for pages in djvu file."""
        cnt = Counter(s_d for _, s_d in self._get_page_info().values())
        (size, dpi), _ = cnt.most_common()[0]
        return size, dpi

    @check_cache
    def has_text(self, force=False):
        """
        Test if the djvu file has a text-layer.

        @param force: if True, refresh the cached data
        @type force: bool
        """
        if not hasattr(self, '_has_text'):
            self._get_page_info(force=force)
        return self._has_text

    def _remove_control_chars(self, data):
        """Remove djvu format control characters.

        See http://djvu.sourceforge.net/doc/man/djvused.html for control chars.
        """
        txt = data.decode('utf-8')
        # vertical tab (\013=\x0b): remove
        txt = txt.replace('\x0b', '')
        # group (\035=\x1d) separator: replace with \n
        txt = txt.replace('\x1d', '\n')
        # unit separator (\037=\x1f): replace with \n
        txt = txt.replace('\x1f', '\n')
        # feed char (\f=\x0c), \n and trailing spaces: strip
        txt = txt.strip('\x0c\n ')
        return txt

    @check_page_number
    @check_cache
    def get_page(self, n, force=False):
        """
        Get page n for djvu file.

        @param force: if True, refresh the cached data
        @type force: bool
        """
        if not self.has_text(force=force):
            raise ValueError('Djvu file %s has no text layer.' % self.file)
        res, stdoutdata = _call_cmd(['djvutxt', '--page=%d' % n, self.file])
        if not res:
            return False
        return self._remove_control_chars(stdoutdata)

    @check_page_number
    def whiten_page(self, n):
        """Replace page 'n' of djvu file with a blank page."""
        # tmp files for creation/insertion of a white page.
        white_ppm = os.path.join(self.dirname, 'white_page.ppm')
        white_djvu = os.path.join(self.dirname, 'white_page.djvu')

        n_tot = self.number_of_images()

        # Check n is in valid range and set ref_page number for final checks.
        ref_page = 2 if n == 1 else n - 1

        size, dpi = self.get_most_common_info()

        # Generate white_page.
        res, data = _call_cmd(['convert', '-size', size, 'xc:white',
                               white_ppm], lib='ImageMagik')
        if not res:
            return False

        # Convert white_page to djvu.
        res, data = _call_cmd(['c44', white_ppm, '-dpi', dpi])
        os.unlink(white_ppm)  # rm white_page.ppm before retuning.
        if not res:
            return False

        # Delete page n.
        # Get ref page info for later checks.
        info_ref_page = self.page_info(ref_page)
        res, data = _call_cmd(['djvm', '-d', self.file, n])
        if not res:
            return False

        # Insert new page
        res, data = _call_cmd(['djvm', '-i', self.file, white_djvu, n])
        os.unlink(white_djvu)  # rm white_page.djvu before returning.
        if not res:
            return False

        # Check if page processing is as expected.
        expected_id = '{%s}' % os.path.basename(white_djvu)
        assert self.number_of_images(force=True) == n_tot
        assert self.page_info(n) == (expected_id, (size, dpi))  # white page id
        assert self.page_info(ref_page) == info_ref_page  # ref page info.

        return True

    @check_page_number
    def delete_page(self, n):
        """Delete page 'n' of djvu file ."""
        n_tot = self.number_of_images()

        # Check n is in valid range and set ref_page number for final checks.
        ref_page = n - 1 if n == n_tot else n + 1
        new_ref_page = n - 1 if n == n_tot else n

        # Delete page n.
        # Get ref page info for later checks.
        info_ref_page = self.page_info(ref_page)
        res, data = _call_cmd(['djvm', '-d', self.file, n])
        if not res:
            return False

        # Check if page processing is as expected.
        # ref page info.
        if n_tot > 2:
            assert self.number_of_images(force=True) == n_tot - 1
            # cache cleared above
            assert self.page_info(new_ref_page) == info_ref_page
        else:
            # If djvu has only one page, FORM:DJVU line in djvudump has no id
            _id, (sz, dpi) = info_ref_page
            assert self.page_info(new_ref_page, force=True) == ('', (sz, dpi))

        return True

    # This is to be used only if this class is subclassed and the decorators
    # needs to be used by the child.
    check_page_number = staticmethod(check_page_number)
    check_cache = staticmethod(check_cache)
