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

Trancluded template may contain the following parameters:

{{TEMPLATE_PAGE
|archive             =
|algo                =
|counter             =
|maxarchivesize      =
|minthreadsleft      =
|minthreadstoarchive =
|archiveheader       =
|key                 =
}}

Meanings of parameters are:

archive              Name of the page to which archived threads will be put.
                     Must be a subpage of the current page. Variables are
                     supported.
algo                 specifies the maximum age of a thread. Must be in the form
                     old(<delay>) where <delay> specifies the age in hours or
                     days like 24h or 5d.
                     Default is old(24h)
counter              The current value of a counter which could be assigned as
                     variable. Will be actualized by bot. Initial value is 1.
maxarchivesize       The maximum archive size before incrementing the counter.
                     Value can be given with appending letter like K or M which
                     indicates KByte or MByte. Default value is 1000M.
minthreadsleft       Minimum number of threads that should be left on a page.
                     Default value is 5.
minthreadstoarchive  The minimum number of threads to archive at once. Default
                     value is 2.
archiveheader        Content that will be put on new archive pages as the
                     header. This parameter supports the use of variables.
                     Default value is {{talkarchive}}
key                  A secret key that (if valid) allows archives to not be
                     subpages of the page being archived.

Variables below can be used in the value for "archive" in the template above:

%(counter)d          the current value of the counter
%(year)d             year of the thread being archived
%(isoyear)d          ISO year of the thread being archived
%(isoweek)d          ISO week number of the thread being archived
%(quarter)d          quarter of the year of the thread being archived
%(month)d            month (as a number 1-12) of the thread being archived
%(monthname)s        English name of the month above
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
# (C) xqt, 2009-2014
# (C) Pywikibot team, 2007-2014
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#
import datetime
import time
import os
import re
import locale
from hashlib import md5
from math import ceil

import pywikibot
from pywikibot import i18n
from pywikibot.textlib import TimeStripper
from pywikibot.textlib import to_local_digits

ZERO = datetime.timedelta(0)


class MalformedConfigError(pywikibot.Error):

    """There is an error in the configuration template."""


class MissingConfigError(pywikibot.Error):

    """
    The config is missing in the header.

    It's in one of the threads or transcluded from another page.
    """


class AlgorithmError(MalformedConfigError):

    """Invalid specification of archiving algorithm."""


class ArchiveSecurityError(pywikibot.Error):

    """
    Page title is not a valid archive of page being archived.

    The page title is neither a subpage of the page being archived,
    nor does it match the key specified in the archive configuration template.
    """


def str2localized_duration(site, string):
    """
    Localise a shorthand duration.

    Translates a duration written in the shorthand notation (ex. "24h", "7d")
    into an expression in the local language of the wiki ("24 hours", "7 days").
    """
    if string[-1] == 'd':
        template = site.mediawiki_message('Days')
    elif string[-1] == 'h':
        template = site.mediawiki_message('Hours')
    if template:
        exp = i18n.translate(site.code, template, int(string[:-1]))
        return to_local_digits(exp.replace('$1', string[:-1]), site.code)
    else:
        return to_local_digits(string, site.code)


def str2time(string):
    """
    Return a timedelta for a shorthand duration.

    Accepts a string defining a time period:
    7d - 7 days
    36h - 36 hours
    Returns the corresponding timedelta object.
    """
    if string.endswith('d'):
        return datetime.timedelta(days=int(string[:-1]))
    elif string.endswith('h'):
        return datetime.timedelta(hours=int(string[:-1]))
    else:
        return datetime.timedelta(seconds=int(string))


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
    val, unit = (int(r.group(1)), r.group(2))
    if unit == 'M':
        val *= 1024
        unit = 'K'
    if unit in ('K', 'k'):
        val *= 1024
    if unit != 'T':
        unit = 'B'
    return val, unit


def generate_transclusions(site, template, namespaces=[]):
    pywikibot.output(u'Fetching template transclusions...')
    transclusion_page = pywikibot.Page(site, template, ns=10)
    return transclusion_page.getReferences(onlyTemplateInclusion=True,
                                           follow_redirects=False,
                                           namespaces=namespaces)


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
    title = tpl_page.title(withNamespace=False)
    if ns.case != 'case-sensitive':
        title = '[%s%s]%s' % (re.escape(title[0].upper()),
                              re.escape(title[0].lower()),
                              re.escape(title[1:]))
    else:
        title = re.escape(title)

    return re.compile(r'(?:(?:%s):)%s%s' % (u'|'.join(ns), marker, title))


