#!/usr/bin/env python3
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

In addition to the logging step, it is possible to automatically report
dead links to the talk page of the article where the link was found. To
use this feature, set report_dead_links_on_talk = True in your user
config file, or specify "-talk" on the command line. Adding "-notalk"
switches this off irrespective of the configuration variable.

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
# (C) Pywikibot team, 2005-2022
#
# Distributed under the terms of the MIT license.
#
import codecs
import pickle
import re
import threading
import time
import urllib.parse as urlparse
from contextlib import suppress
from functools import partial
from http import HTTPStatus

import requests

import pywikibot
from pywikibot import comms, config, i18n, pagegenerators, textlib
from pywikibot.backports import Dict, removeprefix
from pywikibot.bot import ExistingPageBot, SingleSiteBot, suggest_help
from pywikibot.exceptions import (
    IsRedirectPageError,
    NoPageError,
    SpamblacklistError,
)
from pywikibot.pagegenerators import (
    XMLDumpPageGenerator as _XMLDumpPageGenerator,
)
from pywikibot.tools.threading import ThreadList


try:
    from pywikibot.data.memento import get_closest_memento_url
    missing_dependencies = []
except ImportError:
    missing_dependencies = ['memento_client']


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


def get_archive_url(url):
    """Get archive URL."""
    try:
        return get_closest_memento_url(
            url, timegate_uri='http://web.archive.org/web/')
    except Exception:
        return get_closest_memento_url(
            url,
            timegate_uri='http://timetravel.mementoweb.org/webcite/timegate/')


def weblinks_from_text(
    text,
    without_bracketed: bool = False,
    only_bracketed: bool = False
):
    """
    Yield web links from text.

    Only used as text predicate for XmlDumpPageGenerator to speed up
    generator.

    TODO: move to textlib
    """
    text = textlib.removeDisabledParts(text)

    # Ignore links in fullurl template
    text = re.sub(r'{{\s?fullurl:.[^}]*}}', '', text)

    # MediaWiki parses templates before parsing external links. Thus, there
    # might be a | or a } directly after a URL which does not belong to
    # the URL itself.

    # First, remove the curly braces of inner templates:
    nested_template_regex = re.compile(r'{{([^}]*?){{(.*?)}}(.*?)}}')
    while nested_template_regex.search(text):
        text = nested_template_regex.sub(r'{{\1 \2 \3}}', text)

    # Then blow up the templates with spaces so that the | and }} will not
    # be regarded as part of the link:.
    template_with_params_regex = re.compile(r'{{([^}]*?[^ ])\|([^ ][^}]*?)}}',
                                            re.DOTALL)
    while template_with_params_regex.search(text):
        text = template_with_params_regex.sub(r'{{ \1 | \2 }}', text)

    # Add <blank> at the end of a template
    # URL as last param of multiline template would not be correct
    text = text.replace('}}', ' }}')

    # Remove HTML comments in URLs as well as URLs in HTML comments.
    # Also remove text inside nowiki links etc.
    text = textlib.removeDisabledParts(text)
    link_regex = textlib.compileLinkR(without_bracketed, only_bracketed)
    for m in link_regex.finditer(text):
        if m['url']:
            yield m['url']
        else:
            yield m['urlb']


XmlDumpPageGenerator = partial(
    _XMLDumpPageGenerator, text_predicate=weblinks_from_text)


class NotAnURLError(BaseException):

    """The link is not an URL."""


