#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
This bot is used for checking external links found at the wiki.

It checks several pages at once, with a limit set by the config variable
max_external_links, which defaults to 50.

The bot won't change any wiki pages, it will only report dead links such that
people can fix or remove the links themselves.

The bot will store all links found dead in a .dat file in the deadlinks
subdirectory. To avoid the removing of links which are only temporarily
unavailable, the bot ONLY reports links which were reported dead at least
two times, with a time lag of at least one week. Such links will be logged to a
.txt file in the deadlinks subdirectory.

The .txt file uses wiki markup and so it may be useful to post it on the
wiki and then exclude that page from subsequent runs. For example if the
page is named Broken Links, exclude it with '-titleregexnot:^Broken Links$'

After running the bot and waiting for at least one week, you can re-check those
pages where dead links were found, using the -repeat parameter.

In addition to the logging step, it is possible to automatically report dead
links to the talk page of the article where the link was found. To use this
feature, set report_dead_links_on_talk = True in your user-config.py, or
specify "-talk" on the command line. Adding "-notalk" switches this off
irrespective of the configuration variable.

When a link is found alive, it will be removed from the .dat file.

These command line parameters can be used to specify which pages to work on:

&params;

-repeat      Work on all pages were dead links were found before. This is
             useful to confirm that the links are dead after some time (at
             least one week), which is required before the script will report
             the problem.

-namespace   Only process templates in the namespace with the given number or
             name. This parameter may be used multiple times.

-xml         Should be used instead of a simple page fetching method from
             pagegenerators.py for performance and load issues

-xmlstart    Page to start with when using an XML dump

-ignore      HTTP return codes to ignore. Can be provided several times :
                -ignore:401 -ignore:500

Furthermore, the following command line parameters are supported:

-talk        Overrides the report_dead_links_on_talk config variable, enabling
             the feature.

-notalk      Overrides the report_dead_links_on_talk config variable, disabling
             the feature.

-day         Do not report broken link if the link is there only since
             x days or less. If not set, the default is 7 days.

The following config variables are supported:

max_external_links        - The maximum number of web pages that should be
                            loaded simultaneously. You should change this
                            according to your Internet connection speed.
                            Be careful: if it is set too high, the script
                            might get socket errors because your network
                            is congested, and will then think that the page
                            is offline.

report_dead_links_on_talk - If set to true, causes the script to report dead
                            links on the article's talk page if (and ONLY if)
                            the linked page has been unavailable at least two
                            times during a timespan of at least one week.

weblink_dead_days         - sets the timespan (default: one week) after which
                            a dead link will be reported

Syntax examples:
    python pwb.py weblinkchecker -start:!
        Loads all wiki pages in alphabetical order using the Special:Allpages
        feature.

    python pwb.py weblinkchecker -start:Example_page
        Loads all wiki pages using the Special:Allpages feature, starting at
        "Example page"

    python pwb.py weblinkchecker -weblink:www.example.org
        Loads all wiki pages that link to www.example.org

    python pwb.py weblinkchecker Example page
        Only checks links found in the wiki page "Example page"

    python pwb.py weblinkchecker -repeat
        Loads all wiki pages where dead links were found during a prior run
