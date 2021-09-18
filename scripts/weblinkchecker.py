#!/usr/bin/python
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

&params;

Furthermore, the following command line parameters are supported:

-talk        Overrides the report_dead_links_on_talk config variable, enabling
             the feature.

-notalk      Overrides the report_dead_links_on_talk config variable, disabling
             the feature.

-day         Do not report broken link if the link is there only since
             x days or less. If not set, the default is 7 days.

The following config variables are supported:

 max_external_links         The maximum number of web pages that should be
                            loaded simultaneously. You should change this
                            according to your Internet connection speed.
                            Be careful: if it is set too high, the script
                            might get socket errors because your network
                            is congested, and will then think that the page
                            is offline.

 report_dead_links_on_talk  If set to true, causes the script to report dead
                            links on the article's talk page if (and ONLY if)
                            the linked page has been unavailable at least two
                            times during a timespan of at least one week.

 weblink_dead_days          sets the timespan (default: one week) after which
                            a dead link will be reported

Examples
--------

Loads all wiki pages in alphabetical order using the Special:Allpages
feature:

    python pwb.py weblinkchecker -start:!

Loads all wiki pages using the Special:Allpages feature, starting at
"Example page":

    python pwb.py weblinkchecker -start:Example_page

Loads all wiki pages that link to www.example.org:

    python pwb.py weblinkchecker -weblink:www.example.org

Only checks links found in the wiki page "Example page":

    python pwb.py weblinkchecker Example page

Loads all wiki pages where dead links were found during a prior run:

    python pwb.py weblinkchecker -repeat
