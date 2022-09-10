"""
Basic HTTP access interface.

This module handles communication between the bot and the HTTP threads.

This module is responsible for
    - Setting up a connection pool
    - Providing a (blocking) interface for HTTP requests
    - Translate site objects with query strings into URLs
    - URL-encoding all data
    - Basic HTTP error handling

This module creates and uses its own ``requests.Session`` object.
The session is closed if the module terminates.
If required you can use your own Session object passing it to the
``http.session`` variable::

    from pywikibot.comms import http
    session = requests.Session()
    http.session = session

:py:obj:`flush()` can be called to close the session object.
"""
#
# (C) Pywikibot team, 2007-2022
#
# Distributed under the terms of the MIT license.
#
import atexit
import codecs
import re
import sys
from contextlib import suppress
from http import HTTPStatus, cookiejar
from string import Formatter
from typing import Optional, Union
from urllib.parse import quote, urlparse
from warnings import warn

import requests

import pywikibot
from pywikibot import config
from pywikibot.backports import Tuple
from pywikibot.exceptions import (
    FatalServerError,
    Server414Error,
    Server504Error,
)
from pywikibot.logging import critical, debug, error, log, warning
from pywikibot.tools import file_mode_checker


try:
    import requests_oauthlib
except ImportError as e:
    requests_oauthlib = e


# The error message for failed SSL certificate verification
# 'certificate verify failed' is a commonly detectable string
SSL_CERT_VERIFY_FAILED_MSG = 'certificate verify failed'

cookie_file_path = config.datafilepath('pywikibot.lwp')
file_mode_checker(cookie_file_path, create=True)
cookie_jar = cookiejar.LWPCookieJar(cookie_file_path)
try:
    cookie_jar.load(ignore_discard=True)
except cookiejar.LoadError:
    debug('Loading cookies failed.')
else:
    debug('Loaded cookies from file.')

session = requests.Session()
session.cookies = cookie_jar


# Prepare flush on quit
def flush() -> None:  # pragma: no cover
    """Close the session object. This is called when the module terminates."""
    log('Closing network session.')
    session.close()

    if hasattr(sys, 'last_type'):
        critical('Exiting due to uncaught exception {}'.format(sys.last_type))

    log('Network session closed.')


atexit.register(flush)

USER_AGENT_PRODUCTS = {
    'python': 'Python/' + '.'.join(str(i) for i in sys.version_info),
    'http_backend': 'requests/' + requests.__version__,
    'pwb': 'Pywikibot/' + pywikibot.__version__,
}


class _UserAgentFormatter(Formatter):

    """User-agent formatter to load version/revision only if necessary."""

    def get_value(self, key, args, kwargs):
        """Get field as usual except for version and revision."""
        # This is the Pywikibot version; also map it to {revision} at present.
        if key in ('version', 'revision'):
            return pywikibot.version.getversiondict()['rev']
        return super().get_value(key, args, kwargs)


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
        username = quote(username.encode('utf-8'))
    else:
        # % is legal in the default $wgLegalTitleChars
        # This is so that ops know the real pywikibot will not
        # allow a useragent in the username to allow through a hand-coded
        # percent-encoded value.
        if '%' in username:
            username = quote(username)
    return username


def user_agent(site=None, format_string: str = None) -> str:
    """
    Generate the user agent string for a given site and format.

    :param site: The site for which this user agent is intended. May be None.
    :type site: BaseSite
    :param format_string: The string to which the values will be added using
        str.format. Is using config.user_agent_format when it is None.
    :return: The formatted user agent
    """
    values = USER_AGENT_PRODUCTS.copy()
    values.update(dict.fromkeys(['script', 'script_product'],
                                pywikibot.bot.calledModuleName()))

    script_comments = []
    if config.user_agent_description:
        script_comments.append(config.user_agent_description)

    values['family'] = ''
    values['code'] = ''
    values['lang'] = ''  # TODO: use site.lang, if known
    values['site'] = ''

    username = ''
    if site:
        script_comments.append(str(site))

        # TODO: there are several ways of identifying a user, and username
        # is not the best for a HTTP header if the username isn't ASCII.
        if site.username():
            username = user_agent_username(site.username())
            script_comments.append('User:' + username)

        values.update({
            'family': site.family.name,
            'code': site.code,
            'lang': site.code,  # TODO: use site.lang, if known
            'site': str(site),
        })

    values['username'] = username
    values['script_comments'] = '; '.join(script_comments)

    format_string = format_string or config.user_agent_format

    formatted = _USER_AGENT_FORMATTER.format(format_string, **values)
    # clean up after any blank components
    formatted = formatted.replace('()', '').replace('  ', ' ').strip()
    return formatted


def fake_user_agent() -> str:
    """Return a fake user agent."""
    try:
        from fake_useragent import UserAgent
    except ImportError:
        raise ImportError(  # Actually complain when fake_useragent is missing.
            'fake_useragent must be installed to get fake UAs.')
    return UserAgent().random


