# -*- coding: utf-8  -*-
"""Httplib2 threaded cookie layer.

This class extends httplib2, adding support for:
    - Cookies, guarded for cross-site redirects
    - Thread safe ConnectionPool class
    - HttpProcessor thread class
    - HttpRequest object

"""
from __future__ import unicode_literals

# (C) Pywikibot team, 2007-2014
# (C) Httplib 2 team, 2006
# (C) Metaweb Technologies, Inc., 2007
#
# Partially distributed under the MIT license
# Partially distributed under Metaweb Technologies, Incs license
#    which is compatible with the MIT license

__version__ = '$Id$'
__docformat__ = 'epytext'

# standard python libraries
import codecs
import re
import sys
import threading

if sys.version_info[0] > 2:
    from http import cookiejar as cookielib
    from urllib.parse import splittype, splithost, unquote, urlparse, urljoin
else:
    import cookielib
    from urlparse import urlparse, urljoin
    from urllib import splittype, splithost, unquote

import pywikibot

from pywikibot import config

from pywikibot.tools import UnicodeMixin

_logger = "comm.threadedhttp"


import httplib2


class ConnectionPool(object):

    """A thread-safe connection pool."""

    def __init__(self, maxnum=5):
        """
        Constructor.

        @param maxnum: Maximum number of connections per identifier.
                       The pool drops excessive connections added.

        """
        pywikibot.debug(u"Creating connection pool.", _logger)
        self.connections = {}
        self.lock = threading.Lock()
        self.maxnum = maxnum

    def __del__(self):
        """Destructor to close all connections in the pool."""
        self.lock.acquire()
        try:
            pywikibot.debug(u"Closing connection pool (%s connections)"
                            % len(self.connections),
                            _logger)
            for key in self.connections:
                for connection in self.connections[key]:
                    connection.close()
        except (AttributeError, TypeError):
            pass   # this shows up when logger has been destroyed first
        finally:
            self.lock.release()

    def __repr__(self):
        return self.connections.__repr__()

    def pop_connection(self, identifier):
        """Get a connection from identifier's connection pool.

        @param identifier: The pool identifier
        @return: A connection object if found, None otherwise

        """
        self.lock.acquire()
        try:
            if identifier in self.connections:
                if len(self.connections[identifier]) > 0:
                    pywikibot.debug(u"Retrieved connection from '%s' pool."
                                    % identifier,
                                    _logger)
                    return self.connections[identifier].pop()
            return None
        finally:
            self.lock.release()

    def push_connection(self, identifier, connection):
        """Add a connection to identifier's connection pool.

        @param identifier: The pool identifier
        @param connection: The connection to add to the pool

        """
        self.lock.acquire()
        try:
            if identifier not in self.connections:
                self.connections[identifier] = []

            if len(self.connections[identifier]) != self.maxnum:
                self.connections[identifier].append(connection)
            else:
                pywikibot.debug(u"closing %s connection %r"
                                % (identifier, connection),
                                _logger)
                connection.close()
                del connection
        finally:
            self.lock.release()


