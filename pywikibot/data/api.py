# -*- coding: utf-8  -*-
"""
Interface functions to Mediawiki's api.php
"""
#
# (C) Pywikipedia bot team, 2007-12
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

from UserDict import DictMixin
from datetime import datetime, timedelta
from pywikibot.comms import http
from email.mime.multipart import MIMEMultipart
from email.mime.nonmultipart import MIMENonMultipart
import json
import logging
import mimetypes
import pprint
import re
import traceback
import time
import urllib
import warnings

import pywikibot
from pywikibot import config, login
from pywikibot.exceptions import *

_logger = "data.api"

lagpattern = re.compile(r"Waiting for [\d.]+: (?P<lag>\d+) seconds? lagged")

class APIError(pywikibot.Error):
    """The wiki site returned an error message."""
    def __init__(self, code, info, **kwargs):
        """Save error dict returned by MW API."""
        self.code = code
        self.info = info
        self.other = kwargs
        self.unicode = unicode(self.__str__())

    def __repr__(self):
        return 'APIError("%(code)s", "%(info)s", %(other)s)' % self.__dict__

    def __str__(self):
        return "%(code)s: %(info)s" % self.__dict__


class APIWarning(UserWarning):
    """The API returned a warning message."""
    pass


class TimeoutError(pywikibot.Error):
    pass