class LinkCheckThread(threading.Thread):

    """A thread responsible for checking one URL.

    After checking the page, it will die.
    """

    #: Collecting start time of a thread for any host
    hosts: Dict[str, float] = {}
    lock = threading.Lock()

    def __init__(self, page, url, history, http_ignores, day) -> None:
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
        self.http_ignores = http_ignores
        self._use_fake_user_agent = config.fake_user_agent_default.get(
            'weblinkchecker', False)
        self.day = day
        super().__init__()

    @classmethod
    def get_delay(cls, name: str) -> float:
        """Determine delay from class attribute.

        Store the last call for a given hostname with an offset of
        6 seconds to ensure there are no more than 10 calls per minute
        for the same host. Calculate the delay to start the run.

        :param name: The key for the hosts class attribute
        :return: The calulated delay to start the run
        """
        now = time.monotonic()
        with cls.lock:
            timestamp = cls.hosts.get(name, now)
            cls.hosts[name] = max(now, timestamp) + 6
        return max(0, timestamp - now)

    def run(self):
        """Run the bot."""
        time.sleep(self.get_delay(self.name))
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
            pywikibot.info(f'Exception while processing URL {self.url} in '
                           f'page {self.page}')
            raise

        if (
            r.status_code != HTTPStatus.OK
            or r.status_code in self.http_ignores
        ):
            message = HTTPStatus(r.status_code).phrase
            pywikibot.info(f'*{self.page} links to {self.url} - {message}.')
            self.history.set_dead_link(self.url, message, self.page,
                                       config.weblink_dead_days)
        elif self.history.set_link_alive(self.url):
            pywikibot.info(
                f'*Link to {self.url} in {self.page} is back alive.')


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

    def __init__(self, report_thread, site=None) -> None:
        """Initializer."""
        self.report_thread = report_thread
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
        self.log_count = 0
        try:
            with open(self.datfilename, 'rb') as datfile:
                self.history_dict = pickle.load(datfile)
        except (OSError, EOFError):
            # no saved history exists yet, or history dump broken
            self.history_dict = {}

    def log(self, url, error, containing_page, archive_url) -> None:
        """Log an error report to a text file in the deadlinks subdirectory."""
        if archive_url:
            error_report = f'* {url} ([{archive_url} archive])\n'
        else:
            error_report = f'* {url}\n'
        for (page_title, date, error) in self.history_dict[url]:
            # ISO 8601 formulation
            iso_date = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(date))
            error_report += '** In [[{}]] on {}, {}\n'.format(
                page_title, iso_date, error)
        pywikibot.info('** Logging link for deletion.')
        txtfilename = pywikibot.config.datafilepath('deadlinks',
                                                    'results-{}-{}.txt'
                                                    .format(
                                                        self.site.family.name,
                                                        self.site.lang))
        with codecs.open(txtfilename, 'a', 'utf-8') as txtfile:
            self.log_count += 1
            if self.log_count % 30 == 0:
                # insert a caption
                txtfile.write('=== {} ===\n'
                              .format(containing_page.title()[:3]))
            txtfile.write(error_report)

        if self.report_thread and not containing_page.isTalkPage():
            self.report_thread.report(url, error_report, containing_page,
                                      archive_url)

    def set_dead_link(self, url, error, page, weblink_dead_days) -> None:
        """Add the fact that the link was found dead to the .dat file."""
        with self.semaphore:
            now = time.time()
            if url in self.history_dict:
                time_since_first_found = now - self.history_dict[url][0][1]
                time_since_last_found = now - self.history_dict[url][-1][1]
                # if the last time we found this dead link is less than an hour
                # ago, we won't save it in the history this time.
                if time_since_last_found > 60 * 60:
                    self.history_dict[url].append((page.title(), now, error))
                # if the first time we found this link longer than x day ago
                # (default is a week), it should probably be fixed or removed.
                # We'll list it in a file so that it can be removed manually.
                if time_since_first_found > 60 * 60 * 24 * weblink_dead_days:
                    # search for archived page
                    try:
                        archive_url = get_archive_url(url)
                    except Exception as e:
                        pywikibot.warning(
                            'get_closest_memento_url({}) failed: {}'.format(
                                url, e))
                        archive_url = None
                    self.log(url, error, page, archive_url)
            else:
                self.history_dict[url] = [(page.title(), now, error)]

    def set_link_alive(self, url) -> bool:
        """
        Record that the link is now alive.

        If link was previously found dead, remove it from the .dat file.

        :return: True if previously found dead, else returns False.
        """
        if url in self.history_dict:
            with self.semaphore, suppress(KeyError):
                del self.history_dict[url]
            return True

        return False

    def save(self) -> None:
        """Save the .dat file to disk."""
        with open(self.datfilename, 'wb') as f:
            pickle.dump(self.history_dict, f, protocol=config.pickle_protocol)


