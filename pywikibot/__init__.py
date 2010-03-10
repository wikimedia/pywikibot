# -*- coding: utf-8  -*-
"""
The initialization file for the Pywikibot framework.
"""
#
# (C) Pywikipedia bot team, 2008
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import datetime
import difflib
import logging
import re
import sys

import config2 as config
from bot import *
from exceptions import *
from textlib import *


class Timestamp(datetime.datetime):
    """Class for handling Mediawiki timestamps.

    This inherits from datetime.datetime, so it can use all of the methods
    and operations of a datetime object.  To ensure that the results of any
    operation are also a Timestamp object, be sure to use only Timestamp
    objects (and datetime.timedeltas) in any operation.

    Use Timestamp.fromISOformat() and Timestamp.fromtimestampformat() to
    create Timestamp objects from Mediawiki string formats.

    Use Site.getcurrenttime() for the current time; this is more reliable
    than using Timestamp.utcnow().

    """
    mediawikiTSFormat = "%Y%m%d%H%M%S"
    ISO8601Format = "%Y-%m-%dT%H:%M:%SZ"

    @classmethod
    def fromISOformat(cls, ts):
        """Convert an ISO 8601 timestamp to a Timestamp object."""
        return cls.strptime(ts, cls.ISO8601Format)

    @classmethod
    def fromtimestampformat(cls, ts):
        """Convert the internal MediaWiki timestamp format to a Timestamp object."""
        return cls.strptime(ts, cls.mediawikiTSFormat)

    def __str__(self):
        """Return a string format recognized by the API"""
        return self.strftime(self.ISO8601Format)

    def __add__(self, other):
        newdt = datetime.datetime.__add__(self, other)
        if isinstance(newdt, datetime.datetime):
            return Timestamp(newdt.year, newdt.month, newdt.day, newdt.hour,
                             newdt.minute, newdt.second, newdt.microsecond,
                             newdt.tzinfo)
        else:
            return newdt

    def __sub__(self, other):
        newdt = datetime.datetime.__sub__(self, other)
        if isinstance(newdt, datetime.datetime):
            return Timestamp(newdt.year, newdt.month, newdt.day, newdt.hour,
                             newdt.minute, newdt.second, newdt.microsecond,
                             newdt.tzinfo)
        else:
            return newdt


def deprecated(instead=None):
    """Decorator to output a method deprecation warning.

    @param instead: if provided, will be used to specify the replacement
    @type instead: string
    """
    def decorator(method):
        def wrapper(*args, **kwargs):
            funcname = method.func_name
            classname = args[0].__class__.__name__
            if instead:
                output(u"%s.%s is DEPRECATED, use %s instead."
                        % (classname, funcname, instead),
                       level=WARNING)
            else:
                output(u"%s.%s is DEPRECATED." % (classname, funcname),
                       level=WARNING)
            return method(*args, **kwargs)
        wrapper.func_name = method.func_name
        return wrapper
    return decorator

def deprecate_arg(old_arg, new_arg):
    """Decorator to declare old_arg deprecated and replace it with new_arg"""
    logger = logging.getLogger("pywiki")
    def decorator(method):
        def wrapper(*__args, **__kw):
            meth_name = method.__name__
            if old_arg in __kw:
                if new_arg:
                    if new_arg in __kw:
                        pywikibot.output(
"%(new_arg)s argument of %(meth_name)s replaces %(old_arg)s; cannot use both."
                            % locals(), level=WARNING)
                    else:
                        pywikibot.output(
"%(old_arg)s argument of %(meth_name)s is deprecated; use %(new_arg)s instead."
                            % locals(), level=WARNING)
                        __kw[new_arg] = __kw[old_arg]
                else:
                    pywikibot.output(
                        "%(old_arg)s argument of %(meth_name)s is deprecated."
                        % locals(), level=DEBUG)
                del __kw[old_arg]
            return method(*__args, **__kw)
        wrapper.__doc__ = method.__doc__
        wrapper.__name__ = method.__name__
        return wrapper
    return decorator


_sites = {}

