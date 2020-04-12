# -*- coding: utf-8 -*-
"""Classes for detecting a MediaWiki site."""
#
# (C) Pywikibot team, 2010-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import json
import re

from requests.exceptions import RequestException

import pywikibot

from pywikibot.comms.http import fetch
from pywikibot.exceptions import ServerError
from pywikibot.tools import MediaWikiVersion, PY2

if not PY2:
    from html.parser import HTMLParser
    from urllib.parse import urljoin, urlparse
else:
    from HTMLParser import HTMLParser
    from urlparse import urljoin, urlparse


SERVER_DB_ERROR_MSG = \
    '<h1>Sorry! This site is experiencing technical difficulties.</h1>'


class MWSite(object):

    """Minimal wiki site class."""

    REwgEnableApi = re.compile(r'wgEnableAPI ?= ?true')
    REwgServer = re.compile(r'wgServer ?= ?"([^"]*)"')
    REwgScriptPath = re.compile(r'wgScriptPath ?= ?"([^"]*)"')
    REwgArticlePath = re.compile(r'wgArticlePath ?= ?"([^"]*)"')
    REwgContentLanguage = re.compile(r'wgContentLanguage ?= ?"([^"]*)"')
    REwgVersion = re.compile(r'wgVersion ?= ?"([^"]*)"')

    def __init__(self, fromurl):
        """
        Initializer.

        @raises pywikibot.exceptions.ServerError: a server error occurred
            while loading the site
        @raises Timeout: a timeout occurred while loading the site
        @raises RuntimeError: Version not found or version less than 1.14
        """
        if fromurl.endswith('$1'):
            fromurl = fromurl[:-2]
        r = fetch(fromurl)
        check_response(r)

        if fromurl != r.data.url:
            pywikibot.log('{0} redirected to {1}'.format(fromurl, r.data.url))
            fromurl = r.data.url

        self.fromurl = fromurl

        data = r.text

        wp = WikiHTMLPageParser(fromurl)
        wp.feed(data)

        self.version = wp.version
        self.server = wp.server
        self.scriptpath = wp.scriptpath
        self.articlepath = None

        try:
            self._parse_pre_117(data)
        except Exception as e:
            pywikibot.log('MW pre-1.17 detection failed: {0!r}'.format(e))

        if self.api:
            try:
                self._parse_post_117()
            except (ServerError, RequestException):
                raise
            except Exception as e:
                pywikibot.log('MW 1.17+ detection failed: {0!r}'.format(e))

            if not self.version:
                self._fetch_old_version()

        if not self.api:
            raise RuntimeError('Unsupported url: {0}'.format(self.fromurl))

        if not self.articlepath:
            if self.private_wiki:
                if self.api != self.fromurl and self.private_wiki:
                    self.articlepath = self.fromurl.rsplit('/', 1)[0] + '/$1'
                else:
                    raise RuntimeError(
                        'Unable to determine articlepath because the wiki is '
                        'private. Use the Main Page URL instead of the API.')
            else:
                raise RuntimeError('Unable to determine articlepath: '
                                   '{0}'.format(self.fromurl))

        if (not self.version
                or self.version < MediaWikiVersion('1.14')):
            raise RuntimeError('Unsupported version: {0}'.format(self.version))

    def __repr__(self):
        return '{0}("{1}")'.format(
            self.__class__.__name__, self.fromurl)

    @property
    def langs(self):
        """Build interwikimap."""
        response = fetch(
            self.api
            + '?action=query&meta=siteinfo&siprop=interwikimap'
              '&sifilteriw=local&format=json')
        iw = json.loads(response.text)
        if 'error' in iw:
            raise RuntimeError('%s - %s' % (iw['error']['code'],
                                            iw['error']['info']))
        return [wiki for wiki in iw['query']['interwikimap']
                if 'language' in wiki]

    def _parse_pre_117(self, data):
        """Parse HTML."""
        if not self.REwgEnableApi.search(data):
            pywikibot.log(
                'wgEnableApi is not enabled in HTML of %s'
                % self.fromurl)
        try:
            self.version = MediaWikiVersion(
                self.REwgVersion.search(data).group(1))
        except AttributeError:
            pass

        self.server = self.REwgServer.search(data).groups()[0]
        self.scriptpath = self.REwgScriptPath.search(data).groups()[0]
        self.articlepath = self.REwgArticlePath.search(data).groups()[0]
        self.lang = self.REwgContentLanguage.search(data).groups()[0]

    def _fetch_old_version(self):
        """Extract the version from API help with ?version enabled."""
        if self.version is None:
            try:
                d = fetch(self.api + '?version&format=json').text
                try:
                    d = json.loads(d)
                except ValueError:
                    # Fallback for old versions which didn't wrap help in json
                    d = {'error': {'*': d}}

                self.version = list(filter(
                    lambda x: x.startswith('MediaWiki'),
                    (l.strip()
                     for l in d['error']['*'].split('\n'))))[0].split()[1]
            except Exception:
                pass
            else:
                self.version = MediaWikiVersion(self.version)

    def _parse_post_117(self):
        """Parse 1.17+ siteinfo data."""
        response = fetch(self.api + '?action=query&meta=siteinfo&format=json')
        check_response(response)
        # remove preleading newlines and Byte Order Mark (BOM), see T128992
        content = response.text.strip().lstrip('\uFEFF')
        info = json.loads(content)
        self.private_wiki = ('error' in info
                             and info['error']['code'] == 'readapidenied')
        if self.private_wiki:
            # user-config.py is not loaded because PYWIKIBOT_NO_USER_CONFIG
            # is set to '2' by generate_family_file.py.
            # Prepare a temporary config for login.
            username = pywikibot.input(
                'Private wiki detected. Login is required.\n'
                'Please enter your username?')
            # Setup a dummy family so that we can create a site object
            fam = pywikibot.family.AutoFamily(
                'temporary_family',
                self.api[:-8])
            site = pywikibot.Site(fam.code, fam, username)
            site.version = lambda: str(self.version)
            # Now the site object is able to login
            info = site.siteinfo
        else:
            info = info['query']['general']
        self.version = MediaWikiVersion.from_generator(info['generator'])
        if self.version < MediaWikiVersion('1.17'):
            return

        self.server = urljoin(self.fromurl, info['server'])
        for item in ['scriptpath', 'articlepath', 'lang']:
            setattr(self, item, info[item])

    def __eq__(self, other):
        """Return True if equal to other."""
        return (self.server + self.scriptpath
                == other.server + other.scriptpath)

    def __hash__(self):
        """Get hashable representation."""
        return hash(self.server + self.scriptpath)

    @property
    def api(self):
        """
        Get api URL.

        @rtype: str or None
        """
        if self.server is None or self.scriptpath is None:
            return

        return self.server + self.scriptpath + '/api.php'

    @property
    def iwpath(self):
        """Get article path URL."""
        return self.server + self.articlepath


