# -*- coding: utf-8  -*-
"""
Basic HTTP access interface (GET/POST wrappers).
"""
#
# (C) Pywikipedia bot team, 2007
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: $'


import httplib


class HTTP:

    def __init__(self, site):
        self.site = site
        self.useragent = 'PythonWikipediaBot/2.0'
        #TODO: Initiate persistent connection here?


    def GET(self, address):
        #TODO: Resuse said connection.
        conn = httplib.HTTPConnection('en.wikipedia.org',80) #TODO: Obviously, get these from the site object (unimplemented yet)
        conn.putrequest('GET',address)
        conn.putheader('User-agent',self.useragent)
        conn.endheaders()
        conn.send('')

        response = conn.getresponse()
        data = response.read()

        return response.status, data
