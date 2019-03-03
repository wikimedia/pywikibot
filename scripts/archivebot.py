#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
archivebot.py - discussion page archiving bot.

usage:

    python pwb.py archivebot [OPTIONS] TEMPLATE_PAGE

Bot examines backlinks (Special:WhatLinksHere) to TEMPLATE_PAGE.
Then goes through all pages (unless a specific page specified using options)
and archives old discussions. This is done by breaking a page into threads,
then scanning each thread for timestamps. Threads older than a specified
threshold are then moved to another page (the archive), which can be named
either basing on the thread's name or then name can contain a counter which
will be incremented when the archive reaches a certain size.

Transcluded template may contain the following parameters:

 {{TEMPLATE_PAGE
 |archive =
 |algo =
 |counter =
 |maxarchivesize =
 |minthreadsleft =
 |minthreadstoarchive =
 |archiveheader =
 |key =
 }}

Meanings of parameters are:

 archive              Name of the page to which archived threads will be put.
                      Must be a subpage of the current page. Variables are
                      supported.
 algo                 Specifies the maximum age of a thread. Must be
                      in the form old(<delay>) where <delay> specifies
                      the age in seconds (s), hours (h), days (d),
                      weeks (w), or years (y) like 24h or 5d. Default is
                      old(24h).
 counter              The current value of a counter which could be assigned as
                      variable. Will be updated by bot. Initial value is 1.
 maxarchivesize       The maximum archive size before incrementing the counter.
                      Value can be given with appending letter like K or M
                      which indicates KByte or MByte. Default value is 200K.
 minthreadsleft       Minimum number of threads that should be left on a page.
                      Default value is 5.
 minthreadstoarchive  The minimum number of threads to archive at once. Default
                      value is 2.
 archiveheader        Content that will be put on new archive pages as the
                      header. This parameter supports the use of variables.
                      Default value is {{talkarchive}}
 key                  A secret key that (if valid) allows archives not to be
                      subpages of the page being archived.

Variables below can be used in the value for "archive" in the template above:

%(counter)d          the current value of the counter
%(year)d             year of the thread being archived
%(isoyear)d          ISO year of the thread being archived
%(isoweek)d          ISO week number of the thread being archived
%(semester)d         semester term of the year of the thread being archived
%(quarter)d          quarter of the year of the thread being archived
%(month)d            month (as a number 1-12) of the thread being archived
%(monthname)s        localized name of the month above
%(monthnameshort)s   first three letters of the name above
%(week)d             week number of the thread being archived

The ISO calendar starts with the Monday of the week which has at least four
days in the new Gregorian calendar. If January 1st is between Monday and
Thursday (including), the first week of that year started the Monday of that
week, which is in the year before if January 1st is not a Monday. If it's
between Friday or Sunday (including) the following week is then the first week
of the year. So up to three days are still counted as the year before.

See also:
 - http://www.phys.uu.nl/~vgent/calendar/isocalendar.htm
 - https://docs.python.org/3.4/library/datetime.html#datetime.date.isocalendar

Options (may be omitted):

  -help           show this help message and exit
  -calc:PAGE      calculate key for PAGE and exit
  -file:FILE      load list of pages from FILE
  -force          override security options
  -locale:LOCALE  switch to locale LOCALE
  -namespace:NS   only archive pages from a given namespace
  -page:PAGE      archive a single PAGE, default ns is a user talk page
  -salt:SALT      specify salt
"""
#
# (C) Misza13, 2006-2010
# (C) xqt, 2009-2019
# (C) Pywikibot team, 2007-2019
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, division, unicode_literals

import datetime
import locale
import math
import os
import re
import time

from collections import OrderedDict
from hashlib import md5
from math import ceil

import pywikibot

from pywikibot.date import apply_month_delta
from pywikibot import i18n
from pywikibot.textlib import (extract_sections, findmarker, TimeStripper,
                               to_local_digits)
from pywikibot.tools import issue_deprecation_warning, FrozenDict

ZERO = datetime.timedelta(0)

MW_KEYS = FrozenDict({
    's': 'seconds',
    'h': 'hours',
    'd': 'days',
    'w': 'weeks',
    'y': 'years',
    # 'months' and 'minutes' were removed because confusion outweighs merit
}, 'MW_KEYS is a dict constant')


class ArchiveBotSiteConfigError(pywikibot.Error):

    """There is an error originated by archivebot's on-site configuration."""


