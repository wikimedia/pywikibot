"""Objects representing API requests."""
#
# (C) Pywikibot team, 2007-2023
#
# Distributed under the terms of the MIT license.
#
import datetime
import hashlib
import inspect
import os
import pickle
import pprint
import re
import traceback
from collections.abc import MutableMapping
from contextlib import suppress
from email.mime.nonmultipart import MIMENonMultipart
from pathlib import Path
from typing import Any, Optional, Union
from urllib.parse import unquote, urlencode
from warnings import warn

import pywikibot
from pywikibot import config
from pywikibot.backports import Callable, Dict, Match, Tuple, removeprefix
from pywikibot.comms import http
from pywikibot.exceptions import (
    Client414Error,
    Error,
    FatalServerError,
    MaxlagTimeoutError,
    NoUsernameError,
    Server504Error,
    SiteDefinitionError,
    TimeoutError,
)
from pywikibot.login import LoginStatus
from pywikibot.textlib import removeDisabledParts, removeHTMLParts
from pywikibot.tools import PYTHON_VERSION


__all__ = ('CachedRequest', 'Request', 'encode_url')

# Actions that imply database updates on the server, used for various
# things like throttling or skipping actions when we're in simulation
# mode
WRITE_ACTIONS = {
    # main actions, see https://www.mediawiki.org/wiki/API:Main_page
    'block', 'clearhasmsg', 'createaccount', 'createlocalaccount', 'delete',
    'deleteglobalaccount', 'edit', 'editmassmessagelist', 'emailuser',
    'filerevert', 'flowthank', 'globalblock', 'globalpreferenceoverrides',
    'globalpreferences', 'globaluserrights', 'imagerotate', 'import',
    'linkaccount', 'managetags', 'massmessage', 'mergehistory', 'move',
    'newslettersubscribe', 'options', 'patrol', 'protect', 'purge',
    'removeauthenticationdata', 'resetpassword', 'revisiondelete', 'rollback',
    'setglobalaccountstatus', 'setnotificationtimestamp', 'setpagelanguage',
    'strikevote', 'tag', 'thank', 'threadaction', 'transcodereset',
    'translationreview', 'unblock', 'undelete', 'unlinkaccount', 'upload',
    'userrights', 'watch', 'wikilove',
    # wikibase actions, see https://www.mediawiki.org/wiki/Wikibase/API
    'wbcreateclaim', 'wbcreateredirect', 'wbeditentity', 'wblinktitles',
    'wbmergeitems', 'wbremoveclaims', 'wbremovequalifiers',
    'wbremovereferences', 'wbsetaliases', 'wbsetclaim', 'wbsetclaimvalue',
    'wbsetdescription', 'wbsetlabel', 'wbsetqualifier', 'wbsetreference',
    'wbsetsitelink',
    # lexeme (internal) actions
    'wbladdform', 'wbladdsense', 'wbleditformelements', 'wbleditsenseelements',
    'wblmergelexemes', 'wblremoveform', 'wblremovesense',
}

lagpattern = re.compile(
    r'Waiting for [\w.: ]+: (?P<lag>\d+(?:\.\d+)?) seconds? lagged')


