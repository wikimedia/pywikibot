# -*- coding: utf-8  -*-
"""
Interface functions to Mediawiki's api.php
"""
#
# (C) Pywikipedia bot team, 2007-08
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: $'

from UserDict import DictMixin
from datetime import datetime, timedelta
import simplejson as json
import logging
import re
import traceback
import time
import urllib
import warnings

import pywikibot
from pywikibot import login
from pywikibot.exceptions import *

logger = logging.getLogger("data.api")

lagpattern = re.compile(r"Waiting for [\d.]+: (?P<lag>\d+) seconds? lagged")

_modules = {} # cache for retrieved API parameter information


class APIError(pywikibot.Error):
    """The wiki site returned an error message."""
    def __init__(self, code, info, **kwargs):
        """Save error dict returned by MW API."""
        self.code = code
        self.info = info
        self.other = kwargs
    def __repr__(self):
        return 'APIError("%(code)s", "%(info)s", %(other)s)' % self.__dict__
    def __str__(self):
        return "%(code)s: %(info)s" % self.__dict__


class APIWarning(UserWarning):
    """The API returned a warning message."""
    pass


class TimeoutError(pywikibot.Error):
    pass


class Request(DictMixin):
    """A request to a Site's api.php interface.

    Attributes of this object (except for the special parameters listed
    below) get passed as commands to api.php, and can be get or set using
    the dict interface.  All attributes must be strings (or unicode).  Use
    an empty string for parameters that don't require a value (e.g.,
    "action=query&...&redirects").

    This is the lowest-level interface to the API, and can be used for any
    request that a particular site's API supports. See the API documentation
    (http://www.mediawiki.org/wiki/API) and site-specific settings for
    details on what parameters are accepted for each request type.

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
        self.max_retries = kwargs.pop("max_retries", 25)
        self.retry_wait = kwargs.pop("retry_wait", 5)
        self.params = {}
        if "action" not in kwargs:
            raise ValueError("'action' specification missing from Request.")
        self.update(**kwargs)

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
    
    def submit(self):
        """Submit a query and parse the response.

        @return:  The data retrieved from api.php (a dict)
        
        """
        from pywikibot.comms import http

        for key in self.params:
            if isinstance(self.params[key], basestring):
                self.params[key] = self.params[key].split("|")
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
                    info = set(info + ["protection", "talkid", "subjectid"])
                    self.params["info"] = list(info)
        if "maxlag" not in self.params:
            self.params["maxlag"] = [str(pywikibot.config2.maxlag)]
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
                logger.exception("key=%s, params=%s" % (key, self.params[key]))
        params = urllib.urlencode(self.params)
        while True:
            # TODO catch http errors
            action = self.params.get("action", "")
            write = action in (
                        "edit", "move", "rollback", "delete", "undelete",
                        "protect", "block", "unblock"
                    )
            self.site.throttle(write=write)
            uri = self.site.scriptpath() + "/api.php"
            try:
                if write or action in ("login", "expandtemplates", "parse"):
                    # add other actions that require POST requests above
                    rawdata = http.request(self.site, uri, method="POST",
                                headers={'Content-Type':
                                         'application/x-www-form-urlencoded'},
                                body=params)
                else:
                    uri = uri + "?" + params
                    rawdata = http.request(self.site, uri)
            except Exception, e: #TODO: what exceptions can occur here?
                logger.warning(traceback.format_exc())
                logger.warning("%s, %s", uri, params)
                self.wait()
                continue
            logger.debug("API response received:\n%s", rawdata)
            if not isinstance(rawdata, unicode):
                rawdata = rawdata.decode(self.site.encoding())
            if rawdata.startswith(u"unknown_action"):
                raise APIError(rawdata[:14], rawdata[16:])
            try:
                result = json.loads(rawdata)
            except ValueError:
                # if the result isn't valid JSON, there must be a server
                # problem.  Wait a few seconds and try again
                logger.warning(
"Non-JSON response received from server %s; the server may be down."
                              % self.site)
                logger.debug(rawdata)
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

            if "warnings" in result:
                modules = [k for k in result["warnings"] if k != "info"]
                for mod in modules:
                    logger.warning(
                        "API warning (%s): %s"
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
                    logger.info(
                        "Pausing due to database lag: " + info)
                    self.site.throttle.lag(int(lag.group("lag")))
                    continue
            if code in (u'internal_api_error_DBConnectionError', ):
                self.wait()
                continue
            # raise error
            try:
                raise APIError(code, info, **result["error"])
            except TypeError:
                raise RuntimeError(result)

    def wait(self):
        """Determine how long to wait after a failed request."""
        self.max_retries -= 1
        if self.max_retries < 0:
            raise TimeoutError("Maximum retries attempted without success.")
        logger.warn("Waiting %s seconds before retrying." % self.retry_wait)
        time.sleep(self.retry_wait)
        # double the next wait, but do not exceed 120 seconds
        self.retry_wait = min(120, self.retry_wait * 2)


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
        # make sure request type is valid, and get limit key if any
        for modtype in ("generator", "list", "prop", "meta"):
            if modtype in kwargs:
                self.module = kwargs[modtype]
                break
        else:
            raise Error("%s: No query module name found in arguments."
                        % self.__class__.__name__)
        for name in self.module.split("|"):
            if name not in _modules:
                self.get_module()
                break
        self.set_limit()
        if self.query_limit is not None and "generator" in kwargs:
            self.prefix = "g" + self.prefix
        self.request = Request(**kwargs)
        self.limit = None
        if "generator" in kwargs:
            self.resultkey = "pages"        # name of the "query" subelement key
        else:                               # to look for when iterating
            self.resultkey = self.module
        self.continuekey = self.module      # usually the query-continue key
                                            # is the same as the querymodule,
                                            # but not always

    def get_module(self):
        """Query api on self.site for paraminfo on querymodule=self.module"""
        
        paramreq = Request(site=self.site, action="paraminfo",
                           querymodules=self.module)
        data = paramreq.submit()
        assert "paraminfo" in data
        assert "querymodules" in data["paraminfo"]
        assert len(data["paraminfo"]["querymodules"]) == 1+self.module.count("|")
        for paraminfo in data["paraminfo"]["querymodules"]:
            assert paraminfo["name"] in self.module
            if "missing" in paraminfo:
                raise Error("Invalid query module name '%s'." % self.module)
            _modules[paraminfo["name"]] = paraminfo

    def set_limit(self):
        """Set query_limit for self.module based on api response"""

        self.query_limit = None
        for mod in self.module.split('|'):
            for param in _modules[mod].get("parameters", []):
                if param["name"] == "limit":
                    if (self.site.logged_in()
                            and "apihighlimits" in
                                self.site.getuserinfo()["rights"]):
                        self.query_limit = int(param["highmax"])
                    else:
                        self.query_limit = int(param["max"])
                    self.prefix = _modules[mod]["prefix"]
                    logger.debug("%s: Set query_limit to %i."
                                  % (self.__class__.__name__, self.query_limit))
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
                if new_limit is not None:
                    self.request[self.prefix+"limit"] = str(new_limit)
            self.data = self.request.submit()
            if not self.data or not isinstance(self.data, dict):
                logger.debug(
                    "%s: stopped iteration because no dict retrieved from api."
                    % self.__class__.__name__)
                return
            if not ("query" in self.data
                    and self.resultkey in self.data["query"]):
                logger.debug(
"%s: stopped iteration because 'query' and '%s' not found in api response.",
                        self.__class__.__name__, self.resultkey)
                logger.debug(self.data)
                return
            pagedata = self.data["query"][self.resultkey]
            if isinstance(pagedata, dict):
                logger.debug("%s received %s; limit=%s"
                         % (self.__class__.__name__, pagedata.keys(),
                            self.limit))
                pagedata = pagedata.values()
            else:
                logger.debug("%s received %s; limit=%s"
                         % (self.__class__.__name__, pagedata,
                            self.limit))                
            for item in pagedata:
                yield self.result(item)
                count += 1
                if self.limit is not None and self.limit > 0 \
                                          and count >= self.limit:
                    return
            if not "query-continue" in self.data:
                return
            if not self.continuekey in self.data["query-continue"]:
                raise Error("Missing '%s' key in ['query-continue'] value."
                            % self.continuekey)
            update = self.data["query-continue"][self.continuekey]
            for key, value in update.iteritems():
                # query-continue can return ints
                if isinstance(value, int):
                    value = str(value)
                self.request[key] = value

    def result(self, data):
        """Process result data as needed for particular subclass."""
        return data


class PageGenerator(QueryGenerator):
    """Iterator for response to a request of type action=query&generator=foo.

    This class can be used for any of the query types that are listed in the
    API documentation as being able to be used as a generator.  Instances of
    this class iterate Page objects.
    
    """
    def __init__(self, generator, **kwargs):
        """
        Required and optional parameters are as for C{Request}, except that
        action=query is assumed and generator is required.
        
        @param generator: the "generator=" type from api.php
        @type generator: str

        """
        QueryGenerator.__init__(self, generator=generator, **kwargs)
        # get some basic information about every page generated
        if 'prop' in self.request:
            self.request['prop'] += "|info|imageinfo"
        else:
            self.request['prop'] = 'info|imageinfo'
        if "inprop" in self.request:
            if "protection" not in self.request["inprop"]:
                self.request["inprop"] += "|protection"
        else:
            self.request['inprop'] = 'protection'
        if "iiprop" in self.request:
            self.request["iiprop"] += 'timestamp|user|comment|url|size|sha1|metadata'
        else:
            self.request['iiprop'] = 'timestamp|user|comment|url|size|sha1|metadata'
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


class LoginManager(login.LoginManager):
    """Supplies getCookie() method to use API interface."""
    def getCookie(self, remember=True, captchaId=None, captchaAnswer=None):
        """Login to the site.

        Parameters are all ignored.

        Returns cookie data if succesful, None otherwise.
        
        """
        if hasattr(self, '_waituntil'):
            if datetime.now() < self._waituntil:
                time.sleep(self._waituntil - datetime.now())
        login_request = Request(site=self.site,
                                action="login",
                                lgname=self.username,
                                lgpassword=self.password
                               )
        login_result = login_request.submit()
        if u"login" not in login_result:
            raise RuntimeError("API login response does not have 'login' key.")
        if login_result['login']['result'] == u'Success':
            prefix = login_result['login']['cookieprefix']
            cookies = []
            for key in ('Token', 'UserID', 'UserName'):
                cookies.append("%s%s=%s"
                               % (prefix, key,
                                  login_result['login']['lg'+key.lower()]))
            self.username = login_result['login']['lgusername']
            return "\n".join(cookies)
        elif login_result['login']['result'] == "Throttled":
            self._waituntil = datetime.now() \
                              + timedelta(seconds=int(
                                            login_result["login"]["wait"])
                                          )
        raise APIError(code=login_result["login"]["result"], info="")

    def storecookiedata(self, data):
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
    page._redir = 'redirect' in pagedict
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
                                        user=rev['user'],
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


if __name__ == "__main__":
    from pywikibot import Site
    logger.setLevel(pywikibot.logging.DEBUG)
    mysite = Site("en", "wikipedia")
    pywikibot.output("starting test....")
    def _test():
        import doctest
        doctest.testmod()
    try:
        _test()
    finally:
        pywikibot.stopme()