class MalformedConfigError(ArchiveBotSiteConfigError):

    """There is an error in the configuration template."""


class MissingConfigError(ArchiveBotSiteConfigError):

    """
    The config is missing in the header.

    It's in one of the threads or transcluded from another page.
    """


class AlgorithmError(MalformedConfigError):

    """Invalid specification of archiving algorithm."""


class ArchiveSecurityError(ArchiveBotSiteConfigError):

    """
    Page title is not a valid archive of page being archived.

    The page title is neither a subpage of the page being archived,
    nor does it match the key specified in the archive configuration template.
    """


def str2localized_duration(site, string):
    """
    Localise a shorthand duration.

    Translates a duration written in the shorthand notation (ex. "24h", "7d")
    into an expression in the local wiki language ("24 hours", "7 days").
    """
    key, duration = checkstr(string)
    template = site.mediawiki_message(MW_KEYS[key])
    if template:
        # replace plural variants
        exp = i18n.translate(site.code, template, {'$1': int(duration)})
        return exp.replace('$1', to_local_digits(duration, site.code))
    else:
        return to_local_digits(string, site.code)


def str2time(string, timestamp=None):
    """
    Return a timedelta for a shorthand duration.

    @param string: a string defining a time period:
        300s - 300 seconds
        36h - 36 hours
        7d - 7 days
        2w - 2 weeks (14 days)
        1y - 1 year
    @type string: str
    @param timestamp: a timestamp to calculate a more accurate duration offset
        used by years
    @type timestamp: datetime.datetime
    @return: the corresponding timedelta object
    @rtype: datetime.timedelta
    """
    key, duration = checkstr(string)

    if duration.isdigit():
        duration = int(duration)
    else:
        key = ''

    if key in ['d', 's', 'h', 'w']:  # days, seconds, hours, weeks
        return datetime.timedelta(**{MW_KEYS[key]: duration})

    if key == 'y':  # years
        days = math.ceil(duration * 365.25)
        duration *= 12
    else:
        raise MalformedConfigError(
            'Unrecognized parameter in template: {0}'.format(string))

    if timestamp:
        return apply_month_delta(
            timestamp.date(), month_delta=duration) - timestamp.date()
    else:
        return datetime.timedelta(days=days)


def checkstr(string):
    """
    Return the key and duration extracted from the string.

    @param string: a string defining a time period:
        300s - 300 seconds
        36h - 36 hours
        7d - 7 days
        2w - 2 weeks (14 days)
        1y - 1 year
    @type string: str
    @return: key and duration extracted form the string
    @rtype: (str, str)
    """
    key = string[-1]
    if string.isdigit():
        key = 's'
        duration = string
        issue_deprecation_warning('Time period without qualifier',
                                  string + key, 1, UserWarning,
                                  since='20161009')
    else:
        duration = string[:-1]
    return key, duration


def str2size(string):
    """
    Return a size for a shorthand size.

    Accepts a string defining a size:
    1337 - 1337 bytes
    150K - 150 kilobytes
    2M - 2 megabytes
    Returns a tuple (size,unit), where size is an integer and unit is
    'B' (bytes) or 'T' (threads).

    """
    r = re.search(r'(\d+) *([BkKMT]?)', string)
    if not r:
        raise MalformedConfigError("Couldn't parse size: {}".format(string))
    val, unit = (int(r.group(1)), r.group(2))
    if unit == 'M':
        val *= 1024
        unit = 'K'
    if unit in ('K', 'k'):
        val *= 1024
    if unit != 'T':
        unit = 'B'
    return val, unit


def template_title_regex(tpl_page):
    """
    Return a regex that matches to variations of the template title.

    It supports the transcluding variant as well as localized namespaces and
    case-insensitivity depending on the namespace.

    @param tpl_page: The template page
    @type tpl_page: Page
    """
    ns = tpl_page.site.namespaces[tpl_page.namespace()]
    marker = '?' if ns.id == 10 else ''
    title = tpl_page.title(with_ns=False)
    if ns.case != 'case-sensitive':
        title = '[{}{}]{}'.format(re.escape(title[0].upper()),
                                  re.escape(title[0].lower()),
                                  re.escape(title[1:]))
    else:
        title = re.escape(title)

    return re.compile(r'(?:(?:%s):)%s%s' % ('|'.join(ns), marker, title))


