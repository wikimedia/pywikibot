# -*- coding: utf-8  -*-
""" Httplib2 threaded cookie layer

This class extends httplib2, adding support for:
    - Cookies, guarded for cross-site redirects
    - Thread safe ConnectionPool and LockableCookieJar classes
    - HttpProcessor thread class
    - HttpRequest object

"""

# (C) 2007 Pywikipedia bot team, 2007
# (C) 2006 Httplib 2 team, 2006
# (C) 2007 Metaweb Technologies, Inc.
#
# Partially distributed under the MIT license
# Partially distributed under Metaweb Technologies, Incs license
#    which is compatible with the MIT license

__version__ = '$Id$'
__docformat__ = 'epytext'

# standard python libraries
import re
import threading
import time
import logging

import urllib
import cookielib
import sys

import pywikibot
from pywikibot import config

_logger = "comm.threadedhttp"


# easy_install safeguarded dependencies
try:
    import pkg_resources
except ImportError:
    pywikibot.error(
        u"Error: You need the python module setuptools to use this module")
    sys.exit(1)
try:
    import httplib2
except ImportError:
    pkg_resources.require("httplib2")

class ConnectionPool(object):
    """A thread-safe connection pool."""

    def __init__(self, maxnum=5):
        """
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
        except AttributeError:
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

            if len(self.connections[identifier]) == self.maxnum:
                pywikibot.debug(u"closing %s connection %r"
                                     % (identifier, connection),
                                _logger)
                connection.close()
                del connection
            else:
                self.connections[identifier].append(connection)
        finally:
            self.lock.release()


class LockableCookieJar(cookielib.LWPCookieJar):
    """CookieJar with integrated Lock object."""
    def __init__(self, *args, **kwargs):
        cookielib.LWPCookieJar.__init__(self, *args, **kwargs)
        self.lock = threading.Lock()


class Http(httplib2.Http):
    """Subclass of httplib2.Http that stores cookies.

    Overrides httplib2's internal redirect support to prevent cookies being
    eaten by the wrong sites.

    """
    def __init__(self, *args, **kwargs):
        """
        @param cookiejar: (optional) CookieJar to use. A new one will be
               used when not supplied.
        @param connection_pool: (optional) Connection pool to use. A new one
               will be used when not supplied.
        @param max_redirects: (optional) The maximum number of redirects to
               follow. 5 is default.

        """
        try:
            self.cookiejar = kwargs.pop('cookiejar')
        except KeyError:
            self.cookiejar = LockableCookieJar()
        try:
            self.connection_pool = kwargs.pop('connection_pool')
        except KeyError:
            self.connection_pool = ConnectionPool()
        self.max_redirects = kwargs.pop('max_redirects', 5)
        if len(args) < 3:
            kwargs.setdefault('proxy_info', config.proxy)
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
        self.cookiejar.lock.acquire()
        try:
            self.cookiejar.add_cookie_header(req)
        finally:
            self.cookiejar.lock.release()
        headers = req.headers

        # Wikimedia squids: add connection: keep-alive to request headers
        # unless overridden
        headers['connection'] = headers.pop('connection', 'keep-alive')

        # determine connection pool key and fetch connection
        (scheme, authority, request_uri, defrag_uri) = httplib2.urlnorm(
                                                        httplib2.iri2uri(uri))
        conn_key = scheme+":"+authority

        connection = self.connection_pool.pop_connection(conn_key)
        if connection is not None:
            self.connections[conn_key] = connection

        # Redirect hack: we want to regulate redirects
        follow_redirects = self.follow_redirects
        self.follow_redirects = False
        pywikibot.debug(u"%r" % (
                            (uri.replace("%7C","|"), method, body,
                            headers, max_redirects,
                            connection_type),),
                        _logger)
        try:
            (response, content) = httplib2.Http.request(
                                    self, uri, method, body, headers,
                                    max_redirects, connection_type)
        except Exception, e: # what types?
            # return exception instance to be retrieved by the calling thread
            return e
        self.follow_redirects = follow_redirects

        # return connection to pool
        self.connection_pool.push_connection(conn_key,
                                             self.connections[conn_key])
        del self.connections[conn_key]

        # First write cookies
        self.cookiejar.lock.acquire()
        try:
            self.cookiejar.extract_cookies(DummyResponse(response), req)
        finally:
            self.cookiejar.lock.release()

        # Check for possible redirects
        redirectable_response = ((response.status == 303) or
                                 (response.status in [300, 301, 302, 307] and
                                    method in ["GET", "HEAD"]))
        if self.follow_redirects and (max_redirects > 0) \
                                 and redirectable_response:
            (response, content) = self._follow_redirect(
                uri, method, body, headers, response, content, max_redirects)

        return (response, content)

    def _follow_redirect(self, uri, method, body, headers, response,
                         content, max_redirects):
        """Internal function to follow a redirect recieved by L{request}"""
        (scheme, authority, absolute_uri, defrag_uri) = httplib2.urlnorm(
                                                          httplib2.iri2uri(uri))
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
            (scheme, authority, path, query, fragment) = httplib2.parse_uri(
                                                                    location)
            if authority == None:
                response['location'] = httplib2.urlparse.urljoin(uri, location)
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
            raise RedirectLimit(
                "Redirected more times than redirection_limit allows.",
                response, content)


class HttpRequest(object):
    """Object wrapper for HTTP requests that need to block origin thread.

    Usage:

    >>> request = HttpRequest('http://www.google.com')
    >>> queue.put(request)
    >>> request.lock.acquire()
    >>> print request.data

    C{request.lock.acquire()} will block until the data is available.

    """
    def __init__(self, *args, **kwargs):
        """See C{Http.request} for parameters."""
        self.args = args
        self.kwargs = kwargs
        self.data = None
        self.lock = threading.Semaphore(0)


class HttpProcessor(threading.Thread):
    """Thread object to spawn multiple HTTP connection threads."""
    def __init__(self, queue, cookiejar, connection_pool):
        """
        @param queue: The C{Queue.Queue} object that contains L{HttpRequest}
               objects.
        @param cookiejar: The C{LockableCookieJar} cookie object to share among
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
        while (True):
            item = self.queue.get()
            if item is None:
                pywikibot.debug(u"Shutting down thread.", _logger)
                return
            try:
                item.data = self.http.request(*item.args, **item.kwargs)
            finally:
                if item.lock:
                    item.lock.release()