class Request(object, DictMixin):
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
    (http://www.mediawiki.org/wiki/API) and site-specific settings for
    details on what parameters are accepted for each request type.

    Uploading files is a special case: to upload, the parameter "mime" must
    be true, and the parameter "file" must be set equal to a valid
    filename on the local computer, _not_ to the content of the file.

    Returns a dict containing the JSON data returned by the wiki. Normally,
    one of the dict keys will be equal to the value of the 'action'
    parameter.  Errors are caught and raise an APIError exception.

    Example:

    >>> r = Request(site=mysite, action="query", meta="userinfo")
    >>> # This is equivalent to
    >>> # http://{path}/api.php?action=query&meta=userinfo&format=json
    >>> # change a parameter
    >>> r['meta'] = "userinfo|siteinfo"
    >>> # add a new parameter
    >>> r['siprop'] = "namespaces"
    >>> # note that "uiprop" param gets added automatically
    >>> r.params
    {'action': 'query', 'meta': 'userinfo|siteinfo', 'siprop': 'namespaces'}
    >>> data = r.submit()
    >>> type(data)
    <type 'dict'>
    >>> data.keys()
    [u'query']
    >>> data[u'query'].keys()
    [u'userinfo', u'namespaces']

    @param site: The Site to which the request will be submitted. If not
           supplied, uses the user's configured default Site.
    @param mime: If true, send in "multipart/form-data" format (default False)
    @param max_retries: (optional) Maximum number of times to retry after
           errors, defaults to 25
    @param retry_wait: (optional) Minimum time to wait after an error,
           defaults to 5 seconds (doubles each retry until max of 120 is
           reached)
    @param format: (optional) Defaults to "json"

    """
    def __init__(self, **kwargs):
        try:
            self.site = kwargs.pop("site")
        except KeyError:
            self.site = pywikibot.Site()
        self.mime = kwargs.pop("mime", False)
        self.max_retries = kwargs.pop("max_retries", 25)
        self.retry_wait = kwargs.pop("retry_wait", 5)
        self.params = {}
        if "action" not in kwargs:
            raise ValueError("'action' specification missing from Request.")
        self.update(**kwargs)
        self.write = self.params["action"] in (
                        "edit", "move", "rollback", "delete", "undelete",
                        "protect", "block", "unblock", "watch", "patrol",
                        "import", "userrights", "upload", "wbeditentity",
                        "wbsetlabel", "wbsetdescription", "wbsetaliases",
                        "wblinktitles", "wbsetsitelink", "wbcreateclaim",
                        "wbremoveclaims", "wbsetclaimvalue", "wbsetreference",
                        "wbremovereferences"
                    )
        if self.params["action"] == "edit":
            pywikibot.debug(u"Adding user assertion", _logger)
            self.params["assert"] = "user"  # make sure user is logged in

    # implement dict interface
    def __getitem__(self, key):
        return self.params[key]

    def __setitem__(self, key, value):
        self.params[key] = value

    def __delitem__(self, key):
        del self.params[key]

    def keys(self):
        return self.params.keys()

    def __contains__(self, key):
        return self.params.__contains__(key)

    def __iter__(self):
        return self.params.__iter__()

    def iteritems(self):
        return self.params.iteritems()

    def http_params(self):
        """Return the parameters formatted for inclusion in an HTTP request."""

        for key in self.params:
            if isinstance(self.params[key], basestring):
                # convert a stringified sequence into a list
                self.params[key] = self.params[key].split("|")
            try:
                iter(self.params[key])
            except TypeError:
                # convert any non-iterable value into a single-element list
                self.params[key] = [str(self.params[key])]
        if self.params["action"] == ['query']:
            meta = self.params.get("meta", [])
            if "userinfo" not in meta:
                meta.append("userinfo")
                self.params["meta"] = meta
            uiprop = self.params.get("uiprop", [])
            uiprop = set(uiprop + ["blockinfo", "hasmsg"])
            self.params["uiprop"] = list(uiprop)
            if "properties" in self.params:
                if "info" in self.params["properties"]:
                    inprop = self.params.get("inprop", [])
                    info = set(inprop + ["protection", "talkid", "subjectid"])
                    self.params["info"] = list(info)
        if "maxlag" not in self.params and config.maxlag:
            self.params["maxlag"] = [str(config.maxlag)]
        if "format" not in self.params:
            self.params["format"] = ["json"]
        if self.params['format'] != ["json"]:
            raise TypeError("Query format '%s' cannot be parsed."
                            % self.params['format'])
        for key in self.params:
            try:
                self.params[key] = "|".join(self.params[key])
                if isinstance(self.params[key], unicode):
                    self.params[key] = self.params[key].encode(
                                                self.site.encoding())
            except Exception:
                pywikibot.error(
u"http_params: Key '%s' could not be encoded to '%s'; params=%r"
                      % (key, self.site.encoding(), self.params[key]))
        return urllib.urlencode(self.params)

    def __str__(self):
        return urllib.unquote(self.site.scriptpath()
                              + "/api.php?"
                              + self.http_params()
                             )

    def _simulate(self, action):
        if action and config.simulate and action in config.actions_to_block:
            pywikibot.output(
                u'\03{lightyellow}SIMULATION: %s action blocked.\03{default}'
                % action)
            return {action: {'result': 'Success', 'nochange': ''}}

    def submit(self):
        """Submit a query and parse the response.

        @return:  The data retrieved from api.php (a dict)

        """
        paramstring = self.http_params()
        while True:
            action = self.params.get("action", "")
            simulate = self._simulate(action)
            if simulate:
                return simulate
            self.site.throttle(write=self.write)
            uri = self.site.scriptpath() + "/api.php"
            ssl = False
            if self.site.family.name in config.available_ssl_project:
                if action == "login" and config.use_SSL_onlogin:
                    ssl = True
                elif config.use_SSL_always:
                    ssl = True
            try:
                if self.mime:
                    # construct a MIME message containing all API key/values
                    container = MIMEMultipart(_subtype='form-data')
                    for key in self.params:
                        # key "file" requires special treatment in a multipart
                        # message
                        if key == "file":
                            local_filename = self.params[key]
                            filetype = mimetypes.guess_type(local_filename)[0] \
                                       or 'application/octet-stream'
                            file_content = file(local_filename, "rb").read()
                            submsg = MIMENonMultipart(*filetype.split("/"))
                            submsg.add_header("Content-disposition",
                                              "form-data", name=key,
                                              filename=local_filename)
                            submsg.set_payload(file_content)
                        else:
                            try:
                                self.params[key].encode("ascii")
                                keytype = ("text", "plain")
                            except UnicodeError:
                                keytype = ("application", "octet-stream")
                            submsg = MIMENonMultipart(*keytype)
                            submsg.add_header("Content-disposition", "form-data",
                                              name=key)
                            submsg.set_payload(self.params[key])
                        container.attach(submsg)
                    # strip the headers to get the HTTP message body
                    body = container.as_string()
                    marker = "\n\n" # separates headers from body
                    eoh = body.find(marker)
                    body = body[ eoh + len(marker): ]
                    # retrieve the headers from the MIME object
                    mimehead = dict(container.items())
                    rawdata = http.request(self.site, uri, ssl, method="POST",
                                           headers=mimehead, body=body)
                else:
                    rawdata = http.request(self.site, uri, ssl, method="POST",
                                headers={'Content-Type':
                                         'application/x-www-form-urlencoded'},
                                body=paramstring)
##                import traceback
##                traceback.print_stack()
##                print rawdata
            except Server504Error:
                pywikibot.log(u"Caught HTTP 504 error; retrying")
                self.wait()
                continue
            #TODO: what other exceptions can occur here?
            except Exception, e:
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
                pywikibot.debug(rawdata, _logger)
                # there might also be an overflow, so try a smaller limit
                for param in self.params:
                    if param.endswith("limit"):
                        value = self.params[param]
                        try:
                            self.params[param] = str(int(value) // 2)
                            pywikibot.output(u"Set %s = %s"
                                             % (param, self.params[param]))
                        except:
                            pass
                self.wait()
                continue
            if not result:
                result = {}
            if type(result) is not dict:
                raise APIError("Unknown",
                               "Unable to process query response of type %s."
                                   % type(result),
                               {'data': result})
            if self['action'] == 'query':
                if 'userinfo' in result.get('query', ()):
                    if hasattr(self.site, '_userinfo'):
                        self.site._userinfo.update(result['query']['userinfo'])
                    else:
                        self.site._userinfo = result['query']['userinfo']
                status = self.site._loginstatus # save previous login status
                if ( ("error" in result
                            and result["error"]["code"].endswith("limit"))
                      or (status >= 0
                            and self.site._userinfo['name']
                                != self.site._username[status])):
                    # user is no longer logged in (session expired?)
                    # reset userinfo, then make user log in again
                    del self.site._userinfo
                    self.site._loginstatus = -1
                    if status < 0:
                        status = 0  # default to non-sysop login
                    self.site.login(status)
                    # retry the previous query
                    continue
            if "warnings" in result:
                modules = [k for k in result["warnings"] if k != "info"]
                for mod in modules:
                    pywikibot.warning(
                        u"API warning (%s): %s"
                         % (mod, result["warnings"][mod]["*"]))
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
            if code in (u'internal_api_error_DBConnectionError', ):
                self.wait()
                continue
            # raise error
            try:
                pywikibot.log(u"API Error: query=\n%s"
                               % pprint.pformat(self.params))
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

import datetime
import hashlib
import pickle
import os

class CachedRequest(Request):
    def __init__(self, expiry, *args, **kwargs):
        """ expiry should be either a number of days or a datetime.timedelta object """
        super(CachedRequest, self).__init__(*args, **kwargs)
        if not isinstance(expiry, datetime.timedelta):
            expiry = datetime.timedelta(expiry)
        self.expiry = expiry
        self._data = None
        self._cachetime = None

    def _get_cache_dir(self):
        path = os.path.join(pywikibot.config2.base_dir, 'apicache')
        self._make_dir(path)
        return path

    def _make_dir(self, dir):
        try:
            os.makedirs(dir)
        except OSError:
            # directory already exists
            pass

    def _create_file_name(self):
        return hashlib.sha256(str(self.site) + str(self)).hexdigest()

    def _cachefile_path(self):
        return os.path.join(self._get_cache_dir(), self._create_file_name())

    def _expired(self, dt):
        return dt + self.expiry < datetime.datetime.now()

    def _load_cache(self):
        """ Returns whether the cache can be used """
        try:
            sitestr, selfstr, self._data, self._cachetime = pickle.load(open(self._cachefile_path()))
            assert(sitestr == str(self.site))
            assert(selfstr == str(self))
            if self._expired(self._cachetime):
                self._data = None
                return False
            return True
        except Exception:
            return False

    def _write_cache(self, data):
        """ writes data to self._cachefile_path() """
        data = [str(self.site), str(self), data, datetime.datetime.now()]
        pickle.dump(data, open(self._cachefile_path(), 'w'))

    def submit(self):
        cached_available = self._load_cache()
        if not cached_available:
            self._data = super(CachedRequest, self).submit()
            self._write_cache(self._data)
        return self._data


class QueryGenerator(object):
    """Base class for iterators that handle responses to API action=query.

    By default, the iterator will iterate each item in the query response,
    and use the query-continue element, if present, to continue iterating as
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
        """
        Constructor: kwargs are used to create a Request object;
        see that object's documentation for values. 'action'='query' is
        assumed.

        """
        if "action" in kwargs and "action" != "query":
            raise Error("%s: 'action' must be 'query', not %s"
                        % (self.__class__.__name__, kwargs["query"]))
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
        self.request = Request(**kwargs)
        self.prefix = None
        self.update_limit() # sets self.prefix
        if self.api_limit is not None and "generator" in kwargs:
            self.prefix = "g" + self.prefix
        self.limit = None
        self.query_limit = self.api_limit
        if "generator" in kwargs:
            self.resultkey = "pages"        # name of the "query" subelement key
        else:                               # to look for when iterating
            self.resultkey = self.module
        self.continuekey = self.module      # usually the query-continue key
                                            # is the same as the querymodule,
                                            # but not always

    @property
    def __modules(self):
        """
        Instance cache: hold the query data for paraminfo on
        querymodule=self.module at self.site

        """
        if not hasattr(self.site, "_modules"):
            setattr(self.site, "_modules", dict())
        return self.site._modules

    @__modules.deleter
    def __modules(self):
        """Delete the instance cache - maybe we don't need it"""
        if hasattr(self.site, "_modules"):
            del self.site._modules

    @property
    def _modules(self):
        """Query api on self.site for paraminfo on querymodule=self.module"""
        if not set(self.module.split('|')) <= set(self.__modules.keys()):
            paramreq = CachedRequest(expiry=config.API_config_expiry,
                                     site=self.site, action="paraminfo",
                                     querymodules=self.module)
            data = paramreq.submit()
            assert "paraminfo" in data
            assert "querymodules" in data["paraminfo"]
            assert len(data["paraminfo"]["querymodules"]) == 1 + self.module.count("|")
            for paraminfo in data["paraminfo"]["querymodules"]:
                assert paraminfo["name"] in self.module
                if "missing" in paraminfo:
                    raise Error("Invalid query module name '%s'." % self.module)
                self.__modules[paraminfo["name"]] = paraminfo
        _modules = {}
        for m in self.module.split('|'):
            _modules[m] = self.__modules[m]
        return _modules

    def set_query_increment(self, value):
        """Set the maximum number of items to be retrieved per API query.

        If not called, the default is to ask for "max" items and let the
        API decide how many to send.

        """
        limit = int(value)
        # don't update if limit is greater than maximum allowed by API
        self.update_limit()
        if self.api_limit is None:
            self.query_limit = limit
        else:
            self.query_limit = min(self.api_limit, limit)

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
        """Set query limit for self.module based on api response"""

        self.api_limit = None
        for mod in self.module.split('|'):
            for param in self._modules[mod].get("parameters", []):
                if param["name"] == "limit":
                    if (self.site.logged_in()
                        and self.site.has_right('apihighlimits')):
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
                    self.request[self.prefix+"namespace"] = namespaces
                    return

    def __iter__(self):
        """Submit request and iterate the response based on self.resultkey

        Continues response as needed until limit (if any) is reached.

        """
        count = 0
        while True:
            if self.query_limit is not None:
                if self.limit is None:
                    new_limit = self.query_limit
                elif self.limit > 0:
                    new_limit = min(self.query_limit, self.limit - count)
                else:
                    new_limit = None
                if "rvprop" in self.request \
                        and "content" in self.request["rvprop"]:
                    # queries that retrieve page content have lower limits
                    # Note: although API allows up to 500 pages for content
                    #   queries, these sometimes result in server-side errors
                    #   so use 250 as a safer limit
                    new_limit = min(new_limit, self.api_limit // 10, 250)
                if new_limit is not None:
                    self.request[self.prefix+"limit"] = str(new_limit)
            if not hasattr(self, "data"):
                try:
                    self.data = self.request.submit()
                except Server504Error:
                    # server timeout, usually caused by request with high limit
                    old_limit = self.query_limit
                    if old_limit is None or old_limit < 2:
                        raise
                    pywikibot.log("Setting query limit to %s" % (old_limit // 2))
                    self.set_query_increment(old_limit // 2)
                    continue
            if not self.data or not isinstance(self.data, dict):
                pywikibot.debug(
                    u"%s: stopped iteration because no dict retrieved from api."
                        % self.__class__.__name__,
                    _logger)
                return
            if "query" not in self.data:
                pywikibot.debug(
u"%s: stopped iteration because 'query' not found in api response."
                        % (self.__class__.__name__, self.resultkey),
                    _logger)
                pywikibot.debug(unicode(self.data), _logger)
                return
            if self.resultkey in self.data["query"]:
                resultdata = self.data["query"][self.resultkey]
                if isinstance(resultdata, dict):
                    pywikibot.debug(u"%s received %s; limit=%s"
                                      % (self.__class__.__name__,
                                         resultdata.keys(),
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
                    count += 1
                    if self.limit > 0 and count >= self.limit:
                        return
            if not "query-continue" in self.data:
                return
            if not self.continuekey in self.data["query-continue"]:
                pywikibot.log(
                    u"Missing '%s' key in ['query-continue'] value."
                      % self.continuekey)
                return
            update = self.data["query-continue"][self.continuekey]
            for key, value in update.iteritems():
                # query-continue can return ints
                if isinstance(value, int):
                    value = str(value)
                self.request[key] = value
            del self.data # a new request with query-continue is needed

    def result(self, data):
        """Process result data as needed for particular subclass."""
        return data


class PageGenerator(QueryGenerator):
    """Iterator for response to a request of type action=query&generator=foo.

    This class can be used for any of the query types that are listed in the
    API documentation as being able to be used as a generator.  Instances of
    this class iterate Page objects.

    """
    def __init__(self, generator, g_content=False, **kwargs):
        """
        Required and optional parameters are as for C{Request}, except that
        action=query is assumed and generator is required.

        @param generator: the "generator=" type from api.php
        @type generator: str
        @param g_content: if True, retrieve the contents of the current
            version of each Page (default False)

        """
        # get some basic information about every page generated
        if 'prop' in kwargs:
            kwargs['prop'] += "|info|imageinfo|categoryinfo"
        else:
            kwargs['prop'] = 'info|imageinfo|categoryinfo'
        if g_content:
            # retrieve the current revision
            kwargs['prop'] += "|revisions"
            if "rvprop" in kwargs:
                kwargs["rvprop"] += "ids|timestamp|flags|comment|user|content"
            else:
                kwargs["rvprop"] = "ids|timestamp|flags|comment|user|content"
        if "inprop" in kwargs:
            if "protection" not in kwargs["inprop"]:
                kwargs["inprop"] += "|protection"
        else:
            kwargs['inprop'] = 'protection'
        if "iiprop" in kwargs:
            kwargs["iiprop"] += 'timestamp|user|comment|url|size|sha1|metadata'
        else:
            kwargs['iiprop'] = 'timestamp|user|comment|url|size|sha1|metadata'
        QueryGenerator.__init__(self, generator=generator, **kwargs)
        self.resultkey = "pages" # element to look for in result

    def result(self, pagedata):
        """Convert page dict entry from api to Page object.

        This can be overridden in subclasses to return a different type
        of object.

        """
        p = pywikibot.Page(self.site, pagedata['title'], pagedata['ns'])
        update_page(p, pagedata)
        return p


class CategoryPageGenerator(PageGenerator):
    """Like PageGenerator, but yields Category objects instead of Pages."""

    def result(self, pagedata):
        p = PageGenerator.result(self, pagedata)
        return pywikibot.Category(p)


class ImagePageGenerator(PageGenerator):
    """Like PageGenerator, but yields ImagePage objects instead of Pages."""

    def result(self, pagedata):
        p = PageGenerator.result(self, pagedata)
        image = pywikibot.ImagePage(p)
        if 'imageinfo' in pagedata:
            image._imageinfo = pagedata['imageinfo'][0]
        return image


class PropertyGenerator(QueryGenerator):
    """Iterator for queries of type action=query&property=...

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
        Required and optional parameters are as for C{Request}, except that
        action=query is assumed and prop is required.

        @param prop: the "property=" type from api.php
        @type prop: str

        """
        QueryGenerator.__init__(self, prop=prop, **kwargs)
        self.resultkey = "pages"


class ListGenerator(QueryGenerator):
    """Iterator for queries of type action=query&list=...

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
        Required and optional parameters are as for C{Request}, except that
        action=query is assumed and listaction is required.

        @param listaction: the "list=" type from api.php
        @type listaction: str

        """
        QueryGenerator.__init__(self, list=listaction, **kwargs)


class LogEntryListGenerator(ListGenerator):
    """
    Like ListGenerator, but specialized for listaction="logevents" :
    yields LogEntry objects instead of dicts.
    """
    def __init__(self, logtype=None, **kwargs):
        ListGenerator.__init__(self, "logevents", **kwargs)

        import logentries
        self.entryFactory = logentries.LogEntryFactory(logtype)

    def result(self, pagedata):
        return self.entryFactory.create(pagedata)


class LoginManager(login.LoginManager):
    """Supplies getCookie() method to use API interface."""
    def getCookie(self, remember=True, captchaId=None, captchaAnswer=None):
        """Login to the site.

        Parameters are all ignored.

        Returns cookie data if succesful, None otherwise.

        """
        if hasattr(self, '_waituntil'):
            if datetime.now() < self._waituntil:
                diff = self._waituntil - datetime.now()
                pywikibot.warning(u"Too many tries, waiting %s seconds before retrying."
                                    % diff.seconds)
                time.sleep(diff.seconds)
        login_request = Request(site=self.site,
                                action="login",
                                lgname=self.username,
                                lgpassword=self.password
                               )
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
                                      login_result['login']['lg'+key.lower()]))
                self.username = login_result['login']['lgusername']
                return "\n".join(cookies)
            elif login_result['login']['result'] == "NeedToken":
                token = login_result['login']['token']
                login_request["lgtoken"] = token
                continue
            elif login_result['login']['result'] == "Throttled":
                self._waituntil = datetime.now() \
                                  + timedelta(seconds=int(
                                                login_result["login"]["wait"])
                                              )
                break
            else:
                break
        raise APIError(code=login_result["login"]["result"], info="")

    def storecookiedata(self, data):
        # ignore data; cookies are set by threadedhttp module
        pywikibot.cookie_jar.save()


def update_page(page, pagedict):
    """Update attributes of Page object page, based on query data in pagedict

    @param page: object to be updated
    @type page: Page
    @param pagedict: the contents of a "page" element of a query response
    @type pagedict: dict

    """
    if "pageid" in pagedict:
        page._pageid = int(pagedict['pageid'])
    elif "missing" in pagedict:
        page._pageid = 0    # Non-existent page
    else:
        raise AssertionError(
            "Page %s has neither 'pageid' nor 'missing' attribute"
             % pagedict['title'])
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
                                        timestamp=rev['timestamp'],
                                        user=rev.get('user', u''),
                                        anon='anon' in rev,
                                        comment=rev.get('comment',  u''),
                                        minor='minor' in rev,
                                        text=rev.get('*', None)
                                      )
            page._revisions[revision.revid] = revision

    if 'lastrevid' in pagedict:
        page._revid = pagedict['lastrevid']
        if page._revid in page._revisions:
            page._text = page._revisions[page._revid].text

    if "categoryinfo" in pagedict:
        page._catinfo = pagedict["categoryinfo"]

    if "templates" in pagedict:
        page._templates = [ pywikibot.Page(page.site, tl['title'])
                                for tl in pagedict['templates'] ]

    if "langlinks" in pagedict:
        links = []
        for ll in pagedict["langlinks"]:
            link = pywikibot.Link.langlinkUnsafe(ll['lang'],
                                                 ll['*'],
                                                 source=page.site)
            links.append(link)
        page._langlinks = links


if __name__ == "__main__":
    from pywikibot import Site, logging
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

