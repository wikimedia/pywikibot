# -*- coding: utf-8  -*-
"""Dummy objects for use in unit tests."""
#
# (C) Pywikipedia bot team, 2007
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id: $'

# add in any other attributes or methods that are needed for testing

class TestSite(object):
    """Mimic a Site object."""
    def __init__(self, hostname, protocol="http", path="w/"):
        self._hostname = hostname
        self._protocol = protocol
        self._path = path
    def protocol(self):
        return self._protocol
    def hostname(self):
        return self._hostname
    def script_path(self):
        return self._path
    def cookies(self, sysop=False):
        if hasattr(self, "_cookies"):
            return self._cookies
        return u""


class TestPage(object):
    """Mimic a Page object."""
    def __init__(self, site, title):
        self._site = site
        self._title = title

    def site(self):
        return self._site
    def title(self):
        return self._title
    