def calc_md5_hexdigest(txt, salt):
    """Return md5 hexdigest computed from text and salt."""
    s = md5()
    s.update(salt.encode('utf-8'))
    s.update(b'\n')
    s.update(txt.encode('utf8'))
    s.update(b'\n')
    return s.hexdigest()


class TZoneUTC(datetime.tzinfo):

    """Class building a UTC tzinfo object."""

    def utcoffset(self, dt):  # pylint: disable=unused-argument
        """Subclass implementation, return timedelta(0)."""
        return ZERO

    def tzname(self, dt):  # pylint: disable=unused-argument
        """Subclass implementation."""
        return 'UTC'

    def dst(self, dt):  # pylint: disable=unused-argument
        """Subclass implementation, return timedelta(0)."""
        return ZERO

    def __repr__(self):
        """Return a string representation."""
        return '{}()'.format(self.__class__.__name__)


class DiscussionThread(object):

    """
    An object representing a discussion thread on a page.

    It represents something that is of the form:

    == Title of thread ==

    Thread content here. ~~~~
    :Reply, etc. ~~~~
    """

    def __init__(self, title, now, timestripper):
        """Initializer."""
        self.title = title
        self.now = now
        self.ts = timestripper
        self.code = self.ts.site.code
        self.content = ''
        self.timestamp = None

    def __repr__(self):
        """Return a string representation."""
        return '{}("{}",{} bytes)'.format(self.__class__.__name__, self.title,
                                          len(self.content.encode('utf-8')))

    def feed_line(self, line):
        """Add a line to the content and find the newest timestamp."""
        if not self.content and not line:
            return

        self.content += line + '\n'
        timestamp = self.ts.timestripper(line)

        if not self.timestamp:  # first time
            self.timestamp = timestamp

        if timestamp:
            self.timestamp = max(self.timestamp, timestamp)

    def size(self):
        """Return size of discussion thread."""
        return len(self.title.encode('utf-8')) + len(
            self.content.encode('utf-8')) + 12

    def to_text(self):
        """Return wikitext discussion thread."""
        return '== {} ==\n\n{}'.format(self.title, self.content)

    def should_be_archived(self, archiver):
        """
        Check whether thread has to be archived.

        @return: archiving reason i18n string or empty string.
        @rtype: string
        """
        algo = archiver.get_attr('algo')
        re_t = re.search(r'^old\((.*)\)$', algo)
        if re_t:
            if not self.timestamp:
                return ''
            # TODO: handle this:
            # return 'unsigned'
            maxage = str2time(re_t.group(1), self.timestamp)
            if self.now - self.timestamp > maxage:
                duration = str2localized_duration(archiver.site, re_t.group(1))
                return i18n.twtranslate(self.code,
                                        'archivebot-older-than',
                                        {'duration': duration})
        return ''


