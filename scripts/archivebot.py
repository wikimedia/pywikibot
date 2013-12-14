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
                     Default ist old(24h)
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
import os
import re
import time
import locale
import traceback
import string
import urllib
import unicodedata
try:  # Get a constructor for the MD5 hash object
    import hashlib
    new_hash = hashlib.md5
except ImportError:  # Old python?
    import md5
    new_hash = md5.md5

import pywikibot
from pywikibot import i18n, pagegenerators


Site = pywikibot.getSite()
language = Site.language()


def message(key, lang=Site.language()):
    return i18n.twtranslate(lang, key)


class MalformedConfigError(pywikibot.Error):
    """There is an error in the configuration template."""


class MissingConfigError(pywikibot.Error):
    """The config is missing in the header (either it's in one of the threads
    or transcluded from another page).

    """


class AlgorithmError(MalformedConfigError):
    """Invalid specification of archiving algorithm."""


class ArchiveSecurityError(pywikibot.Error):
    """Archive is not a subpage of page being archived and key not specified
    (or incorrect).

    """


def str2time(str):
    """Accepts a string defining a time period:
    7d - 7 days
    36h - 36 hours
    Returns the corresponding time, measured in seconds.

    """
    if str[-1] == 'd':
        return int(str[:-1]) * 24 * 3600
    elif str[-1] == 'h':
        return int(str[:-1]) * 3600
    else:
        return int(str)


def str2size(str):
    """Accepts a string defining a size:
    1337 - 1337 bytes
    150K - 150 kilobytes
    2M - 2 megabytes
    Returns a tuple (size,unit), where size is an integer and unit is
    'B' (bytes) or 'T' (threads).

    """
    if str[-1] in string.digits:  # TODO: de-uglify
        return (int(str), 'B')
    elif str[-1] in ['K', 'k']:
        return (int(str[:-1]) * 1024, 'B')
    elif str[-1] == 'M':
        return (int(str[:-1]) * 1024 * 1024, 'B')
    elif str[-1] == 'T':
        return (int(str[:-1]), 'T')
    else:
        return (int(str[:-1]) * 1024, 'B')


def int2month(num):
    """Returns the locale's full name of month 'num' (1-12)."""
    if hasattr(locale, 'nl_langinfo'):
        return locale.nl_langinfo(locale.MON_1 + num - 1).decode('utf-8')
    Months = ['january', 'february', 'march', 'april', 'may_long', 'june',
              'july', 'august', 'september', 'october', 'november', 'december']
    return Site.mediawiki_message(Months[num - 1])


