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
import threading
from Queue import Queue

# Use pywikibot. prefix for all in-package imports; this is to prevent
# confusion with similarly-named modules in version 1 framework, for users
# who want to continue using both

from pywikibot import config2 as config
from pywikibot.bot import *
from pywikibot.exceptions import *
from pywikibot.textlib import *


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
                warning(u"%s.%s is DEPRECATED, use %s instead."
                         % (classname, funcname, instead))
            else:
                warning(u"%s.%s is DEPRECATED." % (classname, funcname))
            return method(*args, **kwargs)
        wrapper.func_name = method.func_name
        return wrapper
    return decorator

def deprecate_arg(old_arg, new_arg):
    """Decorator to declare old_arg deprecated and replace it with new_arg"""
    _logger = ""
    def decorator(method):
        def wrapper(*__args, **__kw):
            meth_name = method.__name__
            if old_arg in __kw:
                if new_arg:
                    if new_arg in __kw:
                        pywikibot.warning(
u"%(new_arg)s argument of %(meth_name)s replaces %(old_arg)s; cannot use both."
                            % locals())
                    else:
                        pywikibot.warning(
u"%(old_arg)s argument of %(meth_name)s is deprecated; use %(new_arg)s instead."
                            % locals())
                        __kw[new_arg] = __kw[old_arg]
                else:
                    pywikibot.debug(
                        u"%(old_arg)s argument of %(meth_name)s is deprecated."
                            % locals(),
                        _logger)
                del __kw[old_arg]
            return method(*__args, **__kw)
        wrapper.__doc__ = method.__doc__
        wrapper.__name__ = method.__name__
        return wrapper
    return decorator


_sites = {}


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
    _logger = "wiki"

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
    if not key in _sites or not isinstance(_sites[key], __Site):
        _sites[key] = __Site(code=code, fam=fam, user=user, sysop=sysop)
        pywikibot.debug(u"Instantiating Site object '%(site)s'"
                        % {'site': _sites[key]}, _logger)
    return _sites[key]


getSite = Site  # alias for backwards-compability


from page import Page, ImagePage, Category, Link, User, ItemPage, PropertyPage, Claim
from page import html2unicode, url2unicode


link_regex = re.compile(r'\[\[(?P<title>[^\]|[#<>{}]*)(\|.*?)?\]\]')


def setAction(s):
    """Set a summary to use for changed page submissions"""
    config.default_edit_summary = s


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

stopped = False

def stopme():
    """Drop this process from the throttle log, after pending threads finish.

    Can be called manually if desired, but if not, will be called automatically
    at Python exit.

    """
    global stopped
    _logger = "wiki"

    if not stopped:
        pywikibot.debug(u"stopme() called", _logger)
        def remaining():
            import datetime
            remainingPages = page_put_queue.qsize() - 1
                # -1 because we added a None element to stop the queue
            remainingSeconds = datetime.timedelta(
                    seconds=(remainingPages * config.put_throttle))
            return (remainingPages, remainingSeconds)

        page_put_queue.put((None, [], {}))
        stopped = True

        if page_put_queue.qsize() > 1:
            output(u'Waiting for %i pages to be put. Estimated time remaining: %s'
                   % remaining())

        while(_putthread.isAlive()):
            try:
                _putthread.join(1)
            except KeyboardInterrupt:
                answer = inputChoice(u"""\
There are %i pages remaining in the queue. Estimated time remaining: %s
Really exit?"""
                                         % remaining(),
                                     ['yes', 'no'], ['y', 'N'], 'N')
                if answer == 'y':
                    return

    # only need one drop() call because all throttles use the same global pid
    try:
        _sites.values()[0].throttle.drop()
        pywikibot.log(u"Dropped throttle(s).")
    except IndexError:
        pass

import atexit
atexit.register(stopme)

# Create a separate thread for asynchronous page saves (and other requests)

def async_manager():
    """Daemon; take requests from the queue and execute them in background."""
    while True:
        (request, args, kwargs) = page_put_queue.get()
        if request is None:
            break
        request(*args, **kwargs)

def async_request(request, *args, **kwargs):
    """Put a request on the queue, and start the daemon if necessary."""
    if not _putthread.isAlive():
        try:
            page_put_queue.mutex.acquire()
            try:
                _putthread.start()
            except (AssertionError, RuntimeError):
                pass
        finally:
            page_put_queue.mutex.release()
    page_put_queue.put((request, args, kwargs))

# queue to hold pending requests
page_put_queue = Queue(config.max_queue_size)
# set up the background thread
_putthread = threading.Thread(target=async_manager)
# identification for debugging purposes
_putthread.setName('Put-Thread')
_putthread.setDaemon(True)