def request(site,
            uri: Optional[str] = None,
            headers: Optional[dict] = None,
            **kwargs) -> requests.Response:
    """
    Request to Site with default error handling and response decoding.

    See :py:obj:`requests.Session.request` for additional parameters.

    The optional uri is a relative uri from site base uri including the
    document root '/'.

    :param site: The Site to connect to
    :type site: pywikibot.site.BaseSite
    :param uri: the URI to retrieve
    :keyword charset: Either a valid charset (usable for str.decode()) or None
        to automatically chose the charset from the returned header (defaults
        to latin-1)
    :type charset: CodecInfo, str, None
    :return: The received data Response
    """
    kwargs.setdefault('verify', site.verify_SSL_certificate())
    if not headers:
        headers = {}
        format_string = None
    else:
        format_string = headers.get('user-agent')
    headers['user-agent'] = user_agent(site, format_string)

    baseuri = site.base_url(uri)
    r = fetch(baseuri, headers=headers, **kwargs)
    site.throttle.retry_after = int(r.headers.get('retry-after', 0))
    return r


def get_authentication(uri: str) -> Optional[Tuple[str, str]]:
    """
    Retrieve authentication token.

    :param uri: the URI to access
    :return: authentication token
    """
    parsed_uri = requests.utils.urlparse(uri)
    netloc_parts = parsed_uri.netloc.split('.')
    netlocs = [parsed_uri.netloc] + ['.'.join(['*'] + netloc_parts[i + 1:])
                                     for i in range(len(netloc_parts))]
    for path in netlocs:
        if path in config.authenticate:
            if len(config.authenticate[path]) in [2, 4]:
                return config.authenticate[path]
            warn('config.authenticate["{path}"] has invalid value.\n'
                 'It should contain 2 or 4 items, not {length}.\n'
                 'See {url}/OAuth for more info.'
                 .format(path=path,
                         length=len(config.authenticate[path]),
                         url=pywikibot.__url__))
    return None


def error_handling_callback(response):
    """
    Raise exceptions and log alerts.

    :param response: Response returned by Session.request().
    :type response: :py:obj:`requests.Response`
    """
    # TODO: do some error correcting stuff
    if isinstance(response, requests.exceptions.SSLError) \
       and SSL_CERT_VERIFY_FAILED_MSG in str(response):
        raise FatalServerError(str(response))

    if isinstance(response, requests.ConnectionError):
        msg = str(response)
        if 'NewConnectionError' in msg \
           and re.search(r'\[Errno (-2|8|11001)\]', msg):
            raise ConnectionError(response)

    if isinstance(response, Exception):
        with suppress(Exception):
            # request exception may contain response and request attribute
            error('An error occurred for uri ' + response.request.url)
        raise response from None

    if response.status_code == HTTPStatus.GATEWAY_TIMEOUT:
        raise Server504Error('Server {} timed out'
                             .format(urlparse(response.url).netloc))

    if response.status_code == HTTPStatus.REQUEST_URI_TOO_LONG:
        raise Server414Error('Too long GET request')

    # TODO: shall it raise? this might break some code, TBC
    # response.raise_for_status()

    # HTTP status 207 is also a success status for Webdav FINDPROP,
    # used by the version module.
    if response.status_code not in (HTTPStatus.OK, HTTPStatus.MULTI_STATUS):
        warning('Http response status {}'.format(response.status_code))