class Request(MutableMapping):

    """A request to a Site's api.php interface.

    Attributes of this object (except for the special parameters listed
    below) get passed as commands to api.php, and can be get or set
    using the dict interface. All attributes must be strings. Use an
    empty string for parameters that don't require a value. For example,
    ``Request(action="query", titles="Foo bar", prop="info", redirects="")``
    corresponds to the API request
    ``api.php?action=query&titles=Foo%20bar&prop=info&redirects``

    This is the lowest-level interface to the API, and can be used for any
    request that a particular site's API supports. See the API documentation
    (https://www.mediawiki.org/wiki/API) and site-specific settings for
    details on what parameters are accepted for each request type.

    Uploading files is a special case: to upload, the parameter `mime` must
    contain a dict, and the parameter `file` must be set equal to a valid
    filename on the local computer, *not* to the content of the file.

    Returns a dict containing the JSON data returned by the wiki. Normally,
    one of the dict keys will be equal to the value of the 'action'
    parameter. Errors are caught and raise an APIError exception.

    Example:

    >>> r = Request(parameters={'action': 'query', 'meta': 'userinfo'})
    >>> # This is equivalent to
    >>> # https://{path}/api.php?action=query&meta=userinfo&format=json
    >>> # change a parameter
    >>> r['meta'] = "userinfo|siteinfo"
    >>> # add a new parameter
    >>> r['siprop'] = "namespaces"
    >>> # note that "uiprop" param gets added automatically
    >>> r.action
    'query'
    >>> sorted(r._params)
    ['action', 'meta', 'siprop']
    >>> r._params['action']
    ['query']
    >>> r._params['meta']
    ['userinfo', 'siteinfo']
    >>> r._params['siprop']
    ['namespaces']
    >>> data = r.submit()
    >>> isinstance(data, dict)
    True
    >>> set(['query', 'batchcomplete', 'warnings']).issuperset(data.keys())
    True
    >>> 'query' in data
    True
    >>> sorted(data['query'])
    ['namespaces', 'userinfo']
    """

    # To make sure the default value of 'parameters' can be identified.
    _PARAM_DEFAULT = object()

    def __init__(self, site=None,
                 mime: Optional[dict] = None,
                 throttle: bool = True,
                 max_retries: Optional[int] = None,
                 retry_wait: Optional[int] = None,
                 use_get: Optional[bool] = None,
                 parameters=_PARAM_DEFAULT, **kwargs) -> None:
        """
        Create a new Request instance with the given parameters.

        The parameters for the request can be defined via either the
        'parameters' parameter or the keyword arguments. The keyword arguments
        were the previous implementation but could cause problems when there
        are arguments to the API named the same as normal arguments to this
        class. So the second parameter 'parameters' was added which just
        contains all parameters. When a Request instance is created it must use
        either one of them and not both at the same time. To have backwards
        compatibility it adds a parameter named 'parameters' to kwargs when
        both parameters are set as that indicates an old call and 'parameters'
        was originally supplied as a keyword parameter.

        If undefined keyword arguments were given AND the 'parameters'
        parameter was supplied as a positional parameter it still assumes
        'parameters' were part of the keyword arguments.

        If a class is using Request and is directly forwarding the parameters,
        :py:obj:`Request.clean_kwargs` can be used to automatically
        convert the old kwargs mode into the new parameter mode. This
        normalizes the arguments so that when the API parameters are
        modified the changes can always be applied to the 'parameters'
        parameter.

        :param site: The Site to which the request will be submitted. If not
               supplied, uses the user's configured default Site.
        :param mime: If not None, send in "multipart/form-data" format (default
               None). Parameters which should only be transferred via mime
               mode are defined via this parameter (even an empty dict means
               mime shall be used).
        :param max_retries: Maximum number of times to retry after
               errors, defaults to config.max_retries.
        :param retry_wait: Minimum time in seconds to wait after an
               error, defaults to config.retry_wait seconds (doubles each retry
               until config.retry_max seconds is reached).
        :param use_get: Use HTTP GET request if possible. If False it
               uses a POST request. If None, it'll try to determine via
               action=paraminfo if the action requires a POST.
        :param parameters: The parameters used for the request to the API.
        :type parameters: dict
        :param kwargs: The parameters used for the request to the API.
        """
        if site is None:
            self.site = pywikibot.Site()
            warn(f'Request() invoked without a site; setting to {self.site}',
                 RuntimeWarning, 2)
        else:
            self.site = site

        self.mime = mime
        if isinstance(mime, bool):
            raise TypeError('mime param in api.Request() must not be boolean')

        self.throttle = throttle
        self.use_get = use_get
        if max_retries is None:
            self.max_retries = pywikibot.config.max_retries
        else:
            self.max_retries = max_retries
        self.current_retries = 0
        if retry_wait is None:
            self.retry_wait = pywikibot.config.retry_wait
        else:
            self.retry_wait = retry_wait
        self.json_warning = False
        # The only problem with that system is that it won't detect when
        # 'parameters' is actually the only parameter for the request as it
        # then assumes it's using the new mode (and the parameters are actually
        # in the parameter 'parameters' not that the parameter 'parameters' is
        # actually a parameter for the request). But that is invalid anyway as
        # it MUST have at least an action parameter for the request which would
        # be in kwargs if it's using the old mode.
        if kwargs:
            if parameters is not self._PARAM_DEFAULT:
                # 'parameters' AND kwargs is set. In that case think of
                # 'parameters' being an old kwarg which is now filled in an
                # actual parameter
                self._warn_both()
                kwargs['parameters'] = parameters
            # When parameters wasn't set it's likely that kwargs-mode was used
            self._warn_kwargs()
            parameters = kwargs
        elif parameters is self._PARAM_DEFAULT:
            parameters = {}
        self._params = {}
        if 'action' not in parameters:
            raise ValueError("'action' specification missing from Request.")
        self.action = parameters['action']
        self.update(parameters)  # also convert all parameter values to lists
        self._warning_handler: Optional[Callable[[str, str], Union[Match[str], bool, None]]] = None  # noqa: E501
        self.write = self.action in WRITE_ACTIONS
        # Client side verification that the request is being performed
        # by a logged in user, and warn if it isn't a config username.
        if self.write:
            try:
                username = self.site.userinfo['name']
            except KeyError:
                raise Error('API write action attempted without user name')

            if 'anon' in self.site.userinfo:
                raise Error(f'API write action attempted as IP {username!r}')

            if not self.site.user() or self.site.username() != username:
                pywikibot.warning(
                    f'API write action by unexpected username {username} '
                    f'commenced.\nuserinfo: {self.site.userinfo!r}')

        # Make sure user is logged in
        if self.write:
            pywikibot.debug('Adding user assertion')
            self['assert'] = 'user'

    @classmethod
    def create_simple(cls, req_site, **kwargs):
        """Create a new instance using all args except site for the API."""
        # This ONLY support site so that any caller can be sure there will be
        # no conflict with PWB parameters
        # req_site is needed to avoid conflicts with possible site keyword in
        # kwarg until positional-only parameters are supported, see T262926
        # TODO: Use ParamInfo request to determine valid parameters
        if isinstance(kwargs.get('parameters'), dict):
            warn('The request contains already a "parameters" entry which is '
                 'a dict.')
        return cls(site=req_site, parameters=kwargs)

    @classmethod
    def _warn_both(cls) -> None:
        """Warn that kwargs mode was used but parameters was set too."""
        warn('Both kwargs and parameters are set in Request.__init__. It '
             'assumes that "parameters" is actually a parameter of the '
             'Request and is added to kwargs.', DeprecationWarning, 3)

    @classmethod
    def _warn_kwargs(cls) -> None:
        """Warn that kwargs was used instead of parameters."""
        warn('Instead of using kwargs from Request.__init__, parameters '
             'for the request to the API should be added via the '
             '"parameters" parameter.', DeprecationWarning, 3)

    @classmethod
    def clean_kwargs(cls, kwargs: dict) -> dict:
        """
        Convert keyword arguments into new parameters mode.

        If there are no other arguments in kwargs apart from the used arguments
        by the class' initializer it'll just return kwargs and otherwise remove
        those which aren't in the initializer and put them in a dict which is
        added as a 'parameters' keyword. It will always create a shallow copy.

        :param kwargs: The original keyword arguments which is not modified.
        :return: The normalized keyword arguments.
        """
        if 'expiry' in kwargs and kwargs['expiry'] is None:
            del kwargs['expiry']

        args = set()
        for super_cls in inspect.getmro(cls):
            if not super_cls.__name__.endswith('Request'):
                break
            args |= set(inspect.getfullargspec(super_cls.__init__).args)
        else:
            raise ValueError(f'Request was not a super class of {cls!r}')

        args -= {'self'}
        old_kwargs = set(kwargs)
        # all kwargs defined above but not in args indicate 'kwargs' mode
        if old_kwargs - args:
            # Move all kwargs into parameters
            parameters = {name: value for name, value in kwargs.items()
                          if name not in args or name == 'parameters'}
            if 'parameters' in parameters:
                cls._warn_both()
            # Copy only arguments and not the parameters
            kwargs = {name: value for name, value in kwargs.items()
                      if name in args or name == 'self'}
            kwargs['parameters'] = parameters
            # Make sure that all arguments have remained
            assert (old_kwargs | {'parameters'}
                    == set(kwargs) | set(kwargs['parameters']))
            assert (('parameters' in old_kwargs)
                    is ('parameters' in kwargs['parameters']))
            cls._warn_kwargs()
        else:
            kwargs = dict(kwargs)
            kwargs.setdefault('parameters', {})
        return kwargs

    def _format_value(self, value):
        """
        Format the MediaWiki API request parameter.

        Converts from Python datatypes to MediaWiki API parameter values.

        Supports:
         * datetime.datetime (using strftime and ISO8601 format)
         * pywikibot.page.BasePage (using title (+namespace; -section))

        All other datatypes are converted to string.
        """
        if isinstance(value, datetime.datetime):
            return value.strftime(pywikibot.Timestamp.ISO8601Format)
        if isinstance(value, pywikibot.page.BasePage):
            if value.site != self.site:
                raise RuntimeError(f'value.site {value.site!r} is different '
                                   f'from Request.site {self.site!r}')
            return value.title(with_section=False)
        return str(value)

    def __getitem__(self, key):
        """Implement dict interface."""
        return self._params[key]

    def __setitem__(self, key: str, value) -> None:
        """Set MediaWiki API request parameter.

        :param value: param value(s)
        :type value: str in site encoding
            (string types may be a `|`-separated list)
            iterable, where items are converted to string
            with special handling for datetime.datetime to convert it to a
            string using the ISO 8601 format accepted by the MediaWiki API.
        """
        if isinstance(value, bytes):
            value = value.decode(self.site.encoding())

        if isinstance(value, str):
            value = value.split('|')

        if hasattr(value, 'api_iter'):
            self._params[key] = value
        else:
            try:
                iter(value)
            except TypeError:
                # convert any non-iterable value into a single-element list
                self._params[key] = [value]
            else:
                self._params[key] = list(value)

    def __delitem__(self, key) -> None:
        """Implement dict interface."""
        del self._params[key]

    def keys(self):
        """Implement dict interface."""
        return list(self._params)

    def __iter__(self):
        """Implement dict interface."""
        return iter(self._params)

    def __len__(self) -> int:
        """Implement dict interface."""
        return len(self._params)

    def iteritems(self):
        """Implement dict interface."""
        return iter(self._params.items())

    def items(self):
        """Return a list of tuples containing the parameters in any order."""
        return list(self._params.items())

    def _add_defaults(self):
        """
        Add default parameters to the API request.

        This method will only add them once.
        """
        if hasattr(self, '__defaulted'):
            return

        if self.mime is not None and set(self._params) & set(self.mime):
            raise ValueError('The mime and params shall not share the '
                             'same keys.')

        if self.action == 'query':
            meta = self._params.get('meta', [])
            # Special logic for private wikis (T153903).
            # If the wiki requires login privileges to read articles, pywikibot
            # will be blocked from accessing the userinfo.
            # Work around this by requiring userinfo only if 'tokens' and
            # 'login' are not both set.
            typep = self._params.get('type', [])
            if not ('tokens' in meta and 'login' in typep):
                if 'userinfo' not in meta:
                    meta = set(meta + ['userinfo'])
                    self['meta'] = sorted(meta)
                uiprop = self._params.get('uiprop', [])
                uiprop = set(uiprop + ['blockinfo', 'hasmsg'])
                self['uiprop'] = sorted(uiprop)
            if 'prop' in self._params \
               and self.site.has_extension('ProofreadPage'):
                prop = set(self['prop'] + ['proofread'])
                self['prop'] = sorted(prop)
            # When neither 'continue' nor 'rawcontinue' is present and the
            # version number is at least 1.25wmf5 we add a dummy rawcontinue
            # parameter. Querying siteinfo is save as it adds 'continue'
            # except for 'tokens' (T284577)
            if ('tokens' not in meta and 'continue' not in self._params
                    and self.site.mw_version >= '1.25wmf5'):
                self._params.setdefault('rawcontinue', [''])

        elif self.action == 'help':
            self['wrap'] = ''

        if config.maxlag:
            self._params.setdefault('maxlag', [str(config.maxlag)])
        self._params.setdefault('format', ['json'])
        if self['format'] != ['json']:
            raise TypeError(
                f'Query format {self["format"]!r} cannot be parsed.')

        self.__defaulted = True  # skipcq: PTC-W0037

    def _encoded_items(self) -> Dict[str, Union[str, bytes]]:
        """
        Build a dict of params with minimal encoding needed for the site.

        This helper method only prepares params for serialisation or
        transmission, so it only encodes values which are not ASCII,
        requiring callers to consider how to handle ASCII vs other values,
        however the output is designed to enable __str__ and __repr__ to
        do the right thing in most circumstances.

        Servers which use an encoding that is not a superset of ASCII
        are not supported.

        :return: Parameters either in the site encoding, or ASCII strings
        """
        params = {}
        for key, values in self._params.items():
            try:
                iterator = values.api_iter()
            except AttributeError:
                if len(values) == 1:
                    value = values[0]
                    if value is True:
                        values = ['']
                    elif value is False or value is None:
                        # False and None are not included in the http URI
                        continue
                iterator = iter(values)
            value = '|'.join(self._format_value(value) for value in iterator)
            # If the value is encodable as ascii, do not encode it.
            # This means that any value which can be encoded as ascii
            # is presumed to be ascii, and servers using a site encoding
            # which is not a superset of ascii may be problematic.
            try:
                value.encode('ascii')
            except UnicodeError:
                try:
                    value = value.encode(self.site.encoding())
                except Exception:
                    pywikibot.error(
                        f'_encoded_items: {key!r} could not be encoded as '
                        f'{self.site.encoding()!r}: {value!r}')
            assert key.encode('ascii')
            assert isinstance(key, str)
            params[key] = value
        return params

    def _http_param_string(self):
        """
        Return the parameters as a HTTP URL query fragment.

        URL encodes the parameters provided by _encoded_items()

        .. note:: Not all parameters are sorted, therefore for two given
           CachedRequest objects with equal _params, the result of
           _http_param_string() is not necessarily equal.
        """
        return encode_url(self._encoded_items())

    def __str__(self) -> str:
        """Return a string representation."""
        return unquote(self.site.scriptpath()
                       + '/api.php?'
                       + self._http_param_string())

    def __repr__(self) -> str:
        """Return internal representation."""
        cls = type(self)
        return f"{cls.__module__}.{cls.__name__}<{self.site}->'{self}'>"

    def _simulate(self, action):
        """Simulate action."""
        if action and config.simulate and (
                self.write or action in config.actions_to_block):
            pywikibot.info(
                f'<<black;yellow>>SIMULATION: {action} action blocked.')
            # for more realistic simulation
            if config.simulate is not True:
                pywikibot.sleep(float(config.simulate))
            return {
                action: {'result': 'Success', 'nochange': ''},

                # wikibase results
                'entity': {'lastrevid': -1, 'id': '-1'},
                'pageinfo': {'lastrevid': -1},
                'reference': {'hash': -1},
            }
        return None

    def _is_wikibase_error_retryable(self, error):
        # dict of error message and current action.
        # Value is True if action type is to be ignored
        err_msg = {
            'edit-already-exists': 'wbeditentity',
            'actionthrottledtext': True,  # T192912, T268645
        }
        messages = error.get('messages')
        message = None
        # bug T68619; after Wikibase breaking change 1ca9cee we have a
        # list of messages
        if isinstance(messages, list):
            for item in messages:
                message = item['name']
                action = err_msg.get(message)
                if action is True or action == self.action:
                    return True

            return False

        if isinstance(messages, dict):
            try:  # behaviour before gerrit 124323 breaking change
                message = messages['0']['name']
            except KeyError:  # unsure the new output is always a list
                message = messages['name']
        action = err_msg.get(message)
        return action is True or action == self.action

    @staticmethod
    def _generate_mime_part(key, content, keytype=None, headers=None):
        if not keytype:
            try:
                content.encode('ascii')
                keytype = ('text', 'plain')
            except (UnicodeError, AttributeError):
                keytype = ('application', 'octet-stream')
        submsg = MIMENonMultipart(*keytype)
        content_headers = {'name': key}
        if headers:
            content_headers.update(headers)
        submsg.add_header('Content-disposition', 'form-data',
                          **content_headers)

        if keytype != ('text', 'plain'):
            submsg['Content-Transfer-Encoding'] = 'binary'

        submsg.set_payload(content)
        return submsg

    def _use_get(self):
        """Verify whether 'get' is to be used."""
        if (not config.enable_GET_without_SSL
                and self.site.protocol() != 'https'
                or self.site.is_oauth_token_available()):  # T108182 workaround
            use_get = False
        elif self.use_get is None:
            if self.action == 'query':
                # for queries check the query module
                modules = set()
                for mod_type_name in ('list', 'prop', 'generator'):
                    modules.update(self._params.get(mod_type_name, []))
            else:
                modules = {self.action}
            if modules:
                self.site._paraminfo.fetch(modules)
                use_get = all('mustbeposted' not in self.site._paraminfo[mod]
                              for mod in modules)
            else:
                # If modules is empty, just 'meta' was given, which doesn't
                # require POSTs, and is required for ParamInfo
                use_get = True
        else:
            use_get = self.use_get
        return use_get

    @classmethod
    def _build_mime_request(cls, params: dict,
                            mime_params: dict) -> Tuple[dict, bytes]:
        """
        Construct a MIME multipart form post.

        :param params: HTTP request params
        :param mime_params: HTTP request parts which must be sent in the body
        :type mime_params: dict of (content, keytype, headers)  # noqa: DAR103
        :return: HTTP request headers and body
        """
        # construct a MIME message containing all API key/values
        container = pywikibot.data.api.MIMEMultipart(_subtype='form-data')
        for key, value in params.items():
            submsg = cls._generate_mime_part(key, value)
            container.attach(submsg)
        for key, value in mime_params.items():
            submsg = cls._generate_mime_part(key, *value)
            container.attach(submsg)

        # strip the headers to get the HTTP message body
        body = container.as_bytes()
        marker = b'\n\n'  # separates headers from body
        eoh = body.find(marker)
        body = body[eoh + len(marker):]
        # retrieve the headers from the MIME object
        headers = dict(container.items())
        return headers, body

    def _get_request_params(self, use_get, paramstring):
        """Get request parameters."""
        uri = self.site.apipath()
        if self.mime is not None:
            (headers, body) = Request._build_mime_request(
                self._encoded_items(), self.mime)
            use_get = False  # MIME requests require HTTP POST
        else:
            headers = {'Content-Type': 'application/x-www-form-urlencoded'}
            if (not config.maximum_GET_length
                    or config.maximum_GET_length < len(paramstring)):
                use_get = False

            if use_get:
                uri = f'{uri}?{paramstring}'
                body = None
            else:
                body = paramstring

        pywikibot.debug(f'API request to {self.site} (uses get: {use_get}):\n'
                        f'Headers: {headers!r}\nURI: {uri!r}\nBody: {body!r}')
        return use_get, uri, body, headers

    def _http_request(self, use_get: bool, uri: str, data, headers,
                      paramstring) -> tuple:
        """Get or post a http request with exception handling.

        :return: a tuple containing requests.Response object from
            http.request and use_get value
        """
        try:
            response = http.request(self.site, uri=uri,
                                    method='GET' if use_get else 'POST',
                                    data=data, headers=headers)
        except Server504Error:
            pywikibot.log('Caught HTTP 504 error; retrying')
        except Client414Error:
            if use_get:
                pywikibot.log('Caught HTTP 414 error; retrying')
                use_get = False
            else:
                pywikibot.warning(
                    'Caught HTTP 414 error, although not using GET.')
                raise
        except (ConnectionError, FatalServerError):
            # This error is not going to be fixed by just waiting
            pywikibot.error(traceback.format_exc())
            raise
        # TODO: what other exceptions can occur here?
        except Exception:
            # for any other error on the http request, wait and retry
            pywikibot.error(traceback.format_exc())
            pywikibot.log(f'{uri}, {paramstring}')
        else:
            return response, use_get
        self.wait()
        return None, use_get

    def _json_loads(self, response) -> Optional[dict]:
        """Return a dict from requests.Response.

        :param response: a requests.Response object
        :type response: requests.Response
        :return: a data dict
        :raises pywikibot.exceptions.APIError: unknown action found
        :raises pywikibot.exceptions.APIError: unknown query result type
        """
        try:
            result = response.json()
        except ValueError:
            # if the result isn't valid JSON, there may be a server problem.
            # Wait a few seconds and try again.
            # Show 20 lines of bare text without script parts
            text = removeDisabledParts(response.text, ['script'])
            text = re.sub('\n{2,}', '\n',
                          '\n'.join(removeHTMLParts(text).splitlines()[:20]))
            msg = f"""\
Non-JSON response received from server {self.site} for url
{response.url}
The server may be down.
Status code: {response.status_code}

The text message is:
{text}
"""

            # Do not retry for AutoFamily but raise a SiteDefinitionError
            # Note: family.AutoFamily is a function to create that class
            if self.site.family.__class__.__name__ == 'AutoFamily':
                pywikibot.debug(msg)
                raise SiteDefinitionError(
                    f'Invalid AutoFamily({self.site.family.domain!r})')

            if not self.json_warning:  # warn only once
                pywikibot.warning(msg)
                self.json_warning = True

            # there might also be an overflow, so try a smaller limit
            for param in self._params:
                if param.endswith('limit'):
                    # param values are stored a list of str
                    value = self[param][0]
                    if value.isdigit():
                        self[param] = [str(int(value) // 2)]
                        pywikibot.info(f'Set {param} = {self[param]}')
        else:
            return result or {}
        self.wait()
        return None

    def _relogin(self, message: str = '') -> None:
        """Force re-login and inform user."""
        message += ' Forcing re-login.'
        pywikibot.error(f'{message.strip()}')
        self.site._relogin()

    def _userinfo_query(self, result) -> bool:
        """Handle userinfo query."""
        if self.action == 'query' and 'userinfo' in result.get('query', ()):
            # if we get passed userinfo in the query result, we can confirm
            # that we are logged in as the correct user. If this is not the
            # case, force a re-login.
            username = result['query']['userinfo']['name']
            if (self.site.user() is not None and self.site.user() != username
                    and self.site._loginstatus != LoginStatus.IN_PROGRESS):
                self._relogin(f'Logged in as {username!r} instead of '
                              f'{self.site.user()!r}.')
                return True
        return False

    def _handle_warnings(self, result: Dict[str, Any]) -> bool:
        """Handle warnings; return True to retry request, False to resume.

        .. versionchanged:: 7.2
           Return True to retry the current request and Falso to resume.
        """
        retry = False
        if 'warnings' not in result:
            return retry

        for mod, warning in result['warnings'].items():
            if mod == 'info':
                continue
            if '*' in warning:
                text = warning['*']
            elif 'html' in warning:
                # bug T51978
                text = warning['html']['*']
            else:
                pywikibot.warning(
                    f'API warning ({mod}) of unknown format: {warning}')
                continue

            # multiple warnings are in text separated by a newline
            for single_warning in text.splitlines():
                if (not callable(self._warning_handler)
                        or not self._warning_handler(mod, single_warning)):
                    handled = self._default_warning_handler(mod,
                                                            single_warning)
                    if handled is None:
                        pywikibot.warning(
                            f'API warning ({mod}): {single_warning}')
                    else:
                        retry = retry or handled
        return retry

    def _default_warning_handler(self, mode: str, msg: str) -> Optional[bool]:
        """A default warning handler to handle specific warnings.

        Return True to retry the request, False to resume and None if
        the warning is not handled.

        .. versionadded:: 7.2
        """
        warnings = {
            'purge': ("You've exceeded your rate limit. "
                      'Please wait some time and try again.',
                      '_ratelimited', True),
        }
        warning, handler, retry = warnings.get(mode, (None, None, None))
        if handler and msg == warning:
            # Only show the first warning part
            pywikibot.warning(msg.split('.')[0] + '.')
            # call the handler
            getattr(self, handler)()
            return retry
        return None

    def _logged_in(self, code) -> bool:
        """Check whether user is logged in.

        Older wikis returned an error instead of a warning when the request
        asked for too many values. If we get this error, assume we are not
        logged in (we can't check this because the userinfo data is not
        present) and force a re-login
        """
        if code.endswith('limit'):
            message = 'Received API limit error.'

        # If the user assertion failed, we're probably logged out as well.
        elif code == 'assertuserfailed':
            message = 'User assertion failed.'

        # Lastly, the purge module requires a POST if used as anonymous user,
        # but we normally send a GET request. If the API tells us the request
        # has to be POSTed, we're probably logged out.
        elif code == 'mustbeposted' and self.action == 'purge':
            message = "Received unexpected 'mustbeposted' error."

        else:
            return True

        self._relogin(message)
        return False

    def _internal_api_error(self, code, error, result) -> bool:
        """Check for ``internal_api_error_`` or readonly and retry.

        :raises pywikibot.exceptions.APIMWError: internal_api_error or readonly
        """
        iae = 'internal_api_error_'
        if not (code.startswith(iae) or code == 'readonly'):
            return False

        # T154011
        class_name = code if code == 'readonly' else removeprefix(code, iae)

        del error['code']  # is added via class_name
        e = pywikibot.exceptions.APIMWError(class_name, **error)

        # If the error key is in this table, it is probably a temporary
        # problem, so we will retry the edit.
        # TODO: T154011: 'ReadOnlyError' seems replaced by 'readonly'
        retry = class_name in ['DBConnectionError',  # T64974
                               'DBQueryError',  # T60158
                               'DBQueryTimeoutError',  # T297708
                               'ReadOnlyError',  # T61227
                               'readonly',  # T154011
                               ]

        pywikibot.error('Detected MediaWiki API exception {}{}'
                        .format(e, '; retrying' if retry else '; raising'))
        param_repr = str(self._params)
        pywikibot.log(f'MediaWiki exception {class_name} details:\n'
                      f'          query=\n{pprint.pformat(param_repr)}\n'
                      f'          response=\n{result}')
        if not retry:
            raise e

        self.wait()
        return True

    def _ratelimited(self) -> None:
        """Handle ratelimited warning."""
        ratelimits = self.site.userinfo['ratelimits']
        delay = None

        ratelimit = ratelimits.get(self.action, {})
        # find the lowest wait time for the given action
        for limit in ratelimit.values():
            seconds = limit['seconds']
            hits = limit['hits']
            delay = min(delay or seconds, seconds / hits)

        if not delay:
            pywikibot.warning(
                f'No rate limit found for action {self.action}')
        self.wait(delay)

    def _bad_token(self, code) -> bool:
        """Check for bad token.

        Check for bad tokens, call :meth:`TokenWallet.update_tokens()
        <pywikibot.site._tokenwallet.TokenWallet.update_tokens>` method
        to update the bunch of tokens and continue loop in :meth:`submit`.
        """
        if code != 'badtoken':  # Other code not handled here
            return False

        if self.site._loginstatus == LoginStatus.IN_PROGRESS:
            pywikibot.log(f'Login status: {self.site._loginstatus.name}')
            return False

        # invalidate superior wiki cookies (T224712)
        pywikibot.data.api._invalidate_superior_cookies(self.site.family)
        # update tokens
        tokens = self.site.tokens.update_tokens(self._params['token'])
        self._params['token'] = tokens
        return True

    def submit(self) -> dict:
        """Submit a query and parse the response.

        .. versionchanged:: 8.0.4
           in addition to *readapidenied* also try to login when API
           response is *notloggedin*.

        :return: a dict containing data retrieved from api.php
        """
        self._add_defaults()
        use_get = self._use_get()
        retries = 0
        while True:
            paramstring = self._http_param_string()

            simulate = self._simulate(self.action)
            if simulate:
                return simulate

            if self.throttle:
                self.site.throttle(write=self.write)
            else:
                pywikibot.log(
                    f"Submitting unthrottled action '{self.action}'.")

            use_get, uri, body, headers = self._get_request_params(use_get,
                                                                   paramstring)
            response, use_get = self._http_request(use_get, uri, body, headers,
                                                   paramstring)
            if response is None:
                continue

            result = self._json_loads(response)
            if result is None:
                continue

            if self._userinfo_query(result):
                continue

            if self._handle_warnings(result):
                continue

            if 'error' not in result:
                return result

            error = result['error']
            for key in result:
                if key in ('error', 'warnings'):
                    continue
                assert key not in error
                error[key] = result[key]

            if '*' in error:
                # help text returned
                error['help'] = error.pop('*')
            code = error.setdefault('code', 'Unknown')
            info = error.setdefault('info', None)

            if not self._logged_in(code):
                continue

            if code == 'maxlag':
                retries += 1
                if retries > max(5, pywikibot.config.max_retries):
                    break
                pywikibot.log('Pausing due to database lag: ' + info)

                try:
                    lag = error['lag']
                except KeyError:
                    lag = lagpattern.search(info)
                    lag = float(lag['lag']) if lag else 0.0

                self.site.throttle.lag(lag * retries)
                continue

            if code == 'help' and self.action == 'help':
                # The help module returns an error result with the complete
                # API information. As this data was requested, return the
                # data instead of raising an exception.
                return {'help': {'mime': 'text/plain',
                                 'help': error['help']}}

            pywikibot.warning(f'API error {code}: {info}')
            pywikibot.log(f'           headers=\n{response.headers}')

            if self._internal_api_error(code, error.copy(), result):
                continue

            # Phab. tickets T48535, T64126, T68494, T68619
            if code == 'failed-save' \
               and self._is_wikibase_error_retryable(error):
                self.wait()
                continue

            if code == 'ratelimited':
                self._ratelimited()
                continue

            # If notloggedin or readapidenied is returned try to login
            if code in ('notloggedin', 'readapidenied') \
               and self.site._loginstatus in (LoginStatus.NOT_ATTEMPTED,
                                              LoginStatus.NOT_LOGGED_IN):
                self.site.login()
                continue

            if self._bad_token(code):
                continue

            if 'mwoauth-invalid-authorization' in code:
                msg = f'OAuth authentication for {self.site}: {info}'
                if 'Nonce already used' in info:
                    pywikibot.error(f'Retrying failed {msg}')
                    continue
                raise NoUsernameError(f'Failed {msg}')
            if code == 'cirrussearch-too-busy-error':  # T170647
                self.wait()
                continue

            if code in ('search-title-disabled', 'search-text-disabled'):
                prefix = 'gsr' if 'gsrsearch' in self._params else 'sr'
                del self._params[prefix + 'what']
                # use intitle: search instead
                if code == 'search-title-disabled' \
                   and self.site.has_extension('CirrusSearch'):
                    key = prefix + 'search'
                    self._params[key] = ['intitle:' + search
                                         for search in self._params[key]]
                continue

            if code == 'urlshortener-blocked':  # T244062
                # add additional informations to error dict
                error['current site'] = self.site
                if self.site.user():
                    error['current user'] = self.site.user()
                else:  # not logged in; show the IP
                    uinfo = self.site.userinfo
                    error['current user'] = uinfo['name']

            # raise error
            try:
                param_repr = str(self._params)
                pywikibot.log(
                    f'API Error: query=\n{pprint.pformat(param_repr)}')
                pywikibot.log(f'           response=\n{result}')

                args = {'param': body} if body else {}
                args.update(error)
                raise pywikibot.exceptions.APIError(**args)
            except TypeError:
                raise RuntimeError(result)

        msg = 'Maximum retries attempted due to maxlag without success.'
        if os.environ.get('PYWIKIBOT_TEST_RUNNING', '0') == '1':
            import unittest
            raise unittest.SkipTest(msg)

        raise MaxlagTimeoutError(msg)

    def wait(self, delay=None):
        """Determine how long to wait after a failed request."""
        self.current_retries += 1
        if self.current_retries > self.max_retries:
            raise TimeoutError('Maximum retries attempted without success.')

        # double the next wait, but do not exceed config.retry_max seconds
        delay = delay or self.retry_wait
        delay *= 2 ** (self.current_retries - 1)
        delay = min(delay, config.retry_max)

        pywikibot.warning(f'Waiting {delay:.1f} seconds before retrying.')
        pywikibot.sleep(delay)


class CachedRequest(Request):

    """Cached request."""

    def __init__(self, expiry, *args, **kwargs) -> None:
        """Initialize a CachedRequest object.

        :param expiry: either a number of days or a datetime.timedelta object
        """
        assert expiry is not None
        super().__init__(*args, **kwargs)
        if not isinstance(expiry, datetime.timedelta):
            expiry = datetime.timedelta(expiry)
        self.expiry = min(expiry, datetime.timedelta(config.API_config_expiry))
        self._data = None
        self._cachetime = None

    @classmethod
    def create_simple(cls, req_site, **kwargs):
        """Unsupported as it requires at least two parameters."""
        raise NotImplementedError('CachedRequest cannot be created simply.')

    @classmethod
    def _get_cache_dir(cls) -> Path:
        """
        Return the base directory path for cache entries.

        The directory will be created if it does not already exist.

        .. versionchanged:: 8.0
           return a `pathlib.Path` object.

        :return: base directory path for cache entries
        """
        path = Path(config.base_dir, f'apicache-py{PYTHON_VERSION[0]:d}')
        cls._make_dir(path)
        cls._get_cache_dir = classmethod(lambda c: path)  # cache the result
        return path

    @staticmethod
    def _make_dir(dir_name: Union[str, Path]) -> Path:
        """Create directory if it does not exist already.

        .. versionchanged:: 7.0
           Only `FileExistsError` is ignored but other OS exceptions can
           be still raised
        .. versionchanged:: 8.0
           use *dir_name* as str or `pathlib.Path` object but always
           return a Path object.

        :param dir_name: directory path
        :return: directory path as `pathlib.Path` object for test purpose
        """
        if isinstance(dir_name, str):
            dir_name = Path(dir_name)
        dir_name.mkdir(exist_ok=True)
        return dir_name

    def _uniquedescriptionstr(self) -> str:
        """Return unique description for the cache entry.

        If this is modified, please also update
        scripts/maintenance/cache.py to support
        the new key and all previous keys.
        """
        login_status = self.site._loginstatus

        if login_status >= LoginStatus.AS_USER:
            # This uses the format of Page.__repr__, without performing
            # config.console_encoding as done by Page.__repr__.
            # The returned value can't be encoded to anything other than
            # ascii otherwise it creates an exception when _create_file_name()
            # tries to encode it as utf-8.
            user_key = f'User(User:{self.site.userinfo["name"]})'
        else:
            user_key = repr(LoginStatus(LoginStatus.NOT_LOGGED_IN))

        request_key = repr(sorted(self._encoded_items().items()))
        return f'{self.site!r}{user_key}{request_key}'

    def _create_file_name(self) -> str:
        """Return a unique ascii identifier for the cache entry."""
        return hashlib.sha256(
            self._uniquedescriptionstr().encode('utf-8')
        ).hexdigest()

    def _cachefile_path(self) -> Path:
        """Create the cachefile path.

        .. versionchanged:: 8.0
           return a `pathlib.Path` object.
        """
        return CachedRequest._get_cache_dir() / self._create_file_name()

    def _expired(self, dt):
        return dt + self.expiry < datetime.datetime.utcnow()

    def _load_cache(self) -> bool:
        """Load cache entry for request, if available.

        :return: Whether the request was loaded from the cache
        """
        self._add_defaults()
        try:
            filename = self._cachefile_path()
            with filename.open('rb') as f:
                uniquedescr, self._data, self._cachetime = pickle.load(f)

            if uniquedescr != self._uniquedescriptionstr():
                raise RuntimeError('Expected unique description for the cache '
                                   'entry is different from file entry.')

            if self._expired(self._cachetime):
                self._data = None
                return False

            pywikibot.debug(
                f'{type(self).__name__}: cache ({filename.parent}) hit\n'
                f'{filename.name}, API request:\n{uniquedescr}')

        except OSError:
            pass  # file not found
        except Exception as e:
            pywikibot.info(f'Could not load cache: {e!r}')
        else:
            return True

        return False

    def _write_cache(self, data) -> None:
        """Write data to self._cachefile_path()."""
        data = (self._uniquedescriptionstr(), data, datetime.datetime.utcnow())
        path = self._cachefile_path()
        with suppress(OSError), path.open('wb') as f:
            pickle.dump(data, f, protocol=config.pickle_protocol)
            return
        # delete invalid cache entry
        path.unlink()

    def submit(self):
        """Submit cached request."""
        cached_available = self._load_cache()
        if not cached_available:
            self._data = super().submit()
            self._write_cache(self._data)
        else:
            self._handle_warnings(self._data)
        return self._data


def encode_url(query) -> str:
    """Encode parameters to pass with a url.

    Reorder parameters so that token parameters go last and call wraps
    :py:obj:`urlencode`. Return an HTTP URL query fragment which
    complies with :api:`Edit#Parameters` (See the 'token' bullet.)

    :param query: keys and values to be uncoded for passing with a url
    :type query: mapping object or a sequence of two-element tuples
    :return: encoded parameters with token parameters at the end
    """
    if hasattr(query, 'items'):
        query = list(query.items())

    # parameters ending on 'token' should go last
    # wpEditToken should go very last
    query.sort(key=lambda x: x[0].lower().endswith('token')
               + (x[0] == 'wpEditToken'))
    return urlencode(query)