class Http(httplib2.Http):

    """Subclass of httplib2.Http that stores cookies.

    Overrides httplib2's internal redirect support to prevent cookies being
    eaten by the wrong sites.
    """

    def __init__(self, *args, **kwargs):
        """
        Constructor.

        @kwarg cookiejar: (optional) CookieJar to use. A new one will be
               used when not supplied.
        @kwarg connection_pool: (optional) Connection pool to use. A new one
               will be used when not supplied.
        @kwarg max_redirects: (optional) The maximum number of redirects to
               follow. 5 is default.
        @kwarg timeout: (optional) Socket timeout in seconds. Default is
               config.socket_timeout. Disable with None.

        """
        try:
            self.cookiejar = kwargs.pop('cookiejar')
        except KeyError:
            self.cookiejar = cookielib.CookieJar()

        try:
            self.connection_pool = kwargs.pop('connection_pool')
        except KeyError:
            self.connection_pool = ConnectionPool()
        self.max_redirects = kwargs.pop('max_redirects', 5)
        if len(args) < 3:
            kwargs.setdefault('proxy_info', config.proxy)
        kwargs.setdefault('timeout', config.socket_timeout)
        httplib2.Http.__init__(self, *args, **kwargs)

    def request(self, uri, method="GET", body=None, headers=None,
                max_redirects=None, connection_type=None):
        """Start an HTTP request.

        @param uri: The uri to retrieve
        @param method: (optional) The HTTP method to use. Default is 'GET'
        @param body: (optional) The request body. Default is no body.
        @param headers: (optional) Additional headers to send. Defaults
               include C{connection: keep-alive}, C{user-agent} and
               C{content-type}.
        @param max_redirects: (optional) The maximum number of redirects to
               use for this request. The class instance's max_redirects is
               default
        @param connection_type: (optional) see L{httplib2.Http.request}

        @return: (response, content) tuple

        """
        if max_redirects is None:
            max_redirects = self.max_redirects
        if headers is None:
            headers = {}
        # Prepare headers
        headers.pop('cookie', None)
        req = DummyRequest(uri, headers)
        self.cookiejar.add_cookie_header(req)

        headers = req.headers

        # Wikimedia squids: add connection: keep-alive to request headers
        # unless overridden
        headers['connection'] = headers.pop('connection', 'keep-alive')

        # determine connection pool key and fetch connection
        (scheme, authority, request_uri,
         defrag_uri) = httplib2.urlnorm(httplib2.iri2uri(uri))
        conn_key = scheme + ":" + authority

        connection = self.connection_pool.pop_connection(conn_key)
        if connection is not None:
            self.connections[conn_key] = connection

        # Redirect hack: we want to regulate redirects
        follow_redirects = self.follow_redirects
        self.follow_redirects = False
        pywikibot.debug(u"%r" % (
            (uri.replace("%7C", "|"), method, body,
             headers, max_redirects,
             connection_type),
        ), _logger)
        try:
            if authority in config.authenticate:
                self.add_credentials(*config.authenticate[authority])

            (response, content) = httplib2.Http.request(
                self, uri, method, body, headers,
                max_redirects, connection_type
            )
        except Exception as e:  # what types?
            # return exception instance to be retrieved by the calling thread
            return e
        finally:
            self.follow_redirects = follow_redirects

        # return connection to pool
        self.connection_pool.push_connection(conn_key,
                                             self.connections[conn_key])
        del self.connections[conn_key]

        # First write cookies
        self.cookiejar.extract_cookies(DummyResponse(response), req)

        # Check for possible redirects
        redirectable_response = ((response.status == 303) or
                                 (response.status in [300, 301, 302, 307] and
                                  method in ["GET", "HEAD"]))
        if (self.follow_redirects and (max_redirects > 0) and
                redirectable_response):
            # Return directly and not unpack the values in case the result was
            # an exception, which can't be unpacked
            return self._follow_redirect(
                uri, method, body, headers, response, content, max_redirects)
        else:
            return response, content

    def _follow_redirect(self, uri, method, body, headers, response,
                         content, max_redirects):
        """Internal function to follow a redirect recieved by L{request}."""
        (scheme, authority, absolute_uri,
         defrag_uri) = httplib2.urlnorm(httplib2.iri2uri(uri))
        if self.cache:
            cachekey = defrag_uri
        else:
            cachekey = None

        # Pick out the location header and basically start from the beginning
        # remembering first to strip the ETag header and decrement our 'depth'
        if "location" not in response and response.status != 300:
            raise httplib2.RedirectMissingLocation(
                "Redirected but the response is missing a Location: header.",
                response, content)
        # Fix-up relative redirects (which violate an RFC 2616 MUST)
        if "location" in response:
            location = response['location']
            (scheme, authority, path, query,
             fragment) = httplib2.parse_uri(location)
            if authority is None:
                response['location'] = urljoin(uri, location)
                pywikibot.debug(u"Relative redirect: changed [%s] to [%s]"
                                % (location, response['location']),
                                _logger)
        if response.status == 301 and method in ["GET", "HEAD"]:
            response['-x-permanent-redirect-url'] = response['location']
            if "content-location" not in response:
                response['content-location'] = absolute_uri
            httplib2._updateCache(headers, response, content, self.cache,
                                  cachekey)

        headers.pop('if-none-match', None)
        headers.pop('if-modified-since', None)

        if "location" in response:
            location = response['location']
            redirect_method = ((response.status == 303) and
                               (method not in ["GET", "HEAD"])
                               ) and "GET" or method
            return self.request(location, redirect_method, body=body,
                                headers=headers,
                                max_redirects=max_redirects - 1)
        else:
            return httplib2.RedirectLimit(
                "Redirected more times than redirection_limit allows.",
                response, content)