@deprecate_arg("persistent_http", None)
def Site(code=None, fam=None, user=None, sysop=None, interface=None):
    """Return the specified Site object.

    Returns a cached object if possible, otherwise instantiates a new one.

    @param code: language code
    @type code: string
    @param fam: family name or object
    @type fam: string or Family
    @param user: bot user name to use on this site
    @type user: unicode

    """
    logger = logging.getLogger("pywiki.wiki")

    if code is None:
        code = config.mylang
    if fam is None:
        fam = config.family
    if user is None:
        try:
            user = config.usernames[fam][code]
        except KeyError:
            user = None
    if sysop is None:
        try:
            sysop = config.sysopnames[fam][code]
        except KeyError:
            sysop = None
    if interface is None:
        interface = config.site_interface
    try:
        tmp = __import__('pywikibot.site', fromlist=[interface])
        __Site = getattr(tmp, interface)
    except ImportError:
        raise ValueError("Invalid interface name '%(interface)s'" % locals())
    key = '%s:%s:%s' % (fam, code, user)
    if not key in _sites:
        _sites[key] = __Site(code=code, fam=fam, user=user, sysop=sysop)
        pywikibot.output(u"Instantiating Site object '%(site)s'"
                             % {'site': _sites[key]},
                         level=pywikibot.DEBUG)
    return _sites[key]

getSite = Site # alias for backwards-compability


from page import Page, ImagePage, Category, Link, User


link_regex = re.compile(r'\[\[(?P<title>[^\]|[#<>{}]*)(\|.*?)?\]\]')


def setAction(s):
    """Set a summary to use for changed page submissions"""
    config.default_edit_summary = s


def set_debug(layer):
    """Set the logger for specified layer to DEBUG level.

    The framework has four layers (by default, others can be added), each
    designated by a string --

    1.  "comm": the communication layer (http requests, etc.)
    2.  "data": the raw data layer (API requests, XML dump parsing)
    3.  "wiki": the wiki content representation layer (Page and Site objects)
    4.  "bot": the application layer

    This method sets the logger for any specified layer to the DEBUG level,
    causing it to output extensive debugging information.  If this method is
    not called for a layer, the default logging setting is the INFO level.

    This method does not check the 'layer' argument for validity.

    """
    logging.getLogger("pywiki."+layer).setLevel(DEBUG)


def showDiff(oldtext, newtext):
    """
    Output a string showing the differences between oldtext and newtext.
    The differences are highlighted (only on compatible systems) to show which
    changes were made.

    """
    # This is probably not portable to non-terminal interfaces....
    # For information on difflib, see http://pydoc.org/2.3/difflib.html
    color = {
        '+': 'lightgreen',
        '-': 'lightred',
    }
    diff = u''
    colors = []
    # This will store the last line beginning with + or -.
    lastline = None
    # For testing purposes only: show original, uncolored diff
    #     for line in difflib.ndiff(oldtext.splitlines(), newtext.splitlines()):
    #         print line
    for line in difflib.ndiff(oldtext.splitlines(), newtext.splitlines()):
        if line.startswith('?'):
            # initialize color vector with None, which means default color
            lastcolors = [None for c in lastline]
            # colorize the + or - sign
            lastcolors[0] = color[lastline[0]]
            # colorize changed parts in red or green
            for i in range(min(len(line), len(lastline))):
                if line[i] != ' ':
                    lastcolors[i] = color[lastline[0]]
            diff += lastline + '\n'
            # append one None (default color) for the newline character
            colors += lastcolors + [None]
        elif lastline:
            diff += lastline + '\n'
            # colorize the + or - sign only
            lastcolors = [None for c in lastline]
            lastcolors[0] = color[lastline[0]]
            colors += lastcolors + [None]
        lastline = None
        if line[0] in ('+', '-'):
            lastline = line
    # there might be one + or - line left that wasn't followed by a ? line.
    if lastline:
        diff += lastline + '\n'
        # colorize the + or - sign only
        lastcolors = [None for c in lastline]
        lastcolors[0] = color[lastline[0]]
        colors += lastcolors + [None]

    result = u''
    lastcolor = None
    for i in range(len(diff)):
        if colors[i] != lastcolor:
            if lastcolor is None:
                result += '\03{%s}' % colors[i]
            else:
                result += '\03{default}'
        lastcolor = colors[i]
        result += diff[i]
    output(result)


# Throttle and thread handling

threadpool = []   # add page-putting threads to this list as they are created
stopped = False

def stopme():
    """Drop this process from the throttle log, after pending threads finish.

    Can be called manually if desired, but if not, will be called automatically
    at Python exit.

    """
    global stopped
    logger = logging.getLogger("pywiki.wiki")

    if not stopped:
        pywikibot.output(u"stopme() called",
                         level=pywikibot.DEBUG)
        count = sum(1 for thd in threadpool if thd.isAlive())
        if count:
            pywikibot.output(u"Waiting for about %(count)s pages to be saved."
                              % locals())
            for thd in threadpool:
                if thd.isAlive():
                    thd.join()
        stopped = True
    # only need one drop() call because all throttles use the same global pid
    try:
        _sites[_sites.keys()[0]].throttle.drop()
        pywikibot.output(u"Dropped throttle(s).", level=VERBOSE)
    except IndexError:
        pass

import atexit
atexit.register(stopme)
