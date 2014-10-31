# -*- coding: utf-8  -*-
"""Interface to Mediawiki's api.php."""
#
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

from collections import MutableMapping
from pywikibot.comms import http
from email.mime.nonmultipart import MIMENonMultipart
import datetime
import hashlib
import json
import os
try:
    import cPickle as pickle
except ImportError:
    import pickle
import pprint
import re
import traceback
import time

import pywikibot
from pywikibot import config, login
from pywikibot.tools import MediaWikiVersion as LV, deprecated
from pywikibot.exceptions import Server504Error, FatalServerError, Error

import sys

if sys.version_info[0] > 2:
    # Subclassing necessary to fix a possible bug of the email package
    # in py3: see http://bugs.python.org/issue19003
    # The following solution might be removed if/once the bug is fixed,
    # unless the fix is not backported to py3.x versions that should
    # instead support PWB.
    basestring = (str, )
    from urllib.parse import urlencode, unquote
    unicode = str

    from io import BytesIO

    import email.generator
    from email.mime.multipart import MIMEMultipart as MIMEMultipartOrig

    class CTEBinaryBytesGenerator(email.generator.BytesGenerator):

        """Workaround for bug in python 3 email handling of CTE binary."""

        def __init__(self, *args, **kwargs):
            super(CTEBinaryBytesGenerator, self).__init__(*args, **kwargs)
            self._writeBody = self._write_body

        def _write_body(self, msg):
            if msg['content-transfer-encoding'] == 'binary':
                self._fp.write(msg.get_payload(decode=True))
            else:
                super(CTEBinaryBytesGenerator, self)._handle_text(msg)

    class CTEBinaryMIMEMultipart(MIMEMultipartOrig):

        """Workaround for bug in python 3 email handling of CTE binary."""

        def as_bytes(self, unixfrom=False, policy=None):
            """Return unmodified binary payload."""
            policy = self.policy if policy is None else policy
            fp = BytesIO()
            g = CTEBinaryBytesGenerator(fp, mangle_from_=False, policy=policy)
            g.flatten(self, unixfrom=unixfrom)
            return fp.getvalue()

    MIMEMultipart = CTEBinaryMIMEMultipart
else:
    from urllib import urlencode, unquote
    from email.mime.multipart import MIMEMultipart

_logger = "data.api"

lagpattern = re.compile(r"Waiting for [\d.]+: (?P<lag>\d+) seconds? lagged")


class APIError(Error):

    """The wiki site returned an error message."""

    def __init__(self, code, info, **kwargs):
        """Save error dict returned by MW API."""
        self.code = code
        self.info = info
        self.other = kwargs
        self.unicode = unicode(self.__str__())

    def __repr__(self):
        return '{name}("{code}", "{info}", {other})'.format(
            name=self.__class__.__name__, **self.__dict__)

    def __str__(self):
        return "%(code)s: %(info)s" % self.__dict__


class UploadWarning(APIError):

    """Upload failed with a warning message (passed as the argument)."""

    def __init__(self, code, message):
        super(UploadWarning, self).__init__(code, message)

    @property
    def message(self):
        return self.info


class APIMWException(APIError):

    """The API site returned an error about a MediaWiki internal exception."""

    def __init__(self, mediawiki_exception_class_name, info, **kwargs):
        """Save error dict returned by MW API."""
        self.mediawiki_exception_class_name = mediawiki_exception_class_name
        code = 'internal_api_error_' + mediawiki_exception_class_name
        super(APIMWException, self).__init__(code, info, **kwargs)


class TimeoutError(Error):

    """API request failed with a timeout error."""


class EnableSSLSiteWrapper(object):

    """Wrapper to change the site protocol to https."""

    def __init__(self, site):
        self._site = site

    def __repr__(self):
        return repr(self._site)

    def __eq__(self, other):
        return self._site == other

    def __getattr__(self, attr):
        return getattr(self._site, attr)

    def protocol(self):
        return 'https'