"""
#
# (C) Pywikibot team, 2005-2021
#
# Distributed under the terms of the MIT license.
#
import codecs
import datetime
import pickle
import re
import threading
import time
from contextlib import suppress
from functools import partial
from http import HTTPStatus

import requests

import pywikibot
from pywikibot import comms, config, i18n, pagegenerators, textlib
from pywikibot.bot import ExistingPageBot, SingleSiteBot, suggest_help
from pywikibot.exceptions import (
    IsRedirectPageError,
    NoPageError,
    SpamblacklistError,
)
from pywikibot.pagegenerators import (
    XMLDumpPageGenerator as _XMLDumpPageGenerator,
)
from pywikibot.tools import ThreadList
from pywikibot.tools.formatter import color_format


try:
    import memento_client
    from memento_client.memento_client import MementoClientException
except ImportError as e:
    memento_client = e


docuReplacements = {'&params;': pagegenerators.parameterHelp}  # noqa: N816

ignorelist = [
    # Officially reserved for testing, documentation, etc. in
    # https://datatracker.ietf.org/doc/html/rfc2606#page-2
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
    while retry_count <= config.max_retries:
        try:
            memento_info = mc.get_memento_info(url, when)
            break
        except (requests.ConnectionError, MementoClientException) as e:
            error = e
            retry_count += 1
            pywikibot.sleep(config.retry_wait)
    else:
        raise error

    mementos = memento_info.get('mementos')
    if not mementos:
        raise Exception(
            'mementos not found for {} via {}'.format(url, timegate_uri))
    if 'closest' not in mementos:
        raise Exception(
            'closest memento not found for {} via {}'.format(
                url, timegate_uri))
    if 'uri' not in mementos['closest']:
        raise Exception(
            'closest memento uri not found for {} via {}'.format(
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


class LinkCheckThread(threading.Thread):

    """A thread responsible for checking one URL.

    After checking the page, it will die.
    """

    def __init__(self, page, url, history, HTTPignore, day):
        """Initializer."""
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
        self.HTTPignore = HTTPignore
        self._use_fake_user_agent = config.fake_user_agent_default.get(
            'weblinkchecker', False)
        self.day = day

        name = '{} - {}'.format(page.title(), url.encode('utf-8', 'replace'))
        super().__init__(name=name)

    def run(self):
        """Run the bot."""
        try:
            header = self.header
            r = comms.http.fetch(
                self.url, headers=header,
                use_fake_user_agent=self._use_fake_user_agent)
        except requests.exceptions.InvalidURL:
            message = i18n.twtranslate(self.page.site,
                                       'weblinkchecker-badurl_msg',
                                       {'URL': self.url})
        except Exception:
            pywikibot.output('Exception while processing URL {} in page {}'
                             .format(self.url, self.page.title()))
            raise

        if r.status_code != HTTPStatus.OK or r.status_code in self.HTTPignore:
            message = HTTPStatus(r.status_code).phrase
            pywikibot.output('*{} links to {} - {}.'
                             .format(self.page.title(as_link=True), self.url,
                                     message))
            self.history.setLinkDead(self.url, message, self.page,
                                     config.weblink_dead_days)
        elif self.history.setLinkAlive(self.url):
            pywikibot.output(
                '*Link to {} in {} is back alive.'
                .format(self.url, self.page.title(as_link=True)))


class History:

    """
    Store previously found dead links.

    The URLs are dictionary keys, and
    values are lists of tuples where each tuple represents one time the URL was
    found dead. Tuples have the form (title, date, error) where title is the
    wiki page where the URL was found, date is an instance of time, and error
    is a string with error code and message.

    We assume that the first element in the list represents the first time we
    found this dead link, and the last element represents the last time.

    Example::

     dict = {
         'https://www.example.org/page': [
             ('WikiPageTitle', DATE, '404: File not found'),
             ('WikiPageName2', DATE, '404: File not found'),
         ]
     }
    """

    def __init__(self, reportThread, site=None):
        """Initializer."""
        self.reportThread = reportThread
        if not site:
            self.site = pywikibot.Site()
        else:
            self.site = site
        self.semaphore = threading.Semaphore()
        self.datfilename = pywikibot.config.datafilepath(
            'deadlinks', 'deadlinks-{}-{}.dat'.format(self.site.family.name,
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
            errorReport = '* {} ([{} archive])\n'.format(url, archiveURL)
        else:
            errorReport = '* {}\n'.format(url)
        for (pageTitle, date, error) in self.historyDict[url]:
            # ISO 8601 formulation
            isoDate = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(date))
            errorReport += '** In [[{}]] on {}, {}\n'.format(
                pageTitle, isoDate, error)
        pywikibot.output('** Logging link for deletion.')
        txtfilename = pywikibot.config.datafilepath('deadlinks',
                                                    'results-{}-{}.txt'
                                                    .format(
                                                        self.site.family.name,
                                                        self.site.lang))
        with codecs.open(txtfilename, 'a', 'utf-8') as txtfile:
            self.logCount += 1
            if self.logCount % 30 == 0:
                # insert a caption
                txtfile.write('=== {} ===\n'
                              .format(containingPage.title()[:3]))
            txtfile.write(errorReport)

        if self.reportThread and not containingPage.isTalkPage():
            self.reportThread.report(url, errorReport, containingPage,
                                     archiveURL)

    def setLinkDead(self, url, error, page, weblink_dead_days):
        """Add the fact that the link was found dead to the .dat file."""
        with self.semaphore:
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
                            'get_closest_memento_url({}) failed: {}'.format(
                                url, e))
                        archiveURL = None
                    self.log(url, error, page, archiveURL)
            else:
                self.historyDict[url] = [(page.title(), now, error)]

    def setLinkAlive(self, url):
        """
        Record that the link is now alive.

        If link was previously found dead, remove it from the .dat file.

        :return: True if previously found dead, else returns False.
        """
        if url in self.historyDict:
            with self.semaphore, suppress(KeyError):
                del self.historyDict[url]
            return True

        return False

    def save(self):
        """Save the .dat file to disk."""
        with open(self.datfilename, 'wb') as f:
            pickle.dump(self.historyDict, f, protocol=config.pickle_protocol)


class DeadLinkReportThread(threading.Thread):

    """
    A Thread that is responsible for posting error reports on talk pages.

    There is only one DeadLinkReportThread, and it is using a semaphore to make
    sure that two LinkCheckerThreads cannot access the queue at the same time.
    """

    def __init__(self):
        """Initializer."""
        super().__init__()
        self.semaphore = threading.Semaphore()
        self.queue = []
        self.finishing = False
        self.killed = False

    def report(self, url, errorReport, containingPage, archiveURL):
        """Report error on talk page of the page containing the dead link."""
        with self.semaphore:
            self.queue.append((url, errorReport, containingPage, archiveURL))

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
            if not self.queue:
                if self.finishing:
                    break
                time.sleep(0.1)
                continue

            with self.semaphore:
                url, errorReport, containingPage, archiveURL = self.queue[0]
                self.queue = self.queue[1:]
                talkPage = containingPage.toggleTalkPage()
                pywikibot.output(color_format(
                    '{lightaqua}** Reporting dead link on {}...{default}',
                    talkPage))
                try:
                    content = talkPage.get() + '\n\n\n'
                    if url in content:
                        pywikibot.output(color_format(
                            '{lightaqua}** Dead link seems to have '
                            'already been reported on {}{default}',
                            talkPage))
                        continue
                except (NoPageError, IsRedirectPageError):
                    content = ''

                if archiveURL:
                    archiveMsg = '\n' + i18n.twtranslate(
                        containingPage.site, 'weblinkchecker-archive_msg',
                        {'URL': archiveURL})
                else:
                    archiveMsg = ''
                # The caption will default to "Dead link". But if there
                # is already such a caption, we'll use "Dead link 2",
                # "Dead link 3", etc.
                caption = i18n.twtranslate(containingPage.site,
                                           'weblinkchecker-caption')
                i = 1
                count = ''
                # Check if there is already such a caption on
                # the talk page.
                while re.search('= *{}{} *='
                                .format(caption, count), content) is not None:
                    i += 1
                    count = ' ' + str(i)
                caption += count
                content += '== {0} ==\n\n{3}\n\n{1}{2}\n--~~~~'.format(
                    caption, errorReport, archiveMsg,
                    i18n.twtranslate(containingPage.site,
                                     'weblinkchecker-report'))

                comment = '[[{}#{}|→]] {}'.format(
                    talkPage.title(), caption,
                    i18n.twtranslate(containingPage.site,
                                     'weblinkchecker-summary'))
                try:
                    talkPage.put(content, comment)
                except SpamblacklistError as error:
                    pywikibot.output(color_format(
                        '{lightaqua}** SpamblacklistError while trying to '
                        'change {0}: {1}{default}',
                        talkPage, error.url))


class WeblinkCheckerRobot(SingleSiteBot, ExistingPageBot):

    """
    Bot which will search for dead weblinks.

    It uses several LinkCheckThreads at once to process pages from generator.
    """

    def __init__(self, HTTPignore=None, day=7, **kwargs):
        """Initializer."""
        super().__init__(**kwargs)

        if config.report_dead_links_on_talk:
            pywikibot.log('Starting talk page thread')
            reportThread = DeadLinkReportThread()
            reportThread.start()
        else:
            reportThread = None
        self.history = History(reportThread, site=self.site)
        self.HTTPignore = HTTPignore or []
        self.day = day

        # Limit the number of threads started at the same time
        self.threads = ThreadList(limit=config.max_external_links,
                                  wait_time=config.retry_wait)

    def treat_page(self):
        """Process one page."""
        page = self.current_page
        for url in weblinksIn(page.text):
            for ignoreR in ignorelist:
                if ignoreR.match(url):
                    break
            else:
                # Each thread will check one page, then die.
                thread = LinkCheckThread(page, url, self.history,
                                         self.HTTPignore, self.day)
                # thread dies when program terminates
                thread.daemon = True
                self.threads.append(thread)


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


def countLinkCheckThreads() -> int:
    """
    Count LinkCheckThread threads.

    :return: number of LinkCheckThread threads
    """
    i = 0
    for thread in threading.enumerate():
        if isinstance(thread, LinkCheckThread):
            i += 1
    return i


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    gen = None
    xmlFilename = None
    HTTPignore = []

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
                    'Please enter the dumped article to start with:')
            else:
                xmlStart = arg[10:]
        elif arg.startswith('-xml'):
            if len(arg) == 4:
                xmlFilename = i18n.input('pywikibot-enter-xml-filename')
            else:
                xmlFilename = arg[5:]
        else:
            genFactory.handle_arg(arg)

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
        bot = WeblinkCheckerRobot(HTTPignore, config.weblink_dead_days,
                                  generator=gen)
        try:
            bot.run()
        except ImportError:
            suggest_help(missing_dependencies=('memento_client',))
            return
        finally:
            waitTime = 0
            # Don't wait longer than 30 seconds for threads to finish.
            while countLinkCheckThreads() > 0 and waitTime < 30:
                try:
                    pywikibot.output('Waiting for remaining {} threads to '
                                     'finish, please wait...'
                                     .format(countLinkCheckThreads()))
                    # wait 1 second
                    time.sleep(1)
                    waitTime += 1
                except KeyboardInterrupt:
                    pywikibot.output('Interrupted.')
                    break
            if countLinkCheckThreads() > 0:
                pywikibot.output('Remaining {} threads will be killed.'
                                 .format(countLinkCheckThreads()))
                # Threads will die automatically because they are daemonic.
            if bot.history.reportThread:
                bot.history.reportThread.shutdown()
                # wait until the report thread is shut down; the user can
                # interrupt it by pressing CTRL-C.
                try:
                    while bot.history.reportThread.is_alive():
                        time.sleep(0.1)
                except KeyboardInterrupt:
                    pywikibot.output('Report thread interrupted.')
                    bot.history.reportThread.kill()
            pywikibot.output('Saving history...')
            bot.history.save()
    else:
        suggest_help(missing_generator=True)


if __name__ == '__main__':
    main()