class DeadLinkReportThread(threading.Thread):

    """
    A Thread that is responsible for posting error reports on talk pages.

    There is only one DeadLinkReportThread, and it is using a semaphore to make
    sure that two LinkCheckerThreads cannot access the queue at the same time.
    """

    def __init__(self) -> None:
        """Initializer."""
        super().__init__()
        self.semaphore = threading.Semaphore()
        self.queue = []
        self.finishing = False
        self.killed = False

    def report(self, url, error_report, containing_page, archive_url) -> None:
        """Report error on talk page of the page containing the dead link."""
        with self.semaphore:
            self.queue.append((url, error_report, containing_page,
                               archive_url))

    def shutdown(self) -> None:
        """Finish thread."""
        self.finishing = True

    def kill(self) -> None:
        """Kill thread."""
        # TODO: remove if unneeded
        self.killed = True

    def run(self) -> None:
        """Run thread."""
        while not self.killed:
            if not self.queue:
                if self.finishing:
                    break
                time.sleep(0.1)
                continue

            with self.semaphore:
                url, error_report, containing_page, archive_url = self.queue[0]
                self.queue = self.queue[1:]
                talk_page = containing_page.toggleTalkPage()
                pywikibot.info(
                    f'<<lightaqua>>** Reporting dead link on {talk_page}...')
                try:
                    content = talk_page.get() + '\n\n\n'
                    if url in content:
                        pywikibot.info(
                            f'<<lightaqua>>** Dead link seems to have already '
                            f'been reported on {talk_page}')
                        continue
                except (NoPageError, IsRedirectPageError):
                    content = ''

                if archive_url:
                    archive_msg = '\n' + i18n.twtranslate(
                        containing_page.site, 'weblinkchecker-archive_msg',
                        {'URL': archive_url})
                else:
                    archive_msg = ''
                # The caption will default to "Dead link". But if there
                # is already such a caption, we'll use "Dead link 2",
                # "Dead link 3", etc.
                caption = i18n.twtranslate(containing_page.site,
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
                    caption, error_report, archive_msg,
                    i18n.twtranslate(containing_page.site,
                                     'weblinkchecker-report'))

                comment = '[[{}#{}|→]] {}'.format(
                    talk_page.title(), caption,
                    i18n.twtranslate(containing_page.site,
                                     'weblinkchecker-summary'))
                try:
                    talk_page.put(content, comment)
                except SpamblacklistError as error:
                    pywikibot.info(
                        '<<lightaqua>>** SpamblacklistError while trying to '
                        'change {}: {}<<default>>'
                        .format(talk_page, error.url))


