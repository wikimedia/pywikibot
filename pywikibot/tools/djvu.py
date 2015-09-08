#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Wrapper around djvulibre to access djvu files properties and content."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'

import os.path
import subprocess

import pywikibot


class DjVuFile(object):

    """Wrapper around djvulibre to access djvu files properties and content.

    Perform file existance checks.

    Control characters in djvu text-layer are converted for convenience
    (see http://djvu.sourceforge.net/doc/man/djvused.html for control chars
    details).

    """

    def __init__(self, file_djvu):
        """
        Constructor.

        @param file_djvu: filename (including path) to djvu file
        @type  file_djvu: string/unicode
        """
        file_djvu = os.path.expanduser(file_djvu)
        # Check file exists and has read permissions.
        with open(file_djvu):
            self.file_djvu = file_djvu

    def number_of_images(self):
        """Return the (cached) number of images in the djvu file."""
        if not hasattr(self, '_image_count'):
            dp = subprocess.Popen(['djvused', '-e', 'n', self.file_djvu],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdoutdata, stderrdata) = dp.communicate()
            if dp.returncode != 0:
                pywikibot.error('djvulibre library error!\n%s' % stderrdata)
            self._image_count = int(stdoutdata)
        return self._image_count

    def has_text(self):
        """Test if the djvu file has a text-layer."""
        if not hasattr(self, '_has_text'):
            dp = subprocess.Popen(['djvudump', self.file_djvu],
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            (stdoutdata, stderrdata) = dp.communicate()
            if dp.returncode != 0:
                pywikibot.error('djvulibre library error!\n%s' % stderrdata)
            txt = stdoutdata.decode('utf-8')
            self._has_text = 'TXTz' in txt
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

    def get_page(self, n):
        """Get page n for djvu file."""
        if not self.has_text():
            raise ValueError('Djvu file %s has no text layer.' % self.file_djvu)
        if not (1 <= n <= self.number_of_images()):
            raise ValueError('Requested page number %d is not in file %s'
                             ' page range [%d-%d]'
                             % (n, self.file_djvu, 1, self.number_of_images()))
        dp = subprocess.Popen(['djvutxt', '--page=%d' % n, self.file_djvu],
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdoutdata, stderrdata) = dp.communicate()
        if dp.returncode != 0:
            pywikibot.error('djvulibre library error!\n%s' % stderrdata)
        return self._remove_control_chars(stdoutdata)
