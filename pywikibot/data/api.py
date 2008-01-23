# -*- coding: utf-8  -*-
"""
Interface functions to Mediawiki's api.php
"""
#
# (C) Pywikipedia bot team, 2007
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: $'

from UserDict import DictMixin
import http
import simplejson as json
import logging
import re
import traceback
import time
import urllib


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
    the dict interface.  All attributes must be strings (unicode).
    Attributes supplied without values are passed to the API as keys.
    
    @param site: The Site to which the request will be submitted. If not
           supplied, uses the user's configured default Site.
    @param format: (optional) Defaults to "json"
    @param max_retries: (optional) Maximum number of times to retry after
           errors, defaults to 25
    @param retry_wait: (optional) Minimum time to wait after an error,
           defaults to 5 seconds (doubles each retry until max of 120 is
           reached)

    Example:

    >>> r = Request(site=mysite, action="query", meta="userinfo")
    >>> # This is equivalent to
    >>> # http://[path]/api.php?action=query&meta=userinfo&format=json
    >>> # change a parameter
    >>> r['meta'] = "userinfo|siteinfo"
    >>> # add a new parameter
    >>> r['siprop'] = "namespaces"
    >>> r.params
    {'action': 'query', 'meta': 'userinfo|siteinfo', 'siprop': 'namespaces',
    'format': 'json'}
    >>> data = r.submit()
    >>> type(data)
    <type 'dict'>    
    
    """
    def __init__(self, *args, **kwargs):
        self.site = kwargs.pop("site", None)
            # else use defaultSite() ... when written
        self.max_retries = kwargs.pop("max_retries", 25)
        self.retry_wait = kwargs.pop("retry_wait", 5)
        self.params = {}
        if "format" not in kwargs:
            self.params["format"] = "json"
        if "maxlag" not in kwargs:
            self.params["maxlag"] = "5"
        self.update(*args, **kwargs)

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
    
    def update(self, *args, **kwargs):
        """Update the request parameters"""
        self.params.update(kwargs)
        for arg in args:
            if arg not in self.params:
                self.params[arg] = ""

    def submit(self):
        """Submit a query and parse the response.

        @return:  The data retrieved from api.php (a dict)
        
        """
        if self.params['format'] != 'json':
            raise TypeError("Query format '%s' cannot be parsed."
                            % self.params['format'])
        uri = self.site.script_path() + "api.php"
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
            code = result["error"].pop("code", "Unknown")
            info = result["error"].pop("info", None)
            if code == "maxlag":
                lag = lagpattern.search(info)
                if lag:
                    logging.info(
                        "Pausing due to database lag: " + info)
                    self.wait(int(lag.group("lag")))
                    continue
            # raise error
            raise APIError(code, info, **result["error"])


    def wait(self, lag=None):
        """Determine how long to wait after a failed request."""
        self.max_retries -= 1
        if self.max_retries < 0:
            raise TimeoutError("Maximum retries attempted without success.")
        
        if lag is not None:
            if lag > 2 * self.retry_wait:
                self.retry_wait = min(120, lag // 2)
        logging.warn("Waiting %s seconds before retrying." % self.retry_wait)
        time.sleep(self.retry_wait)
        self.retry_wait = min(120, self.retry_wait * 2)
        

if __name__ == "__main__":
    from pywikibot.tests.dummy import TestSite as Site
    mysite = Site("en.wikipedia.org")
    logging.getLogger().setLevel(logging.DEBUG)