def fetch(uri: str, method: str = 'GET', headers: Optional[dict] = None,
          default_error_handling: bool = True,
          use_fake_user_agent: Union[bool, str] = False, **kwargs):
    """
    HTTP request.

    See :py:obj:`requests.Session.request` for parameters.

    :param uri: URL to send
    :param method: HTTP method of the request (default: GET)
    :param headers: dictionary of headers of the request
    :param default_error_handling: Use default error handling
    :param use_fake_user_agent: Set to True to use fake UA, False to use
        pywikibot's UA, str to specify own UA. This behaviour might be
        overridden by domain in config.

    :keyword charset: Either a valid charset (usable for str.decode()) or None
        to automatically chose the charset from the returned header (defaults
        to latin-1)
    :type charset: CodecInfo, str, None
    :keyword verify: verify the SSL certificate (default is True)
    :type verify: bool or path to certificates
    :keyword callbacks: Methods to call once data is fetched
    :type callbacks: list of callable
    :rtype: :py:obj:`requests.Response`
    """
    # Change user agent depending on fake UA settings.
    # Set header to new UA if needed.
    headers = headers or {}
    headers.update(config.extra_headers.copy() or {})

    def assign_fake_user_agent(use_fake_user_agent, uri):
        uri_domain = urlparse(uri).netloc
        use_fake_user_agent = config.fake_user_agent_exceptions.get(
            uri_domain, use_fake_user_agent)

        if use_fake_user_agent is False:
            return user_agent()
        if use_fake_user_agent is True:
            return fake_user_agent()
        if use_fake_user_agent and isinstance(use_fake_user_agent, str):
            return use_fake_user_agent  # Custom UA.
        raise ValueError('Invalid parameter: '
                         'use_fake_user_agent={}'.format(use_fake_user_agent))

    def assign_user_agent(user_agent_format_string):
        if not user_agent_format_string or '{' in user_agent_format_string:
            return user_agent(None, user_agent_format_string)
        # do nothing, it is already a UA
        return user_agent_format_string

    # If not already specified.
    if 'user-agent' not in headers:
        # Get fake UA exceptions from `fake_user_agent_exceptions` config.
        headers['user-agent'] = assign_fake_user_agent(use_fake_user_agent,
                                                       uri)
    # Already specified.
    else:
        headers['user-agent'] = assign_user_agent(headers.get('user-agent'))

    callbacks = kwargs.pop('callbacks', [])
    # error_handling_callback will be executed first.
    if default_error_handling:
        callbacks.insert(0, error_handling_callback)

    charset = kwargs.pop('charset', None)

    auth = get_authentication(uri)
    if auth is not None and len(auth) == 4:
        if isinstance(requests_oauthlib, ImportError):
            warn(str(requests_oauthlib), ImportWarning)
            error('OAuth authentication not supported: {}'
                  .format(requests_oauthlib))
            auth = None
        else:
            auth = requests_oauthlib.OAuth1(*auth)

    timeout = config.socket_timeout

    try:
        # Note that the connections are pooled which mean that a future
        # HTTPS request can succeed even if the certificate is invalid and
        # verify=True, when a request with verify=False happened before
        response = session.request(method, uri,
                                   headers=headers, auth=auth, timeout=timeout,
                                   **kwargs)
    except Exception as e:
        response = e
    else:
        response.encoding = _decide_encoding(response, charset)

    for callback in callbacks:
        callback(response)

    return response


# Extract charset (from content-type header)
CHARSET_RE = re.compile(
    r'charset\s*=\s*(?P<q>[\'"]?)(?P<charset>[^\'",;>/]+)(?P=q)',
    flags=re.I,
)


def get_charset_from_content_type(content_type: str) -> Optional[str]:
    """Get charset from the content-type header.

    .. versionadded:: 7.3
    """
    m = CHARSET_RE.search(content_type)
    if not m:
        return None
    charset = m.group('charset').strip('"\' ').lower()
    # Convert to python correct encoding names
    if re.sub(r'[ _\-]', '', charset) == 'xeucjp':
        charset = 'euc_jp'
    else:
        # fix cp encodings (T304830, T307760, T312230)
        # remove delimiter in front of the code number
        # replace win/windows with cp
        # remove language code in font of win/windows
        charset = re.sub(
            r'\A(?:cp[ _\-]|(?:[a-z]+[_\-]?)?win(?:dows)?[_\-]?)(\d{3,4})',
            r'cp\1', charset)
    return charset


def _get_encoding_from_response_headers(response) -> Optional[str]:
    """Return charset given by the response header."""
    content_type = response.headers.get('content-type')

    if not content_type:
        return None

    charset = get_charset_from_content_type(content_type)
    if charset:
        header_encoding = charset
    elif 'json' in content_type:
        # application/json | application/sparql-results+json
        header_encoding = 'utf-8'
    elif 'xml' in content_type:
        header = response.content[:100].splitlines()[0]  # bytes
        m = re.search(
            br'encoding=(["\'])(?P<encoding>.+?)\1', header)
        if m:
            header_encoding = m.group('encoding').decode('utf-8')
        else:
            header_encoding = 'utf-8'
    else:
        header_encoding = None

    return header_encoding


def _decide_encoding(response, charset) -> Optional[str]:
    """Detect the response encoding."""
    def _try_decode(content, encoding):
        """Helper function to try decoding."""
        if encoding is None:
            return None

        try:
            content.decode(encoding)
        except LookupError:
            pywikibot.warning('Unknown or invalid encoding {!r}'
                              .format(encoding))
        except UnicodeDecodeError as e:
            pywikibot.warning('{} found in {}'.format(e, content))
        else:
            return encoding

        return None  # let chardet do the job

    header_encoding = _get_encoding_from_response_headers(response)
    if header_encoding is None:
        pywikibot.log('Http response does not contain a charset.')

    if charset is None:
        charset = response.request.headers.get('accept-charset')

    # No charset requested, or in request headers or response headers.
    # Defaults to latin1.
    if charset is None:
        return _try_decode(response.content, header_encoding or 'latin1')

    if header_encoding is None:
        return _try_decode(response.content, charset)

    # Both charset and header_encoding are available.
    header_codecs = charset_codecs = None
    with suppress(LookupError):
        header_codecs = codecs.lookup(header_encoding)

    with suppress(LookupError):
        charset_codecs = codecs.lookup(charset)

    if header_codecs and charset_codecs and header_codecs != charset_codecs:
        pywikibot.warning(
            'Encoding "{}" requested but "{}" received in the '
            'response header.'.format(charset, header_encoding))

    _encoding = _try_decode(response.content, header_encoding) \
        or _try_decode(response.content, charset)

    return _encoding
