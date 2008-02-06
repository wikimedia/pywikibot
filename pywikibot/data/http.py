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

__version__ = '$Id: $'
__docformat__ = 'epytext'

import Queue
import urllib
import urlparse
import logging
import atexit

import threadedhttp


# global variables

useragent = 'Pywikipediabot/2.0' # This should include some global version string
numthreads = 1
threads = []

connection_pool = threadedhttp.ConnectionPool()
cookie_jar = threadedhttp.LockableCookieJar()
http_queue = Queue.Queue()

# Build up HttpProcessors
logging.info('Starting %i threads...' % numthreads)
for i in range(numthreads):
    proc = threadedhttp.HttpProcessor(http_queue, cookie_jar, connection_pool)
    threads.append(proc)
    proc.start()

# Prepare flush on quit
def _flush():
    for i in threads:
        http_queue.put(None)
    logging.info('Waiting for threads to finish... ')
    for i in threads:
        i.join()
atexit.register(_flush)
        
def request(site, uri, *args, **kwargs):
    """Queue a request to be submitted to Site.

    All parameters not listed below are the same as
    L{httplib2.Http.request}, but the uri is relative

    @param site: The Site to connect to
    @return: The received data (a unicode string).
    """
    baseuri = "%s://%s/" % (site.protocol(), site.hostname())
    uri = urlparse.urljoin(baseuri, uri)

    request = threadedhttp.HttpRequest(uri, *args, **kwargs)
    http_queue.put(request)
    request.lock.acquire()

    #do some error correcting stuff

    #if all else fails
    if isinstance(request.data, Exception):
        raise request.data

    if request.data[0].status != 200:
        logging.warning("Http response status %s" % request.data[0].status)

    return request.data[1]    
