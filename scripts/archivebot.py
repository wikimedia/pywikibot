#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
archivebot.py - discussion page archiving bot.

usage:

    python pwb.py archivebot [OPTIONS] TEMPLATE_PAGE

Bot examines backlinks (Special:WhatLinksHere) to TEMPLATE_PAGE.
Then goes through all pages (unless a specific page specified using options)
and archives old discussions. This is done by breaking a page into threads,
then scanning each thread for timestamps. Threads older than a specified
treshold are then moved to another page (the archive), which can be named
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
# (C) xqt, 2009-2012
# (C) Pywikibot team, 2007-2013
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#
import pywikibot
from pywikibot import i18n, pagegenerators
from pywikibot.textlib import tzoneFixedOffset, TimeStripper
import datetime
import time
import os
import re
import locale
import traceback


ZERO = datetime.timedelta(0)

Site = pywikibot.getSite()

try:  # Get a constructor for the MD5 hash object
    import hashlib
    new_hash = hashlib.md5
except ImportError:  # Old python?
    import md5
    new_hash = md5.md5

language = Site.language()


def message(key, lang=Site.language()):
    return i18n.twtranslate(lang, key)


class MalformedConfigError(pywikibot.Error):
    """There is an error in the configuration template."""


class MissingConfigError(pywikibot.Error):
    """The config is missing in the header (either it's in one of the threads
    or transcluded from another page)."""


class AlgorithmError(MalformedConfigError):
    """Invalid specification of archiving algorithm."""


class ArchiveSecurityError(pywikibot.Error):
    """Archive is not a subpage of page being archived and key not specified
    (or incorrect)."""


def str2time(str):
    """Accepts a string defining a time period:
    7d - 7 days
    36h - 36 hours
    Returns the corresponding timedelta object."""
    if str[-1] == 'd':
        return datetime.timedelta(days=int(str[:-1]))
    elif str[-1] == 'h':
        return datetime.timedelta(hours=int(str[:-1]))
    else:
        return datetime.timedelta(seconds=int(str))


def str2size(str):
    """Accepts a string defining a size:
    1337 - 1337 bytes
    150K - 150 kilobytes
    2M - 2 megabytes
    Returns a tuple (size,unit), where size is an integer and unit is
    'B' (bytes) or 'T' (threads)."""
    if str[-1].isdigit():  # TODO: de-uglify
        return (int(str), 'B')
    elif str[-1] in ['K', 'k']:
        return (int(str[:-1]) * 1024, 'B')
    elif str[-1] == 'M':
        return (int(str[:-1]) * 1024 * 1024, 'B')
    elif str[-1] == 'T':
        return (int(str[:-1]), 'T')
    else:
        return (int(str[:-1]) * 1024, 'B')


def generateTransclusions(Site, template, namespaces=[]):
    pywikibot.output(u'Fetching template transclusions...')
    transclusionPage = pywikibot.Page(Site, template, ns=10)
    gen = pagegenerators.ReferringPageGenerator(transclusionPage,
                                                onlyTemplateInclusion=True)
    if namespaces:
        gen = pagegenerators.NamespaceFilterPageGenerator(gen, namespaces, Site)
    for page in gen:
        yield page


class tzoneUTC(datetime.tzinfo):
    """
    Class building a UTC tzinfo object
    """

    def utcoffset(self, dt):
        return ZERO

    def tzname(self, dt):
        return 'UTC'

    def dst(self, dt):
        return ZERO

    def __repr__(self):
        return "%s()" % self.__class__.__name__


class DiscussionThread(object):
    """An object representing a discussion thread on a page, that is something of the form:

    == Title of thread ==

    Thread content here. ~~~~
    :Reply, etc. ~~~~
    """

    def __init__(self, title, now):
        self.title = title
        self.now = now
        self.content = ""
        self.ts = TimeStripper(site=Site)
        self.timestamp = None

    def __repr__(self):
        return '%s("%s",%d bytes)' \
               % (self.__class__.__name__, self.title, len(self.content))

    def feedLine(self, line):
        if not self.content and not line:
            return

        self.content += line + '\n'

        timestamp = self.ts.timestripper(line)

        if not self.timestamp:  # first time
            self.timestamp = timestamp

        if timestamp:
            self.timestamp = max(self.timestamp, timestamp)

    def size(self):
        return len(self.title) + len(self.content) + 12

    def toText(self):
        return "== " + self.title + ' ==\n\n' + self.content

    def shouldBeArchived(self, Archiver):
        algo = Archiver.get('algo')
        reT = re.search(r'^old\((.*)\)$', algo)
        if reT:
            if not self.timestamp:
                return ''
            #TODO: handle this:
                #return 'unsigned'
            maxage = str2time(reT.group(1))
            if self.now - self.timestamp > maxage:
                return message('archivebot-older-than') + ' ' + reT.group(1)
        return ''


