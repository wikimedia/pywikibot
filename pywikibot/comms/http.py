# -*- coding: utf-8 -*-
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
# (C) Pywikibot team, 2007-2020
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals


__docformat__ = 'epytext'

import atexit
import sys

from string import Formatter
from warnings import warn

import requests

from pywikibot import __version__, __url__, config
from pywikibot.bot import calledModuleName
from pywikibot.comms import threadedhttp
from pywikibot.exceptions import (
    FatalServerError, Server504Error, Server414Error
)
from pywikibot.logging import critical, debug, error, log, warning
from pywikibot.tools import (
    deprecated,
    deprecate_arg,
    file_mode_checker,
    issue_deprecation_warning,
    PY2,
    StringTypes,
)
import pywikibot.version

try:
    import requests_oauthlib
except ImportError as e:
    requests_oauthlib = e

if not PY2:
    from http import cookiejar as cookielib
    from urllib.parse import quote, urlparse
else:
    import cookielib
    from urllib2 import quote
    from urlparse import urlparse


# The error message for failed SSL certificate verification
# 'certificate verify failed' is a commonly detectable string
SSL_CERT_VERIFY_FAILED_MSG = 'certificate verify failed'

_logger = 'comm.http'


# Should be marked as deprecated after PywikibotCookieJar is removed.
def mode_check_decorator(func):
    """Decorate load()/save() CookieJar methods."""
    def wrapper(cls, **kwargs):
        try:
            filename = kwargs['filename']
        except KeyError:
            filename = cls.filename
        res = func(cls, **kwargs)
        file_mode_checker(filename, mode=0o600)
        return res
    return wrapper


# in PY2 cookielib.LWPCookieJar is not a new-style class.
class PywikibotCookieJar(cookielib.LWPCookieJar, object):

    """DEPRECATED. CookieJar which checks file permissions."""

    @deprecated(since='20181007')
    def __init__(self, *args, **kwargs):
        """Initialize the class."""
        super(PywikibotCookieJar, self).__init__(*args, **kwargs)

    @mode_check_decorator
    def load(self, **kwargs):
        """Load cookies from file."""
        super(PywikibotCookieJar, self).load()

    @mode_check_decorator
    def save(self, **kwargs):
        """Save cookies to file."""
        super(PywikibotCookieJar, self).save()


cookie_file_path = config.datafilepath('pywikibot.lwp')
file_mode_checker(cookie_file_path, create=True)
cookie_jar = cookielib.LWPCookieJar(cookie_file_path)
try:
    cookie_jar.load()
except cookielib.LoadError:
    debug('Loading cookies failed.', _logger)
else:
    debug('Loaded cookies from file.', _logger)

session = requests.Session()
session.cookies = cookie_jar


# Prepare flush on quit
def _flush():
    log('Closing network session.')
    session.close()

    if hasattr(sys, 'last_type'):
        critical('Exiting due to uncaught exception {}'.format(sys.last_type))

    log('Network session closed.')


atexit.register(_flush)

USER_AGENT_PRODUCTS = {
    'python': 'Python/' + '.'.join(str(i) for i in sys.version_info),
    'http_backend': 'requests/' + requests.__version__,
    'pwb': 'Pywikibot/' + __version__,
}


