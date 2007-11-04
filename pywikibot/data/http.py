# -*- coding: utf-8  -*-
"""
Basic HTTP access interface (GET/POST/HEAD wrappers).
"""
#
# (C) Pywikipedia bot team, 2007
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: $'


import urllib, httplib


class HTTP:

    def __init__(self, site):
        self.site = site
        self.useragent = 'PythonWikipediaBot/2.0'
        #TODO: Initiate persistent connection here?

    def GET(self, address, query={}):
        return self._request('GET',address + '?' + urllib.urlencode(query))

    def POST(self, address, query={}):
        return self._request('POST',address,urllib.urlencode(query))

    def HEAD(self, address, query={}):
        return self._request('HEAD',address + '?' + urllib.urlencode(query))

    def _request(self, method, address, data=''):
        #TODO: Resuse said connection.
        conn = httplib.HTTPConnection('en.wikipedia.org',80) #TODO: Obviously, get these from the site object (unimplemented yet)
        conn.putrequest(method,address)
        conn.putheader('User-agent',self.useragent)
        conn.putheader('Content-type','application/x-www-form-urlencoded')
        conn.putheader('Content-Length',len(data))
        conn.endheaders()
        conn.send(data)

        response = conn.getresponse()
        rdata = response.read()

        return response.status, rdata