class DiscussionPage(pywikibot.Page):

    """
    A class that represents a single page of discussion threads.

    Feed threads to it and run an update() afterwards.
    """

    def __init__(self, source, archiver, params=None):
        """Initializer."""
        super(DiscussionPage, self).__init__(source)
        self.threads = []
        self.full = False
        self.archiver = archiver
        # for testing purposes we allow archiver to be None and we are able
        # to create the a DiscussionPage in this way:
        # >>> import pywikibot as py
        # >>> from scripts.archivebot import DiscussionPage
        # >>> d = DiscussionPage(py.Page(py.Site(), <talk page name>), None)
        if archiver is None:
            self.timestripper = TimeStripper(self.site)
        else:
            self.timestripper = self.archiver.timestripper
        self.params = params
        self.now = datetime.datetime.utcnow().replace(tzinfo=TZoneUTC())
        try:
            self.load_page()
        except pywikibot.NoPage:
            self.header = archiver.get_attr('archiveheader',
                                            i18n.twtranslate(
                                                self.site.code,
                                                'archivebot-archiveheader'))
            if self.params:
                self.header = self.header % self.params

    def load_page(self):
        """Load the page to be archived and break it up into threads."""
        self.header = ''
        self.threads = []
        self.archives = {}
        self.archived_threads = 0

        # Exclude non-thread headings
        text = self.get()
        marker = findmarker(text)
        text = re.sub(r'^===', marker + r'===', text, flags=re.M)

        # Find threads, avoid archiving categories or interwiki
        header, threads, footer = extract_sections(text, self.site)
        header = header.replace(marker, '')
        if header and footer:
            self.header = '\n\n'.join((header.rstrip(), footer, ''))
        else:
            self.header = header + footer
        for thread_heading, thread_content in threads:
            cur_thread = DiscussionThread(thread_heading.strip('= '), self.now,
                                          self.timestripper)
            lines = thread_content.replace(marker, '').splitlines()
            lines = lines[1:]  # remove heading line
            for line in lines:
                cur_thread.feed_line(line)
            self.threads.append(cur_thread)

        # This extra info is not desirable when run under the unittest
        # framework, which may be run either directly or via setup.py
        if pywikibot.calledModuleName() not in ['archivebot_tests', 'setup']:
            pywikibot.output('{} thread(s) found on {}'
                             .format(len(self.threads), self))

    def feed_thread(self, thread, max_archive_size=(250 * 1024, 'B')):
        """Check whether archive size exceeded."""
        self.threads.append(thread)
        self.archived_threads += 1
        if max_archive_size[1] == 'B':
            if self.size() >= max_archive_size[0]:
                self.full = True
        elif max_archive_size[1] == 'T':
            if len(self.threads) >= max_archive_size[0]:
                self.full = True
        return self.full

    def size(self):
        """Return size of talk page threads."""
        return len(self.header.encode('utf-8')) + sum(t.size()
                                                      for t in self.threads)

    def update(self, summary, sort_threads=False):
        """Recombine threads and save page."""
        if sort_threads:
            pywikibot.output('Sorting threads...')
            self.threads.sort(key=lambda t: t.timestamp)
        newtext = re.sub('\n*$', '\n\n', self.header)  # Fix trailing newlines
        for t in self.threads:
            newtext += t.to_text()
        if self.full:
            summary += ' ' + i18n.twtranslate(self.site.code,
                                              'archivebot-archive-full')
        self.text = newtext
        self.save(summary)


