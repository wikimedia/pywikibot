# -*- coding: utf-8  -*-
"""
This module contains backports to support older Python versions.

They contain the backported code originally developed for Python. It is
therefore distributed under the PSF license, as follows:

PYTHON SOFTWARE FOUNDATION LICENSE VERSION 2
--------------------------------------------
1. This LICENSE AGREEMENT is between the Python Software Foundation
("PSF"), and the Individual or Organization ("Licensee") accessing and
otherwise using this software ("Python") in source or binary form and
its associated documentation.

2. Subject to the terms and conditions of this License Agreement, PSF hereby
grants Licensee a nonexclusive, royalty-free, world-wide license to reproduce,
analyze, test, perform and/or display publicly, prepare derivative works,
distribute, and otherwise use Python alone or in any derivative version,
provided, however, that PSF's License Agreement and PSF's notice of copyright,
i.e., "Copyright (c) 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
2011, 2012, 2013, 2014 Python Software Foundation; All Rights Reserved" are
retained in Python alone or in any derivative version prepared by Licensee.

3. In the event Licensee prepares a derivative work that is based on
or incorporates Python or any part thereof, and wants to make
the derivative work available to others as provided herein, then
Licensee hereby agrees to include in any such work a brief summary of
the changes made to Python.

4. PSF is making Python available to Licensee on an "AS IS"
basis. PSF MAKES NO REPRESENTATIONS OR WARRANTIES, EXPRESS OR
IMPLIED. BY WAY OF EXAMPLE, BUT NOT LIMITATION, PSF MAKES NO AND
DISCLAIMS ANY REPRESENTATION OR WARRANTY OF MERCHANTABILITY OR FITNESS
FOR ANY PARTICULAR PURPOSE OR THAT THE USE OF PYTHON WILL NOT
INFRINGE ANY THIRD PARTY RIGHTS.

5. PSF SHALL NOT BE LIABLE TO LICENSEE OR ANY OTHER USERS OF PYTHON
FOR ANY INCIDENTAL, SPECIAL, OR CONSEQUENTIAL DAMAGES OR LOSS AS
A RESULT OF MODIFYING, DISTRIBUTING, OR OTHERWISE USING PYTHON,
OR ANY DERIVATIVE THEREOF, EVEN IF ADVISED OF THE POSSIBILITY THEREOF.

6. This License Agreement will automatically terminate upon a material
breach of its terms and conditions.

7. Nothing in this License Agreement shall be deemed to create any
relationship of agency, partnership, or joint venture between PSF and
Licensee. This License Agreement does not grant permission to use PSF
trademarks or trade name in a trademark sense to endorse or promote
products or services of Licensee, or any third party.

8. By copying, installing or otherwise using Python, Licensee
agrees to be bound by the terms and conditions of this License
Agreement.
"""
#
# (C) Python Software Foundation, 2001-2014
# (C) with modifications from Pywikibot team, 2015
#
# Distributed under the terms of the PSF license.
#
from __future__ import unicode_literals

import logging
import warnings


def format_range_unified(start, stop):
    """
    Convert range to the "ed" format.

    Copied from C{difflib._format_range_unified()} which was introduced in
    Python 2.7.2.

    @see: https://hg.python.org/cpython/file/8527427914a2/Lib/difflib.py#l1147
    """
    # Per the diff spec at http://www.unix.org/single_unix_specification/
    beginning = start + 1  # lines start numbering with one
    length = stop - start
    if length == 1:
        return '{0}'.format(beginning)
    if not length:
        beginning -= 1  # empty ranges begin at line just before the range
    return '{0},{1}'.format(beginning, length)


# Logging/Warnings integration

_warnings_showwarning = None


class NullHandler(logging.Handler):

    """
    This handler does nothing.

    It's intended to be used to avoid the "No handlers could be found for
    logger XXX" one-off warning. This is important for library code, which
    may contain code to log events. If a user of the library does not configure
    logging, the one-off warning might be produced; to avoid this, the library
    developer simply needs to instantiate a NullHandler and add it to the
    top-level logger of the library module or package.

    Copied from C{logging.NullHandler} which was introduced in Python 2.7.

    @see: http://bugs.python.org/issue4384
    """

    def handle(self, record):
        """Dummy handling."""
        pass

    def emit(self, record):
        """Dummy handling."""
        pass

    def createLock(self):
        """Dummy handling."""
        self.lock = None


def _showwarning(message, category, filename, lineno, file=None, line=None):
    """
    Implementation of showwarnings which redirects to logging.

    It will first check to see if the file parameter is None. If a file is
    specified, it will delegate to the original warnings implementation of
    showwarning. Otherwise, it will call warnings.formatwarning and will log
    the resulting string to a warnings logger named "py.warnings" with level
    logging.WARNING.

    Copied from C{logging._showwarning} which was introduced in Python 2.7.

    @see: http://bugs.python.org/issue4384
    """
    if file is not None:
        if _warnings_showwarning is not None:
            _warnings_showwarning(message, category, filename, lineno, file, line)
    else:
        s = warnings.formatwarning(message, category, filename, lineno, line)
        logger = logging.getLogger("py.warnings")
        if not logger.handlers:
            logger.addHandler(NullHandler())
        logger.warning("%s", s)


def captureWarnings(capture):
    """
    Capture warnings into logging.

    If capture is true, redirect all warnings to the logging package.
    If capture is False, ensure that warnings are not redirected to logging
    but to their original destinations.

    Copied from C{logging.captureWarnings} which was introduced in Python 2.7.

    @see: http://bugs.python.org/issue4384
    """
    global _warnings_showwarning
    if capture:
        if _warnings_showwarning is None:
            _warnings_showwarning = warnings.showwarning
            warnings.showwarning = _showwarning
    else:
        if _warnings_showwarning is not None:
            warnings.showwarning = _warnings_showwarning
            _warnings_showwarning = None
