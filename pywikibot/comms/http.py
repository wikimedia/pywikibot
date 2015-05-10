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
from __future__ import unicode_literals

#
# (C) Pywikibot team, 2007-2015
#
# Distributed under the terms of the MIT license.
#

__version__ = '$Id$'
__docformat__ = 'epytext'

import atexit
import sys
import time

from distutils.version import StrictVersion
from string import Formatter
from warnings import warn

# Verify that a working httplib2 is present.
try:
    import httplib2
except ImportError:
    print("Error: Python module httplib2 >= 0.6.0 is required.")
    sys.exit(1)

# httplib2 0.6.0 was released with __version__ as '$Rev$'
#                and no module variable CA_CERTS.
if httplib2.__version__ == '$Rev$' and 'CA_CERTS' not in httplib2.__dict__:
    httplib2.__version__ = '0.6.0'
if StrictVersion(httplib2.__version__) < StrictVersion("0.6.0"):
    print("Error: Python module httplib2 (%s) is not 0.6.0 or greater." %
          httplib2.__file__)
    sys.exit(1)

if sys.version_info[0] > 2:
    from ssl import SSLError as SSLHandshakeError
    import queue as Queue
    from http import cookiejar as cookielib
    from urllib.parse import quote
else:
    if 'SSLHandshakeError' in httplib2.__dict__:
        from httplib2 import SSLHandshakeError
    elif httplib2.__version__ == '0.6.0':
        from httplib2 import ServerNotFoundError as SSLHandshakeError

    import Queue
    import cookielib
    from urllib2 import quote

from pywikibot import config
from pywikibot.exceptions import (
    FatalServerError, Server504Error, Server414Error
)
from pywikibot.comms import threadedhttp
from pywikibot.tools import deprecate_arg
import pywikibot.version

if sys.version_info[:3] >= (2, 7, 9):
    # Python 2.7.9 includes a backport of the ssl module from Python 3
    # https://www.python.org/dev/peps/pep-0466/
    SSL_CERT_VERIFY_FAILED_MSG = "SSL: CERTIFICATE_VERIFY_FAILED"
else:
    # The OpenSSL error code for
    #   certificate verify failed
    # cf. `openssl errstr 14090086`
    SSL_CERT_VERIFY_FAILED_MSG = ":14090086:"

_logger = "comm.http"

# global variables

numthreads = 1
threads = []

connection_pool = threadedhttp.ConnectionPool()
http_queue = Queue.Queue()

