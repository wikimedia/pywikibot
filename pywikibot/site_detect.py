"""Classes for detecting a MediaWiki site."""
#
# (C) Pywikibot team, 2010-2023
#
# Distributed under the terms of the MIT license.
#
import json
import re
from contextlib import suppress
from html.parser import HTMLParser
from http import HTTPStatus
from typing import Optional
from urllib.parse import urljoin, urlparse

from requests.exceptions import RequestException

import pywikibot
from pywikibot.backports import removesuffix
from pywikibot.comms.http import fetch
from pywikibot.exceptions import ClientError, ServerError
from pywikibot.tools import MediaWikiVersion


try:
    from requests import JSONDecodeError
except ImportError:  # requests < 2.27.0
    from json import JSONDecodeError


SERVER_DB_ERROR_MSG = \
    '<h1>Sorry! This site is experiencing technical difficulties.</h1>'

MIN_VERSION = MediaWikiVersion('1.27')


class MWSite:

    """Minimal wiki site class."""

    def __init__(self, fromurl, **kwargs) -> None:
        """
        Initializer.

        :raises pywikibot.exceptions.ServerError: a server error occurred
            while loading the site
        :raises Timeout: a timeout occurred while loading the site
        :raises RuntimeError: Version not found or version less than 1.27
        """
        fromurl = removesuffix(fromurl, '$1')

        r = fetch(fromurl, **kwargs)
        check_response(r)

        if fromurl != r.url:
            pywikibot.log(f'{fromurl} redirected to {r.url}')
            fromurl = r.url

        self.fromurl = fromurl

        data = r.text

        wp = WikiHTMLPageParser(fromurl)
        wp.feed(data)

        self.version = wp.version
        self.server = wp.server
        self.scriptpath = wp.scriptpath
        self.articlepath = None

        if self.api:
            try:
                self._parse_site()
            except (ServerError, RequestException):
                raise
            except Exception as e:
                pywikibot.log(f'MW detection failed: {e!r}')

            if not self.version:
                self._fetch_old_version()

        if not self.api:
            raise RuntimeError(f'Unsupported url: {self.fromurl}')

        if not self.version or self.version < MIN_VERSION:
            raise RuntimeError(f'Unsupported version: {self.version}')

        if not self.articlepath:
            if self.private_wiki:
                if self.api != self.fromurl and self.private_wiki:
                    self.articlepath = self.fromurl.rsplit('/', 1)[0] + '/$1'
                else:
                    raise RuntimeError(
                        'Unable to determine articlepath because the wiki is '
                        'private. Use the Main Page URL instead of the API.')
            else:
                raise RuntimeError(
                    f'Unable to determine articlepath: {self.fromurl}')

    def __repr__(self) -> str:
        return f'{type(self).__name__}("{self.fromurl}")'

    @property
    def langs(self):
        """Build interwikimap."""
        response = fetch(
            self.api
            + '?action=query&meta=siteinfo&siprop=interwikimap'
              '&sifilteriw=local&format=json')
        iw = response.json()

        error = iw.get('error')
        if error:
            raise RuntimeError(f"{error['code']} - {error['info']}")

        return [wiki for wiki in iw['query']['interwikimap']
                if 'language' in wiki]

    def _fetch_old_version(self) -> None:
        """Extract the version from API help with ?version enabled."""
        if self.version is None:
            try:
                r = fetch(self.api + '?version&format=json')
                try:
                    d = r.json()
                except JSONDecodeError:
                    # Fallback for old versions which didn't wrap help in json
                    d = {'error': {'*': r.text}}

                self.version = list(filter(
                    lambda x: x.startswith('MediaWiki'),
                    (line.strip()
                     for line in d['error']['*'].split('\n'))))[0].split()[1]
            except Exception:
                pass
            else:
                self.version = MediaWikiVersion(self.version)

    def _parse_site(self) -> None:
        """Parse siteinfo data."""
        response = fetch(self.api + '?action=query&meta=siteinfo&format=json')
        check_response(response)
        # remove preleading newlines and Byte Order Mark (BOM), see T128992
        content = response.text.strip().lstrip('\uFEFF')
        info = json.loads(content)
        self.private_wiki = ('error' in info
                             and info['error']['code'] == 'readapidenied')
        if self.private_wiki:
            # user config is not loaded because PYWIKIBOT_NO_USER_CONFIG
            # is set to '2' by generate_family_file.py.
            # Prepare a temporary config for login.
            username = pywikibot.input(
                'Private wiki detected. Login is required.\n'
                'Please enter your username?')
            # Setup a dummy family so that we can create a site object
            fam = pywikibot.family.AutoFamily('temporary_family',
                                              self.server + self.scriptpath)
            site = pywikibot.Site(fam.code, fam, username)
            site.version = lambda: str(self.version)
            # Now the site object is able to login
            info = site.siteinfo
        else:
            info = info['query']['general']

        self.version = MediaWikiVersion.from_generator(info['generator'])
        if self.version < MIN_VERSION:
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
    def api(self) -> Optional[str]:
        """Get api URL."""
        if self.server is None or self.scriptpath is None:
            return None

        return self.server + self.scriptpath + '/api.php'

    @property
    def iwpath(self):
        """Get article path URL."""
        return self.server + self.articlepath


