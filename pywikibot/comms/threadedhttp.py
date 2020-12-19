# -*- coding: utf-8 -*-
"""Http backend layer providing a HTTP requests wrapper."""
#
# (C) Pywikibot team, 2007-2020
#
# Distributed under the terms of the MIT license.
#
import codecs
import re

from typing import Optional
from urllib.parse import urlparse

import pywikibot
from pywikibot.tools import (
    deprecated,
    deprecated_args,
    issue_deprecation_warning,
    PYTHON_VERSION,
)

if PYTHON_VERSION >= (3, 9):
    Dict = dict
else:
    from typing import Dict

_logger = 'comms.threadedhttp'


class HttpRequest:

    """Object wrapper for HTTP requests.

    self.data will be either:
    * requests.Response object if the request was successful
    * an exception
    """

    @deprecated_args(uri=True, method=True, params=True, body=True,
                     headers=True, all_headers=True)
    def __init__(self, url=None, method=None, params=None, body=None,
                 all_headers=None, callbacks=None, charset=None, **kwargs):
        """Initializer."""
        if isinstance(charset, codecs.CodecInfo):
            self.charset = charset.name
        else:
            self.charset = charset

        self._kwargs = kwargs
        self._parsed_uri = None
        self._data = None

        # deprecate positional parameters
        if url:
            issue_deprecation_warning("'url' parameter", depth=3,
                                      warning_class=FutureWarning,
                                      since='20201211')
        if method:
            issue_deprecation_warning("'method' parameter",
                                      warning_class=FutureWarning,
                                      since='20201211')
        if params:
            issue_deprecation_warning("'params' parameter",
                                      warning_class=FutureWarning,
                                      since='20201211')
        if body:
            issue_deprecation_warning("'body' parameter",
                                      warning_class=FutureWarning,
                                      since='20201211')
        if all_headers:
            issue_deprecation_warning("'all_headers' parameter",
                                      warning_class=FutureWarning,
                                      since='20201211')
        if callbacks:
            issue_deprecation_warning("'callbacks' parameter",
                                      warning_class=FutureWarning,
                                      since='20201211')
        if kwargs:
            for item in kwargs.items():
                issue_deprecation_warning('{}={!r} parameter'.format(*item),
                                          warning_class=FutureWarning,
                                          since='20201211')

    def __getattr__(self, name):
        """Delegate undefined method calls to request.Response object."""
        if self.exception and name in ('content', 'status_code'):
            return None
        return getattr(self.data, name)

    @property
    @deprecated(since='20201211', future_warning=True)
    def args(self):  # pragma: no cover
        """DEPRECATED: Return predefined argument list."""
        return [
            self.url,
            self.request.method,
            self.request.body,
            self.all_headers,
        ]

    @property
    @deprecated('the `request.body` attribute',
                since='20201211', future_warning=True)
    def body(self):  # pragma: no cover
        """DEPRECATED: Return request body attribute."""
        return self.request.body

    @property
    @deprecated(since='20201211', future_warning=True)
    def kwargs(self):  # pragma: no cover
        """DEPRECATED: Return request body attribute."""
        return self._kwargs

    @property
    @deprecated('the `request.method` attribute',
                since='20201211', future_warning=True)
    def method(self):  # pragma: no cover
        """DEPRECATED: Return request body attribute."""
        return self.request.method

    @property
    @deprecated('the `url` attribute', since='20201011', future_warning=True)
    def uri(self):  # pragma: no cover
        """DEPRECATED. Return the response URL."""
        return self.url

    @property
    @deprecated('the `request.headers` property', since='20201011',
                future_warning=True)
    def headers(self):  # pragma: no cover
        """DEPRECATED. Return the response headers."""
        return self.request.headers

    @property
    @deprecated('the `request.headers` property', since='20201211',
                future_warning=True)
    def all_headers(self):  # pragma: no cover
        """DEPRECATED. Return the response headers."""
        return self.request.headers

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
    @deprecated('the `content` property', since='20201210',
                future_warning=True)
    def raw(self) -> Optional[bytes]:  # pragma: no cover
        """DEPRECATED. Return the raw response body.

        @note: The behaviour will be changed.
        """
        return self.content

    @property
    @deprecated('urlparse(HttpRequest.url)',
                since='20201011', future_warning=True)
    def parsed_uri(self):  # pragma: no cover
        """DEPRECATED. Return the parsed requested uri."""
        if not self._parsed_uri:
            self._parsed_uri = urlparse(self.uri)
        return self._parsed_uri

    @property
    @deprecated('urlparse(HttpRequest.url).netloc',
                since='20201011', future_warning=True)
    def hostname(self):  # pragma: no cover
        """DEPRECATED. Return the host of the request."""
        return self.parsed_uri.netloc

    @property
    @deprecated('the `status_code` property', since='20201011',
                future_warning=True)
    def status(self) -> Optional[int]:  # pragma: no cover
        """DEPRECATED. Return the HTTP response status."""
        return self.status_code

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
            header = self.content[:100].splitlines()[0]  # bytes
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
        if hasattr(self, '_encoding'):
            return self._encoding

        if self.charset is None and self.request is not None:
            self.charset = self.request.headers.get('accept-charset')

        if self.charset is None and self.header_encoding is None:
            pywikibot.log("Http response doesn't contain a charset.")
            charset = 'latin1'
        else:
            charset = self.charset

        _encoding = UnicodeError()
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
            _encoding = self._try_decode(self.header_encoding)

        if charset and isinstance(_encoding, Exception):
            _encoding = self._try_decode(charset)

        if isinstance(_encoding, Exception):
            raise _encoding
        else:
            self._encoding = _encoding
        return self._encoding

    def _try_decode(self, encoding):
        """Helper function to try decoding."""
        try:
            self.content.decode(encoding)
        except UnicodeError as e:
            result = e
        else:
            result = encoding
        return result

    @deprecated('the `text` property', since='20201011', future_warning=True)
    def decode(self, encoding, errors='strict') -> str:  # pragma: no cover
        """Return the decoded response."""
        return self.content.decode(
            encoding, errors) if not self.exception else None

    @property
    def text(self) -> str:
        """Return the response decoded by the detected encoding."""
        return self.content.decode(self.encoding)

    @deprecated('the `text` property', since='20201011', future_warning=True)
    def __str__(self) -> str:  # pragma: no cover
        """Return the response decoded by the detected encoding."""
        return self.text

    @deprecated(since='20201011', future_warning=True)
    def __bytes__(self) -> Optional[bytes]:  # pragma: no cover
        """Return the undecoded response."""
        return self.content