class DiscussionPage(pywikibot.Page):
    """A class that represents a single discussion page as well as an archive
    page. Feed threads to it and run an update() afterwards."""

    def __init__(self, title, archiver, vars=None):
        pywikibot.Page.__init__(self, Site, title)
        self.threads = []
        self.full = False
        self.archiver = archiver
        self.vars = vars
        self.now = datetime.datetime.utcnow().replace(tzinfo=tzoneUTC())

        try:
            self.loadPage()
        except pywikibot.NoPage:
            self.header = archiver.get('archiveheader',
                                       message('archivebot-archiveheader'))
            if self.vars:
                self.header = self.header % self.vars

    def loadPage(self):
        """Loads the page to be archived and breaks it up into threads."""
        self.header = ''
        self.threads = []
        self.archives = {}
        self.archivedThreads = 0
        lines = self.get().split('\n')
        found = False  # Reading header
        curThread = None
        for line in lines:
            threadHeader = re.search('^== *([^=].*?) *== *$', line)
            if threadHeader:
                found = True  # Reading threads now
                if curThread:
                    self.threads.append(curThread)
                curThread = DiscussionThread(threadHeader.group(1), self.now)
            else:
                if found:
                    curThread.feedLine(line)
                else:
                    self.header += line + '\n'
        if curThread:
            self.threads.append(curThread)
        pywikibot.output(u'%d Threads found on %s' % (len(self.threads), self))

    def feedThread(self, thread, maxArchiveSize=(250 * 1024, 'B')):
        self.threads.append(thread)
        self.archivedThreads += 1
        if maxArchiveSize[1] == 'B':
            if self.size() >= maxArchiveSize[0]:
                self.full = True
        elif maxArchiveSize[1] == 'T':
            if len(self.threads) >= maxArchiveSize[0]:
                self.full = True
        return self.full

    def size(self):
        return len(self.header) + sum([t.size() for t in self.threads])

    def update(self, summary, sortThreads=False):
        if sortThreads:
            pywikibot.output(u'Sorting threads...')
            self.threads.sort(key=lambda t: t.timestamp)
        newtext = re.sub('\n*$', '\n\n', self.header)  # Fix trailing newlines
        for t in self.threads:
            newtext += t.toText()
        if self.full:
            summary += ' ' + message('archivebot-archive-full')
        self.put(newtext, comment=summary)