class HttpRequest(UnicodeMixin):

    """Object wrapper for HTTP requests that need to block origin thread.

    Usage:

    >>> from .http import Queue
    >>> queue = Queue.Queue()
    >>> cookiejar = cookielib.CookieJar()
    >>> connection_pool = ConnectionPool()
    >>> proc = HttpProcessor(queue, cookiejar, connection_pool)
    >>> proc.setDaemon(True)
    >>> proc.start()
    >>> request = HttpRequest('https://hostname.invalid/')
    >>> queue.put(request)
    >>> request.lock.acquire()
    True
    >>> print(type(request.data))
    <class 'httplib2.ServerNotFoundError'>
    >>> print(request.data)
    Unable to find the server at hostname.invalid
    >>> queue.put(None)  # Stop the http processor thread

    C{request.lock.acquire()} will block until the data is available.

    self.data will be either:
    * a tuple of (dict, unicode) if the request was successful
    * an exception
    """

    def __init__(self, uri, method="GET", body=None, headers=None,
                 callbacks=None, charset=None, **kwargs):
        """
        Constructor.

        See C{Http.request} for parameters.
        """
        self.uri = uri
        self.method = method
        self.body = body
        self.headers = headers
        if isinstance(charset, codecs.CodecInfo):
            self.charset = charset.name
        elif charset:
            self.charset = charset
        elif headers and 'accept-charset' in headers:
            self.charset = headers['accept-charset']
        else:
            self.charset = None

        self.callbacks = callbacks

        self.args = [uri, method, body, headers]
        self.kwargs = kwargs

        self._parsed_uri = None
        self._data = None
        self.lock = threading.Semaphore(0)

    def _join(self):
        """Block until response has arrived."""
        self.lock.acquire(True)

    @property
    def data(self):
        """Return the httplib2 response tuple."""
        if not self._data:
            self._join()

        assert(self._data)
        return self._data

    @data.setter
    def data(self, value):
        """Set the httplib2 response and invoke each callback."""
        self._data = value

        if self.callbacks:
            for callback in self.callbacks:
                callback(self)

    @property
    def exception(self):
        """Get the exception raised by httplib2, if any."""
        if isinstance(self.data, Exception):
            return self.data

    @property
    def response_headers(self):
        """Return the response headers."""
        if not self.exception:
            return self.data[0]

    @property
    def raw(self):
        """Return the raw response body."""
        if not self.exception:
            return self.data[1]

    @property
    def parsed_uri(self):
        """Return the parsed requested uri."""
        if not self._parsed_uri:
            self._parsed_uri = urlparse(self.uri)
        return self._parsed_uri

    @property
    def hostname(self):
        """Return the host of the request."""
        return self.parsed_uri.netloc

    @property
    def status(self):
        """HTTP response status.

        @rtype: int
        """
        return self.response_headers.status

    @property
    def header_encoding(self):
        """Return charset given by the response header."""
        if not hasattr(self, '_header_encoding'):
            pos = self.response_headers['content-type'].find('charset=')
            if pos >= 0:
                pos += len('charset=')
                encoding = self.response_headers['content-type'][pos:]
                self._header_encoding = encoding
            else:
                self._header_encoding = None
        return self._header_encoding

    @property
    def encoding(self):
        """Detect the response encoding."""
        if not hasattr(self, '_encoding'):
            if not self.charset and not self.header_encoding:
                pywikibot.log(u"Http response doesn't contain a charset.")
                charset = 'latin1'
            else:
                charset = self.charset
            if (self.header_encoding and codecs.lookup(self.header_encoding) !=
                    (codecs.lookup(charset) if charset else None)):
                if charset:
                    pywikibot.warning(u'Encoding "{0}" requested but "{1}" '
                                       'received in the header.'.format(
                        charset, self.header_encoding))
                try:
                    # TODO: Buffer decoded content, weakref does remove it too
                    #       early (directly after this method)
                    self.raw.decode(self.header_encoding)
                except UnicodeError as e:
                    self._encoding = e
                else:
                    self._encoding = self.header_encoding
            else:
                self._encoding = None

            if charset and (isinstance(self._encoding, Exception) or
                            not self._encoding):
                try:
                    self.raw.decode(charset)
                except UnicodeError as e:
                    self._encoding = e
                else:
                    self._encoding = charset

        if isinstance(self._encoding, Exception):
            raise self._encoding
        return self._encoding

    def decode(self, encoding, errors='strict'):
        """Return the decoded response."""
        return self.raw.decode(encoding, errors)

    @property
    def content(self):
        """Return the response decoded by the detected encoding."""
        return self.decode(self.encoding)

    def __unicode__(self):
        """Return the response decoded by the detected encoding."""
        return self.content

    def __bytes__(self):
        """Return the undecoded response."""
        return self.raw


