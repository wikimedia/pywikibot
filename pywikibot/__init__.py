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

import sys
import logging
import re

from exceptions import *
import config2 as config
import textlib
from bot import *


def deprecate_arg(old_arg, new_arg):
    """Decorator to declare old_arg deprecated and replace it with new_arg"""
    logger = logging.getLogger()
    def decorator(method):
        def wrapper(*__args, **__kw):
            meth_name = method.__name__
            if old_arg in __kw:
                if new_arg:
                    if new_arg in __kw:
                        logger.warn(
"%(new_arg)s argument of %(meth_name)s replaces %(old_arg)s; cannot use both."
                            % locals())
                    else:
                        logger.debug(
"%(old_arg)s argument of %(meth_name)s is deprecated; use %(new_arg)s instead."
                            % locals())
                        __kw[new_arg] = __kw[old_arg]
                else:
                    logger.debug(
                        "%(old_arg)s argument of %(meth_name)s is deprecated."
                        % locals())
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
    logger = logging.getLogger("wiki")
    
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
        exec "from site import %s as __Site" % interface
    except ImportError:
        raise ValueError("Invalid interface name '%(interface)s'" % locals())
    key = '%s:%s:%s' % (fam, code, user)
    if not _sites.has_key(key):
        _sites[key] = __Site(code=code, fam=fam, user=user, sysop=sysop)
        logger.debug("Instantiating Site object '%(site)s'"
                      % {'site': _sites[key]})
    return _sites[key]

getSite = Site # alias for backwards-compability


from page import Page, ImagePage, Category, Link


link_regex = re.compile(r'\[\[(?P<title>[^\]|[#<>{}]*)(\|.*?)?\]\]')


# User interface functions (kept extremely simple for debugging)

def output(text, toStdout=False):
    print text.encode(config.console_encoding, "xmlcharrefreplace")

def input(prompt, password=False):
    if isinstance(prompt, unicode):
        encoding = sys.stdout.encoding
        # Fallback to _some_ encoding for virtual consoles (cron, screen !)
        if not encoding:
            encoding = "UTF-8"
        prompt = prompt.encode(encoding, "xmlcharrefreplace")
    if password:
        import getpass
        return getpass.getpass(prompt)
    return raw_input(prompt)


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
    logging.getLogger(layer).setLevel(logging.DEBUG)


# Throttle and thread handling

threadpool = []   # add page-putting threads to this list as they are created
stopped = False

def stopme():
    """Drop this process from the throttle log, after pending threads finish.

    Can be called manually if desired, but if not, will be called automatically
    at Python exit.

    """
    global stopped
    logger = logging.getLogger("wiki")

    if not stopped:
        logger.debug("stopme() called")
        count = sum(1 for thd in threadpool if thd.isAlive())
        if count:
            logger.info("Waiting for about %(count)s pages to be saved."
                         % locals())
            for thd in threadpool:
                if thd.isAlive():
                    thd.join()
        stopped = True
    # only need one drop() call because all throttles use the same global pid
    try:
        _sites[_sites.keys()[0]].throttle.drop()
        logger.log("VERBOSE", "Dropped throttle(s).")
    except IndexError:
        pass

import atexit
atexit.register(stopme)