class Request(MutableMapping):

    """A request to a Site's api.php interface.

    Attributes of this object (except for the special parameters listed
    below) get passed as commands to api.php, and can be get or set using
    the dict interface.  All attributes must be strings (or unicode).  Use
    an empty string for parameters that don't require a value. For example,
    Request(action="query", titles="Foo bar", prop="info", redirects="")
    corresponds to the API request
    "api.php?action=query&titles=Foo%20bar&prop=info&redirects"

    This is the lowest-level interface to the API, and can be used for any
    request that a particular site's API supports. See the API documentation
    (https://www.mediawiki.org/wiki/API) and site-specific settings for
    details on what parameters are accepted for each request type.

    Uploading files is a special case: to upload, the parameter "mime" must
    be true, and the parameter "file" must be set equal to a valid
    filename on the local computer, _not_ to the content of the file.

    Returns a dict containing the JSON data returned by the wiki. Normally,
    one of the dict keys will be equal to the value of the 'action'
    parameter.  Errors are caught and raise an APIError exception.

    Example:

    >>> r = Request(action="query", meta="userinfo")
    >>> # This is equivalent to
    >>> # https://{path}/api.php?action=query&meta=userinfo&format=json
    >>> # change a parameter
    >>> r['meta'] = "userinfo|siteinfo"
    >>> # add a new parameter
    >>> r['siprop'] = "namespaces"
    >>> # note that "uiprop" param gets added automatically
    >>> r.action  # doctest: +IGNORE_UNICODE
    u'query'
    >>> sorted(r._params.keys())  # doctest: +IGNORE_UNICODE
    [u'action', u'meta', u'siprop']
    >>> r._params['action']  # doctest: +IGNORE_UNICODE
    [u'query']
    >>> r._params['meta']  # doctest: +IGNORE_UNICODE
    [u'userinfo', u'siteinfo']
    >>> r._params['siprop']  # doctest: +IGNORE_UNICODE
    [u'namespaces']
    >>> data = r.submit()  # doctest: +IGNORE_UNICODE
    >>> isinstance(data, dict)
    True
    >>> set(['query', 'batchcomplete', 'warnings']).issuperset(data.keys())
    True
    >>> 'query' in data
    True
    >>> sorted(data[u'query'].keys())  # doctest: +IGNORE_UNICODE
    ['namespaces', 'userinfo']

    """

    def __init__(self, **kwargs):
        """
        Constructor.

        @kwarg site: The Site to which the request will be submitted. If not
               supplied, uses the user's configured default Site.
        @kwarg mime: If true, send in "multipart/form-data" format (default False)
        @kwarg mime_params: A dictionary of parameter which should only be
               transferred via mime mode. If not None sets mime to True.
        @kwarg max_retries: (optional) Maximum number of times to retry after
               errors, defaults to 25
        @kwarg retry_wait: (optional) Minimum time to wait after an error,
               defaults to 5 seconds (doubles each retry until max of 120 is
               reached)
        @kwarg format: (optional) Defaults to "json"
        """
        try:
            self.site = kwargs.pop("site")
        except KeyError:
            self.site = pywikibot.Site()
        if 'mime_params' in kwargs:
            self.mime_params = kwargs.pop('mime_params')
            # mime may not be different from mime_params
            if 'mime' in kwargs and kwargs.pop('mime') != self.mime:
                raise ValueError('If mime_params is set, mime may not differ '
                                 'from it.')
        else:
            self.mime = kwargs.pop('mime', False)
        self.throttle = kwargs.pop('throttle', True)
        self.max_retries = kwargs.pop("max_retries", pywikibot.config.max_retries)
        self.retry_wait = kwargs.pop("retry_wait", pywikibot.config.retry_wait)
        self._params = {}
        if "action" not in kwargs:
            raise ValueError("'action' specification missing from Request.")
        self.action = kwargs['action']
        self.update(**kwargs)
        self._warning_handler = None
        # Actions that imply database updates on the server, used for various
        # things like throttling or skipping actions when we're in simulation
        # mode
        self.write = self.action in (
            "edit", "move", "rollback", "delete", "undelete",
            "protect", "block", "unblock", "watch", "patrol",
            "import", "userrights", "upload", "emailuser",
            "createaccount", "setnotificationtimestamp",
            "filerevert", "options", "purge", "revisiondelete",
            "wbeditentity", "wbsetlabel", "wbsetdescription",
            "wbsetaliases", "wblinktitles", "wbsetsitelink",
            "wbcreateclaim", "wbremoveclaims", "wbsetclaimvalue",
            "wbsetreference", "wbremovereferences"
        )
        # MediaWiki 1.23 allows assertion for any action,
        # whereas earlier WMF wikis and others used an extension which
        # could only allow assert for action=edit.
        #
        # When we can't easily check whether the extension is loaded,
        # to avoid cyclic recursion in the Pywikibot codebase, assume
        # that it is present, which will cause a API warning emitted
        # to the logging (console) if it is not present, but will not
        # otherwise be a problem.
        # This situation is only tripped when one of the first actions
        # on the site is a write action and the extension isn't installed.
        if ((self.write and LV(self.site.version()) >= LV("1.23")) or
                (self.action == 'edit' and
                 self.site.has_extension('AssertEdit'))):
            pywikibot.debug(u"Adding user assertion", _logger)
            self["assert"] = 'user'  # make sure user is logged in

        if (self.site.protocol() == 'http' and (config.use_SSL_always or (
                self.action == 'login' and config.use_SSL_onlogin))
                and self.site.family.name in config.available_ssl_project):
            self.site = EnableSSLSiteWrapper(self.site)

    # implement dict interface
    def __getitem__(self, key):
        return self._params[key]

    def __setitem__(self, key, value):
        """Set MediaWiki API request parameter.

        @param key: param key
        @type key: basestring
        @param value: param value
        @type value: list of unicode, unicode, or str in site encoding
            Any string type may use a |-separated list
        """
        # Allow site encoded bytes (note: str is a subclass of bytes in py2)
        if isinstance(value, bytes):
            value = value.decode(self.site.encoding())

        if isinstance(value, unicode):
            value = value.split("|")

        try:
            iter(value)
        except TypeError:
            # convert any non-iterable value into a single-element list
            value = [unicode(value)]

        self._params[key] = value

    def __delitem__(self, key):
        del self._params[key]

    def keys(self):
        return list(self._params.keys())

    def __contains__(self, key):
        return self._params.__contains__(key)

    def __iter__(self):
        return self._params.__iter__()

    def __len__(self):
        return len(self._params)

    def iteritems(self):
        return iter(self._params.items())

    def items(self):
        """Return a list of tuples containg the parameters in any order."""
        return list(self._params.items())

    @property
    def mime(self):
        """Return whether mime parameters are defined."""
        return self.mime_params is not None

    @mime.setter
    def mime(self, value):
        """
        Change whether mime parameter should be defined.

        This will clear the mime parameters.
        """
        try:
            self.mime_params = dict(value)
        except TypeError:
            self.mime_params = {} if value else None

    @deprecated('_http_param_string')
    def http_params(self):
        """Return the parameters formatted for inclusion in an HTTP request.

        DEPRECATED.  See _encoded_items for explanation of encoding used.
        """
        self._add_defaults()
        return self._http_param_string()

    def _add_defaults(self):
        """
        Add default parameters to the API request.

        This method will only add them once.
        """
        if hasattr(self, '__defaulted'):
            return

        if self.mime_params and set(self._params.keys()) & set(self.mime_params.keys()):
            raise ValueError('The mime_params and params may not share the '
                             'same keys.')

        if self.action == 'query':
            meta = self._params.get("meta", [])
            if "userinfo" not in meta:
                meta.append("userinfo")
                self._params["meta"] = meta
            uiprop = self._params.get("uiprop", [])
            uiprop = set(uiprop + ["blockinfo", "hasmsg"])
            self._params["uiprop"] = list(sorted(uiprop))
            if "properties" in self._params:
                if "info" in self._params["properties"]:
                    inprop = self._params.get("inprop", [])
                    info = set(inprop + ["protection", "talkid", "subjectid"])
                    self._params["info"] = list(info)
            # When neither 'continue' nor 'rawcontinue' is present and the
            # version number is at least 1.25wmf5 we add a dummy rawcontinue
            # parameter. Querying siteinfo is save as it adds 'continue'.
            if ('continue' not in self._params and
                    'rawcontinue' not in self._params and
                    LV(self.site.version()) >= LV('1.25wmf5')):
                self._params['rawcontinue'] = ['']
        if "maxlag" not in self._params and config.maxlag:
            self._params["maxlag"] = [str(config.maxlag)]
        if "format" not in self._params:
            self._params["format"] = ["json"]
        elif self._params['format'] != ["json"]:
            raise TypeError("Query format '%s' cannot be parsed."
                            % self._params['format'])

        self.__defaulted = True

    def _encoded_items(self):
        """
        Build a dict of params with minimal encoding needed for the site.

        This helper method only prepares params for serialisation or
        transmission, so it only encodes values which are not ASCII,
        requiring callers to consider how to handle ASCII vs other values,
        however the output is designed to enable __str__ and __repr__ to
        do the right thing in most circumstances.

        Servers which use an encoding that is not a superset of ASCII
        are not supported.

        @return: Parameters either in the site encoding, or ASCII strings
        @rtype: dict with values of either str or bytes
        """
        params = {}
        for key, value in self._params.items():
            value = u"|".join(value)
            # If the value is encodable as ascii, do not encode it.
            # This means that any value which can be encoded as ascii
            # is presumed to be ascii, and servers using a site encoding
            # which is not a superset of ascii may be problematic.
            try:
                value.encode('ascii')
                # In Python 2, ascii API params should be represented as 'foo'
                # rather than u'foo'
                if sys.version_info[0] == 2:
                    value = str(value)
            except UnicodeError:
                try:
                    value = value.encode(self.site.encoding())
                except Exception:
                    pywikibot.error(
                        u"_encoded_items: '%s' could not be encoded as '%s':"
                        u" %r" % (key, self.site.encoding(), value))
            params[key] = value
        return params

    def _http_param_string(self):
        """
        Return the parameters as a HTTP URL query fragment.

        URL encodes the parameters provided by _encoded_items()
        """
        return urlencode(self._encoded_items())

    def __str__(self):
        return unquote(self.site.scriptpath()
                              + "/api.php?"
                              + self._http_param_string())

    def __repr__(self):
        return "%s.%s<%s->%r>" % (self.__class__.__module__, self.__class__.__name__, self.site, str(self))

    def _simulate(self, action):
        if action and config.simulate and (self.write or action in config.actions_to_block):
            pywikibot.output(
                u'\03{lightyellow}SIMULATION: %s action blocked.\03{default}'
                % action)
            return {action: {'result': 'Success', 'nochange': ''}}

    def _is_wikibase_error_retryable(self, error):
        ERR_MSG = u'edit-already-exists'
        messages = error.pop("messages", None)
        # bug 66619, after gerrit 124323 breaking change we have a
        # list of messages
        if isinstance(messages, list):
            for item in messages:
                message = item["name"]
                if message == ERR_MSG:
                    break
            else:  # no break
                message = None
        elif isinstance(messages, dict):
            try:  # behaviour before gerrit 124323 braking change
                message = messages["0"]["name"]
            except KeyError:  # unsure the new output is always a list
                message = messages["name"]
        else:
            message = None
        return message == ERR_MSG

    @staticmethod
    def _generate_MIME_part(key, content, keytype=None, headers=None):
        if not keytype:
            try:
                content.encode("ascii")
                keytype = ("text", "plain")
            except (UnicodeError, AttributeError):
                keytype = ("application", "octet-stream")
        submsg = MIMENonMultipart(*keytype)
        content_headers = {'name': key}
        if headers:
            content_headers.update(headers)
        submsg.add_header("Content-disposition", "form-data",
                          **content_headers)

        if keytype != ("text", "plain"):
            submsg['Content-Transfer-Encoding'] = 'binary'

        submsg.set_payload(content)
        return submsg

    @staticmethod
    def _build_mime_request(params, mime_params):
        """Construct a MIME multipart form post.

        @param params: HTTP request params
        @type params: dict
        @param mime_params: HTTP request parts which must be sent in the body
        @type mime_params: dict of (content, keytype, headers)
        @return: HTTP request headers and body
        @rtype: (headers, body)
        """
        # construct a MIME message containing all API key/values
        container = MIMEMultipart(_subtype='form-data')
        for key, value in params.items():
            submsg = Request._generate_MIME_part(key, value)
            container.attach(submsg)
        for key, value in mime_params.items():
            submsg = Request._generate_MIME_part(key, *value)
            container.attach(submsg)

        # strip the headers to get the HTTP message body
        if sys.version_info[0] > 2:
            body = container.as_bytes()
            marker = b"\n\n"  # separates headers from body
        else:
            body = container.as_string()
            marker = "\n\n"  # separates headers from body
        eoh = body.find(marker)
        body = body[eoh + len(marker):]
        # retrieve the headers from the MIME object
        headers = dict(container.items())
        return headers, body

    def _handle_warnings(self, result):
        if 'warnings' in result:
            for mod, warning in result['warnings'].items():
                if mod == 'info':
                    continue
                if '*' in warning:
                    text = warning['*']
                elif 'html' in warning:
                    # Bugzilla 49978
                    text = warning['html']['*']
                else:
                    pywikibot.warning(
                        u'API warning ({0})of unknown format: {1}'.
                        format(mod, warning))
                    continue
                # multiple warnings are in text separated by a newline
                for single_warning in text.splitlines():
                    if (not callable(self._warning_handler) or
                            not self._warning_handler(mod, single_warning)):
                        pywikibot.warning(u"API warning (%s): %s" % (mod, single_warning))

    def submit(self):
        """Submit a query and parse the response.

        @return: a dict containing data retrieved from api.php

        """
        self._add_defaults()
        while True:
            paramstring = self._http_param_string()
            simulate = self._simulate(self.action)
            if simulate:
                return simulate
            if self.throttle:
                self.site.throttle(write=self.write)
            else:
                pywikibot.log(
                    "Submitting unthrottled action '{0}'.".format(self.action))
            uri = self.site.scriptpath() + "/api.php"
            try:
                if self.mime:
                    (headers, body) = Request._build_mime_request(
                        self._encoded_items(), self.mime_params)
                else:
                    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
                    body = paramstring

                rawdata = http.request(
                    self.site, uri, method="POST",
                    headers=headers, body=body)
            except Server504Error:
                pywikibot.log(u"Caught HTTP 504 error; retrying")
                self.wait()
                continue
            except FatalServerError:
                # This error is not going to be fixed by just waiting
                pywikibot.error(traceback.format_exc())
                raise
            # TODO: what other exceptions can occur here?
            except Exception:
                # for any other error on the http request, wait and retry
                pywikibot.error(traceback.format_exc())
                pywikibot.log(u"%s, %s" % (uri, paramstring))
                self.wait()
                continue
            if not isinstance(rawdata, unicode):
                rawdata = rawdata.decode(self.site.encoding())
            pywikibot.debug(u"API response received:\n" + rawdata, _logger)
            if rawdata.startswith(u"unknown_action"):
                raise APIError(rawdata[:14], rawdata[16:])
            try:
                result = json.loads(rawdata)
            except ValueError:
                # if the result isn't valid JSON, there must be a server
                # problem.  Wait a few seconds and try again
                pywikibot.warning(
                    "Non-JSON response received from server %s; the server may be down."
                    % self.site)
                # there might also be an overflow, so try a smaller limit
                for param in self._params:
                    if param.endswith("limit"):
                        # param values are stored a list of str
                        value = self._params[param][0]
                        try:
                            self._params[param] = [str(int(value) // 2)]
                            pywikibot.output(u"Set %s = %s"
                                             % (param, self._params[param]))
                        except:
                            pass
                self.wait()
                continue
            if not result:
                result = {}
            if not isinstance(result, dict):
                raise APIError("Unknown",
                               "Unable to process query response of type %s."
                               % type(result),
                               data=result)
            if self.action == 'query':
                if 'userinfo' in result.get('query', ()):
                    if hasattr(self.site, '_userinfo'):
                        self.site._userinfo.update(result['query']['userinfo'])
                    else:
                        self.site._userinfo = result['query']['userinfo']
                status = self.site._loginstatus  # save previous login status
                if (("error" in result
                     and result["error"]["code"].endswith("limit"))
                    or (status >= 0
                        and self.site._userinfo['name'] != self.site._username[status])):
                    # user is no longer logged in (session expired?)
                    # reset userinfo, then make user log in again
                    del self.site._userinfo
                    self.site._loginstatus = -1
                    if status < 0:
                        status = 0  # default to non-sysop login
                    self.site.login(status)
                    # retry the previous query
                    continue
            self._handle_warnings(result)
            if "error" not in result:
                return result

            if "*" in result["error"]:
                # help text returned
                result['error']['help'] = result['error'].pop("*")
            code = result["error"].pop("code", "Unknown")
            info = result["error"].pop("info", None)
            if code == "maxlag":
                lag = lagpattern.search(info)
                if lag:
                    pywikibot.log(
                        u"Pausing due to database lag: " + info)
                    self.site.throttle.lag(int(lag.group("lag")))
                    continue

            if code.startswith(u'internal_api_error_'):
                class_name = code[len(u'internal_api_error_'):]
                if class_name in ['DBConnectionError',  # r 4984 & r 4580
                                  'DBQueryError',  # bug 58158
                                  'ReadOnlyError'  # bug 59227
                                  ]:

                    pywikibot.log(u'MediaWiki exception %s; retrying.'
                                  % class_name)
                    self.wait()
                    continue

                pywikibot.log(u"MediaWiki exception %s: query=\n%s"
                              % (class_name,
                                 pprint.pformat(self._params)))
                pywikibot.log(u"           response=\n%s" % result)

                raise APIMWException(class_name, info, **result["error"])

            # bugs 46535, 62126, 64494, 66619
            # maybe removed when it 46535 is solved
            if code == "failed-save" and \
               self.action == 'wbeditentity' and \
               self._is_wikibase_error_retryable(result["error"]):
                self.wait()
                continue
            # raise error
            try:
                pywikibot.log(u"API Error: query=\n%s"
                              % pprint.pformat(self._params))
                pywikibot.log(u"           response=\n%s"
                              % result)

                raise APIError(code, info, **result["error"])
            except TypeError:
                raise RuntimeError(result)

    def wait(self):
        """Determine how long to wait after a failed request."""
        self.max_retries -= 1
        if self.max_retries < 0:
            raise TimeoutError("Maximum retries attempted without success.")
        pywikibot.warning(u"Waiting %s seconds before retrying."
                          % self.retry_wait)
        time.sleep(self.retry_wait)
        # double the next wait, but do not exceed 120 seconds
        self.retry_wait = min(120, self.retry_wait * 2)


class CachedRequest(Request):

    """Cached request."""

    def __init__(self, expiry, *args, **kwargs):
        """Construct a CachedRequest object.

        @param expiry: either a number of days or a datetime.timedelta object
        """
        super(CachedRequest, self).__init__(*args, **kwargs)
        if not isinstance(expiry, datetime.timedelta):
            expiry = datetime.timedelta(expiry)
        self.expiry = expiry
        self._data = None
        self._cachetime = None

    @staticmethod
    def _get_cache_dir():
        """Return the base directory path for cache entries.

        The directory will be created if it does not already exist.

        @return: basestring
        """
        path = os.path.join(pywikibot.config2.base_dir, 'apicache')
        CachedRequest._make_dir(path)
        return path

    @staticmethod
    def _make_dir(dir):
        """Create directory if it does not exist already.

        The directory name (dir) is returned unmodified.

        @param dir: directory path
        @type dir: basestring

        @return: basestring
        """
        try:
            os.makedirs(dir)
        except OSError:
            # directory already exists
            pass
        return dir

    def _uniquedescriptionstr(self):
        """Return unique description for the cache entry.

        If this is modified, please also update
        scripts/maintenance/cache.py to support
        the new key and all previous keys.

        @rtype: unicode
        """
        login_status = self.site._loginstatus

        if login_status > pywikibot.site.LoginStatus.NOT_LOGGED_IN and \
                hasattr(self.site, '_userinfo') and \
                'name' in self.site._userinfo:
            # This uses the format of Page.__repr__, without performing
            # config.console_encoding as done by Page.__repr__.
            # The returned value cant be encoded to anything other than
            # ascii otherwise it creates an exception when _create_file_name()
            # tries to encode it as utf-8.
            user_key = u'User(User:%s)' % self.site._userinfo['name']
        else:
            user_key = pywikibot.site.LoginStatus(
                max(login_status, pywikibot.site.LoginStatus.NOT_LOGGED_IN))
            user_key = repr(user_key)

        request_key = repr(sorted(list(self._encoded_items().items())))
        return repr(self.site) + user_key + request_key

    def _create_file_name(self):
        """
        Return a unique ascii identifier for the cache entry.

        @rtype: str (hexademical; i.e. characters 0-9 and a-f only)
        """
        return hashlib.sha256(
            self._uniquedescriptionstr().encode('utf-8')
        ).hexdigest()

    def _cachefile_path(self):
        return os.path.join(CachedRequest._get_cache_dir(),
                            self._create_file_name())

    def _expired(self, dt):
        return dt + self.expiry < datetime.datetime.now()

    def _load_cache(self):
        """Load cache entry for request, if available.

        @return: Whether the request was loaded from the cache
        @rtype: bool
        """
        self._add_defaults()
        try:
            filename = self._cachefile_path()
            with open(filename, 'rb') as f:
                uniquedescr, self._data, self._cachetime = pickle.load(f)
            assert(uniquedescr == self._uniquedescriptionstr())
            if self._expired(self._cachetime):
                self._data = None
                return False
            pywikibot.debug(u"%s: cache hit (%s) for API request: %s"
                            % (self.__class__.__name__, filename, uniquedescr),
                            _logger)
            return True
        except IOError as e:
            # file not found
            return False
        except Exception as e:
            pywikibot.output("Could not load cache: %r" % e)
            return False

    def _write_cache(self, data):
        """Write data to self._cachefile_path()."""
        data = [self._uniquedescriptionstr(), data, datetime.datetime.now()]
        with open(self._cachefile_path(), 'wb') as f:
            pickle.dump(data, f, protocol=config.pickle_protocol)

    def submit(self):
        cached_available = self._load_cache()
        if not cached_available:
            self._data = super(CachedRequest, self).submit()
            self._write_cache(self._data)
        else:
            self._handle_warnings(self._data)
        return self._data


class QueryGenerator(object):

    """Base class for iterators that handle responses to API action=query.

    By default, the iterator will iterate each item in the query response,
    and use the (query-)continue element, if present, to continue iterating as
    long as the wiki returns additional values.  However, if the iterator's
    limit attribute is set to a positive int, the iterator will stop after
    iterating that many values. If limit is negative, the limit parameter
    will not be passed to the API at all.

    Most common query types are more efficiently handled by subclasses, but
    this class can be used directly for custom queries and miscellaneous
    types (such as "meta=...") that don't return the usual list of pages or
    links. See the API documentation for specific query options.

    """

    def __init__(self, **kwargs):
        """Construct a QueryGenerator object.

        kwargs are used to create a Request object; see that object's
        documentation for values. 'action'='query' is assumed.

        """
        if "action" in kwargs and kwargs["action"] != "query":
            raise Error("%s: 'action' must be 'query', not %s"
                        % (self.__class__.__name__, kwargs["action"]))
        else:
            kwargs["action"] = "query"
        try:
            self.site = kwargs["site"]
        except KeyError:
            self.site = pywikibot.Site()
            kwargs["site"] = self.site
        # make sure request type is valid, and get limit key if any
        for modtype in ("generator", "list", "prop", "meta"):
            if modtype in kwargs:
                self.module = kwargs[modtype]
                break
        else:
            raise Error("%s: No query module name found in arguments."
                        % self.__class__.__name__)

        kwargs["indexpageids"] = ""  # always ask for list of pageids
        if LV(self.site.version()) < LV('1.21'):
            self.continue_name = 'query-continue'
            self.continue_update = self._query_continue
        else:
            self.continue_name = 'continue'
            self.continue_update = self._continue
            # Explicitly enable the simplified continuation
            kwargs['continue'] = ''
        self.request = Request(**kwargs)
        self.prefix = None
        self.api_limit = None
        self.update_limit()  # sets self.prefix
        if self.api_limit is not None and "generator" in kwargs:
            self.prefix = "g" + self.prefix
        self.limit = None
        self.query_limit = self.api_limit
        if "generator" in kwargs:
            self.resultkey = "pages"        # name of the "query" subelement key
        else:                               # to look for when iterating
            self.resultkey = self.module

        # usually the (query-)continue key is the same as the querymodule,
        # but not always
        # API can return more than one query-continue key, if multiple properties
        # are requested by the query, e.g.
        # "query-continue":{
        #     "langlinks":{"llcontinue":"12188973|pt"},
        #     "templates":{"tlcontinue":"310820|828|Namespace_detect"}}
        # self.continuekey is a list
        self.continuekey = self.module.split('|')

    @property
    def __modules(self):
        """
        Cache paraminfo in this request's Site object.

        Hold the query data for paraminfo on
        querymodule=self.module at self.site.

        """
        if not hasattr(self.site, "_modules"):
            setattr(self.site, "_modules", dict())
        return self.site._modules

    @__modules.deleter
    def __modules(self):
        """Delete the instance cache - maybe we don't need it."""
        if hasattr(self.site, "_modules"):
            del self.site._modules

    @property
    def _modules(self):
        """Query api on self.site for paraminfo on self.module."""
        modules = self.module.split('|')
        if not set(modules) <= set(self.__modules.keys()):
            if LV(self.site.version()) < LV('1.25wmf4'):
                key = 'querymodules'
                value = self.module
            else:
                key = 'modules'
                value = ['query+' + module for module in modules]
            paramreq = CachedRequest(expiry=config.API_config_expiry,
                                     site=self.site, action="paraminfo",
                                     **{key: value})
            data = paramreq.submit()
            assert "paraminfo" in data
            assert key in data["paraminfo"]
            assert len(data["paraminfo"][key]) == len(modules)
            for paraminfo in data["paraminfo"][key]:
                assert paraminfo["name"] in self.module
                if "missing" in paraminfo:
                    raise Error("Invalid query module name '%s'." % self.module)
                self.__modules[paraminfo["name"]] = paraminfo
        _modules = {}
        for m in modules:
            _modules[m] = self.__modules[m]
        return _modules

    def set_query_increment(self, value):
        """Set the maximum number of items to be retrieved per API query.

        If not called, the default is to ask for "max" items and let the
        API decide how many to send.

        """
        limit = int(value)

        # don't update if limit is greater than maximum allowed by API
        if self.api_limit is None:
            self.query_limit = limit
        else:
            self.query_limit = min(self.api_limit, limit)
        pywikibot.debug(u"%s: Set query_limit to %i."
                        % (self.__class__.__name__, self.query_limit),
                        _logger)

    def set_maximum_items(self, value):
        """Set the maximum number of items to be retrieved from the wiki.

        If not called, most queries will continue as long as there is
        more data to be retrieved from the API.

        If set to -1 (or any negative value), the "limit" parameter will be
        omitted from the request. For some request types (such as
        prop=revisions), this is necessary to signal that only current
        revision is to be returned.

        """
        self.limit = int(value)

    def update_limit(self):
        """Set query limit for self.module based on api response."""
        for mod in self.module.split('|'):
            for param in self._modules[mod].get("parameters", []):
                if param["name"] == "limit":
                    if self.site.logged_in() and self.site.has_right('apihighlimits'):
                        self.api_limit = int(param["highmax"])
                    else:
                        self.api_limit = int(param["max"])
                    if self.prefix is None:
                        self.prefix = self._modules[mod]["prefix"]
                    pywikibot.debug(u"%s: Set query_limit to %i."
                                    % (self.__class__.__name__,
                                       self.api_limit),
                                    _logger)
                    return

    def set_namespace(self, namespaces):
        """Set a namespace filter on this query.

        @param namespaces: Either an int or a list of ints

        """
        if isinstance(namespaces, list):
            namespaces = "|".join(str(n) for n in namespaces)
        else:
            namespaces = str(namespaces)
        for mod in self.module.split('|'):
            for param in self._modules[mod].get("parameters", []):
                if param["name"] == "namespace":
                    self.request[self.prefix + "namespace"] = namespaces
                    return

    def _query_continue(self):
        if all(key not in self.data[self.continue_name]
               for key in self.continuekey):
            pywikibot.log(
                u"Missing '%s' key(s) in ['%s'] value."
                % (self.continuekey, self.continue_name))
            return True
        for query_continue_pair in self.data['query-continue'].values():
            self._add_continues(query_continue_pair)

    def _continue(self):
        self._add_continues(self.data['continue'])

    def _add_continues(self, continue_pair):
        for key, value in continue_pair.items():
            # query-continue can return ints (continue too?)
            if isinstance(value, int):
                value = str(value)
            self.request[key] = value

    def __iter__(self):
        """Submit request and iterate the response based on self.resultkey.

        Continues response as needed until limit (if any) is reached.

        """
        previous_result_had_data = True
        prev_limit = new_limit = None

        count = 0
        while True:
            if self.query_limit is not None:
                prev_limit = new_limit
                if self.limit is None:
                    new_limit = self.query_limit
                elif self.limit > 0:
                    if previous_result_had_data:
                        # self.resultkey in data in last request.submit()
                        new_limit = min(self.query_limit, self.limit - count)
                    else:
                        # only "(query-)continue" returned. See Bug 72209.
                        # increase new_limit to advance faster until new
                        # useful data are found again.
                        new_limit = min(new_limit * 2, self.query_limit)
                else:
                    new_limit = None

                if new_limit and \
                        "rvprop" in self.request \
                        and "content" in self.request["rvprop"]:
                    # queries that retrieve page content have lower limits
                    # Note: although API allows up to 500 pages for content
                    #   queries, these sometimes result in server-side errors
                    #   so use 250 as a safer limit
                    new_limit = min(new_limit, self.api_limit // 10, 250)
                if new_limit is not None:
                    self.request[self.prefix + "limit"] = str(new_limit)
                if prev_limit != new_limit:
                    pywikibot.debug(
                        u"%s: query_limit: %s, api_limit: %s, "
                        u"limit: %s, new_limit: %s, count: %s"
                        % (self.__class__.__name__,
                           self.query_limit, self.api_limit,
                           self.limit, new_limit, count),
                        _logger)
                    pywikibot.debug(
                        u"%s: %s: %s"
                        % (self.__class__.__name__,
                           self.prefix + "limit",
                           self.request[self.prefix + "limit"]),
                        _logger)
            if not hasattr(self, "data"):
                self.data = self.request.submit()
            if not self.data or not isinstance(self.data, dict):
                pywikibot.debug(
                    u"%s: stopped iteration because no dict retrieved from api."
                    % self.__class__.__name__,
                    _logger)
                return
            if "query" not in self.data:
                pywikibot.debug(
                    u"%s: stopped iteration because 'query' not found in api "
                    u"response." % self.__class__.__name__,
                    _logger)
                pywikibot.debug(unicode(self.data), _logger)
                return
            if self.resultkey in self.data["query"]:
                resultdata = self.data["query"][self.resultkey]
                if isinstance(resultdata, dict):
                    pywikibot.debug(u"%s received %s; limit=%s"
                                    % (self.__class__.__name__,
                                       list(resultdata.keys()),
                                       self.limit),
                                    _logger)
                    if "results" in resultdata:
                        resultdata = resultdata["results"]
                    elif "pageids" in self.data["query"]:
                        # this ensures that page data will be iterated
                        # in the same order as received from server
                        resultdata = [resultdata[k]
                                      for k in self.data["query"]["pageids"]]
                    else:
                        resultdata = [resultdata[k]
                                      for k in sorted(resultdata.keys())]
                else:
                    pywikibot.debug(u"%s received %s; limit=%s"
                                    % (self.__class__.__name__,
                                       resultdata,
                                       self.limit),
                                    _logger)
                if "normalized" in self.data["query"]:
                    self.normalized = dict((item['to'], item['from'])
                                           for item in
                                           self.data["query"]["normalized"])
                else:
                    self.normalized = {}
                for item in resultdata:
                    yield self.result(item)
                    if isinstance(item, dict) and set(self.continuekey) & set(item.keys()):
                        # if we need to count elements contained in items in
                        # self.data["query"]["pages"], we want to count
                        # item[self.continuekey] (e.g. 'revisions') and not
                        # self.resultkey (i.e. 'pages')
                        for key in set(self.continuekey) & set(item.keys()):
                            count += len(item[key])
                    # otherwise we proceed as usual
                    else:
                        count += 1
                    # note: self.limit could be -1
                    if self.limit and self.limit > 0 and count >= self.limit:
                        return
                # self.resultkey in data in last request.submit()
                previous_result_had_data = True
            else:
                # if (query-)continue is present, self.resultkey might not have
                # been fetched yet
                if self.continue_name not in self.data:
                    # No results.
                    return
                # self.resultkey not in data in last request.submit()
                # only "(query-)continue" was retrieved.
                previous_result_had_data = False
            if self.module == "random" and self.limit:
                # "random" module does not return "(query-)continue"
                # now we loop for a new random query
                del self.data  # a new request is needed
                continue
            if self.continue_name not in self.data:
                return
            if self.continue_update():
                return

            del self.data  # a new request with (query-)continue is needed

    def result(self, data):
        """Process result data as needed for particular subclass."""
        return data


class PageGenerator(QueryGenerator):

    """Iterator for response to a request of type action=query&generator=foo.

    This class can be used for any of the query types that are listed in the
    API documentation as being able to be used as a generator. Instances of
    this class iterate Page objects.

    """

    def __init__(self, generator, g_content=False, **kwargs):
        """
        Constructor.

        Required and optional parameters are as for C{Request}, except that
        action=query is assumed and generator is required.

        @param generator: the "generator=" type from api.php
        @type generator: str
        @param g_content: if True, retrieve the contents of the current
            version of each Page (default False)

        """
        def appendParams(params, key, value):
            if key in params:
                params[key] += '|' + value
            else:
                params[key] = value
        # get some basic information about every page generated
        appendParams(kwargs, 'prop', 'info|imageinfo|categoryinfo')
        if g_content:
            # retrieve the current revision
            appendParams(kwargs, 'prop', 'revisions')
            appendParams(kwargs, 'rvprop', 'ids|timestamp|flags|comment|user|content')
        if not ('inprop' in kwargs and 'protection' in kwargs['inprop']):
            appendParams(kwargs, 'inprop', 'protection')
        appendParams(kwargs, 'iiprop', 'timestamp|user|comment|url|size|sha1|metadata')
        self.props = kwargs['prop'].split('|')
        QueryGenerator.__init__(self, generator=generator, **kwargs)
        self.resultkey = "pages"  # element to look for in result

    def result(self, pagedata):
        """Convert page dict entry from api to Page object.

        This can be overridden in subclasses to return a different type
        of object.

        """
        p = pywikibot.Page(self.site, pagedata['title'], pagedata['ns'])
        update_page(p, pagedata, self.props)
        return p


class CategoryPageGenerator(PageGenerator):

    """Like PageGenerator, but yields Category objects instead of Pages."""

    def result(self, pagedata):
        p = PageGenerator.result(self, pagedata)
        return pywikibot.Category(p)


class ImagePageGenerator(PageGenerator):

    """Like PageGenerator, but yields FilePage objects instead of Pages."""

    def result(self, pagedata):
        p = PageGenerator.result(self, pagedata)
        filepage = pywikibot.FilePage(p)
        if 'imageinfo' in pagedata:
            filepage._imageinfo = pagedata['imageinfo'][0]
        return filepage


class PropertyGenerator(QueryGenerator):

    """Iterator for queries of type action=query&prop=foo.

    See the API documentation for types of page properties that can be
    queried.

    This iterator yields one or more dict object(s) corresponding
    to each "page" item(s) from the API response; the calling module has to
    decide what to do with the contents of the dict. There will be one
    dict for each page queried via a titles= or ids= parameter (which must
    be supplied when instantiating this class).

    """

    def __init__(self, prop, **kwargs):
        """
        Constructor.

        Required and optional parameters are as for C{Request}, except that
        action=query is assumed and prop is required.

        @param prop: the "prop=" type from api.php
        @type prop: str

        """
        QueryGenerator.__init__(self, prop=prop, **kwargs)
        self._props = frozenset(prop.split('|'))
        self.resultkey = "pages"

    @property
    def props(self):
        """The requested property names."""
        return self._props


class ListGenerator(QueryGenerator):

    """Iterator for queries of type action=query&list=foo.

    See the API documentation for types of lists that can be queried.  Lists
    include both side-wide information (such as 'allpages') and page-specific
    information (such as 'backlinks').

    This iterator yields a dict object for each member of the list returned
    by the API, with the format of the dict depending on the particular list
    command used.  For those lists that contain page information, it may be
    easier to use the PageGenerator class instead, as that will convert the
    returned information into a Page object.

    """

    def __init__(self, listaction, **kwargs):
        """
        Constructor.

        Required and optional parameters are as for C{Request}, except that
        action=query is assumed and listaction is required.

        @param listaction: the "list=" type from api.php
        @type listaction: str

        """
        QueryGenerator.__init__(self, list=listaction, **kwargs)


class LogEntryListGenerator(ListGenerator):

    """
    Iterator for queries of list 'logevents'.

    Yields LogEntry objects instead of dicts.
    """

    def __init__(self, logtype=None, **kwargs):
        """Constructor."""
        ListGenerator.__init__(self, "logevents", **kwargs)

        from pywikibot import logentries
        self.entryFactory = logentries.LogEntryFactory(logtype)

    def result(self, pagedata):
        return self.entryFactory.create(pagedata)


class LoginManager(login.LoginManager):

    """Supply getCookie() method to use API interface."""

    def getCookie(self, remember=True, captchaId=None, captchaAnswer=None):
        """Login to the site.

        Parameters are all ignored.

        @return: cookie data if successful, None otherwise.

        """
        if hasattr(self, '_waituntil'):
            if datetime.datetime.now() < self._waituntil:
                diff = self._waituntil - datetime.datetime.now()
                pywikibot.warning(u"Too many tries, waiting %s seconds before retrying."
                                  % diff.seconds)
                time.sleep(diff.seconds)
        login_request = Request(site=self.site,
                                action="login",
                                lgname=self.username,
                                lgpassword=self.password)
        self.site._loginstatus = -2
        while True:
            login_result = login_request.submit()
            if u"login" not in login_result:
                raise RuntimeError("API login response does not have 'login' key.")
            if login_result['login']['result'] == "Success":
                prefix = login_result['login']['cookieprefix']
                cookies = []
                for key in ('Token', 'UserID', 'UserName'):
                    cookies.append("%s%s=%s"
                                   % (prefix, key,
                                      login_result['login']['lg' + key.lower()]))
                self.username = login_result['login']['lgusername']
                return "\n".join(cookies)
            elif login_result['login']['result'] == "NeedToken":
                token = login_result['login']['token']
                login_request["lgtoken"] = token
                continue
            elif login_result['login']['result'] == "Throttled":
                self._waituntil = datetime.datetime.now() + datetime.timedelta(
                    seconds=int(login_result["login"]["wait"]))
                break
            else:
                break
        raise APIError(code=login_result["login"]["result"], info="")

    def storecookiedata(self, data):
        # ignore data; cookies are set by threadedhttp module
        pywikibot.cookie_jar.save()


def update_page(page, pagedict, props=[]):
    """Update attributes of Page object page, based on query data in pagedict.

    @param page: object to be updated
    @type page: Page
    @param pagedict: the contents of a "page" element of a query response
    @type pagedict: dict
    @param props: the property names which resulted in pagedict. If a missing
        value in pagedict can indicate both 'false' and 'not present' the
        property which would make the value present must be in the props
        parameter.
    @type props: iterable of string
    """
    if "pageid" in pagedict:
        page._pageid = int(pagedict['pageid'])
    elif "missing" in pagedict:
        page._pageid = 0    # Non-existent page
    else:
        raise AssertionError(
            "Page %s has neither 'pageid' nor 'missing' attribute" % pagedict['title'])
    if 'info' in props:
        page._isredir = 'redirect' in pagedict
    if 'touched' in pagedict:
        page._timestamp = pagedict['touched']
    if 'protection' in pagedict:
        page._protection = {}
        for item in pagedict['protection']:
            page._protection[item['type']] = item['level'], item['expiry']
    if 'revisions' in pagedict:
        for rev in pagedict['revisions']:
            revision = pywikibot.page.Revision(
                revid=rev['revid'],
                timestamp=pywikibot.Timestamp.fromISOformat(rev['timestamp']),
                user=rev.get('user', u''),
                anon='anon' in rev,
                comment=rev.get('comment', u''),
                minor='minor' in rev,
                text=rev.get('*', None),
                rollbacktoken=rev.get('rollbacktoken', None)
            )
            page._revisions[revision.revid] = revision

    if 'lastrevid' in pagedict:
        page._revid = pagedict['lastrevid']
        if page._revid in page._revisions:
            page._text = page._revisions[page._revid].text

    if "categoryinfo" in pagedict:
        page._catinfo = pagedict["categoryinfo"]

    if "templates" in pagedict:
        templates = [pywikibot.Page(page.site, tl['title'])
                     for tl in pagedict['templates']]
        if hasattr(page, "_templates"):
            page._templates.extend(templates)
        else:
            page._templates = templates

    if "langlinks" in pagedict:
        links = []
        for ll in pagedict["langlinks"]:
            link = pywikibot.Link.langlinkUnsafe(ll['lang'],
                                                 ll['*'],
                                                 source=page.site)
            links.append(link)

        if hasattr(page, "_langlinks"):
            page._langlinks.extend(links)
        else:
            page._langlinks = links

    if "coordinates" in pagedict:
        coords = []
        for co in pagedict['coordinates']:
            coord = pywikibot.Coordinate(lat=co['lat'],
                                         lon=co['lon'],
                                         typ=co.get('type', ''),
                                         name=co.get('name', ''),
                                         dim=int(co['dim']),
                                         globe=co['globe'],  # See [[gerrit:67886]]
                                         )
            coords.append(coord)
        page._coords = coords

    if "pageprops" in pagedict:
        page._pageprops = pagedict['pageprops']

    if 'preload' in pagedict:
        page._preloadedtext = pagedict['preload']

    if "flowinfo" in pagedict:
        page._flowinfo = pagedict['flowinfo']['flow']


if __name__ == "__main__":
    import logging
    from pywikibot import Site
    logging.getLogger("pywiki.data.api").setLevel(logging.DEBUG)
    mysite = Site("en", "wikipedia")
    pywikibot.output(u"starting test....")

    def _test():
        import doctest
        doctest.testmod()
    try:
        _test()
    finally:
        pywikibot.stopme()
