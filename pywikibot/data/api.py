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
import urllib
import http
import simplejson as json
import warnings


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


class Request(DictMixin):
    """A request to a Site's api.php interface.

    Attributes of this object get passed as commands to api.php, and can be
    get or set using the dict interface.  All attributes must be strings
    (unicode). Attributes supplied without values are passed to the API as
    keys.
    
    @param   site: The Site to which the request will be submitted. If not
                   supplied, uses the user's configured default Site.
    @param format: (optional) Defaults to "json"

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
        if "site" in kwargs:
            self.site = kwargs["site"]
            del kwargs["site"]
            # else use defaultSite() ... when written
        self.params = {}
        if not "format" in kwargs:
            self.params["format"] = "json"
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

        @return:       The data retrieved from api.php (a dict)
        
        """
        if self.params['format'] != 'json':
            raise TypeError("Query format '%s' cannot be parsed."
                            % self.params['format'])
        uri = self.site.script_path() + "api.php"
        params = urllib.urlencode(self.params)
        while True:
            # TODO wait on errors
            # TODO catch http errors
            if self.params.get("action", "") in ("login",):
                rawdata = http.request(self.site, uri, method="POST",
                                headers={'Content-Type':
                                        'application/x-www-form-urlencoded'},
                                body=params)
                return rawdata
            else:
                uri = uri + "?" + params
                rawdata = http.request(self.site, uri)
            if rawdata.startswith(u"unknown_action"):
                e = {'code': data[:14], 'info': data[16:]}
                raise APIError(e)
            try:
                result = json.loads(rawdata)
            except ValueError:
                # if the result isn't valid JSON, there must be a server
                # problem.  Wait a few seconds and try again
                # TODO: implement a throttle
                warnings.warn(
"Non-JSON response received from server %s; the server may be down."
                              % self.site)
                print rawdata
                continue
            if not result:
                return {}
            if type(result) is dict:
                if "error" in result:
                    if "code" in result["error"]:
                        code = result["error"]["code"]
                        del result["error"]["code"]
                    else:
                        code = "Unknown"
                    if "info" in result["error"]:
                        info = result["error"]["info"]
                        del result["error"]["info"]
                    else:
                        info = None
                    # raise error
                    raise APIError(code, info, **result["error"])
                return result
            raise APIError("Unknown",
                           "Unable to process query response of type %s."
                               % type(result),
                           {'data': result})

if __name__ == "__main__":
    from pywikibot.tests.dummy import TestSite as Site
    mysite = Site("en.wikipedia.org")
    