class _UserAgentFormatter(Formatter):

    """User-agent formatter to load version/revision only if necessary."""

    def get_value(self, key, args, kwargs):
        """Get field as usual except for version and revision."""
        # This is the Pywikibot revision; also map it to {version} at present.
        if key == 'version' or key == 'revision':
            return pywikibot.version.getversiondict()['rev']
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
    @rtype: str
    """
    values = USER_AGENT_PRODUCTS.copy()

    script_name = calledModuleName()

    values['script'] = script_name

    # TODO: script_product should add the script version, if known
    values['script_product'] = script_name

    script_comments = []
    username = ''
    if config.user_agent_description:
        script_comments.append(config.user_agent_description)
    if site:
        script_comments.append(str(site))

        # TODO: there are several ways of identifying a user, and username
        # is not the best for a HTTP header if the username isn't ASCII.
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
    formatted = formatted.replace('()', '').replace('  ', ' ').strip()
    return formatted


@deprecated('pywikibot.comms.http.fake_user_agent', since='20161205')
def get_fake_user_agent():
    """
    Return a fake user agent depending on `fake_user_agent` option in config.

    Deprecated, use fake_user_agent() instead.

    @rtype: str
    """
    if isinstance(config.fake_user_agent, StringTypes):
        return config.fake_user_agent
    if config.fake_user_agent is False:
        return user_agent()
    return fake_user_agent()


def fake_user_agent():
    """
    Return a fake user agent.

    @rtype: str
    """
    try:
        from fake_useragent import UserAgent
    except ImportError:
        raise ImportError(  # Actually complain when fake_useragent is missing.
            'fake_useragent must be installed to get fake UAs.')
    return UserAgent().random


@deprecate_arg('ssl', None)
def request(site=None, uri=None, method='GET', params=None, body=None,
            headers=None, data=None, **kwargs):
    """
    Request to Site with default error handling and response decoding.

    See L{requests.Session.request} for additional parameters.

    If the site argument is provided, the uri is a relative uri from
    and including the document root '/'.

    If the site argument is None, the uri must be absolute.

    @param site: The Site to connect to
    @type site: L{pywikibot.site.BaseSite}
    @param uri: the URI to retrieve
    @type uri: str
    @keyword charset: Either a valid charset (usable for str.decode()) or None
        to automatically chose the charset from the returned header (defaults
        to latin-1)
    @type charset: CodecInfo, str, None
    @return: The received data
    @rtype: a unicode string
    """
    # body and data parameters both map to the data parameter of
    # requests.Session.request.
    if data:
        body = data

    assert(site or uri)
    if not site:
        # +1 because of @deprecate_arg
        issue_deprecation_warning(
            'Invoking http.request without argument site', 'http.fetch()', 3,
            since='20150814')
        r = fetch(uri, method, params, body, headers, **kwargs)
        return r.text

    kwargs.setdefault('disable_ssl_certificate_validation',
                      site.ignore_certificate_error())

    if not headers:
        headers = {}
        format_string = None
    else:
        format_string = headers.get('user-agent')
    headers['user-agent'] = user_agent(site, format_string)

    baseuri = site.base_url(uri)
    r = fetch(baseuri, method, params, body, headers, **kwargs)
    site.throttle.retry_after = int(r.response_headers.get('retry-after', 0))
    return r.text


def get_authentication(uri):
    """
    Retrieve authentication token.

    @param uri: the URI to access
    @type uri: str
    @return: authentication token
    @rtype: None or tuple of two str
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
                 .format(path=path, length=len(config.authenticate[path]),
                         url=__url__))
    return None


def _http_process(session, http_request):
    """
    Process an `threadedhttp.HttpRequest` instance.

    @param session: Session that will be used to process the `http_request`.
    @type session: L{requests.Session}
    @param http_request: Request that will be processed.
    @type http_request: L{threadedhttp.HttpRequest}
    @return: None
    @rtype: None
    """
    method = http_request.method
    uri = http_request.uri
    params = http_request.params
    body = http_request.body
    headers = http_request.headers
    if PY2 and headers:
        headers = {key: str(value) for key, value in headers.items()}
    auth = get_authentication(uri)
    if auth is not None and len(auth) == 4:
        if isinstance(requests_oauthlib, ImportError):
            warn('%s' % requests_oauthlib, ImportWarning)
            error('OAuth authentication not supported: %s'
                  % requests_oauthlib)
            auth = None
        else:
            auth = requests_oauthlib.OAuth1(*auth)
    timeout = config.socket_timeout
    try:
        ignore_validation = http_request.kwargs.pop(
            'disable_ssl_certificate_validation', False)
        # Note that the connections are pooled which mean that a future
        # HTTPS request can succeed even if the certificate is invalid and
        # verify=True, when a request with verify=False happened before
        response = session.request(method, uri, params=params, data=body,
                                   headers=headers, auth=auth, timeout=timeout,
                                   verify=not ignore_validation,
                                   **http_request.kwargs)
    except Exception as e:
        http_request.data = e
    else:
        http_request.data = response


