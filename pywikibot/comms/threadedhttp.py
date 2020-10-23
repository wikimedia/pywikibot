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
from pywikibot.tools import deprecated, deprecated_args


_logger = 'comms.threadedhttp'


class HttpRequest:

    """Object wrapper for HTTP requests that need to block origin thread.

    self.data will be either:
    * a tuple of (dict, str) if the request was successful
    * an exception
    """

    @deprecated_args(headers='all_headers', uri='url')
    def __init__(self, url, method='GET', params=None, body=None,
                 all_headers=None, callbacks=None, charset=None, **kwargs):
        """Initializer.

        See C{Http.request} for parameters.
        """
        self.url = url
        self.method = method
        self.params = params
        self.body = body
        self.all_headers = all_headers
        if isinstance(charset, codecs.CodecInfo):
            self.charset = charset.name
        elif charset:
            self.charset = charset
        elif all_headers and 'accept-charset' in all_headers:
            self.charset = all_headers['accept-charset']
        else:
            self.charset = None

        self.callbacks = callbacks

        self.args = [url, method, body, all_headers]
        self.kwargs = kwargs

        self._parsed_uri = None
        self._data = None

    @property
    @deprecated('the `url` attribute', since='20201011', future_warning=True)
    def uri(self):
        """DEPRECATED. Return the response URL."""
        return self.url

    @uri.setter
    @deprecated('the `url` attribute', since='20201011', future_warning=True)
    def uri(self, value):
        """DEPRECATED. Set the response URL."""
        self.url = value

    @property
    @deprecated('the `all_headers` property', since='20201011',
                future_warning=True)
    def headers(self):
        """DEPRECATED. Return the response headers."""
        return self.all_headers

    @headers.setter
    @deprecated('the `all_headers` property', since='20201011',
                future_warning=True)
    def headers(self, value):
        """DEPRECATED. Set the response headers."""
        self.all_headers = value

    @property
    def data(self):
        """DEPRECATED. Return the requests response tuple.

        @note: This property will removed.
        """
        assert(self._data is not None)
        return self._data

    @data.setter
    def data(self, value):
        """DEPRECATED. Set the requests response and invoke each callback.

        @note: This property setter will removed.
        """
        self._data = value

        if self.callbacks:
            for callback in self.callbacks:
                callback(self)

    @property
    def exception(self) -> Optional[Exception]:
        """DEPRECATED. Get the exception, if any.

        @note: This property will removed.
        """
        return self.data if isinstance(self.data, Exception) else None

    @property
    def response_headers(self) -> Optional[Dict[str, str]]:
        """DEPRECATED. Return the response headers.

        @note: This property will renamed to headers.
        """
        return self.data.headers if not self.exception else None

    @property
    def raw(self) -> Optional[bytes]:
        """Return the raw response body."""
        return self.data.content if not self.exception else None

    @property
    @deprecated('urlparse(HttpRequest.url)',
                since='20201011', future_warning=True)
    def parsed_uri(self):
        """DEPRECATED. Return the parsed requested uri."""
        if not self._parsed_uri:
            self._parsed_uri = urlparse(self.uri)
        return self._parsed_uri

    @property
    @deprecated('urlparse(HttpRequest.url).netloc',
                since='20201011', future_warning=True)
    def hostname(self):
        """DEPRECATED. Return the host of the request."""
        return self.parsed_uri.netloc

    @property
    @deprecated('the `status_code` property', since='20201011',
                future_warning=True)
    def status(self) -> Optional[int]:
        """DEPRECATED. Return the HTTP response status."""
        return self.status_code

    @property
    def status_code(self) -> Optional[int]:
        """Return the HTTP response status."""
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

    @deprecated('the `text` property', since='20201011', future_warning=True)
    def decode(self, encoding, errors='strict') -> str:
        """Return the decoded response."""
        return self.raw.decode(encoding,
                               errors) if not self.exception else None

    @property
    @deprecated('the `text` property', since='20180321', future_warning=True)
    def content(self) -> str:
        """DEPRECATED. Return the response decoded by the detected encoding.

        @note: The behaviour will be changed.
            This method will return the content of the response in bytes.
        """
        return self.text

    @property
    def text(self) -> str:
        """Return the response decoded by the detected encoding."""
        return self.raw.decode(self.encoding)

    @deprecated('the `text` property', since='20201011', future_warning=True)
    def __str__(self) -> str:
        """Return the response decoded by the detected encoding."""
        return self.text

    @deprecated(since='20201011', future_warning=True)
    def __bytes__(self) -> Optional[bytes]:
        """Return the undecoded response."""
        return self.raw
