# -*- coding: utf-8  -*-
"""Classes for detecting a MediaWiki site."""
#
# (C) Pywikibot team, 2010-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import json
import re
import sys

from collections import defaultdict
from distutils.version import LooseVersion as V

from pywikibot.tools import PY2

if not PY2:
    from html.parser import HTMLParser
    from urllib.parse import urljoin
    from urllib.error import HTTPError
    import urllib.request as urllib2
else:
    from HTMLParser import HTMLParser
    from urlparse import urljoin
    from urllib2 import HTTPError
    import urllib2


def urlopen(url):
    req = urllib2.Request(
        url,
        headers={'User-agent': 'Pywikibot Family File Generator 2.0'
                               ' - https://www.mediawiki.org/wiki/Pywikibot'})
    uo = urllib2.urlopen(req)
    try:
        if sys.version_info[0] > 2:
            uo.charset = uo.headers.get_content_charset()
        else:
            uo.charset = uo.headers.getfirstmatchingheader('Content-Type')[0].strip().split('charset=')[1]
    except IndexError:
        uo.charset = 'latin-1'
    return uo


class MWSite(object):

    """Minimal wiki site class."""

    REwgEnableApi = re.compile(r'wgEnableAPI ?= ?true')
    REwgServer = re.compile(r'wgServer ?= ?"([^"]*)"')
    REwgScriptPath = re.compile(r'wgScriptPath ?= ?"([^"]*)"')
    REwgArticlePath = re.compile(r'wgArticlePath ?= ?"([^"]*)"')
    REwgContentLanguage = re.compile(r'wgContentLanguage ?= ?"([^"]*)"')
    REwgVersion = re.compile(r'wgVersion ?= ?"([^"]*)"')

    def __init__(self, fromurl):
        self.fromurl = fromurl
        if fromurl.endswith("$1"):
            fromurl = fromurl[:-2]
        try:
            uo = urlopen(fromurl)
            data = uo.read().decode(uo.charset)
        except HTTPError as e:
            if e.code != 404:
                raise
            data = e.read().decode('latin-1')  # don't care about mojibake for errors
            pass

        wp = WikiHTMLPageParser()
        wp.feed(data)
        try:
            self.version = wp.generator.replace("MediaWiki ", "")
        except Exception:
            self.version = "0.0"

        if V(self.version) < V("1.17.0"):
            self._parse_pre_117(data)
        else:
            self._parse_post_117(wp, fromurl)

    @property
    def langs(self):
        data = urlopen(
            self.api +
            "?action=query&meta=siteinfo&siprop=interwikimap&sifilteriw=local&format=json")
        iw = json.loads(data.read().decode(data.charset))
        if 'error' in iw:
            raise RuntimeError('%s - %s' % (iw['error']['code'],
                                            iw['error']['info']))
        self.langs = [wiki for wiki in iw['query']['interwikimap']
                      if u'language' in wiki]
        return self.langs

    def _parse_pre_117(self, data):
        if not self.REwgEnableApi.search(data):
            print("*** WARNING: Api does not seem to be enabled on %s"
                  % self.fromurl)
        try:
            self.version = self.REwgVersion.search(data).groups()[0]
        except AttributeError:
            self.version = None

        self.server = self.REwgServer.search(data).groups()[0]
        self.scriptpath = self.REwgScriptPath.search(data).groups()[0]
        self.articlepath = self.REwgArticlePath.search(data).groups()[0]
        self.lang = self.REwgContentLanguage.search(data).groups()[0]

        if self.version is None:
            # try to get version using api
            try:
                d = json.load(urlopen(self.api + "?version&format=json"))
                self.version = filter(
                    lambda x: x.startswith("MediaWiki"),
                    [l.strip()
                     for l in d['error']['*'].split("\n")])[0].split()[1]
            except Exception:
                pass

    def _parse_post_117(self, wp, fromurl):
        apipath = wp.edituri.split("?")[0]
        fullurl = urljoin(fromurl, apipath)
        data = urlopen(fullurl + "?action=query&meta=siteinfo&format=json")
        info = json.loads(data.read().decode(data.charset))['query']['general']
        self.server = urljoin(fromurl, info['server'])
        for item in ['scriptpath', 'articlepath', 'lang']:
            setattr(self, item, info[item])

    def __cmp__(self, other):
        return (self.server + self.scriptpath ==
                other.server + other.scriptpath)

    def __hash__(self):
        return hash(self.server + self.scriptpath)

    @property
    def api(self):
        return self.server + self.scriptpath + "/api.php"

    @property
    def iwpath(self):
        return self.server + self.articlepath


class WikiHTMLPageParser(HTMLParser):

    """Wiki HTML page parser."""

    def __init__(self, *args, **kwargs):
        HTMLParser.__init__(self, *args, **kwargs)
        self.generator = None

    def handle_starttag(self, tag, attrs):
        attrs = defaultdict(lambda: None, attrs)
        if tag == "meta":
            if attrs["name"] == "generator":
                self.generator = attrs["content"]
        if tag == "link":
            if attrs["rel"] == "EditURI":
                self.edituri = attrs["href"]
