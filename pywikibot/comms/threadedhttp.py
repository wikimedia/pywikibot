# -*- coding: utf-8 -*-
"""Http backend layer, formerly providing a httplib2 wrapper."""
#
# (C) Pywikibot team, 2007-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals


__docformat__ = 'epytext'

# standard python libraries
import codecs
import re

import pywikibot
from pywikibot.tools import deprecated, PY2, UnicodeMixin

if not PY2:
    from urllib.parse import urlparse
else:
    from urlparse import urlparse


_logger = 'comm.threadedhttp'


class HttpRequest(UnicodeMixin):

    """Object wrapper for HTTP requests that need to block origin thread.

    self.data will be either:
    * a tuple of (dict, unicode) if the request was successful
    * an exception
    """

    def __init__(self, uri, method='GET', params=None, body=None, headers=None,
                 callbacks=None, charset=None, **kwargs):
        """
        Initializer.

        See C{Http.request} for parameters.
        """
        self.uri = uri
        self.method = method
        self.params = params
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

    @property
    def data(self):
        """Return the requests response tuple."""
        assert(self._data is not None)
        return self._data

    @data.setter
    def data(self, value):
        """Set the requests response and invoke each callback."""
        self._data = value

        if self.callbacks:
            for callback in self.callbacks:
                callback(self)

    @property
    def exception(self):
        """Get the exception, if any."""
        if isinstance(self.data, Exception):
            return self.data

    @property
    def response_headers(self):
        """Return the response headers."""
        if not self.exception:
            return self.data.headers

    @property
    def raw(self):
        """Return the raw response body."""
        if not self.exception:
            return self.data.content

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
        """Return the HTTP response status.

        @rtype: int
        """
        if not self.exception:
            return self.data.status_code

    @property
    def header_encoding(self):
        """Return charset given by the response header."""
        if not hasattr(self, '_header_encoding'):
            content_type = self.response_headers.get('content-type', '')
            pos = content_type.find('charset=')
            if pos >= 0:
                pos += len('charset=')
                encoding = self.response_headers['content-type'][pos:]
                self._header_encoding = encoding
            elif 'json' in content_type:
                # application/json | application/sparql-results+json
                self._header_encoding = 'utf-8'
            elif 'xml' in content_type:
                header = self.raw[:100].splitlines()[0]  # bytestr in py3
                m = re.search(br'encoding=("|'
                              br"')(?P<encoding>.+?)\1", header)
                if m:
                    self._header_encoding = m.group('encoding').decode('utf-8')
                else:
                    self._header_encoding = 'utf-8'
            else:
                self._header_encoding = None
        return self._header_encoding

    @property
    def encoding(self):
        """Detect the response encoding."""
        if not hasattr(self, '_encoding'):
            if not self.charset and not self.header_encoding:
                pywikibot.log("Http response doesn't contain a charset.")
                charset = 'latin1'
            else:
                charset = self.charset
            if (self.header_encoding
                and codecs.lookup(
                    self.header_encoding) != (
                        codecs.lookup(charset) if charset else None)):
                if charset:
                    pywikibot.warning(
                        'Encoding "{0}" requested but "{1}" '
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

            if charset and (isinstance(self._encoding, Exception)
                            or not self._encoding):
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
    @deprecated('the `text` property', since='20180321')
    def content(self):
        """DEPRECATED. Return the response decoded by the detected encoding."""
        return self.text

    @property
    def text(self):
        """Return the response decoded by the detected encoding."""
        return self.decode(self.encoding)

    def __unicode__(self):
        """Return the response decoded by the detected encoding."""
        return self.text

    def __bytes__(self):
        """Return the undecoded response."""
        return self.raw
