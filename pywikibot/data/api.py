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

import config
import pywikibot
from pywikibot import login

lagpattern = re.compile(r"Waiting for [\d.]+: (?P<lag>\d+) seconds? lagged")


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


class TimeoutError(pywikibot.Error):
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
    >>> # http://{path}/api.php?action=query&meta=userinfo&format=json
    >>> # r.data is undefined until request is submitted
    >>> print r.data
    Traceback (most recent call last):
        ...
    AttributeError: Request instance has no attribute 'data'
    >>> # change a parameter
    >>> r['meta'] = "userinfo|siteinfo"
    >>> # add a new parameter
    >>> r['siprop'] = "namespaces"
    >>> # note that "uiprop" param gets added automatically
    >>> r.params
    {'maxlag': '5', 'format': 'json', 'meta': 'userinfo|siteinfo', 'action': 'query', 'siprop': 'namespaces', 'uiprop': 'blockinfo|hasmsg'}
    >>> data = r.submit()
    >>> type(data)
    <type 'dict'>
    >>> data.keys()
    [u'query']
    >>> data[u'query'].keys()
    [u'userinfo', u'namespaces']
    
    """
    def __init__(self, **kwargs):
        self.site = kwargs.pop("site", pywikibot.Site())
        self.max_retries = kwargs.pop("max_retries", 25)
        self.retry_wait = kwargs.pop("retry_wait", 5)
        self.params = {}
        if "action" not in kwargs:
            raise ValueError("'action' specification missing from Request.")
        if kwargs["action"] == 'query':
            if "meta" in kwargs:
                if "userinfo" not in kwargs["meta"]:
                    kwargs["meta"] += "|userinfo"
            else:
                kwargs["meta"] = "userinfo"
            if "uiprop" in kwargs:
                kwargs["uiprop"] += "|blockinfo|hasmsg"
            else:
                kwargs["uiprop"] = "blockinfo|hasmsg"
        if "format" not in kwargs:
            self.params["format"] = "json"
        if "maxlag" not in kwargs:
            self.params["maxlag"] = str(config.maxlag)
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
        if self.params['format'] != 'json':
            raise TypeError("Query format '%s' cannot be parsed."
                            % self.params['format'])
        for key in self.params:
            if isinstance(self.params[key], unicode):
                self.params[key] = self.params[key].encode(self.site.encoding())
        params = urllib.urlencode(self.params)
        while True:
            # TODO catch http errors
            self.site.throttle()  # TODO: add write=True when needed
            uri = self.site.scriptpath() + "/api.php"
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
                logging.warning(
"Non-JSON response received from server %s; the server may be down."
                              % self.site)
                print rawdata
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
        logging.warn("Waiting %s seconds before retrying." % self.retry_wait)
        time.sleep(self.retry_wait)
        # double the next wait, but do not exceed 120 seconds
        self.retry_wait = min(120, self.retry_wait * 2)

    def lag_wait(self, lag):
        """Wait due to server lag."""
        # unlike regular wait, this shuts down all access to site
        self.site.sitelock.acquire()
        try:
            # wait at least 5 seconds, no more than 120
            wait = max(5, min(120, lag//2))
            logging.warn("Pausing %s seconds due to server lag." % wait)
            time.sleep(wait)
        finally:
            self.site.sitelock.release()


class PageGenerator(object):
    """Iterator for response to a request of type action=query&generator=foo."""
    def __init__(self, generator, **kwargs):
        """
        Required and optional parameters are as for C{Request}, except that
        action=query is assumed and generator is required.
        
        @param generator: the "generator=" type from api.php
        @type generator: str

        """
        if generator not in self.limits:
            raise ValueError("Unrecognized generator '%s'" % generator)
        self.request = Request(action="query", generator=generator, **kwargs)
        # set limit to max, if applicable
        if self.limits[generator]:
            self.request['g'+self.limits[generator]] = "max"
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
        self.generator = generator
        self.site = self.request.site
        self.resultkey = "pages" # element to look for in result

    # dict mapping generator types to their limit parameter names
    limits = {'links': None,
              'images': None,
              'templates': None,
              'categories': None,
              'allpages': 'aplimit',
              'alllinks': 'allimit',
              'allcategories': 'aclimit',
              'backlinks': 'bllimit',
              'categorymembers': 'cmlimit',
              'embeddedin': 'eilimit',
              'imageusage': 'iulimit',
              'search': 'srlimit',
              'watchlist': 'wllimit',
              'exturlusage': 'eulimit',
              'random': 'rnlimit',
             }

    def __iter__(self):
        """Iterate objects for elements found in response."""
        # FIXME: this won't handle generators with <redirlinks> subelements
        #        correctly yet
        while True:
            self.site.throttle()
            self.data = self.request.submit()
            if not self.data or not isinstance(self.data, dict):
                raise StopIteration
            if not "query" in self.data:
                raise StopIteration
            query = self.data["query"]
            if not self.resultkey in query:
                raise StopIteration
            if isinstance(query[self.resultkey], dict):
                for v in query[self.resultkey].itervalues():
                    yield self.result(v) 
            elif isinstance(query[self.resultkey], list):
                for v in query[self.resultkey]:
                    yield self.result(v)
            else:
                raise APIError("Unknown",
                               "Unknown format in ['query']['%s'] value."
                                 % self.resultkey,
                               data=query[self.resultkey])
            if not "query-continue" in self.data:
                return
            if not self.generator in self.data["query-continue"]:
                raise APIError("Unknown",
                               "Missing '%s' key in ['query-continue'] value.",
                               data=self.data["query-continue"])
            self.request.update(self.data["query-continue"][self.generator])

    def result(self, pagedata):
        """Convert page dict entry from api to Page object.

        This can be overridden in subclasses to return a different type
        of object.
        
        """
        p = pywikibot.Page(self.site, pagedata['title'], pagedata['ns'])
        update_page(p, pagedata)
        return p


class CategoryPageGenerator(PageGenerator):
    """Generator that yields Category objects instead of Pages."""
    def result(self, pagedata):
        p = PageGenerator.result(self, pagedata)
        return pywikibot.Category(p)


class ImagePageGenerator(PageGenerator):
    """Generator that yields ImagePage objects instead of Pages."""
    def result(self, pagedata):
        p = PageGenerator.result(self, pagedata)
        image = pywikibot.ImagePage(p)
        if 'imageinfo' in pagedata:
            image._imageinfo = pagedata['imageinfo']
        return image


class PropertyGenerator(object):
    """Generator for queries of type action=query&property=...

    Note that this generator yields one or more dict object(s) corresponding
    to each "page" item(s) from the API response; the calling module has to
    decide what to do with the contents of the dict."""

    def __init__(self, prop, **kwargs):
        """
        Required and optional parameters are as for C{Request}, except that
        action=query is assumed and prop is required.
        
        @param prop: the "property=" type from api.php
        @type prop: str

        """
        self.request = Request(action="query", prop=prop, **kwargs)
        if prop not in self.limits:
            raise ValueError("Unrecognized property '%s'" % prop)
        # set limit to max, if applicable
        if self.limits[prop] and kwargs.pop("getAll", False):
            self.request['g'+self.limits[generator]] = "max"
        self.site = self.request.site
        self.resultkey = prop

    # dict mapping property types to their limit parameter names
    limits = {'revisions': 'rvlimit',
              'imageinfo': 'iilimit',
              'info': None,
              'links': None,
              'langlinks': None,
              'images': None,
              'imageinfo': None,
              'templates': None,
              'categories': None,
              'extlinks': None,
             }

    def __iter__(self):
        """Iterate objects for elements found in response."""
        # this looks for the resultkey ''inside'' a <page> entry
        while True:
            self.site.throttle()
            self.data = self.request.submit()
            if not self.data or not isinstance(self.data, dict):
                raise StopIteration
            if not ("query" in self.data and "pages" in self.data["query"]):
                raise StopIteration
            pagedata = self.data["query"]["pages"].values()
            for item in pagedata:
                yield item
            if not "query-continue" in self.data:
                return
            if not self.resultkey in self.data["query-continue"]:
                raise APIError("Unknown",
                               "Missing '%s' key in ['query-continue'] value.",
                               data=self.data["query-continue"])
            self.request.update(self.data["query-continue"][self.resultkey])


class LoginManager(login.LoginManager):
    """Supplies getCookie() method to use API interface."""
    def getCookie(self, remember=True, captchaId=None, captchaAnswer=None):
        """
        Login to the site.

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

    def storecookiedata(self, data):
        pywikibot.cookie_jar.save()


def update_page(page, pagedict):
    """Update attributes of Page object page, based on query data in pagequery

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
    if 'lastrevid' in pagedict:
        page._revid = pagedict['lastrevid']
    if 'touched' in pagedict:
        page._timestamp = pagedict['touched']
    if 'protection' in pagedict:
        page._protection = {}
        for item in pagedict['protection']:
            page._protection[item['type']] = item['level'], item['expiry']

if __name__ == "__main__":
    from pywikibot import Site
    logging.getLogger().setLevel(logging.DEBUG)
    mysite = Site("en", "wikipedia")
    print "starting test...."
    def _test():
        import doctest
        doctest.testmod()
    try:
        _test()
    finally:
        pywikibot.stopme()