def int2month_short(num):
    """Returns the locale's abbreviated name of month 'num' (1-12)."""
    if hasattr(locale, 'nl_langinfo'):
        #filter out non-alpha characters
        return ''.join([c for c in
                        locale.nl_langinfo(
                            locale.ABMON_1 + num - 1).decode('utf-8')
                        if c.isalpha()])
    Months = ['jan', 'feb', 'mar', 'apr', 'may', 'jun',
              'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
    return Site.mediawiki_message(Months[num - 1])


def txt2timestamp(txt, format):
    """Attempts to convert the timestamp 'txt' according to given 'format'.
    On success, returns the time tuple; on failure, returns None.

    """
##    print txt, format
    try:
        return time.strptime(txt, format)
    except ValueError:
        try:
            return time.strptime(txt.encode('utf8'), format)
        except:
            pass


def generateTransclusions(Site, template, namespaces=[]):
    pywikibot.output(u'Fetching template transclusions...')
    transclusionPage = pywikibot.Page(Site, template, ns=10)
    gen = pagegenerators.ReferringPageGenerator(transclusionPage,
                                                onlyTemplateInclusion=True)
    if namespaces:
        gen = pagegenerators.NamespaceFilterPageGenerator(gen, namespaces, Site)
    for page in gen:
        yield page


class DiscussionThread(object):
    """An object representing a discussion thread on a page, that is something
    of the form:

    == Title of thread ==

    Thread content here. ~~~~
    :Reply, etc. ~~~~

    """

    def __init__(self, title):
        self.title = title
        self.content = ""
        self.timestamp = None

    def __repr__(self):
        return '%s("%s",%d bytes)' \
               % (self.__class__.__name__, self.title, len(self.content))

    def feedLine(self, line):
        if not self.content and not line:
            return
        self.content += line + '\n'
        #Update timestamp
# nnwiki:
# 19:42, 25 mars 2008 (CET)
# enwiki
# 16:36, 30 March 2008 (UTC)
# huwiki
# 2007. december 8., 13:42 (CET)
        TM = re.search(r'(\d\d):(\d\d), (\d\d?) (\S+) (\d\d\d\d) \(.*?\)', line)
        if not TM:
            TM = re.search(r'(\d\d):(\d\d), (\S+) (\d\d?), (\d\d\d\d) \(.*?\)',
                           line)
        if not TM:
            TM = re.search(r'(\d{4})\. (\S+) (\d\d?)\., (\d\d:\d\d) \(.*?\)',
                           line)
# 18. apr 2006 kl.18:39 (UTC)
# 4. nov 2006 kl. 20:46 (CET)
        if not TM:
            TM = re.search(r'(\d\d?)\. (\S+) (\d\d\d\d) kl\.\W*(\d\d):(\d\d) \(.*?\)',
                           line)
#3. joulukuuta 2008 kello 16.26 (EET)
        if not TM:
            TM = re.search(r'(\d\d?)\. (\S+) (\d\d\d\d) kello \W*(\d\d).(\d\d) \(.*?\)',
                           line)
        if not TM:
# 14:23, 12. Jan. 2009 (UTC)
            pat = re.compile(r'(\d\d):(\d\d), (\d\d?)\. (\S+)\.? (\d\d\d\d) \((?:UTC|CES?T)\)')
            TM = pat.search(line)
# ro.wiki: 4 august 2012 13:01 (EEST)
        if not TM:
            TM = re.search(r'(\d\d?) (\S+) (\d\d\d\d) (\d\d):(\d\d) \(.*?\)',
                           line)
# Japanese: 2012年8月4日 (日) 13:01 (UTC)
        if not TM:
            TM = re.search(re.compile(u'(\d\d\d\d)年(\d\d?)月(\d\d?)日 \(.\) (\d\d):(\d\d) \(.*?\)'),
                           line)
        if TM:
            # Strip away all diacritics in the Mn ('Mark, non-spacing') category
            # NFD decomposition splits combined characters (e.g. 'ä",
            # LATIN SMALL LETTER A WITH DIAERESIS) into two entities:
            # LATIN SMALL LETTER A and COMBINING DIAERESIS. The latter falls
            # in the Mn category and is filtered out, resuling in 'a'.
            _TM = ''.join(c for c in unicodedata.normalize('NFD', TM.group(0))
                          if unicodedata.category(c) != 'Mn')

            TIME = txt2timestamp(_TM, "%d. %b %Y kl. %H:%M (%Z)")
            if not TIME:
                TIME = txt2timestamp(_TM, "%Y. %B %d., %H:%M (%Z)")
            if not TIME:
                TIME = txt2timestamp(_TM, "%d. %b %Y kl.%H:%M (%Z)")
            if not TIME:
                TIME = txt2timestamp(re.sub(' *\([^ ]+\) *', '', _TM),
                                     "%H:%M, %d %B %Y")
            if not TIME:
                TIME = txt2timestamp(_TM, "%H:%M, %d %b %Y (%Z)")
            if not TIME:
                TIME = txt2timestamp(re.sub(' *\([^ ]+\) *', '', _TM),
                                     "%H:%M, %d %b %Y")
            if not TIME:
                TIME = txt2timestamp(_TM, "%H:%M, %b %d %Y (%Z)")
            if not TIME:
                TIME = txt2timestamp(_TM, "%H:%M, %B %d %Y (%Z)")
            if not TIME:
                TIME = txt2timestamp(_TM, "%H:%M, %b %d, %Y (%Z)")
            if not TIME:
                TIME = txt2timestamp(_TM, "%H:%M, %B %d, %Y (%Z)")
            if not TIME:
                TIME = txt2timestamp(_TM, "%d. %Bta %Y kello %H.%M (%Z)")
            if not TIME:
                TIME = txt2timestamp(_TM, "%d %B %Y %H:%M (%Z)")
            if not TIME:
                TIME = txt2timestamp(_TM, "%Y年%B%d日 (%a) %H:%M (%Z)")
            if not TIME:
                TIME = txt2timestamp(re.sub(' *\([^ ]+\) *', '', _TM),
                                     "%H:%M, %d. %b. %Y")
            if TIME:
                self.timestamp = max(self.timestamp, time.mktime(TIME))
##                pywikibot.output(u'Time to be parsed: %s' % TM.group(0))
##                pywikibot.output(u'Parsed time: %s' % TIME)
##                pywikibot.output(u'Newest timestamp in thread: %s' % TIME)

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
            if self.timestamp + maxage < time.time():
                return message('archivebot-older-than') + ' ' + reT.group(1)
        return ''


class DiscussionPage(pywikibot.Page):
    """A class that represents a single discussion page as well as an archive
    page. Feed threads to it and run an update() afterwards.

    """

    def __init__(self, title, archiver, vars=None):
        pywikibot.Page.__init__(self, Site, title)
        self.threads = []
        self.full = False
        self.archiver = archiver
        self.vars = vars
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
                curThread = DiscussionThread(threadHeader.group(1))
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
        return '{{%s\n%s\n}}' % (self.tpl,
                                 '\n'.join(['|%s = %s '
                                            % (a, self.get(a))
                                            for a in self.saveables()]))

    def key_ok(self):
        s = new_hash()
        s.update(self.salt + '\n')
        s.update(self.Page.title().encode('utf8') + '\n')
        return self.get('key') == s.hexdigest()

    def loadConfig(self):
        pywikibot.output(u'Looking for: {{%s}} in %s' % (self.tpl, self.Page))
        found = False
        for tpl in self.Page.templatesWithParams():
            if tpl[0].title() == self.tpl:
                for param in tpl[1]:
                    item, value = param.split('=', 1)
                    self.set(item.strip(), value.strip())
                found = True
                break
        if not found:
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
           and not self.Page.title() + '/' == archive[
               :len(self.Page.title()) + 1] \
           and not self.key_ok():
            raise ArchiveSecurityError
        if not archive in self.archives:
            self.archives[archive] = DiscussionPage(archive, self, vars)
        return self.archives[archive].feedThread(thread, maxArchiveSize)

    def analyzePage(self):
        maxArchSize = str2size(self.get('maxarchivesize'))
        archCounter = int(self.get('counter', '1'))
        oldthreads = self.Page.threads
        self.Page.threads = []
        T = time.mktime(time.gmtime())
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
                TStuple = time.gmtime(t.timestamp)
                vars = {
                    'counter': archCounter,
                    'year': TStuple[0],
                    'month': TStuple[1],
                    'monthname': int2month(TStuple[1]),
                    'monthnameshort': int2month_short(TStuple[1]),
                    'week': int(time.strftime('%W', TStuple)),
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

            #Save the page itself
            rx = re.compile('{{%s\n.*?\n}}' % self.tpl, re.DOTALL)
            self.Page.header = rx.sub(self.attr2text(), self.Page.header)
            self.commentParams['count'] = self.archivedThreads
            self.commentParams['archives'] = ', '.join(
                ['[[%s]]' % a.title() for a in self.archives.values()])
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
        for v in if_arg_value(arg, '-pagename'):
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