class PageArchiver(object):
    """A class that encapsulates all archiving methods.
    __init__ expects a pywikibot.Page object.
    Execute by running the .run() method."""

    algo = 'none'

    def __init__(self, Page, tpl, salt, force=False):
        self.attributes = {
            'algo': ['old(24h)', False],
            'archive': ['', False],
            'maxarchivesize': ['1000M', False],
            'counter': ['1', False],
            'key': ['', False],
        }
        self.tpl = tpl
        self.salt = salt
        self.force = force
        self.Page = DiscussionPage(Page.title(), self)
        self.loadConfig()
        self.commentParams = {
            'from': self.Page.title(),
        }
        self.archives = {}
        self.archivedThreads = 0
        self.monthNum2origNames = {}
        for n, (_long, _short) in enumerate(Site.months_names):
            self.monthNum2origNames[n + 1] = {"long": _long, "short": _short}

    def get(self, attr, default=''):
        return self.attributes.get(attr, [default])[0]

    def set(self, attr, value, out=True):
        if attr == 'archive':
            value = value.replace('_', ' ')
        self.attributes[attr] = [value, out]

    def saveables(self):
        return [a for a in self.attributes if self.attributes[a][1]
                and a != 'maxage']

    def attr2text(self):
        return '{{%s\n%s\n}}' \
               % (self.tpl,
                  '\n'.join(['|%s = %s' % (a, self.get(a))
                             for a in self.saveables()]))

    def key_ok(self):
        s = new_hash()
        s.update(self.salt + '\n')
        s.update(self.Page.title().encode('utf8') + '\n')
        return self.get('key') == s.hexdigest()

    def loadConfig(self):
        pywikibot.output(u'Looking for: {{%s}} in %s' % (self.tpl, self.Page))
        for tpl in self.Page.templatesWithParams():
            if tpl[0] == pywikibot.Page(Site, self.tpl, ns=10):
                for param in tpl[1]:
                    item, value = param.split('=', 1)
                    self.set(item.strip(), value.strip())
                break
        else:
            raise MissingConfigError(u'Missing or malformed template')
        if not self.get('algo', ''):
            raise MissingConfigError(u'Missing algo')

    def feedArchive(self, archive, thread, maxArchiveSize, vars=None):
        """Feed the thread to one of the archives.
        If it doesn't exist yet, create it.
        If archive name is an empty string (or None),
        discard the thread (/dev/null).
        Also checks for security violations."""
        if not archive:
            return
        if not self.force \
           and not self.Page.title() + '/' == archive[:len(self.Page.title()) + 1] \
           and not self.key_ok():
            raise ArchiveSecurityError("Archive page %r does not start with page title (%s)!" % (archive, self.Page.title()))
        if not archive in self.archives:
            self.archives[archive] = DiscussionPage(archive, self, vars)
        return self.archives[archive].feedThread(thread, maxArchiveSize)

    def analyzePage(self):
        maxArchSize = str2size(self.get('maxarchivesize'))
        archCounter = int(self.get('counter', '1'))
        oldthreads = self.Page.threads
        self.Page.threads = []
        whys = []
        pywikibot.output(u'Processing %d threads' % len(oldthreads))
        for t in oldthreads:
            if len(oldthreads) - self.archivedThreads \
               <= int(self.get('minthreadsleft', 5)):
                self.Page.threads.append(t)
                continue  # Because there's too little threads left.
            # TODO: Make an option so that unstamped (unsigned) posts get
            # archived.
            why = t.shouldBeArchived(self)
            if why:
                archive = self.get('archive')
                vars = {
                    'counter': archCounter,
                    'year': t.timestamp.year,
                    'month': t.timestamp.month,
                    'monthname': self.monthNum2origNames[t.timestamp.month]['long'],
                    'monthnameshort': self.monthNum2origNames[t.timestamp.month]['short'],
                    'week': int(time.strftime('%W', t.timestamp.timetuple())),
                }
                archive = pywikibot.Page(Site, archive % vars).title()
                if self.feedArchive(archive, t, maxArchSize, vars):
                    archCounter += 1
                    self.set('counter', str(archCounter))
                whys.append(why)
                self.archivedThreads += 1
            else:
                self.Page.threads.append(t)
        return set(whys)

    def run(self):
        if not self.Page.botMayEdit():
            return
        whys = self.analyzePage()
        if self.archivedThreads < int(self.get('minthreadstoarchive', 2)):
            # We might not want to archive a measly few threads
            # (lowers edit frequency)
            pywikibot.output(u'There are only %d Threads. Skipping'
                             % self.archivedThreads)
            return
        if whys:
            pywikibot.output(u'Archiving %d thread(s).' % self.archivedThreads)
            # Save the archives first (so that bugs don't cause a loss of data)
            for a in sorted(self.archives.keys()):
                self.commentParams['count'] = self.archives[a].archivedThreads
                comment = i18n.twntranslate(language,
                                            'archivebot-archive-summary',
                                            self.commentParams)
                self.archives[a].update(comment)

            # Save the page itself
            rx = re.compile('{{' + self.tpl + '\n.*?\n}}', re.DOTALL)
            self.Page.header = rx.sub(self.attr2text(), self.Page.header)
            self.commentParams['count'] = self.archivedThreads
            self.commentParams['archives'] \
                = ', '.join(['[[' + a.title() + ']]' for a in self.archives.values()])
            if not self.commentParams['archives']:
                self.commentParams['archives'] = '/dev/null'
            self.commentParams['why'] = ', '.join(whys)
            comment = i18n.twntranslate(language,
                                        'archivebot-page-summary',
                                        self.commentParams)
            self.Page.update(comment)


def main():
    global Site, language

    import sys

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

    for arg in pywikibot.handleArgs(*sys.argv):
        for v in if_arg_value(arg, '-file'):
            filename = v
        for v in if_arg_value(arg, '-locale'):
            #Required for english month names
            locale.setlocale(locale.LC_TIME, v.encode('utf8'))
        for v in if_arg_value(arg, '-timezone'):
            os.environ['TZ'] = v.timezone
            #Or use the preset value
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

    if calc:
        if not salt:
            parser.error('Note: you must specify a salt to calculate a key')
        s = new_hash()
        s.update(salt + '\n')
        s.update(calc + '\n')
        pywikibot.output(u'key = ' + s.hexdigest())
        return

    if not salt:
        salt = ''

    Site = pywikibot.getSite()
    language = Site.language()

    if not args or len(args) <= 1:
        pywikibot.output(u'NOTE: you must specify a template to run the bot')
        pywikibot.showHelp('archivebot')
        return

    for a in args[1:]:
        pagelist = []
        a = a.decode('utf8')
        if not filename and not pagename:
            if namespace is not None:
                ns = [str(namespace)]
            else:
                ns = []
            for pg in generateTransclusions(Site, a, ns):
                pagelist.append(pg)
        if filename:
            for pg in file(filename, 'r').readlines():
                pagelist.append(pywikibot.Page(Site, pg, ns=10))
        if pagename:
            pagelist.append(pywikibot.Page(Site, pagename,
                                           ns=3))
        pagelist = sorted(pagelist)
        for pg in iter(pagelist):
            pywikibot.output(u'Processing %s' % pg)
            # Catching exceptions, so that errors in one page do not bail out
            # the entire process
            try:
                Archiver = PageArchiver(pg, a, salt, force)
                Archiver.run()
                time.sleep(10)
            except:
                pywikibot.output(u'Error occured while processing page %s' % pg)
                traceback.print_exc()

if __name__ == '__main__':
    try:
        main()
    finally:
        pywikibot.stopme()
