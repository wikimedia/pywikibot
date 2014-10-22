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

    # The OpenSSL error code for
    #   certificate verify failed
    # cf. `openssl errstr 14090086`
    SSL_CERT_VERIFY_FAILED_MSG = ":14090086:"

    import Queue
    import urlparse
    import cookielib
    from urllib2 import quote
else:
    from ssl import SSLError as SSLHandshakeError
    SSL_CERT_VERIFY_FAILED_MSG = "SSL: CERTIFICATE_VERIFY_FAILED"
    import queue as Queue
    import urllib.parse as urlparse
    from http import cookiejar as cookielib
    from urllib.parse import quote

from pywikibot import config
from pywikibot.exceptions import FatalServerError, Server504Error
from pywikibot.comms import threadedhttp
from pywikibot.tools import deprecate_arg
import pywikibot.version

_logger = "comm.http"


# global variables

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

USER_AGENT_PRODUCTS = {
    'python': 'Python/' + '.'.join([str(i) for i in sys.version_info]),
    'httplib2': 'httplib2/' + httplib2.__version__,
    'pwb': 'Pywikibot/' + pywikibot.__release__,
}


def user_agent_username(username=None):
    """
    Reduce username to a representation permitted in HTTP headers.

    To achieve that, this function:
    1) replaces spaces (' ') with '_'
    2) encodes the username as 'utf-8' and if the username is not ASCII
    3) URL encodes the username if it is not ASCII, or contains '%'
    """
    if not username:
        return ''
    username = username.replace(' ', '_')  # Avoid spaces or %20.
    try:
        username.encode('ascii')  # just test, but not actually use it
    except UnicodeEncodeError:
        pass
    else:
        # % is legal in the default $wgLegalTitleChars
        # This is so that ops know the real pywikibot will not
        # allow a useragent in the username to allow through a hand-coded
        # percent-encoded value.
        if '%' in username:
            return quote(username)
        else:
            return username
    username = quote(username.encode('utf-8'))
    return username


def user_agent(site=None, format_string=None):
    values = USER_AGENT_PRODUCTS.copy()

    # This is the Pywikibot revision; also map it to {version} at present.
    if pywikibot.version.cache:
        values['revision'] = pywikibot.version.cache['rev']
    else:
        values['revision'] = ''
    values['version'] = values['revision']

    values['script'] = pywikibot.calledModuleName()

    # TODO: script_product should add the script version, if known
    values['script_product'] = pywikibot.calledModuleName()

    script_comments = []
    username = ''
    if site:
        script_comments.append(str(site))

        # TODO: there are several ways of identifying a user, and username
        # is not the best for a HTTP header if the username isnt ASCII.
        if site.username():
            username = user_agent_username(site.username())
            script_comments.append(
                'User:' + username)

    values.update({
        'family': site.family.name if site else '',
        'code': site.code if site else '',
        'lang': site.code if site else '',  # TODO: use site.lang, if known
        'site': str(site) if site else '',
        'username': username,
        'script_comments': '; '.join(script_comments)
    })

    if not format_string:
        format_string = config.user_agent_format

    formatted = format_string.format(**values)
    # clean up after any blank components
    formatted = formatted.replace(u'()', u'').replace(u'  ', u' ').strip()
    return formatted


@deprecate_arg('ssl', None)
def request(site=None, uri=None, *args, **kwargs):
    """Queue a request to be submitted to Site.

    All parameters not listed below are the same as
    L{httplib2.Http.request}.

    If the site argument is provided, the uri is relative to the site's
    scriptpath.

    If the site argument is None, the uri must be absolute, and is
    used for requests to non wiki pages.

    @param site: The Site to connect to
    @type site: L{pywikibot.site.Site}
    @param uri: the URI to retrieve
    @type uri: str
    @return: The received data (a unicode string).

    """
    assert(site or uri)
    if site:
        proto = site.protocol()
        if proto == 'https':
            host = site.ssl_hostname()
            uri = site.ssl_pathprefix() + uri
        else:
            host = site.hostname()
        baseuri = urlparse.urljoin("%s://%s" % (proto, host), uri)

        kwargs.setdefault("disable_ssl_certificate_validation",
                          site.ignore_certificate_error())
    else:
        baseuri = uri

    format_string = kwargs.setdefault("headers", {}).get("user-agent")
    kwargs["headers"]["user-agent"] = user_agent(site, format_string)

    request = threadedhttp.HttpRequest(baseuri, *args, **kwargs)
    http_queue.put(request)
    while not request.lock.acquire(False):
        time.sleep(0.1)

    # TODO: do some error correcting stuff
    if isinstance(request.data, SSLHandshakeError):
        if SSL_CERT_VERIFY_FAILED_MSG in str(request.data):
            raise FatalServerError(str(request.data))

    # if all else fails
    if isinstance(request.data, Exception):
        raise request.data

    if request.data[0].status == 504:
        raise Server504Error("Server %s timed out" % site.hostname())

    # HTTP status 207 is also a success status for Webdav FINDPROP,
    # used by the version module.
    if request.data[0].status not in (200, 207):
        pywikibot.warning(u"Http response status %(status)s"
                          % {'status': request.data[0].status})

    pos = request.data[0]['content-type'].find('charset=')
    if pos >= 0:
        pos += len('charset=')
        encoding = request.data[0]['content-type'][pos:]
    else:
        encoding = 'ascii'
        # Don't warn, many pages don't contain one
        pywikibot.log(u"Http response doesn't contain a charset.")

    return request.data[1].decode(encoding)