class TZoneUTC(datetime.tzinfo):

    """Class building a UTC tzinfo object."""

    def utcoffset(self, dt):  # pylint: disable=unused-argument
        return ZERO

    def tzname(self, dt):  # pylint: disable=unused-argument
        return 'UTC'

    def dst(self, dt):  # pylint: disable=unused-argument
        return ZERO

    def __repr__(self):
        return "%s()" % self.__class__.__name__


class DiscussionThread(object):

    """
    An object representing a discussion thread on a page.

    It represents something that is of the form:

    == Title of thread ==

    Thread content here. ~~~~
    :Reply, etc. ~~~~
    """

    def __init__(self, title, now, timestripper):
        self.title = title
        self.now = now
        self.ts = timestripper
        self.code = self.ts.site.code
        self.content = ""
        self.timestamp = None

    def __repr__(self):
        return '%s("%s",%d bytes)' \
               % (self.__class__.__name__, self.title,
                  len(self.content.encode('utf-8')))

    def feed_line(self, line):
        if not self.content and not line:
            return

        self.content += line + '\n'
        timestamp = self.ts.timestripper(line)

        if not self.timestamp:  # first time
            self.timestamp = timestamp

        if timestamp:
            self.timestamp = max(self.timestamp, timestamp)

    def size(self):
        return len(self.title.encode('utf-8')) + len(
            self.content.encode('utf-8')) + 12

    def to_text(self):
        return u"== %s ==\n\n%s" % (self.title, self.content)

    def should_be_archived(self, archiver):
        algo = archiver.get_attr('algo')
        re_t = re.search(r'^old\((.*)\)$', algo)
        if re_t:
            if not self.timestamp:
                return ''
            # TODO: handle this:
            # return 'unsigned'
            maxage = str2time(re_t.group(1))
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
        super(DiscussionPage, self).__init__(source)
        self.threads = []
        self.full = False
        self.archiver = archiver
        # for testing purposes we allow archiver to be None and we are able
        # to create the a DiscussionPage in this way:
        # >>> import pwb, pywikibot as py
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
        lines = self.get().split('\n')
        found = False  # Reading header
        cur_thread = None
        for line in lines:
            thread_header = re.search('^== *([^=].*?) *== *$', line)
            if thread_header:
                found = True  # Reading threads now
                if cur_thread:
                    self.threads.append(cur_thread)
                cur_thread = DiscussionThread(thread_header.group(1), self.now,
                                              self.timestripper)
            else:
                if found:
                    cur_thread.feed_line(line)
                else:
                    self.header += line + '\n'
        if cur_thread:
            self.threads.append(cur_thread)
        # This extra info is not desirable when run under the unittest
        # framework, which may be run either directly or via setup.py
        if pywikibot.calledModuleName() not in ['archivebot_tests', 'setup']:
            pywikibot.output(u'%d Threads found on %s'
                             % (len(self.threads), self))

    def feed_thread(self, thread, max_archive_size=(250 * 1024, 'B')):
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
        return len(self.header.encode('utf-8')) + sum(t.size()
                                                      for t in self.threads)

    def update(self, summary, sort_threads=False):
        if sort_threads:
            pywikibot.output(u'Sorting threads...')
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

    """A class that encapsulates all archiving methods.

    __init__ expects a pywikibot.Page object.
    Execute by running the .run() method.
    """

    algo = 'none'

    def __init__(self, page, tpl, salt, force=False):
        self.attributes = {
            'algo': ['old(24h)', False],
            'archive': ['', False],
            'maxarchivesize': ['1000M', False],
            'counter': ['1', False],
            'key': ['', False],
        }
        self.salt = salt
        self.force = force
        self.site = page.site
        self.tpl = pywikibot.Page(self.site, tpl)
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
            self.month_num2orig_names[n + 1] = {"long": _long, "short": _short}

    def get_attr(self, attr, default=''):
        return self.attributes.get(attr, [default])[0]

    def set_attr(self, attr, value, out=True):
        if attr == 'archive':
            value = value.replace('_', ' ')
        self.attributes[attr] = [value, out]

    def saveables(self):
        return [a for a in self.attributes if self.attributes[a][1] and
                a != 'maxage']

    def attr2text(self):
        return '{{%s\n%s\n}}' \
               % (self.tpl.title(withNamespace=(self.tpl.namespace() != 10)),
                  '\n'.join('|%s = %s' % (a, self.get_attr(a))
                            for a in self.saveables()))

    def key_ok(self):
        s = md5()
        s.update(self.salt + '\n')
        s.update(self.page.title().encode('utf8') + '\n')
        return self.get_attr('key') == s.hexdigest()

    def load_config(self):
        pywikibot.output(u'Looking for: {{%s}} in %s' % (self.tpl.title(), self.page))
        for tpl in self.page.templatesWithParams():
            if tpl[0] == pywikibot.Page(self.site, self.tpl.title(), ns=10):
                for param in tpl[1]:
                    item, value = param.split('=', 1)
                    self.set_attr(item.strip(), value.strip())
                break
        else:
            raise MissingConfigError(u'Missing or malformed template')
        if not self.get_attr('algo', ''):
            raise MissingConfigError(u'Missing algo')

    def feed_archive(self, archive, thread, max_archive_size, params=None):
        """Feed the thread to one of the archives.

        If it doesn't exist yet, create it.
        If archive name is an empty string (or None),
        discard the thread.
        Also checks for security violations.

        """
        title = archive.title()
        if not title:
            return
        if not self.force \
           and not self.page.title() + '/' == title[:len(self.page.title()) + 1] \
           and not self.key_ok():
            raise ArchiveSecurityError(
                u"Archive page %s does not start with page title (%s)!"
                % (archive, self.page.title()))
        if title not in self.archives:
            self.archives[title] = DiscussionPage(archive, self, params)
        return self.archives[title].feed_thread(thread, max_archive_size)

    def analyze_page(self):
        max_arch_size = str2size(self.get_attr('maxarchivesize'))
        arch_counter = int(self.get_attr('counter', '1'))
        oldthreads = self.page.threads
        self.page.threads = []
        whys = []
        pywikibot.output(u'Processing %d threads' % len(oldthreads))
        for t in oldthreads:
            if len(oldthreads) - self.archived_threads \
               <= int(self.get_attr('minthreadsleft', 5)):
                self.page.threads.append(t)
                continue  # Because there's too little threads left.
            # TODO: Make an option so that unstamped (unsigned) posts get
            # archived.
            why = t.should_be_archived(self)
            if why:
                archive = self.get_attr('archive')
                lang = self.site.lang
                params = {
                    'counter': to_local_digits(arch_counter, lang),
                    'year': to_local_digits(t.timestamp.year, lang),
                    'isoyear': to_local_digits(t.timestamp.isocalendar()[0], lang),
                    'isoweek': to_local_digits(t.timestamp.isocalendar()[1], lang),
                    'quarter': to_local_digits(
                        int(ceil(float(t.timestamp.month) / 3)), lang),
                    'month': to_local_digits(t.timestamp.month, lang),
                    'monthname': self.month_num2orig_names[t.timestamp.month]['long'],
                    'monthnameshort': self.month_num2orig_names[t.timestamp.month]['short'],
                    'week': to_local_digits(
                        int(time.strftime('%W', t.timestamp.timetuple())), lang),
                }
                archive = pywikibot.Page(self.site, archive % params)
                if self.feed_archive(archive, t, max_arch_size, params):
                    arch_counter += 1
                    self.set_attr('counter', str(arch_counter))
                whys.append(why)
                self.archived_threads += 1
            else:
                self.page.threads.append(t)
        return set(whys)

    def run(self):
        if not self.page.botMayEdit():
            return
        whys = self.analyze_page()
        mintoarchive = int(self.get_attr('minthreadstoarchive', 2))
        if self.archived_threads < mintoarchive:
            # We might not want to archive a measly few threads
            # (lowers edit frequency)
            pywikibot.output(u'Only %d (< %d) threads are old enough. Skipping'
                             % (self.archived_threads, mintoarchive))
            return
        if whys:
            # Search for the marker template
            rx = re.compile(r'\{\{%s\s*?\n.*?\n\}\}'
                            % (template_title_regex(self.tpl).pattern), re.DOTALL)
            if not rx.search(self.page.header):
                pywikibot.error("Couldn't find the template in the header")
                return

            pywikibot.output(u'Archiving %d thread(s).' % self.archived_threads)
            # Save the archives first (so that bugs don't cause a loss of data)
            for a in sorted(self.archives.keys()):
                self.comment_params['count'] = self.archives[a].archived_threads
                comment = i18n.twntranslate(self.site.code,
                                            'archivebot-archive-summary',
                                            self.comment_params)
                self.archives[a].update(comment)

            # Save the page itself
            self.page.header = rx.sub(self.attr2text(), self.page.header)
            self.comment_params['count'] = self.archived_threads
            comma = self.site.mediawiki_message('comma-separator')
            self.comment_params['archives'] \
                = comma.join(a.title(asLink=True)
                             for a in self.archives.values())
            self.comment_params['why'] = comma.join(whys)
            comment = i18n.twntranslate(self.site.code,
                                        'archivebot-page-summary',
                                        self.comment_params)
            self.page.update(comment)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    filename = None
    pagename = None
    namespace = None
    salt = None
    force = False
    calc = None
    args = []

    def if_arg_value(arg, name):
        if arg.startswith(name):
            yield arg[len(name) + 1:]

    for arg in pywikibot.handle_args(args):
        for v in if_arg_value(arg, '-file'):
            filename = v
        for v in if_arg_value(arg, '-locale'):
            # Required for english month names
            locale.setlocale(locale.LC_TIME, v.encode('utf8'))
        for v in if_arg_value(arg, '-timezone'):
            os.environ['TZ'] = v.timezone
            # Or use the preset value
            if hasattr(time, 'tzset'):
                time.tzset()
        for v in if_arg_value(arg, '-calc'):
            calc = v
        for v in if_arg_value(arg, '-salt'):
            salt = v
        for v in if_arg_value(arg, '-force'):
            force = True
        for v in if_arg_value(arg, '-filename'):
            filename = v
        for v in if_arg_value(arg, '-page'):
            pagename = v
        for v in if_arg_value(arg, '-namespace'):
            namespace = v
        if not arg.startswith('-'):
            args.append(arg)

    site = pywikibot.Site()

    if calc:
        if not salt:
            pywikibot.showHelp()
            pywikibot.output(
                'NOTE: you must specify a salt to calculate a key using '
                '-salt:SALT option.')
            return
        page = pywikibot.Page(site, calc)
        if page.exists():
            calc = page.title()
        else:
            pywikibot.output(u'NOTE: the specified page "%s" does not (yet) exist.' % calc)
        s = md5()
        s.update(salt + '\n')
        s.update(calc + '\n')
        pywikibot.output(u'key = ' + s.hexdigest())
        return

    if not salt:
        salt = ''

    if not args:
        pywikibot.showHelp()
        pywikibot.output(u'NOTE: you must specify a template to run the bot.')
        return

    for a in args:
        pagelist = []
        a = pywikibot.Page(site, a, ns=10).title()
        if not filename and not pagename:
            if namespace is not None:
                ns = [str(namespace)]
            else:
                ns = []
            for pg in generate_transclusions(site, a, ns):
                pagelist.append(pg)
        if filename:
            for pg in open(filename, 'r').readlines():
                pagelist.append(pywikibot.Page(site, pg, ns=10))
        if pagename:
            pagelist.append(pywikibot.Page(site, pagename, ns=3))
        pagelist = sorted(pagelist)
        for pg in iter(pagelist):
            pywikibot.output(u'Processing %s' % pg)
            # Catching exceptions, so that errors in one page do not bail out
            # the entire process
            try:
                archiver = PageArchiver(pg, a, salt, force)
                archiver.run()
                time.sleep(10)
            except Exception:
                pywikibot.error(u'Error occurred while processing page %s' % pg)
                pywikibot.exception(tb=True)


if __name__ == '__main__':
    main()