class WikiHTMLPageParser(HTMLParser):

    """Wiki HTML page parser."""

    def __init__(self, url) -> None:
        """Initializer."""
        super().__init__(convert_charrefs=True)
        self.url = urlparse(url)
        self.generator = None
        self.version = None
        self._parsed_url = None
        self.server = None
        self.scriptpath = None

    def set_version(self, value) -> None:
        """Set highest version."""
        if self.version and value < self.version:
            return

        self.version = value

    def set_api_url(self, url) -> None:
        """Set api_url."""
        url = url.split('.php', 1)[0]
        try:
            value, script_name = url.rsplit('/', 1)
        except ValueError:
            return

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
                '{}://{}{}'.format(
                    new_parsed_url.scheme or self.url.scheme,
                    new_parsed_url.netloc or self.url.netloc,
                    new_parsed_url.path))
        else:
            if self._parsed_url:
                # allow upgrades to https, but not downgrades
                if self._parsed_url.scheme == 'https' \
                   and new_parsed_url.scheme != self._parsed_url.scheme:
                    return

                # allow http://www.brickwiki.info/ vs http://brickwiki.info/
                if (new_parsed_url.netloc in self._parsed_url.netloc
                        or self._parsed_url.netloc in new_parsed_url.netloc):
                    return

                assert new_parsed_url == self._parsed_url, '{} != {}'.format(
                    self._parsed_url, new_parsed_url)

        self._parsed_url = new_parsed_url
        self.server = '{url.scheme}://{url.netloc}'.format(
            url=self._parsed_url)
        self.scriptpath = self._parsed_url.path

    def handle_starttag(self, tag, attrs) -> None:
        """Handle an opening tag."""
        attrs = dict(attrs)
        if tag == 'meta':
            if attrs.get('name') == 'generator':
                self.generator = attrs['content']
                with suppress(ValueError):
                    self.version = MediaWikiVersion.from_generator(
                        self.generator)
        elif tag == 'link' and 'rel' in attrs and 'href' in attrs:
            if attrs['rel'] in ('EditURI', 'stylesheet', 'search'):
                self.set_api_url(attrs['href'])
        elif tag == 'script' and 'src' in attrs:
            self.set_api_url(attrs['src'])


def check_response(response):
    """Raise ClientError or ServerError depending on http status.

    .. versionadded:: 3.0
    .. versionchanged:: 7.0
       Raise a generic :class:`exceptions.ServerError` if http status
       code is not IANA-registered but unofficial code
    .. versionchanged:: 8.1
       Raise a :class:`exceptions.ClientError` if status code is 4XX
    """
    for status_code, err_class, err_type in [
        (HTTPStatus.INTERNAL_SERVER_ERROR, ServerError, 'Server'),
        (HTTPStatus.BAD_REQUEST, ClientError, 'Client')
    ]:  # highest http status code first
        if response.status_code >= status_code:
            try:
                status = HTTPStatus(response.status_code)
            except ValueError as err:
                m = re.search(r'\d{3}', err.args[0], flags=re.ASCII)
                if not m:
                    raise err
                msg = f'Generic {err_type} Error ({m.group()})'
            else:
                msg = f'({status}) {status.description}'

            raise err_class(msg)

    if response.status_code == HTTPStatus.OK \
       and SERVER_DB_ERROR_MSG in response.text:
        raise ServerError('Server cannot access the database')
