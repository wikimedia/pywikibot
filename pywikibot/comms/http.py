# -*- coding: utf-8  -*-
"""
Basic HTTP access interface.

This module handles communication between the bot and the HTTP threads.

This module is responsible for
    - Setting up a connection pool
    - Providing a (blocking) interface for HTTP requests
    - Translate site objects with query strings into urls
    - Urlencoding all data
    - Basic HTTP error handling
"""

#
# (C) Pywikipedia bot team, 2007
#
# Distributed under the terms of the MIT license.
#

__version__ = '$Id$'
__docformat__ = 'epytext'

import Queue
import urllib
import urlparse
import logging
import atexit

from pywikibot import config
from pywikibot.exceptions import Server504Error
import pywikibot
import cookielib
import threadedhttp

logger = logging.getLogger("comms.http")


# global variables

useragent = 'Pywikipediabot/2.0' # This should include some global version string
numthreads = 1
threads = []

connection_pool = threadedhttp.ConnectionPool()
http_queue = Queue.Queue()

cookie_jar = threadedhttp.LockableCookieJar(
                 config.datafilepath("pywikibot.lwp"))
try:
    cookie_jar.load()
except (IOError, cookielib.LoadError):
    logger.debug("Loading cookies failed.")
else:
    logger.debug("Loaded cookies from file.")


# Build up HttpProcessors
pywikibot.output('Starting %(numthreads)i threads...' % locals(),
                 level=pywikibot.VERBOSE)
for i in range(numthreads):
    proc = threadedhttp.HttpProcessor(http_queue, cookie_jar, connection_pool)
    proc.setDaemon(True)
    threads.append(proc)
    proc.start()

# Prepare flush on quit
def _flush():
    for i in threads:
        http_queue.put(None)
    pywikibot.output(u'Waiting for threads to finish... ',
                     level=pywikibot.VERBOSE)
    for i in threads:
        i.join()
    logger.debug('All threads finished.')
atexit.register(_flush)

# export cookie_jar to global namespace
pywikibot.cookie_jar = cookie_jar

def request(site, uri, ssl=False, *args, **kwargs):
    """Queue a request to be submitted to Site.

    All parameters not listed below are the same as
    L{httplib2.Http.request}, but the uri is relative

    @param site: The Site to connect to
    @param uri: the URI to retrieve (relative to the site's scriptpath)
    @param ssl: Use https connection
    @return: The received data (a unicode string).
    
    """
    if ssl:
        proto = "https"
        host = site.ssl_hostname()
    else:
        proto = "http"
        host = site.hostname()
    full_uri = "%(proto)s://%(host)s%(uri)s" % locals()

    # set default user-agent string
    kwargs.setdefault("headers", {})
    kwargs["headers"].setdefault("user-agent", useragent)
    request = threadedhttp.HttpRequest(full_uri, *args, **kwargs)
    http_queue.put(request)
    request.lock.acquire()

    #TODO: do some error correcting stuff
    #if all else fails
    if isinstance(request.data, Exception):
        raise request.data

    if request.data[0].status == 504:
        raise Server504Error("Server %s timed out" % site.hostname())

    if request.data[0].status != 200:
        pywikibot.output(u"Http response status %(status)s"
                          % {'status': request.data[0].status},
                         level=pywikibot.WARNING)

    return request.data[1]    