cookie_jar = cookielib.LWPCookieJar(
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


class _UserAgentFormatter(Formatter):

    """User-agent formatter to load version/revision only if necessary."""

    def get_value(self, key, args, kwargs):
        """Get field as usual except for version and revision."""
        # This is the Pywikibot revision; also map it to {version} at present.
        if key == 'version' or key == 'revision':
            return pywikibot.version.getversiondict()['rev']
        else:
            return super(_UserAgentFormatter, self).get_value(key, args, kwargs)


_USER_AGENT_FORMATTER = _UserAgentFormatter()


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
    """
    Generate the user agent string for a given site and format.

    @param site: The site for which this user agent is intended. May be None.
    @type site: BaseSite
    @param format_string: The string to which the values will be added using
        str.format. Is using config.user_agent_format when it is None.
    @type format_string: basestring
    @return: The formatted user agent
    @rtype: unicode
    """
    values = USER_AGENT_PRODUCTS.copy()

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

    formatted = _USER_AGENT_FORMATTER.format(format_string, **values)
    # clean up after any blank components
    formatted = formatted.replace(u'()', u'').replace(u'  ', u' ').strip()
    return formatted


@deprecate_arg('ssl', None)
def request(site=None, uri=None, method='GET', body=None, headers=None,
            **kwargs):
    """
    Request to Site with default error handling and response decoding.

    See L{httplib2.Http.request} for additional parameters.

    If the site argument is provided, the uri is a relative uri from
    and including the document root '/'.

    If the site argument is None, the uri must be absolute.

    @param site: The Site to connect to
    @type site: L{pywikibot.site.BaseSite}
    @param uri: the URI to retrieve
    @type uri: str
    @param charset: Either a valid charset (usable for str.decode()) or None
        to automatically chose the charset from the returned header (defaults
        to latin-1)
    @type charset: CodecInfo, str, None
    @return: The received data
    @rtype: a unicode string
    """
    assert(site or uri)
    if not site:
        warn('Invoking http.request without argument site is deprecated. '
             'Use http.fetch.', DeprecationWarning, 2)
        r = fetch(uri, method, body, headers, **kwargs)
        return r.content

    baseuri = site.base_url(uri)

    kwargs.setdefault("disable_ssl_certificate_validation",
                      site.ignore_certificate_error())

    if not headers:
        headers = {}
        format_string = None
    else:
        format_string = headers.get('user-agent', None)

    headers['user-agent'] = user_agent(site, format_string)

    r = fetch(baseuri, method, body, headers, **kwargs)
    return r.content


def error_handling_callback(request):
    """
    Raise exceptions and log alerts.

    @param request: Request that has completed
    @rtype request: L{threadedhttp.HttpRequest}
    """
    # TODO: do some error correcting stuff
    if isinstance(request.data, SSLHandshakeError):
        if SSL_CERT_VERIFY_FAILED_MSG in str(request.data):
            raise FatalServerError(str(request.data))

    # if all else fails
    if isinstance(request.data, Exception):
        raise request.data

    if request.status == 504:
        raise Server504Error("Server %s timed out" % request.hostname)

    if request.status == 414:
        raise Server414Error('Too long GET request')

    # HTTP status 207 is also a success status for Webdav FINDPROP,
    # used by the version module.
    if request.status not in (200, 207):
        pywikibot.warning(u"Http response status %(status)s"
                          % {'status': request.data[0].status})


def _enqueue(uri, method="GET", body=None, headers=None, **kwargs):
    """
    Enqueue non-blocking threaded HTTP request with callback.

    Callbacks, including the default error handler if enabled, are run in the
    HTTP thread, where exceptions are logged but are not able to be caught.
    The default error handler is called first, then 'callback' (singular),
    followed by each callback in 'callbacks' (plural).  All callbacks are
    invoked, even if the default error handler detects a problem, so they
    must check request.exception before using the response data.

    Note: multiple async requests do not automatically run concurrently,
    as they are limited by the number of http threads in L{numthreads},
    which is set to 1 by default.

    @see: L{httplib2.Http.request} for parameters.

    @kwarg default_error_handling: Use default error handling
    @type default_error_handling: bool
    @kwarg callback: Method to call once data is fetched
    @type callback: callable
    @kwarg callbacks: Methods to call once data is fetched
    @type callbacks: list of callable
    @rtype: L{threadedhttp.HttpRequest}
    """
    default_error_handling = kwargs.pop('default_error_handling', None)
    callback = kwargs.pop('callback', None)

    callbacks = []
    if default_error_handling:
        callbacks.append(error_handling_callback)
    if callback:
        callbacks.append(callback)

    callbacks += kwargs.pop('callbacks', [])

    if not headers:
        headers = {}

    user_agent_format_string = headers.get("user-agent", None)
    if not user_agent_format_string or '{' in user_agent_format_string:
        headers["user-agent"] = user_agent(None, user_agent_format_string)

    request = threadedhttp.HttpRequest(
        uri, method, body, headers, callbacks, **kwargs)
    http_queue.put(request)
    return request


def fetch(uri, method="GET", body=None, headers=None,
          default_error_handling=True, **kwargs):
    """
    Blocking HTTP request.

    Note: The callback runs in the HTTP thread, where exceptions are logged
    but are not able to be caught.

    See L{httplib2.Http.request} for parameters.

    @param default_error_handling: Use default error handling
    @type default_error_handling: bool
    @rtype: L{threadedhttp.HttpRequest}
    """
    request = _enqueue(uri, method, body, headers, **kwargs)
    request._join()  # wait for it
    assert(request._data)  # if there's no data in the answer we're in trouble
    # Run the error handling callback in the callers thread so exceptions
    # may be caught.
    if default_error_handling:
        error_handling_callback(request)
    return request