# Metaweb Technologies, Inc. License:
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
    """Simulated urllib2.Request object for httplib2
       implements only what's necessary for cookielib.CookieJar to work
    """
    def __init__(self, url, headers=None):
        self.url = url
        self.headers = headers
        self.origin_req_host = cookielib.request_host(self)
        self.type, r = urllib.splittype(url)
        self.host, r = urllib.splithost(r)
        if self.host:
            self.host = urllib.unquote(self.host)

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

class DummyResponse(object):
    """Simulated urllib2.Request object for httplib2
       implements only what's necessary for cookielib.CookieJar to work
    """
    def __init__(self, response):
        self.response = response

    def info(self):
        return DummyMessage(self.response)

class DummyMessage(object):
    """Simulated mimetools.Message object for httplib2
       implements only what's necessary for cookielib.CookieJar to work
    """
    def __init__(self, response):
        self.response = response

    def getheaders(self, k):
        k = k.lower()
        v = self.response.get(k.lower(), None)
        if k not in self.response:
            return []
        #return self.response[k].split(re.compile(',\\s*'))

        # httplib2 joins multiple values for the same header
        #  using ','.  but the netscape cookie format uses ','
        #  as part of the expires= date format.  so we have
        #  to split carefully here - header.split(',') won't do it.
        HEADERVAL= re.compile(r'\s*(([^,]|(,\s*\d))+)')
        return [h[0] for h in HEADERVAL.findall(self.response[k])]
