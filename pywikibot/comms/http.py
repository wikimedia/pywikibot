# -*- coding: utf-8  -*-
"""
Basic HTTP access interface.

This module handles communication between the bot and the HTTP threads.

This module is responsible for
    - Setting up a connection pool
    - Providing a (blocking) interface for HTTP requests
    - Translate site objects with query strings into URLs
    - URL-encoding all data
    - Basic HTTP error handling
"""

#
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#

__version__ = '$Id$'
__docformat__ = 'epytext'

import sys
import atexit
import time

# Verify that a working httplib2 is present.
try:
    import httplib2
except ImportError:
    print("Error: Python module httplib2 >= 0.6.0 is required.")
    sys.exit(1)

from distutils.version import StrictVersion
# httplib2 0.6.0 was released with __version__ as '$Rev$'
#                and no module variable CA_CERTS.
if httplib2.__version__ == '$Rev$' and 'CA_CERTS' not in httplib2.__dict__:
    httplib2.__version__ = '0.6.0'
if StrictVersion(httplib2.__version__) < StrictVersion("0.6.0"):
    print("Error: Python module httplib2 (%s) is not 0.6.0 or greater." %
          httplib2.__file__)
    sys.exit(1)

if sys.version_info[0] == 2:
    if 'SSLHandshakeError' in httplib2.__dict__:
        from httplib2 import SSLHandshakeError
    elif httplib2.__version__ == '0.6.0':
        from httplib2 import ServerNotFoundError as SSLHandshakeError

    import Queue
    import urlparse
    import cookielib
    from urllib2 import quote
else:
    from ssl import SSLError as SSLHandshakeError
    import queue as Queue
    import urllib.parse as urlparse
    from http import cookiejar as cookielib
    from urlparse import quote

from pywikibot import config
from pywikibot.exceptions import FatalServerError, Server504Error
import pywikibot
from . import threadedhttp
import pywikibot.version

_logger = "comm.http"


# global variables

# The OpenSSL error code for
#   certificate verify failed
# cf. `openssl errstr 14090086`
SSL_CERT_VERIFY_FAILED = ":14090086:"


numthreads = 1
threads = []

connection_pool = threadedhttp.ConnectionPool()
http_queue = Queue.Queue()

cookie_jar = threadedhttp.LockableCookieJar(
    config.datafilepath("pywikibot.lwp"))
try:
    cookie_jar.load()
except (IOError, cookielib.LoadError):
    pywikibot.debug(u"Loading cookies failed.", _logger)
else:
    pywikibot.debug(u"Loaded cookies from file.", _logger)


# Build up HttpProcessors
pywikibot.log(u'Starting %(numthreads)i threads...' % locals())
for i in range(numthreads):
    proc = threadedhttp.HttpProcessor(http_queue, cookie_jar, connection_pool)
    proc.setDaemon(True)
    threads.append(proc)
    proc.start()


# Prepare flush on quit
def _flush():
    for i in threads:
        http_queue.put(None)

    message = (u'Waiting for %i network thread(s) to finish. '
               u'Press ctrl-c to abort' % len(threads))
    if hasattr(sys, 'last_type'):
        # we quit because of an exception
        print(sys.last_type)
        pywikibot.critical(message)
    else:
        pywikibot.log(message)

    while any(t for t in threads if t.isAlive()):
        time.sleep(.1)

    pywikibot.log(u"All threads finished.")
atexit.register(_flush)

# export cookie_jar to global namespace
pywikibot.cookie_jar = cookie_jar


def request(site, uri, ssl=False, *args, **kwargs):
    """Queue a request to be submitted to Site.

    All parameters not listed below are the same as
    L{httplib2.Http.request}, but the uri is relative

    If the site argument is None the uri has to be absolute and is
    taken. In this case SSL is ignored. Used for requests to non wiki
    pages.

    @param site: The Site to connect to
    @param uri: the URI to retrieve (relative to the site's scriptpath)
    @param ssl: Use HTTPS connection
    @return: The received data (a unicode string).

    """
    if site:
        if ssl:
            proto = "https"
            host = site.ssl_hostname()
            uri = site.ssl_pathprefix() + uri
        else:
            proto = site.protocol()
            host = site.hostname()
        baseuri = urlparse.urljoin("%s://%s" % (proto, host), uri)
    else:
        baseuri = uri

    kwargs["headers"]["user-agent"] = config.USER_AGENT_FORMAT.format(
        script=pywikibot.calledModuleName(),
        version=pywikibot.version.getversiondict()['rev'],
        username=quote(site.username()),
        lang=site.lang,
        family=site.family.name)
    request = threadedhttp.HttpRequest(baseuri, *args, **kwargs)
    http_queue.put(request)
    while not request.lock.acquire(False):
        time.sleep(0.1)

    # TODO: do some error correcting stuff
    if isinstance(request.data, SSLHandshakeError):
        if SSL_CERT_VERIFY_FAILED in str(request.data):
            raise FatalServerError(str(request.data))

    # if all else fails
    if isinstance(request.data, Exception):
        raise request.data

    if request.data[0].status == 504:
        raise Server504Error("Server %s timed out" % site.hostname())

    if request.data[0].status != 200:
        pywikibot.warning(u"Http response status %(status)s"
                          % {'status': request.data[0].status})

    return request.data[1]