class WeblinkCheckerRobot(SingleSiteBot, ExistingPageBot):

    """
    Bot which will search for dead weblinks.

    It uses several LinkCheckThreads at once to process pages from generator.
    """

    use_redirects = False

    def __init__(self, http_ignores=None, day: int = 7, **kwargs) -> None:
        """Initializer."""
        super().__init__(**kwargs)

        if config.report_dead_links_on_talk:
            pywikibot.log('Starting talk page thread')
            report_thread = DeadLinkReportThread()
            report_thread.start()
        else:
            report_thread = None
        self.history = History(report_thread, site=self.site)
        self.http_ignores = http_ignores or []
        self.day = day

        # Limit the number of threads started at the same time
        self.threads = ThreadList(limit=config.max_external_links,
                                  wait_time=config.retry_wait)

    def treat_page(self) -> None:
        """Process one page."""
        page = self.current_page
        for url in page.extlinks():
            for ignore_regex in ignorelist:
                if ignore_regex.match(url):
                    break
            else:
                # Each thread will check one page, then die.
                thread = LinkCheckThread(page, url, self.history,
                                         self.http_ignores, self.day)
                # thread dies when program terminates
                thread.daemon = True
                # use hostname as thread.name
                thread.name = removeprefix(
                    urlparse.urlparse(url).hostname, 'www.')
                self.threads.append(thread)

    def teardown(self) -> None:
        """Finish remaining threads and save history file."""
        num = self.count_link_check_threads()
        if num:
            pywikibot.info('<<lightblue>>Waiting for remaining {} threads '
                           'to finish, please wait...'.format(num))

        while self.count_link_check_threads():
            try:
                time.sleep(0.1)
            except KeyboardInterrupt:
                # Threads will die automatically because they are daemonic.
                if pywikibot.input_yn('There are {} pages remaining in the '
                                      'queue. Really exit?'
                                      .format(self.count_link_check_threads()),
                                      default=False, automatic_quit=False):
                    break

        num = self.count_link_check_threads()
        if num:
            pywikibot.info('<<yellow>>>Remaining {} threads will be killed.'
                           .format(num))

        if self.history.report_thread:
            self.history.report_thread.shutdown()
            # wait until the report thread is shut down; the user can
            # interrupt it by pressing CTRL-C.
            try:
                while self.history.report_thread.is_alive():
                    time.sleep(0.1)
            except KeyboardInterrupt:
                pywikibot.info('Report thread interrupted.')
                self.history.report_thread.kill()

        pywikibot.info('Saving history...')
        self.history.save()

    @staticmethod
    def count_link_check_threads() -> int:
        """Count LinkCheckThread threads.

        :return: number of LinkCheckThread threads
        """
        return sum(isinstance(thread, LinkCheckThread)
                   for thread in threading.enumerate())


def RepeatPageGenerator():  # noqa: N802
    """Generator for pages in History."""
    history = History(None)
    page_titles = set()
    for value in history.history_dict.values():
        for entry in value:
            page_titles.add(entry[0])
    for page_title in sorted(page_titles):
        page = pywikibot.Page(pywikibot.Site(), page_title)
        yield page


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    gen = None
    xml_filename = None
    http_ignores = []

    # Process global args and prepare generator args parser
    local_args = pywikibot.handle_args(args)
    gen_factory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if arg == '-talk':
            config.report_dead_links_on_talk = True
        elif arg == '-notalk':
            config.report_dead_links_on_talk = False
        elif arg == '-repeat':
            gen = RepeatPageGenerator()
        elif arg.startswith('-ignore:'):
            http_ignores.append(int(arg[8:]))
        elif arg.startswith('-day:'):
            config.weblink_dead_days = int(arg[5:])
        elif arg.startswith('-xmlstart'):
            if len(arg) == 9:
                xml_start = pywikibot.input(
                    'Please enter the dumped article to start with:')
            else:
                xml_start = arg[10:]
        elif arg.startswith('-xml'):
            if len(arg) == 4:
                xml_filename = i18n.input('pywikibot-enter-xml-filename')
            else:
                xml_filename = arg[5:]
        else:
            gen_factory.handle_arg(arg)

    if xml_filename:
        try:
            xml_start
        except NameError:
            xml_start = None
        gen = XmlDumpPageGenerator(xml_filename, xml_start,
                                   gen_factory.namespaces)

    if not gen:
        gen = gen_factory.getCombinedGenerator()

    if not suggest_help(missing_generator=not gen,
                        missing_dependencies=missing_dependencies):
        bot = WeblinkCheckerRobot(http_ignores, config.weblink_dead_days,
                                  generator=gen)
        bot.run()


if __name__ == '__main__':
    main()
