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


import urllib
import http
import simplejson as json
import warnings

class APIError(Exception):
    """The wiki site returned an error message."""
    def __init__(self, errordict):
        """Save error dict returned by MW API."""
        self.errors = errordict

    def __str__(self):
        return "%(code)s: %(info)s" % self.errors


class API:

    def __init__(self, site):
        self.site = site

    def request(self, **params):
        if not params.has_key('format'): #Most probably, we want the JSON format
            params['format'] = 'json'
        return http.HTTP(None).POST('/w/api.php',params) #TODO: Use site's HTTP object instead

    def query(self, **params):
        if not params.has_key('action'):
            params['action'] = 'query'
        return self.request(**params)

    def query_response(self, **params):
        """Submit a query and parse the response, returning a dict or None."""
        if params.has_key('format') and params['format'] != 'json':
            raise TypeError("Query format '%s' cannot be parsed." % params['format'])
        while True:
            httpcode, rawdata = self.query(**params)
            if httpcode != 200:
                raise APIError(
                    {'code': httpcode,
                     'info': "HTTP error code received.",
                     'data': rawdata})
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
                continue
            if type(result) is dict:
                if result.has_key("error"):
                    # raise error
                    raise APIError(result['error'])
                if result.has_key("query"):
                    return result
                raise APIError(
                    {'code': "Unknown API error",
                     'info': "Response received with no 'query' key.",
                     'data': result})
            if type(result) is list:
                if result == []:
                    return None
                raise APIError(
                    {'code': "Unknown API error",
                     'info': "Query returned a list instead of a dict.",
                     'data': result})
            raise APIError(
                {'code': "Unknown API error",
                 'info': "Unable to process query response of type %s."
                         % type(result),
                 'data': result})
    
