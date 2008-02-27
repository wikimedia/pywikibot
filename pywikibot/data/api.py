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
import http
import simplejson as json
import logging
import re
import traceback
import time
import urllib

from pywikibot import login


lagpattern = re.compile(r"Waiting for [\d.]+: (?P<lag>\d+) seconds? lagged")


class APIError(Exception):
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


class TimeoutError(Exception):
    pass


class Request(DictMixin):
    """A request to a Site's api.php interface.

    Attributes of this object (except for the special parameters listed
    below) get passed as commands to api.php, and can be get or set using
    the dict interface.  All attributes must be strings (or unicode).  Use
    an empty string for parameters that don't require a value (e.g.,
    "action=query&...&redirects").
    
    @param site: The Site to which the request will be submitted. If not
           supplied, uses the user's configured default Site.
    @param max_retries: (optional) Maximum number of times to retry after
           errors, defaults to 25
    @param retry_wait: (optional) Minimum time to wait after an error,
           defaults to 5 seconds (doubles each retry until max of 120 is
           reached)
    @param format: (optional) Defaults to "json"

    Example:

    >>> r = Request(site=mysite, action="query", meta="userinfo")
    >>> # This is equivalent to
    >>> # http://[path]/api.php?action=query&meta=userinfo&format=json
    >>> # r.data is undefined until request is submitted
    >>> print r.data
    Traceback (most recent call last):
        ...
    AttributeError: Request instance has no attribute 'data'
    >>> # change a parameter
    >>> r['meta'] = "userinfo|siteinfo"
    >>> # add a new parameter
    >>> r['siprop'] = "namespaces"
    >>> r.params
    {'action': 'query', 'meta': 'userinfo|siteinfo', 'maxlag': '5', 'siprop': 'namespaces', 'format': 'json'}
    >>> data = r.submit()
    >>> type(data)
    <type 'dict'>
    >>> data.keys()
    [u'query']
    >>> data[u'query'].keys()
    [u'userinfo', u'namespaces']
    
    """
    def __init__(self, **kwargs):
        self.site = kwargs.pop("site", None)
            # else use defaultSite() ... when written
        self.max_retries = kwargs.pop("max_retries", 25)
        self.retry_wait = kwargs.pop("retry_wait", 5)
        self.params = {}
        if "format" not in kwargs:
            self.params["format"] = "json"
        if "maxlag" not in kwargs:
            self.params["maxlag"] = "5" # replace with configurable constant?
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
        if self.params['format'] != 'json':
            raise TypeError("Query format '%s' cannot be parsed."
                            % self.params['format'])
        uri = self.site.scriptpath() + "/api.php"
        params = urllib.urlencode(self.params)
        while True:
            # TODO wait on errors
            # TODO catch http errors
            try:
                if self.params.get("action", "") in ("login",):
                    rawdata = http.request(self.site, uri, method="POST",
                                headers={'Content-Type':
                                         'application/x-www-form-urlencoded'},
                                body=params)
                else:
                    uri = uri + "?" + params
                    rawdata = http.request(self.site, uri)
            except Exception, e: #TODO: what exceptions can occur here?
                logging.warning(traceback.format_exc())
                print uri, params
                self.wait()
                continue
            if rawdata.startswith(u"unknown_action"):
                raise APIError(rawdata[:14], rawdata[16:])
            try:
                result = json.loads(rawdata)
            except ValueError:
                # if the result isn't valid JSON, there must be a server
                # problem.  Wait a few seconds and try again
                # TODO: implement a throttle
                logging.warning(
"Non-JSON response received from server %s; the server may be down."
                              % self.site)
                print rawdata
                self.wait(max_retries, retry_wait)
                continue
            if not result:
                result = {}
            if type(result) is not dict:
                raise APIError("Unknown",
                               "Unable to process query response of type %s."
                                   % type(result),
                               {'data': result})
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
                    logging.info(
                        "Pausing due to database lag: " + info)
                    self.wait(int(lag.group("lag")))
                    continue
            if code in (u'internal_api_error_DBConnectionError', ):
                self.wait()
                continue
            # raise error
            try:
                raise APIError(code, info, **result["error"])
            except TypeError:
                raise RuntimeError(result)

    def wait(self, lag=None):
        """Determine how long to wait after a failed request."""
        self.max_retries -= 1
        if self.max_retries < 0:
            raise TimeoutError("Maximum retries attempted without success.")

        wait = self.retry_wait
        if lag is not None:
            if lag > 2 * self.retry_wait:
                wait = min(120, lag // 2)
        logging.warn("Waiting %s seconds before retrying." % self.retry_wait)
        time.sleep(wait)
        self.retry_wait = min(120, self.retry_wait * 2)


class PageGenerator(object):
    """Iterator for response to a request of type action=query&generator=foo."""
    def __init__(self, generator="", **kwargs):
        """
        Required and optional parameters are as for C{Request}, except that
        action=query is assumed and generator is required.
        
        @param generator: the "generator=" type from api.php
        @type generator: str

        """
        if not generator:
            raise ValueError("generator argument is required.")
        self.request = Request(action="query", generator=generator, **kwargs)
        self.generator = generator
        self.site = self.request.site

    def __iter__(self):
        """Iterate Page objects for pages found in response."""
        while True:
            # following "if" is used for testing with plugged-in data; it wouldn't
            # be needed for actual usage
            if not hasattr(self, "data"):
                self.data = self.request.submit()
            if not self.data or not isinstance(self.data, dict):
                raise StopIteration
            if not "query" in self.data:
                raise StopIteration
            query = self.data["query"]
            if not "pages" in query:
                raise StopIteration
            # TODO: instead of "yield Page", yield a Page returned by a
            # method that converts the dict info to a Page object
            if isinstance(query["pages"], dict):
                for v in query["pages"].itervalues():
                    yield Page(self.site, v['title']) 
            elif isinstance(query["pages"], list):
                for v in query["pages"]:
                    yield Page(self.site, v['title'])
            else:
                raise APIError("Unknown",
                               "Unknown format in ['query']['pages'] value.",
                               data=query["pages"])
            if not "query-continue" in self.data:
                return
            if not self.generator in self.data["query-continue"]:
                raise APIError("Unknown",
                               "Missing '%s' key in ['query-continue'] value.",
                               data=self.data["query-continue"])
            self.request.update(self.data["query-continue"][self.generator])
            del self.data


class LoginManager(login.LoginManager):
    """Supplies getCookie() method to use API interface."""
    def getCookie(self, remember=True, captchaId=None, captchaAnswer=None):
        """
        Login to the site.

        Paramters are all ignored.

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
        if login_result['login']['result'] != u'Success':
            self._waituntil = datetime.datetime.now() + datetime.timedelta(seconds=60)
            return None

        prefix = login_result['login']['cookieprefix']
        cookies = []
        for key in ('Token', 'UserID', 'UserName'):
            cookies.append("%s%s=%s"
                           % (prefix, key,
                              login_result['login']['lg'+key.lower()]))
        self.username = login_result['login']['lgusername']
        return "\n".join(cookies)


if __name__ == "__main__":
    from pywikibot import Site
    mysite = Site("en", "wikipedia")
    logging.getLogger().setLevel(logging.DEBUG)
    def _test():
        import doctest
        doctest.testmod()
    _test()