class PageArchiver(object):

    """A class that encapsulates all archiving methods."""

    algo = 'none'

    def __init__(self, page, template, salt, force=False):
        """Initializer.

        param page: a page object to be archived
        type page: pywikibot.Page
        param template: a template with configuration settings
        type template: pywikibot.Page
        param salt: salt value
        type salt: str
        param force: override security value
        type force: bool
        """
        self.attributes = OrderedDict([
            ('archive', ['', False]),
            ('algo', ['old(24h)', False]),
            ('counter', ['1', False]),
            ('maxarchivesize', ['200K', False]),
        ])
        self.salt = salt
        self.force = force
        self.site = page.site
        self.tpl = template
        self.timestripper = TimeStripper(site=self.site)
        self.page = DiscussionPage(page, self)
        self.load_config()
        self.comment_params = {
            'from': self.page.title(),
        }
        self.archives = {}
        self.archived_threads = 0
        self.month_num2orig_names = {}
        for n, (_long, _short) in enumerate(self.site.months_names):
            self.month_num2orig_names[n + 1] = {'long': _long, 'short': _short}

    def get_attr(self, attr, default=''):
        """Get an archiver attribute."""
        return self.attributes.get(attr, [default])[0]

    def set_attr(self, attr, value, out=True):
        """Set an archiver attribute."""
        if attr == 'archive':
            value = value.replace('_', ' ')
        self.attributes[attr] = [value, out]

    def saveables(self):
        """Return a list of saveable attributes."""
        return [a for a in self.attributes if self.attributes[a][1]
                and a != 'maxage']

    def attr2text(self):
        """Return a template with archiver saveable attributes."""
        return '{{%s\n%s\n}}' \
               % (self.tpl.title(with_ns=(self.tpl.namespace() != 10)),
                  '\n'.join('|{} = {}'.format(a, self.get_attr(a))
                            for a in self.saveables()))

    def key_ok(self):
        """Return whether key is valid."""
        hexdigest = calc_md5_hexdigest(self.page.title(), self.salt)
        return self.get_attr('key') == hexdigest

    def load_config(self):
        """Load and validate archiver template."""
        pywikibot.output('Looking for: {{%s}} in %s' % (self.tpl.title(),
                                                        self.page))
        for tpl in self.page.templatesWithParams():
            if tpl[0] == pywikibot.Page(self.site, self.tpl.title(), ns=10):
                for param in tpl[1]:
                    item, value = param.split('=', 1)
                    self.set_attr(item.strip(), value.strip())
                break
        else:
            raise MissingConfigError('Missing or malformed template')
        if not self.get_attr('algo', ''):
            raise MissingConfigError('Missing argument "algo" in template')
        if not self.get_attr('archive', ''):
            raise MissingConfigError('Missing argument "archive" in template')

    def get_archive(self, archive, params=None):
        """
        Get the archive for the given page.

        If it doesn't exist yet, create it.
        Also check for security violations.

        @rtype: DiscussionPage
        """
        title = archive.title()
        page_title = self.page.title()
        if not (self.force or title.startswith(page_title + '/')
                or self.key_ok()):
            raise ArchiveSecurityError(
                'Archive page {} does not start with page title ({})!'
                .format(archive, page_title))
        if title not in self.archives:
            self.archives[title] = DiscussionPage(archive, self, params)
        return self.archives[title]

    def feed_archive(self, archive, thread, max_archive_size, params=None):
        """
        Feed the thread to the archive.

        @return: whether the archive is full
        @rtype: bool
        """
        return self.get_archive(archive, params).feed_thread(
            thread, max_archive_size)

    def analyze_page(self):
        """Analyze DiscussionPage."""
        max_arch_size = str2size(self.get_attr('maxarchivesize'))
        arch_counter = int(self.get_attr('counter', '1'))
        oldthreads = self.page.threads
        self.page.threads = []
        whys = set()
        pywikibot.output('Processing {} threads'.format(len(oldthreads)))
        for t in oldthreads:
            if len(oldthreads) - self.archived_threads \
               <= int(self.get_attr('minthreadsleft', 5)):
                self.page.threads.append(t)
                continue  # Because there's too little threads left.
            # TODO: Make an option so that unstamped (unsigned) posts get
            # archived.
            why = t.should_be_archived(self)
            if why:
                archive_pattern = self.get_attr('archive')
                lang = self.site.lang
                params = {
                    'counter': to_local_digits(arch_counter, lang),
                    'year': to_local_digits(t.timestamp.year, lang),
                    'isoyear': to_local_digits(t.timestamp.isocalendar()[0],
                                               lang),
                    'isoweek': to_local_digits(t.timestamp.isocalendar()[1],
                                               lang),
                    'semester': to_local_digits(
                        int(ceil(float(t.timestamp.month) / 6)), lang),
                    'quarter': to_local_digits(
                        int(ceil(float(t.timestamp.month) / 3)), lang),
                    'month': to_local_digits(t.timestamp.month, lang),
                    'monthname': self.month_num2orig_names[
                        t.timestamp.month]['long'],
                    'monthnameshort': self.month_num2orig_names[
                        t.timestamp.month]['short'],
                    'week': to_local_digits(
                        int(time.strftime('%W',
                                          t.timestamp.timetuple())), lang),
                }
                archive_title = archive_pattern % params
                archive_page = pywikibot.Page(self.site, archive_title)
                archive = self.get_archive(archive_page, params)
                new_params = dict(params)
                new_params.update({
                    'counter': to_local_digits(arch_counter + 1, lang),
                })
                new_archive_title = archive_pattern % new_params
                counter_matters = (new_archive_title != archive_title)
                if (counter_matters
                        and arch_counter > 1 and not archive.exists()):
                    # the above may happen because a new year/month etc.
                    # or simply because of the increment
                    new_params.update({
                        'counter': to_local_digits(1, lang),
                    })
                    archive_page = pywikibot.Page(
                        self.site, archive_pattern % new_params)
                    new_archive = self.get_archive(archive_page, new_params)
                    if not new_archive.exists():
                        # reset counter and update vars
                        arch_counter = 1
                        archive = new_archive
                        params = new_params
                if self.feed_archive(archive, t, max_arch_size, params):
                    if counter_matters:
                        arch_counter += 1
                whys.add(why)
                self.archived_threads += 1
            else:
                self.page.threads.append(t)
            self.set_attr('counter', str(arch_counter))
        return whys

    def run(self):
        """Process a single DiscussionPage object."""
        if not self.page.botMayEdit():
            return
        whys = self.analyze_page()
        mintoarchive = int(self.get_attr('minthreadstoarchive', 2))
        if self.archived_threads < mintoarchive:
            # We might not want to archive a measly few threads
            # (lowers edit frequency)
            pywikibot.output('Only {} (< {}) threads are old enough. Skipping'
                             .format(self.archived_threads, mintoarchive))
            return
        if whys:
            # Search for the marker template
            rx = re.compile(r'\{\{%s\s*?\n.*?\n\}\}'
                            % (template_title_regex(self.tpl).pattern),
                            re.DOTALL)
            if not rx.search(self.page.header):
                raise MalformedConfigError(
                    "Couldn't find the template in the header"
                )

            pywikibot.output('Archiving {0} thread(s).'
                             .format(self.archived_threads))
            # Save the archives first (so that bugs don't cause a loss of data)
            for a in sorted(self.archives.keys()):
                self.comment_params['count'] = self.archives[
                    a].archived_threads
                comment = i18n.twtranslate(self.site.code,
                                           'archivebot-archive-summary',
                                           self.comment_params)
                self.archives[a].update(comment)

            # Save the page itself
            self.page.header = rx.sub(self.attr2text(), self.page.header)
            self.comment_params['count'] = self.archived_threads
            comma = self.site.mediawiki_message('comma-separator')
            self.comment_params['archives'] \
                = comma.join(a.title(as_link=True)
                             for a in self.archives.values())
            self.comment_params['why'] = comma.join(whys)
            comment = i18n.twtranslate(self.site.code,
                                       'archivebot-page-summary',
                                       self.comment_params)
            self.page.update(comment)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: unicode
    """
    filename = None
    pagename = None
    namespace = None
    salt = ''
    force = False
    calc = None
    templates = []

    local_args = pywikibot.handle_args(args)
    for arg in local_args:
        option, _, value = arg.partition(':')
        if not option.startswith('-'):
            templates.append(arg)
            continue
        option = option[1:]
        if option in ('file', 'filename'):
            filename = value
        elif option == 'locale':
            # Required for english month names
            locale.setlocale(locale.LC_TIME, value.encode('utf8'))
        elif option == 'timezone':
            os.environ['TZ'] = value.timezone
            # Or use the preset value
            if hasattr(time, 'tzset'):
                time.tzset()
        elif option == 'calc':
            calc = value
        elif option == 'salt':
            salt = value
        elif option == 'force':
            force = True
        elif option == 'page':
            pagename = value
        elif option == 'namespace':
            namespace = value

    site = pywikibot.Site()

    if calc:
        if not salt:
            pywikibot.bot.suggest_help(missing_parameters=['-salt'])
            return False
        page = pywikibot.Page(site, calc)
        if page.exists():
            calc = page.title()
        else:
            pywikibot.output(
                'NOTE: the specified page "{0}" does not (yet) exist.'
                .format(calc))
        pywikibot.output('key = {}'.format(calc_md5_hexdigest(calc, salt)))
        return

    if not templates:
        pywikibot.bot.suggest_help(
            additional_text='No template was specified.')
        return False

    for template_name in templates:
        pagelist = []
        tmpl = pywikibot.Page(site, template_name, ns=10)
        if not filename and not pagename:
            if namespace is not None:
                ns = [str(namespace)]
            else:
                ns = []
            pywikibot.output('Fetching template transclusions...')
            for pg in tmpl.getReferences(only_template_inclusion=True,
                                         follow_redirects=False,
                                         namespaces=ns):
                pagelist.append(pg)
        if filename:
            for pg in open(filename, 'r').readlines():
                pagelist.append(pywikibot.Page(site, pg, ns=10))
        if pagename:
            pagelist.append(pywikibot.Page(site, pagename, ns=3))
        pagelist = sorted(pagelist)
        for pg in iter(pagelist):
            pywikibot.output('Processing {}'.format(pg))
            # Catching exceptions, so that errors in one page do not bail out
            # the entire process
            try:
                archiver = PageArchiver(pg, tmpl, salt, force)
                archiver.run()
            except ArchiveBotSiteConfigError as e:
                # no stack trace for errors originated by pages on-site
                pywikibot.error('Missing or malformed template in page {}: {}'
                                .format(pg, e))
            except Exception:
                pywikibot.error('Error occurred while processing page {}'
                                .format(pg))
                pywikibot.exception(tb=True)


if __name__ == '__main__':
    main()
