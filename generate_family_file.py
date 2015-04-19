#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This script generates a family file from a given URL.

Hackish, etc. Regexps, yes. Sorry, jwz.
"""
from __future__ import (absolute_import, division,
                        print_function, unicode_literals)
#
# (C) Merlijn van Deen, 2010-2013
# (C) Pywikibot team, 2010-2015
#
# Distributed under the terms of the MIT license
#
__version__ = '$Id$'
#

# system imports
import sys
import re
import codecs
from collections import defaultdict
from distutils.version import LooseVersion as V
import json

# creating & retrieving urls
if sys.version_info[0] > 2:
    from urllib.parse import urlparse, urljoin
    from urllib.error import HTTPError
    import urllib.request as urllib2
    from html.parser import HTMLParser
    raw_input = input
else:
    from urlparse import urlparse, urljoin
    import urllib2
    from urllib2 import HTTPError
    from HTMLParser import HTMLParser


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


class FamilyFileGenerator(object):

    """Family file creator."""

    def __init__(self, url=None, name=None, dointerwiki=None):
        if url is None:
            url = raw_input("Please insert URL to wiki: ")
        if name is None:
            name = raw_input("Please insert a short name (eg: freeciv): ")
        self.dointerwiki = dointerwiki
        self.base_url = url
        self.name = name

        self.wikis = {}  # {'https://wiki/$1': Wiki('https://wiki/$1'), ...}
        self.langs = []  # [Wiki('https://wiki/$1'), ...]

    def run(self):
        print("Generating family file from %s" % self.base_url)

        w = Wiki(self.base_url)
        self.wikis[w.iwpath] = w
        print()
        print("==================================")
        print("api url: %s" % w.api)
        print("MediaWiki version: %s" % w.version)
        print("==================================")
        print()

        self.getlangs(w)
        self.getapis()
        self.writefile()

    def getlangs(self, w):
        print("Determining other languages...", end="")
        try:
            data = urlopen(
                w.api +
                "?action=query&meta=siteinfo&siprop=interwikimap&sifilteriw=local&format=json")
            iw = json.loads(data.read().decode(data.charset))
            if 'error' in iw:
                raise RuntimeError('%s - %s' % (iw['error']['code'],
                                                iw['error']['info']))
            self.langs = [wiki for wiki in iw['query']['interwikimap']
                          if u'language' in wiki]
            print(u' '.join(sorted([wiki[u'prefix'] for wiki in self.langs])))
        except HTTPError as e:
            self.langs = []
            print(e, "; continuing...")

        if len([lang for lang in self.langs if lang['url'] == w.iwpath]) == 0:
            self.langs.append({u'language': w.lang,
                               u'local': u'',
                               u'prefix': w.lang,
                               u'url': w.iwpath})

        if len(self.langs) > 1:
            if self.dointerwiki is None:
                makeiw = raw_input(
                    "\nThere are %i languages available."
                    "\nDo you want to generate interwiki links?"
                    "This might take a long time. ([y]es/[N]o/[e]dit)"
                    % len(self.langs)).lower()
            else:
                makeiw = self.dointerwiki

            if makeiw == "y":
                pass
            elif makeiw == "e":
                for wiki in self.langs:
                    print(wiki['prefix'], wiki['url'])
                do_langs = raw_input("Which languages do you want: ")
                self.langs = [wiki for wiki in self.langs
                              if wiki['prefix'] in do_langs or
                              wiki['url'] == w.iwpath]
            else:
                self.langs = [wiki for wiki in self.langs
                              if wiki[u'url'] == w.iwpath]

    def getapis(self):
        print("Loading wikis... ")
        for lang in self.langs:
            print("  * %s... " % (lang[u'prefix']), end="")
            if lang[u'url'] not in self.wikis:
                try:
                    self.wikis[lang[u'url']] = Wiki(lang[u'url'])
                    print("downloaded")
                except Exception as e:
                    print(e)
            else:
                print("in cache")

    def writefile(self):
        fn = "pywikibot/families/%s_family.py" % self.name
        print("Writing %s... " % fn)
        try:
            open(fn)
            if raw_input("%s already exists. Overwrite? (y/n)"
                         % fn).lower() == 'n':
                print("Terminating.")
                sys.exit(1)
        except IOError:  # file not found
            pass
        f = codecs.open(fn, 'w', 'utf-8')

        f.write("""
# -*- coding: utf-8 -*-
\"\"\"
This family file was auto-generated by $Id$
Configuration parameters:
  url = %(url)s
  name = %(name)s

Please do not commit this to the Git repository!
\"\"\"

from pywikibot import family
from pywikibot.tools import deprecated


class Family(family.Family):
    def __init__(self):
        family.Family.__init__(self)
        self.name = '%(name)s'
        self.langs = {
""".lstrip() % {'url': self.base_url, 'name': self.name})

        for w in self.wikis.values():
            f.write("            '%(lang)s': '%(hostname)s',\n"
                    % {'lang': w.lang, 'hostname': urlparse(w.server).netloc})

        f.write("        }\n\n")

        f.write("    def scriptpath(self, code):\n")
        f.write("        return {\n")

        for w in self.wikis.values():
            f.write("            '%(lang)s': '%(path)s',\n"
                    % {'lang': w.lang, 'path': w.scriptpath})
        f.write("        }[code]\n")
        f.write("\n")

        f.write("    @deprecated('APISite.version()')\n")
        f.write("    def version(self, code):\n")
        f.write("        return {\n")
        for w in self.wikis.values():
            if w.version is None:
                f.write("            '%(lang)s': None,\n" % {'lang': w.lang})
            else:
                f.write("            '%(lang)s': u'%(ver)s',\n"
                        % {'lang': w.lang, 'ver': w.version})
        f.write("        }[code]\n")


class Wiki(object):

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


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: %s <url> <short name>" % sys.argv[0])
        print("Example: %s https://www.mywiki.bogus/wiki/Main_Page mywiki"
              % sys.argv[0])
        print("This will create the file families/mywiki_family.py")

    FamilyFileGenerator(*sys.argv[1:]).run()