"""
#
# (C) Daniel Herding, 2005
# (C) Pywikibot team, 2005-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import codecs
import datetime
import pickle
import re
import socket
import sys
import threading
import time

from functools import partial
from time import sleep
from warnings import warn

try:
    import memento_client
except ImportError as e:
    memento_client = e

import pywikibot

from pywikibot import (
    comms, i18n, config, pagegenerators, textlib, weblib, config2,
)

from pywikibot.bot import ExistingPageBot, SingleSiteBot
from pywikibot.pagegenerators import (
    XMLDumpPageGenerator as _XMLDumpPageGenerator,
)
from pywikibot.tools import deprecated
from pywikibot.tools.formatter import color_format

import requests

if sys.version_info[0] > 2:
    import http.client as httplib
    import urllib.parse as urlparse
    import urllib.request as urllib

    basestring = (str, )
    unicode = str
else:
    import httplib
    import urllib
    import urlparse

docuReplacements = {
    '&params;': pagegenerators.parameterHelp
}

ignorelist = [
    # Officially reserved for testing, documentation, etc. in
    # https://tools.ietf.org/html/rfc2606#page-2
    # top-level domains:
    re.compile(r'.*[\./@]test(/.*)?'),
    re.compile(r'.*[\./@]example(/.*)?'),
    re.compile(r'.*[\./@]invalid(/.*)?'),
    re.compile(r'.*[\./@]localhost(/.*)?'),
    # second-level domains:
    re.compile(r'.*[\./@]example\.com(/.*)?'),
    re.compile(r'.*[\./@]example\.net(/.*)?'),
    re.compile(r'.*[\./@]example\.org(/.*)?'),

    # Other special cases
    re.compile(r'.*[\./@]berlinonline\.de(/.*)?'),
    # above entry to be manually fixed per request at
    # [[de:Benutzer:BLueFiSH.as/BZ]]
    # bot can't handle their redirects:

    # bot rejected on the site, already archived
    re.compile(r'.*[\./@]web\.archive\.org(/.*)?'),

    # Ignore links containing * in domain name
    # as they are intentionally fake
    re.compile(r'https?\:\/\/\*(/.*)?'),
]


def _get_closest_memento_url(url, when=None, timegate_uri=None):
    """Get most recent memento for url."""
    if isinstance(memento_client, ImportError):
        raise memento_client

    if not when:
        when = datetime.datetime.now()

    mc = memento_client.MementoClient()
    if timegate_uri:
        mc.timegate_uri = timegate_uri

    retry_count = 0
    while retry_count <= config2.max_retries:
        try:
            memento_info = mc.get_memento_info(url, when)
            break
        except requests.ConnectionError as e:
            error = e
            retry_count += 1
            sleep(config2.retry_wait)
    else:
        raise error

    mementos = memento_info.get('mementos')
    if not mementos:
        raise Exception(
            'mementos not found for {0} via {1}'.format(url, timegate_uri))
    if 'closest' not in mementos:
        raise Exception(
            'closest memento not found for {0} via {1}'.format(
                url, timegate_uri))
    if 'uri' not in mementos['closest']:
        raise Exception(
            'closest memento uri not found for {0} via {1}'.format(
                url, timegate_uri))
    return mementos['closest']['uri'][0]


def get_archive_url(url):
    """Get archive URL."""
    try:
        archive = _get_closest_memento_url(
            url,
            timegate_uri='http://web.archive.org/web/')
    except Exception:
        archive = _get_closest_memento_url(
            url,
            timegate_uri='http://timetravel.mementoweb.org/webcite/timegate/')

    # FIXME: Hack for T167463: Use https instead of http for archive.org links
    if archive.startswith('http://web.archive.org'):
        archive = archive.replace('http://', 'https://', 1)
    return archive


def weblinksIn(text, withoutBracketed=False, onlyBracketed=False):
    """
    Yield web links from text.

    TODO: move to textlib
    """
    text = textlib.removeDisabledParts(text)

    # Ignore links in fullurl template
    text = re.sub(r'{{\s?fullurl:.[^}]*}}', '', text)

    # MediaWiki parses templates before parsing external links. Thus, there
    # might be a | or a } directly after a URL which does not belong to
    # the URL itself.

    # First, remove the curly braces of inner templates:
    nestedTemplateR = re.compile(r'{{([^}]*?){{(.*?)}}(.*?)}}')
    while nestedTemplateR.search(text):
        text = nestedTemplateR.sub(r'{{\1 \2 \3}}', text)

    # Then blow up the templates with spaces so that the | and }} will not
    # be regarded as part of the link:.
    templateWithParamsR = re.compile(r'{{([^}]*?[^ ])\|([^ ][^}]*?)}}',
                                     re.DOTALL)
    while templateWithParamsR.search(text):
        text = templateWithParamsR.sub(r'{{ \1 | \2 }}', text)

    # Add <blank> at the end of a template
    # URL as last param of multiline template would not be correct
    text = text.replace('}}', ' }}')

    # Remove HTML comments in URLs as well as URLs in HTML comments.
    # Also remove text inside nowiki links etc.
    text = textlib.removeDisabledParts(text)
    linkR = textlib.compileLinkR(withoutBracketed, onlyBracketed)
    for m in linkR.finditer(text):
        if m.group('url'):
            yield m.group('url')
        else:
            yield m.group('urlb')


XmlDumpPageGenerator = partial(
    _XMLDumpPageGenerator, text_predicate=weblinksIn)


class NotAnURLError(BaseException):

    """The link is not an URL."""


@deprecated('requests')
class LinkChecker(object):

    """
    Check links.

    Given a HTTP URL, tries to load the page from the Internet and checks if it
    is still online.

    Returns a (boolean, string) tuple saying if the page is online and
    including a status reason.

    Per-domain user-agent faking is not supported in this deprecated class.

    Warning: Also returns false if your Internet connection isn't working
    correctly! (This will give a Socket Error)

    """

    def __init__(self, url, redirectChain=[], serverEncoding=None,
                 HTTPignore=[]):
        """
        Constructor.

        redirectChain is a list of redirects which were resolved by
        resolveRedirect(). This is needed to detect redirect loops.
        """
        self.url = url
        self.serverEncoding = serverEncoding

        fake_ua_config = config.fake_user_agent_default.get(
            'weblinkchecker', False)
        if fake_ua_config and isinstance(fake_ua_config, str):
            user_agent = fake_ua_config
        elif fake_ua_config:
            user_agent = comms.http.fake_user_agent()
        else:
            user_agent = comms.http.user_agent()
        self.header = {
            'user-agent': user_agent,
            'Accept': 'text/xml,application/xml,application/xhtml+xml,'
                      'text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
            'Accept-Language': 'de-de,de;q=0.8,en-us;q=0.5,en;q=0.3',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Keep-Alive': '30',
            'Connection': 'keep-alive',
        }
        self.redirectChain = redirectChain + [url]
        self.changeUrl(url)
        self.HTTPignore = HTTPignore

    def getConnection(self):
        """Get a connection."""
        if self.scheme == 'http':
            return httplib.HTTPConnection(self.host)
        elif self.scheme == 'https':
            return httplib.HTTPSConnection(self.host)
        else:
            raise NotAnURLError(self.url)

    def getEncodingUsedByServer(self):
        """Get encodung used by server."""
        if not self.serverEncoding:
            try:
                pywikibot.output(
                    u'Contacting server %s to find out its default encoding...'
                    % self.host)
                conn = self.getConnection()
                conn.request('HEAD', '/', None, self.header)
                self.response = conn.getresponse()
                self.readEncodingFromResponse(self.response)
            except:
                pass
            if not self.serverEncoding:
                # TODO: We might also load a page, then check for an encoding
                # definition in a HTML meta tag.
                pywikibot.output('Error retrieving server\'s default charset. '
                                 'Using ISO 8859-1.')
                # most browsers use ISO 8859-1 (Latin-1) as the default.
                self.serverEncoding = 'iso8859-1'
        return self.serverEncoding

    def readEncodingFromResponse(self, response):
        """Read encoding from response."""
        if not self.serverEncoding:
            try:
                ct = response.getheader('Content-Type')
                charsetR = re.compile('charset=(.+)')
                charset = charsetR.search(ct).group(1)
                self.serverEncoding = charset
            except:
                pass

    def changeUrl(self, url):
        """Change url."""
        self.url = url
        # we ignore the fragment
        (self.scheme, self.host, self.path, self.query,
         self.fragment) = urlparse.urlsplit(self.url)
        if not self.path:
            self.path = '/'
        if self.query:
            self.query = '?' + self.query
        self.protocol = url.split(':', 1)[0]
        # check if there are non-ASCII characters inside path or query, and if
        # so, encode them in an encoding that hopefully is the right one.
        try:
            self.path.encode('ascii')
            self.query.encode('ascii')
        except UnicodeEncodeError:
            encoding = self.getEncodingUsedByServer()
            self.path = unicode(urllib.quote(self.path.encode(encoding)))
            self.query = unicode(urllib.quote(self.query.encode(encoding),
                                              '=&'))

    def resolveRedirect(self, useHEAD=False):
        """
        Return the redirect target URL as a string, if it is a HTTP redirect.

        If useHEAD is true, uses the HTTP HEAD method, which saves bandwidth
        by not downloading the body. Otherwise, the HTTP GET method is used.

        @rtype: unicode or None
        """
        conn = self.getConnection()
        try:
            if useHEAD:
                conn.request('HEAD', '%s%s' % (self.path, self.query), None,
                             self.header)
            else:
                conn.request('GET', '%s%s' % (self.path, self.query), None,
                             self.header)
            self.response = conn.getresponse()
            # read the server's encoding, in case we need it later
            self.readEncodingFromResponse(self.response)
        except httplib.BadStatusLine:
            # Some servers don't seem to handle HEAD requests properly,
            # e.g. http://www.radiorus.ru/ which is running on a very old
            # Apache server. Using GET instead works on these (but it uses
            # more bandwidth).
            if useHEAD:
                return self.resolveRedirect(useHEAD=False)
            else:
                raise
        if self.response.status >= 300 and self.response.status <= 399:
            # to debug, print response.getheaders()
            redirTarget = self.response.getheader('Location')
            if redirTarget:
                try:
                    redirTarget.encode('ascii')
                except UnicodeError:
                    redirTarget = redirTarget.decode(
                        self.getEncodingUsedByServer())
                if redirTarget.startswith('http://') or \
                   redirTarget.startswith('https://'):
                    self.changeUrl(redirTarget)
                    return True
                elif redirTarget.startswith('/'):
                    self.changeUrl(u'%s://%s%s'
                                   % (self.protocol, self.host, redirTarget))
                    return True
                else:  # redirect to relative position
                    # cut off filename
                    directory = self.path[:self.path.rindex('/') + 1]
                    # handle redirect to parent directory
                    while redirTarget.startswith('../'):
                        redirTarget = redirTarget[3:]
                        # some servers redirect to .. although we are already
                        # in the root directory; ignore this.
                        if directory != '/':
                            # change /foo/bar/ to /foo/
                            directory = directory[:-1]
                            directory = directory[:directory.rindex('/') + 1]
                    self.changeUrl('%s://%s%s%s'
                                   % (self.protocol, self.host, directory,
                                      redirTarget))
                    return True
        else:
            return False  # not a redirect

    def check(self, useHEAD=False):
        """
        Return True and the server status message if the page is alive.

        @rtype: tuple of (bool, unicode)
        """
        try:
            wasRedirected = self.resolveRedirect(useHEAD=useHEAD)
        except UnicodeError as error:
            return False, u'Encoding Error: %s (%s)' % (
                error.__class__.__name__, error)
        except httplib.error as error:
            return False, u'HTTP Error: %s' % error.__class__.__name__
        except socket.error as error:
            # https://docs.python.org/2/library/socket.html :
            # socket.error :
            # The accompanying value is either a string telling what went
            # wrong or a pair (errno, string) representing an error
            # returned by a system call, similar to the value
            # accompanying os.error
            if isinstance(error, basestring):
                msg = error
            else:
                try:
                    msg = error[1]
                except IndexError:
                    pywikibot.output('### DEBUG information for T57282')
                    raise IndexError(type(error))
            # TODO: decode msg. On Linux, it's encoded in UTF-8.
            # How is it encoded in Windows? Or can we somehow just
            # get the English message?
            return False, u'Socket Error: %s' % repr(msg)
        if wasRedirected:
            if self.url in self.redirectChain:
                if useHEAD:
                    # Some servers don't seem to handle HEAD requests properly,
                    # which leads to a cyclic list of redirects.
                    # We simply start from the beginning, but this time,
                    # we don't use HEAD, but GET requests.
                    redirChecker = LinkChecker(
                        self.redirectChain[0],
                        serverEncoding=self.serverEncoding,
                        HTTPignore=self.HTTPignore)
                    return redirChecker.check(useHEAD=False)
                else:
                    urlList = ['[%s]' % url
                               for url in self.redirectChain + [self.url]]
                    return (False,
                            u'HTTP Redirect Loop: %s' % ' -> '.join(urlList))
            elif len(self.redirectChain) >= 19:
                if useHEAD:
                    # Some servers don't seem to handle HEAD requests properly,
                    # which leads to a long (or infinite) list of redirects.
                    # We simply start from the beginning, but this time,
                    # we don't use HEAD, but GET requests.
                    redirChecker = LinkChecker(
                        self.redirectChain[0],
                        serverEncoding=self.serverEncoding,
                        HTTPignore=self.HTTPignore)
                    return redirChecker.check(useHEAD=False)
                else:
                    urlList = ['[%s]' % url
                               for url in self.redirectChain + [self.url]]
                    return (False,
                            u'Long Chain of Redirects: %s'
                            % ' -> '.join(urlList))
            else:
                redirChecker = LinkChecker(self.url, self.redirectChain,
                                           self.serverEncoding,
                                           HTTPignore=self.HTTPignore)
                return redirChecker.check(useHEAD=useHEAD)
        else:
            try:
                conn = self.getConnection()
            except httplib.error as error:
                return False, u'HTTP Error: %s' % error.__class__.__name__
            try:
                conn.request('GET', '%s%s'
                             % (self.path, self.query), None, self.header)
            except socket.error as error:
                return False, u'Socket Error: %s' % repr(error[1])
            try:
                self.response = conn.getresponse()
            except Exception as error:
                return False, u'Error: %s' % error
            # read the server's encoding, in case we need it later
            self.readEncodingFromResponse(self.response)
            # site down if the server status is between 400 and 499
            alive = self.response.status not in range(400, 500)
            if self.response.status in self.HTTPignore:
                alive = False
            return alive, '%s %s' % (self.response.status,
                                     self.response.reason)


class LinkCheckThread(threading.Thread):

    """A thread responsible for checking one URL.

    After checking the page, it will die.
    """

    def __init__(self, page, url, history, HTTPignore, day):
        """Constructor."""
        threading.Thread.__init__(self)
        self.page = page
        self.url = url
        self.history = history
        self.header = {
            'Accept': 'text/xml,application/xml,application/xhtml+xml,'
                      'text/html;q=0.9,text/plain;q=0.8,image/png,*/*;q=0.5',
            'Accept-Language': 'de-de,de;q=0.8,en-us;q=0.5,en;q=0.3',
            'Accept-Charset': 'ISO-8859-1,utf-8;q=0.7,*;q=0.7',
            'Keep-Alive': '30',
            'Connection': 'keep-alive',
        }
        # identification for debugging purposes
        self.setName((u'%s - %s' % (page.title(), url)).encode('utf-8',
                                                               'replace'))
        self.HTTPignore = HTTPignore
        self._use_fake_user_agent = config.fake_user_agent_default.get(
            'weblinkchecker', False)
        self.day = day

    def run(self):
        """Run the bot."""
        ok = False
        try:
            header = self.header
            r = comms.http.fetch(
                self.url, headers=header,
                use_fake_user_agent=self._use_fake_user_agent)
        except requests.exceptions.InvalidURL:
            message = i18n.twtranslate(self.page.site,
                                       'weblinkchecker-badurl_msg',
                                       {'URL': self.url})
        except:
            pywikibot.output('Exception while processing URL %s in page %s'
                             % (self.url, self.page.title()))
            raise
        if (r.status == requests.codes.ok and
                str(r.status) not in self.HTTPignore):
            ok = True
        else:
            message = '{0}'.format(r.status)
        if ok:
            if self.history.setLinkAlive(self.url):
                pywikibot.output('*Link to %s in [[%s]] is back alive.'
                                 % (self.url, self.page.title()))
        else:
            pywikibot.output('*[[%s]] links to %s - %s.'
                             % (self.page.title(), self.url, message))
            self.history.setLinkDead(self.url, message, self.page,
                                     config.weblink_dead_days)


class History(object):

    """
    Store previously found dead links.

    The URLs are dictionary keys, and
    values are lists of tuples where each tuple represents one time the URL was
    found dead. Tuples have the form (title, date, error) where title is the
    wiki page where the URL was found, date is an instance of time, and error
    is a string with error code and message.

    We assume that the first element in the list represents the first time we
    found this dead link, and the last element represents the last time.

    Example:

    dict = {
        'https://www.example.org/page': [
            ('WikiPageTitle', DATE, '404: File not found'),
            ('WikiPageName2', DATE, '404: File not found'),
        ]

    """

    def __init__(self, reportThread, site=None):
        """Constructor."""
        self.reportThread = reportThread
        if not site:
            self.site = pywikibot.Site()
        else:
            self.site = site
        self.semaphore = threading.Semaphore()
        self.datfilename = pywikibot.config.datafilepath(
            'deadlinks', 'deadlinks-%s-%s.dat' % (self.site.family.name,
                                                  self.site.code))
        # Count the number of logged links, so that we can insert captions
        # from time to time
        self.logCount = 0
        try:
            with open(self.datfilename, 'rb') as datfile:
                self.historyDict = pickle.load(datfile)
        except (IOError, EOFError):
            # no saved history exists yet, or history dump broken
            self.historyDict = {}

    def log(self, url, error, containingPage, archiveURL):
        """Log an error report to a text file in the deadlinks subdirectory."""
        if archiveURL:
            errorReport = u'* %s ([%s archive])\n' % (url, archiveURL)
        else:
            errorReport = u'* %s\n' % url
        for (pageTitle, date, error) in self.historyDict[url]:
            # ISO 8601 formulation
            isoDate = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(date))
            errorReport += "** In [[%s]] on %s, %s\n" % (pageTitle, isoDate,
                                                         error)
        pywikibot.output(u"** Logging link for deletion.")
        txtfilename = pywikibot.config.datafilepath('deadlinks',
                                                    'results-%s-%s.txt'
                                                    % (self.site.family.name,
                                                       self.site.lang))
        txtfile = codecs.open(txtfilename, 'a', 'utf-8')
        self.logCount += 1
        if self.logCount % 30 == 0:
            # insert a caption
            txtfile.write('=== %s ===\n' % containingPage.title()[:3])
        txtfile.write(errorReport)
        txtfile.close()

        if self.reportThread and not containingPage.isTalkPage():
            self.reportThread.report(url, errorReport, containingPage,
                                     archiveURL)

    def setLinkDead(self, url, error, page, weblink_dead_days):
        """Add the fact that the link was found dead to the .dat file."""
        self.semaphore.acquire()
        now = time.time()
        if url in self.historyDict:
            timeSinceFirstFound = now - self.historyDict[url][0][1]
            timeSinceLastFound = now - self.historyDict[url][-1][1]
            # if the last time we found this dead link is less than an hour
            # ago, we won't save it in the history this time.
            if timeSinceLastFound > 60 * 60:
                self.historyDict[url].append((page.title(), now, error))
            # if the first time we found this link longer than x day ago
            # (default is a week), it should probably be fixed or removed.
            # We'll list it in a file so that it can be removed manually.
            if timeSinceFirstFound > 60 * 60 * 24 * weblink_dead_days:
                # search for archived page
                try:
                    archiveURL = get_archive_url(url)
                except Exception as e:
                    pywikibot.warning(
                        'get_closest_memento_url({0}) failed: {1}'.format(
                            url, e))
                    archiveURL = None
                if archiveURL is None:
                    archiveURL = weblib.getInternetArchiveURL(url)
                if archiveURL is None:
                    archiveURL = weblib.getWebCitationURL(url)
                self.log(url, error, page, archiveURL)
        else:
            self.historyDict[url] = [(page.title(), now, error)]
        self.semaphore.release()

    def setLinkAlive(self, url):
        """
        Record that the link is now alive.

        If link was previously found dead, remove it from the .dat file.

        @return: True if previously found dead, else returns False.
        """
        if url in self.historyDict:
            self.semaphore.acquire()
            try:
                del self.historyDict[url]
            except KeyError:
                # Not sure why this can happen, but I guess we can ignore this.
                pass
            self.semaphore.release()
            return True
        else:
            return False

    def save(self):
        """Save the .dat file to disk."""
        with open(self.datfilename, 'wb') as f:
            pickle.dump(self.historyDict, f, protocol=config.pickle_protocol)


class DeadLinkReportThread(threading.Thread):

    """
    A Thread that is responsible for posting error reports on talk pages.

    There is only one DeadLinkReportThread, and it is using a semaphore to make
    sure that two LinkCheckerThreads can not access the queue at the same time.
    """

    def __init__(self):
        """Constructor."""
        threading.Thread.__init__(self)
        self.semaphore = threading.Semaphore()
        self.queue = []
        self.finishing = False
        self.killed = False

    def report(self, url, errorReport, containingPage, archiveURL):
        """Report error on talk page of the page containing the dead link."""
        self.semaphore.acquire()
        self.queue.append((url, errorReport, containingPage, archiveURL))
        self.semaphore.release()

    def shutdown(self):
        """Finish thread."""
        self.finishing = True

    def kill(self):
        """Kill thread."""
        # TODO: remove if unneeded
        self.killed = True

    def run(self):
        """Run thread."""
        while not self.killed:
            if len(self.queue) == 0:
                if self.finishing:
                    break
                else:
                    time.sleep(0.1)
            else:
                self.semaphore.acquire()
                (url, errorReport, containingPage, archiveURL) = self.queue[0]
                self.queue = self.queue[1:]
                talkPage = containingPage.toggleTalkPage()
                pywikibot.output(color_format(
                    '{lightaqua}** Reporting dead link on {0}...{default}',
                    talkPage.title(asLink=True)))
                try:
                    content = talkPage.get() + "\n\n\n"
                    if url in content:
                        pywikibot.output(color_format(
                            '{lightaqua}** Dead link seems to have already '
                            'been reported on {0}{default}',
                            talkPage.title(asLink=True)))
                        self.semaphore.release()
                        continue
                except (pywikibot.NoPage, pywikibot.IsRedirectPage):
                    content = u''

                if archiveURL:
                    archiveMsg = u'\n' + \
                                 i18n.twtranslate(containingPage.site,
                                                  'weblinkchecker-archive_msg',
                                                  {'URL': archiveURL})
                else:
                    archiveMsg = u''
                # The caption will default to "Dead link". But if there is
                # already such a caption, we'll use "Dead link 2",
                # "Dead link 3", etc.
                caption = i18n.twtranslate(containingPage.site,
                                           'weblinkchecker-caption')
                i = 1
                count = u''
                # Check if there is already such a caption on the talk page.
                while re.search('= *%s%s *=' % (caption, count),
                                content) is not None:
                    i += 1
                    count = u' ' + str(i)
                caption += count
                content += '== %s ==\n\n%s\n\n%s%s\n--~~~~' % \
                           (caption,
                            i18n.twtranslate(containingPage.site,
                                             'weblinkchecker-report'),
                            errorReport,
                            archiveMsg)
                comment = u'[[%s#%s|→]] %s' % \
                          (talkPage.title(), caption,
                           i18n.twtranslate(containingPage.site,
                                            'weblinkchecker-summary'))
                try:
                    talkPage.put(content, comment)
                except pywikibot.SpamfilterError as error:
                    pywikibot.output(color_format(
                        '{lightaqua}** SpamfilterError while trying to '
                        'change {0}: {1}{default}',
                        talkPage.title(asLink=True), error.url))

                self.semaphore.release()


class WeblinkCheckerRobot(SingleSiteBot, ExistingPageBot):

    """
    Bot which will search for dead weblinks.

    It uses several LinkCheckThreads at once to process pages from generator.
    """

    def __init__(self, generator, HTTPignore=None, day=7, site=True):
        """Constructor."""
        super(WeblinkCheckerRobot, self).__init__(
            generator=generator, site=site)

        if config.report_dead_links_on_talk:
            pywikibot.log("Starting talk page thread")
            reportThread = DeadLinkReportThread()
            # thread dies when program terminates
            # reportThread.setDaemon(True)
            reportThread.start()
        else:
            reportThread = None
        self.history = History(reportThread, site=self.site)
        if HTTPignore is None:
            self.HTTPignore = []
        else:
            self.HTTPignore = HTTPignore
        self.day = day

    def treat_page(self):
        """Process one page."""
        page = self.current_page
        text = page.get()
        for url in weblinksIn(text):
            ignoreUrl = False
            for ignoreR in ignorelist:
                if ignoreR.match(url):
                    ignoreUrl = True
            if not ignoreUrl:
                # Limit the number of threads started at the same time. Each
                # thread will check one page, then die.
                while threading.activeCount() >= config.max_external_links:
                    time.sleep(config.retry_wait)
                thread = LinkCheckThread(page, url, self.history,
                                         self.HTTPignore, self.day)
                # thread dies when program terminates
                thread.setDaemon(True)
                try:
                    thread.start()
                except threading.ThreadError:
                    pywikibot.warning(
                        "Can't start a new thread.\nPlease decrease "
                        "max_external_links in your user-config.py or use\n"
                        "'-max_external_links:' option with a smaller value. "
                        "Default is 50.")
                    raise


def RepeatPageGenerator():
    """Generator for pages in History."""
    history = History(None)
    pageTitles = set()
    for value in history.historyDict.values():
        for entry in value:
            pageTitles.add(entry[0])
    for pageTitle in sorted(pageTitles):
        page = pywikibot.Page(pywikibot.Site(), pageTitle)
        yield page


def countLinkCheckThreads():
    """
    Count LinkCheckThread threads.

    @return: number of LinkCheckThread threads
    @rtype: int
    """
    i = 0
    for thread in threading.enumerate():
        if isinstance(thread, LinkCheckThread):
            i += 1
    return i


@deprecated('requests')
def check(url):
    """DEPRECATED: Use requests instead. Perform a check on URL."""
    c = LinkChecker(url)
    return c.check()


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    gen = None
    xmlFilename = None
    HTTPignore = []

    if isinstance(memento_client, ImportError):
        warn('memento_client not imported: %s' % memento_client, ImportWarning)

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg == '-talk':
            config.report_dead_links_on_talk = True
        elif arg == '-notalk':
            config.report_dead_links_on_talk = False
        elif arg == '-repeat':
            gen = RepeatPageGenerator()
        elif arg.startswith('-ignore:'):
            HTTPignore.append(int(arg[8:]))
        elif arg.startswith('-day:'):
            config.weblink_dead_days = int(arg[5:])
        elif arg.startswith('-xmlstart'):
            if len(arg) == 9:
                xmlStart = pywikibot.input(
                    u'Please enter the dumped article to start with:')
            else:
                xmlStart = arg[10:]
        elif arg.startswith('-xml'):
            if len(arg) == 4:
                xmlFilename = i18n.input('pywikibot-enter-xml-filename')
            else:
                xmlFilename = arg[5:]
        else:
            genFactory.handleArg(arg)

    if xmlFilename:
        try:
            xmlStart
        except NameError:
            xmlStart = None
        gen = XmlDumpPageGenerator(xmlFilename, xmlStart,
                                   genFactory.namespaces)

    if not gen:
        gen = genFactory.getCombinedGenerator()
    if gen:
        if not genFactory.nopreload:
            # fetch at least 240 pages simultaneously from the wiki, but more
            # if a high thread number is set.
            pageNumber = max(240, config.max_external_links * 2)
            gen = pagegenerators.PreloadingGenerator(gen, groupsize=pageNumber)
        gen = pagegenerators.RedirectFilterPageGenerator(gen)
        bot = WeblinkCheckerRobot(gen, HTTPignore, config.weblink_dead_days)
        try:
            bot.run()
        finally:
            waitTime = 0
            # Don't wait longer than 30 seconds for threads to finish.
            while countLinkCheckThreads() > 0 and waitTime < 30:
                try:
                    pywikibot.output(u"Waiting for remaining %i threads to "
                                     u"finish, please wait..."
                                     % countLinkCheckThreads())
                    # wait 1 second
                    time.sleep(1)
                    waitTime += 1
                except KeyboardInterrupt:
                    pywikibot.output(u'Interrupted.')
                    break
            if countLinkCheckThreads() > 0:
                pywikibot.output(u'Remaining %i threads will be killed.'
                                 % countLinkCheckThreads())
                # Threads will die automatically because they are daemonic.
            if bot.history.reportThread:
                bot.history.reportThread.shutdown()
                # wait until the report thread is shut down; the user can
                # interrupt it by pressing CTRL-C.
                try:
                    while bot.history.reportThread.isAlive():
                        time.sleep(0.1)
                except KeyboardInterrupt:
                    pywikibot.output(u'Report thread interrupted.')
                    bot.history.reportThread.kill()
            pywikibot.output(u'Saving history...')
            bot.history.save()
        return True
    else:
        pywikibot.bot.suggest_help(missing_generator=True)
        return False


if __name__ == "__main__":
    main()