def error_handling_callback(request):
    """
    Raise exceptions and log alerts.

    @param request: Request that has completed
    @type request: L{threadedhttp.HttpRequest}
    """
    # TODO: do some error correcting stuff
    if isinstance(request.data, requests.exceptions.SSLError):
        if SSL_CERT_VERIFY_FAILED_MSG in str(request.data):
            raise FatalServerError(str(request.data))

    # if all else fails
    if isinstance(request.data, Exception):
        error('An error occurred for uri ' + request.uri)
        raise request.data

    if request.status == 504:
        raise Server504Error('Server %s timed out' % request.hostname)

    if request.status == 414:
        raise Server414Error('Too long GET request')

    # HTTP status 207 is also a success status for Webdav FINDPROP,
    # used by the version module.
    if request.status not in (200, 207):
        warning('Http response status {0}'.format(request.data.status_code))


def _enqueue(uri, method='GET', params=None, body=None, headers=None,
             data=None, **kwargs):
    """
    Enqueue non-blocking threaded HTTP request with callback.

    Callbacks, including the default error handler if enabled, are run in the
    HTTP thread, where exceptions are logged but are not able to be caught.
    The default error handler is called first, then 'callback' (singular),
    followed by each callback in 'callbacks' (plural). All callbacks are
    invoked, even if the default error handler detects a problem, so they
    must check request.exception before using the response data.

    Note: multiple async requests do not automatically run concurrently,
    as they are limited by the number of http threads in L{numthreads},
    which is set to 1 by default.

    @see: L{requests.Session.request} for parameters.

    @kwarg default_error_handling: Use default error handling
    @type default_error_handling: bool
    @kwarg callback: Method to call once data is fetched
    @type callback: callable
    @kwarg callbacks: Methods to call once data is fetched
    @type callbacks: list of callable
    @rtype: L{threadedhttp.HttpRequest}
    """
    # body and data parameters both map to the data parameter of
    # requests.Session.request.
    if data:
        body = data

    default_error_handling = kwargs.pop('default_error_handling', None)
    callback = kwargs.pop('callback', None)

    callbacks = []
    if default_error_handling:
        callbacks.append(error_handling_callback)
    if callback:
        callbacks.append(callback)

    callbacks += kwargs.pop('callbacks', [])

    all_headers = config.extra_headers.copy()
    all_headers.update(headers or {})

    user_agent_format_string = all_headers.get('user-agent')
    if not user_agent_format_string or '{' in user_agent_format_string:
        all_headers['user-agent'] = user_agent(None, user_agent_format_string)

    request = threadedhttp.HttpRequest(
        uri, method, params, body, all_headers, callbacks, **kwargs)
    _http_process(session, request)
    return request


def fetch(uri, method='GET', params=None, body=None, headers=None,
          default_error_handling=True, use_fake_user_agent=False, data=None,
          **kwargs):
    """
    Blocking HTTP request.

    Note: The callback runs in the HTTP thread, where exceptions are logged
    but are not able to be caught.

    See L{requests.Session.request} for parameters.

    @param default_error_handling: Use default error handling
    @type default_error_handling: bool
    @type use_fake_user_agent: bool, str
    @param use_fake_user_agent: Set to True to use fake UA, False to use
        pywikibot's UA, str to specify own UA. This behaviour might be
        overridden by domain in config.
    @rtype: L{threadedhttp.HttpRequest}
    """
    # body and data parameters both map to the data parameter of
    # requests.Session.request.
    if data:
        body = data

    # Change user agent depending on fake UA settings.
    # Set header to new UA if needed.
    headers = headers or {}
    # Skip if already specified in request.
    if not headers.get('user-agent', None):
        # Get fake UA exceptions from `fake_user_agent_exceptions` config.
        uri_domain = urlparse(uri).netloc
        use_fake_user_agent = config.fake_user_agent_exceptions.get(
            uri_domain, use_fake_user_agent)

        if use_fake_user_agent and isinstance(
                use_fake_user_agent, StringTypes):  # Custom UA.
            headers['user-agent'] = use_fake_user_agent
        elif use_fake_user_agent is True:
            headers['user-agent'] = fake_user_agent()

    request = _enqueue(uri, method, params, body, headers, **kwargs)
    # if there's no data in the answer we're in trouble
    assert request._data is not None
    # Run the error handling callback in the callers thread so exceptions
    # may be caught.
    if default_error_handling:
        error_handling_callback(request)
    return request