class HttpProcessor(threading.Thread):

    """Thread object to spawn multiple HTTP connection threads."""

    def __init__(self, queue, cookiejar, connection_pool):
        """
        Constructor.

        @param queue: The C{Queue.Queue} object that contains L{HttpRequest}
               objects.
        @param cookiejar: The C{cookielib.CookieJar} cookie object to share among
               requests.
        @param connection_pool: The C{ConnectionPool} object which contains
               connections to share among requests.

        """
        threading.Thread.__init__(self)
        self.queue = queue
        self.http = Http(cookiejar=cookiejar, connection_pool=connection_pool)

    def run(self):
        # The Queue item is expected to either an HttpRequest object
        # or None (to shut down the thread)
        pywikibot.debug(u"Thread started, waiting for requests.", _logger)
        while True:
            item = self.queue.get()
            if item is None:
                pywikibot.debug(u"Shutting down thread.", _logger)
                return

            # This needs to be set per request, however it is only used
            # the first time the pooled connection is created.
            self.http.disable_ssl_certificate_validation = \
                item.kwargs.pop('disable_ssl_certificate_validation', False)
            try:
                item.data = self.http.request(*item.args, **item.kwargs)
            finally:
                if item.lock:
                    item.lock.release()
                # if data wasn't set others might hang; but wait on lock release
                assert(item._data)


# Metaweb Technologies, Inc. License:
#
# ========================================================================
# The following dummy classes are:
# ========================================================================
# Copyright (c) 2007, Metaweb Technologies, Inc.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above
#       copyright notice, this list of conditions and the following
#       disclaimer in the documentation and/or other materials provided
#       with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY METAWEB TECHNOLOGIES AND CONTRIBUTORS
# ``AS IS'' AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL METAWEB
# TECHNOLOGIES OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ========================================================================

class DummyRequest(object):

    """Simulated urllib2.Request object for httplib2.

    Implements only what's necessary for cookielib.CookieJar to work.
    """

    def __init__(self, url, headers=None):
        self.url = url
        self.headers = headers
        self.origin_req_host = cookielib.request_host(self)
        self.type, r = splittype(url)
        self.host, r = splithost(r)
        if self.host:
            self.host = unquote(self.host)

    def get_full_url(self):
        return self.url

    def get_origin_req_host(self):
        # TODO to match urllib2 this should be different for redirects
        return self.origin_req_host

    def get_type(self):
        return self.type

    def get_host(self):
        return self.host

    def get_header(self, key, default=None):
        return self.headers.get(key.lower(), default)

    def has_header(self, key):
        return key in self.headers

    def add_unredirected_header(self, key, val):
        # TODO this header should not be sent on redirect
        self.headers[key.lower()] = val

    def is_unverifiable(self):
        # TODO to match urllib2, this should be set to True when the
        #  request is the result of a redirect
        return False

    unverifiable = property(is_unverifiable)


class DummyResponse(object):

    """Simulated urllib2.Request object for httplib2.

    Implements only what's necessary for cookielib.CookieJar to work.
    """

    def __init__(self, response):
        self.response = response

    def info(self):
        return DummyMessage(self.response)


class DummyMessage(object):

    """Simulated mimetools.Message object for httplib2.

    Implements only what's necessary for cookielib.CookieJar to work.
    """

    def __init__(self, response):
        self.response = response

    def getheaders(self, k):
        k = k.lower()
        self.response.get(k.lower(), None)
        if k not in self.response:
            return []
        # return self.response[k].split(re.compile(',\\s*'))

        # httplib2 joins multiple values for the same header
        #  using ','.  but the netscape cookie format uses ','
        #  as part of the expires= date format.  so we have
        #  to split carefully here - header.split(',') won't do it.
        HEADERVAL = re.compile(r'\s*(([^,]|(,\s*\d))+)')
        return [h[0] for h in HEADERVAL.findall(self.response[k])]

    def get_all(self, k, failobj=None):
        rv = self.getheaders(k)
        if not rv:
            return failobj
        return rv
