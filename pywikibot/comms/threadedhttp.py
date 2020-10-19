# -*- coding: utf-8 -*-
"""Http backend layer providing a HTTP requests wrapper."""
#
# (C) Pywikibot team, 2007-2020
#
# Distributed under the terms of the MIT license.
#
import codecs
import re

from typing import Dict, Optional
from urllib.parse import urlparse

import pywikibot
from pywikibot.tools import deprecated


_logger = 'comms.threadedhttp'


class HttpRequest:

    """Object wrapper for HTTP requests that need to block origin thread.

    self.data will be either:
    * a tuple of (dict, str) if the request was successful
    * an exception
    """

    def __init__(self, uri, method='GET', params=None, body=None, headers=None,
                 callbacks=None, charset=None, **kwargs):
        """Initializer.

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
    def exception(self) -> Optional[Exception]:
        """Get the exception, if any."""
        return self.data if isinstance(self.data, Exception) else None

    @property
    def response_headers(self) -> Optional[Dict[str, str]]:
        """Return the response headers."""
        return self.data.headers if not self.exception else None

    @property
    def raw(self) -> Optional[bytes]:
        """Return the raw response body."""
        return self.data.content if not self.exception else None

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
        return self.data.status_code if not self.exception else None

    @property
    def header_encoding(self):
        """Return charset given by the response header."""
        if hasattr(self, '_header_encoding'):
            return self._header_encoding

        content_type = self.response_headers.get('content-type', '')
        m = re.search('charset=(?P<charset>.*?$)', content_type)
        if m:
            self._header_encoding = m.group('charset')
        elif 'json' in content_type:
            # application/json | application/sparql-results+json
            self._header_encoding = 'utf-8'
        elif 'xml' in content_type:
            header = self.raw[:100].splitlines()[0]  # bytes
            m = re.search(
                br'encoding=(["\'])(?P<encoding>.+?)\1', header)
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
            if self.charset is None and self.header_encoding is None:
                pywikibot.log("Http response doesn't contain a charset.")
                charset = 'latin1'
            else:
                charset = self.charset

            if self.header_encoding is not None \
               and (charset is None
                    or codecs.lookup(self.header_encoding)
                    != codecs.lookup(charset)):
                if charset:
                    pywikibot.warning(
                        'Encoding "{}" requested but "{}" received in the '
                        'header.'.format(charset, self.header_encoding))

                # TODO: Buffer decoded content, weakref does remove it too
                #       early (directly after this method)
                self._encoding = self._try_decode(self.header_encoding)
            else:
                self._encoding = None

            if charset and (isinstance(self._encoding, Exception)
                            or self._encoding is None):
                self._encoding = self._try_decode(charset)

        if isinstance(self._encoding, Exception):
            raise self._encoding
        return self._encoding

    def _try_decode(self, encoding):
        """Helper function to try decoding."""
        try:
            self.raw.decode(encoding)
        except UnicodeError as e:
            result = e
        else:
            result = encoding
        return result

    def decode(self, encoding, errors='strict') -> str:
        """Return the decoded response."""
        return self.raw.decode(encoding, errors)

    @property
    @deprecated('the `text` property', since='20180321')
    def content(self) -> str:
        """DEPRECATED. Return the response decoded by the detected encoding."""
        return self.text

    @property
    def text(self) -> str:
        """Return the response decoded by the detected encoding."""
        return self.decode(self.encoding)

    def __str__(self) -> str:
        """Return the response decoded by the detected encoding."""
        return self.text

    def __bytes__(self) -> Optional[bytes]:
        """Return the undecoded response."""
        return self.raw
