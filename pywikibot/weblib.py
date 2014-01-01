# -*- coding: utf-8  -*-
"""
Functions for manipulating external links
or querying third-party sites.

"""
#
# (C) Pywikibot team, 2013
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

import pywikibot
from pywikibot.comms import http


def getInternetArchiveURL(url, timestamp=None):
    """Return archived URL by Internet Archive."""
    # See [[:mw:Archived Pages]] and http://archive.org/help/wayback_api.php
    import json
    query = u'http://archive.org/wayback/available?'
    query += u'url='
    query += url
    if not timestamp is None:
        query += u'&timestamp='
        query += timestamp
    jsontext = http.request(uri=query, site=None)
    if "closest" in jsontext:
        data = json.loads(jsontext)
        return data['archived_snapshots']['closest']['url']
    else:
        return None


def getWebCitationURL(url, timestamp=None):
    """Return archived URL by Web Citation."""
    # See http://www.webcitation.org/doc/WebCiteBestPracticesGuide.pdf
    import xml.etree.ElementTree as ET
    query = u'http://www.webcitation.org/query?'
    query += u'returnxml=true'
    query += u'&url='
    query += url
    if not timestamp is None:
        query += u'&date='
        query += timestamp
    xmltext = http.request(uri=query, site=None)
    if "success" in xmltext:
        data = ET.fromstring(xmltext)
        return data.find('.//webcite_url').text
    else:
        return None