class WikiHTMLPageParser(HTMLParser):

    """Wiki HTML page parser."""

    def __init__(self, url):
        """Initializer."""
        if PY2:
            HTMLParser.__init__(self)
        else:
            super().__init__(convert_charrefs=True)
        self.url = urlparse(url)
        self.generator = None
        self.version = None
        self._parsed_url = None
        self.server = None
        self.scriptpath = None

    def set_version(self, value):
        """Set highest version."""
        if self.version and value < self.version:
            return

        self.version = value

    def set_api_url(self, url):
        """Set api_url."""
        url = url.split('.php', 1)[0]
        (value, script_name) = url.rsplit('/', 1)
        if script_name not in ('api', 'load', 'opensearch_desc'):
            return

        if script_name == 'load':
            self.set_version(MediaWikiVersion('1.17.0'))
            if self._parsed_url:
                # A Resource Loader link is less reliable than other links.
                # Resource Loader can load resources from a different site.
                # e.g. http://kino.skripov.com/index.php/$1
                # loads resources from http://megawiki.net/
                return

        new_parsed_url = urlparse(value)
        if self._parsed_url:
            assert new_parsed_url.path == self._parsed_url.path

        if not new_parsed_url.scheme or not new_parsed_url.netloc:
            new_parsed_url = urlparse(
                '{0}://{1}{2}'.format(
                    new_parsed_url.scheme or self.url.scheme,
                    new_parsed_url.netloc or self.url.netloc,
                    new_parsed_url.path))
        else:
            if self._parsed_url:
                # allow upgrades to https, but not downgrades
                if self._parsed_url.scheme == 'https':
                    if new_parsed_url.scheme != self._parsed_url.scheme:
                        return

                # allow http://www.brickwiki.info/ vs http://brickwiki.info/
                if (new_parsed_url.netloc in self._parsed_url.netloc
                        or self._parsed_url.netloc in new_parsed_url.netloc):
                    return

                assert new_parsed_url == self._parsed_url, '{0} != {1}'.format(
                    self._parsed_url, new_parsed_url)

        self._parsed_url = new_parsed_url
        self.server = '{0}://{1}'.format(
            self._parsed_url.scheme, self._parsed_url.netloc)
        self.scriptpath = self._parsed_url.path

    def handle_starttag(self, tag, attrs):
        """Handle an opening tag."""
        attrs = dict(attrs)
        if tag == 'meta':
            if attrs.get('name') == 'generator':
                self.generator = attrs['content']
                try:
                    self.version = MediaWikiVersion.from_generator(
                        self.generator)
                except ValueError:
                    pass
        elif tag == 'link' and 'rel' in attrs and 'href' in attrs:
            if attrs['rel'] in ('EditURI', 'stylesheet', 'search'):
                self.set_api_url(attrs['href'])
        elif tag == 'script' and 'src' in attrs:
            self.set_api_url(attrs['src'])


def check_response(response):
    """Raise ServerError if the response indicates a server error."""
    if response.status == 503:
        raise ServerError('Service Unavailable')
    elif response.status == 502:
        raise ServerError('Bad Gateway')
    elif response.status == 500:
        raise ServerError('Internal Server Error')
    elif response.status == 200 and SERVER_DB_ERROR_MSG in response.text:
        raise ServerError('Server cannot access the database')
