#!/usr/bin/env python3
"""archivebot.py - Discussion page archiving bot.

usage:

    python pwb.py archivebot [OPTIONS] [TEMPLATE_PAGE]

Multiple TEMPLATE_PAGE templates can be given in a single command. The
default is ``User:MiszaBot/config``. The bot examines backlinks (i.e.
Special:WhatLinksHere) to all given TEMPLATE_PAGE templates. It then
processes those pages (unless a specific page is specified via options)
and archives old discussions.

This is done by splitting each page into threads and scanning them for
timestamps. Threads older than a configured threshold are moved to an
archive page. The archive page name can be based on the thread's title,
or include a counter that increments when the archive reaches a
configured size.

The transcluded configuration template may include the following
parameters:

.. code:: wikitext

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

**Parameters meanings:**

archive
    Name of the archive page where threads will be moved. Must be a
    subpage of the current page, unless a valid ``key`` is provided.
    Supports variables.

algo
    Specifies the maximum age of a thread using the syntax:
    :code:`old(<delay>)`, where ``<delay>`` can be in seconds (s), hours (h),
    days (d), weeks (w), or years (y). For example: ``24h`` or ``5d``.
    Default: :code:`old(24h)`.

counter
    The current value of the archive counter used in archive page naming.
    Will be updated automatically by the bot. Default: 1.

maxarchivesize
    The maximum size of an archive page before incrementing the counter.
    A suffix of ``K`` or ``M`` may be used for kilobytes or megabytes.
    Default: ``200K``.

minthreadsleft
    Minimum number of threads that must remain on the main page after
    archiving. Default: 5.

minthreadstoarchive
    Minimum number of threads that must be eligible for archiving before
    any are moved. Default: 2.

archiveheader
    Content placed at the top of each newly created archive page.
    Supports variables. If not set explicitly, a localized default will
    be retrieved from Wikidata using known archive header templates. If
    no localized template is found, the fallback ``{{talkarchive}}`` is
    used.

    .. note::
       If no ``archiveheader`` is set and no localized template can be
       retrieved from Wikidata, the fallback ``{{talkarchive}}`` is used.
       This generic fallback may not be appropriate for all wikis, so it
       is recommended to set ``archiveheader`` explicitly in such cases.

key
    A secret key that, if valid, allows archive pages to exist outside
    of the subpage structure of the current page.

Variables below can be used in the value of the "archive" parameter in
the template above. Numbers are represented as **ASCII** digits by
default; alternatively, **localized** digits may be used. Localized
digits are only available for a few site languages. Please refer to
:attr:`NON_ASCII_DIGITS <userinterfaces.transliteration.NON_ASCII_DIGITS>`
to check if a localized version is available.

.. list-table::
   :header-rows: 1

   * - ascii
     - localized
     - Description
   * - %(counter)d
     - %(localcounter)s
     - the current value of the counter
   * - %(year)d
     - %(localyear)s
     - year of the thread being archived
   * - %(isoyear)d
     - %(localisoyear)s
     - ISO year of the thread being archived
   * - %(isoweek)d
     - %(localisoweek)s
     - ISO week number of the thread being archived
   * - %(semester)d
     - %(localsemester)s
     - semester term of the year of the thread being archived
   * - %(quarter)d
     - %(localquarter)s
     - quarter of the year of the thread being archived
   * - %(month)d
     - %(localmonth)s
     - month (as a number 1-12) of the thread being archived
   * - %(monthname)s
     -
     - localized name of the month above
   * - %(monthnameshort)s
     -
     - first three letters of the name above
   * - %(week)d
     - %(localweek)s
     - week number of the thread being archived

The ISO calendar defines the first week of the year as the week
containing the first Thursday of the Gregorian calendar year. This means:

- If January 1st falls on a Monday, Tuesday, Wednesday, or Thursday, then
  the week containing January 1st is considered the first week of the year.

- If January 1st falls on a Friday, Saturday, or Sunday, then the first ISO
  week starts on the following Monday.

Because of this, up to three days at the start of January can belong to the
last week of the previous year according to the ISO calendar.

.. seealso:: Python :python:`datetime.date.isocalendar
   <library/datetime.html#datetime.date.isocalendar>`,
   https://webspace.science.uu.nl/~gent0113/calendar/isocalendar.htm

Options (may be omitted):

-help           Show this help message and exit.

-calc:PAGE      Calculate key for PAGE and exit.

-file:FILE      Load list of pages from FILE.

-force          Override security options.

-locale:LOCALE  Switch to locale LOCALE.

-namespace:NS   Only archive pages from the given namespace.

-page:PAGE      Archive a single PAGE. Default namespace is a user talk
                page.

-salt:SALT      Specify salt.

-keep           Preserve thread order in archive even if threads are
                archived later.

-sort           Sort archive by timestamp; should not be used with `keep`.

-async          Run the bot in parallel tasks.

Version historty:

.. versionchanged:: 7.6
   Localized variables for the ``archive`` parameter are supported.
   ``User:MiszaBot/config`` is the default template. The ``-keep`` option
   was added.

.. versionchanged:: 7.7
   ``-sort`` and ``-async`` options were added.

.. versionchanged:: 8.2
   KeyboardInterrupt support added when using the ``-async`` option.

.. versionchanged:: 10.3
   If ``archiveheader`` is not set, the bot now attempts to retrieve a
   localized template from Wikidata (based on known item IDs). If none is
   found, ``{{talkarchive}}`` is used as fallback.

.. versionchanged:: 11.0
   The ``-namespace`` option is now respected by ``-page`` option.
"""
#
# (C) Pywikibot team, 2006-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import datetime
import locale
import os
import re
import signal
import threading
import time
from collections import OrderedDict, defaultdict
from contextlib import nullcontext
from hashlib import md5
from math import ceil
from textwrap import fill
from typing import Any
from warnings import warn

import pywikibot
from pywikibot import i18n
from pywikibot.backports import pairwise
from pywikibot.exceptions import Error, NoPageError
from pywikibot.textlib import (
    TimeStripper,
    case_escape,
    extract_sections,
    findmarker,
    to_local_digits,
)
from pywikibot.time import MW_KEYS, parse_duration, str2timedelta
from pywikibot.tools.threading import BoundedPoolExecutor


ARCHIVE_HEADER = 'Q6068612', 'Q6723402'


class ArchiveBotSiteConfigError(Error):

    """There is an error originated by archivebot's on-site configuration."""


class MalformedConfigError(ArchiveBotSiteConfigError):

    """There is an error in the configuration template."""


class MissingConfigError(ArchiveBotSiteConfigError):

    """The config is missing in the header.

    It's in one of the threads or transcluded from another page.
    """


class ArchiveSecurityError(ArchiveBotSiteConfigError):

    """Page title is not a valid archive of page being archived.

    The page title is neither a subpage of the page being archived, nor
    does it match the key specified in the archive configuration
    template.
    """


def str2localized_duration(site, string: str) -> str:
    """Localise a shorthand duration.

    Translates a duration written in the shorthand notation (ex. "24h",
    "7d") into an expression in the local wiki language ("24 hours", "7
    days").
    """
    try:
        key, duration = parse_duration(string)
    except ValueError as e:
        raise MalformedConfigError(e) from None
    template = site.mediawiki_message(MW_KEYS[key])
    if template:
        # replace plural variants
        exp = i18n.translate(site.code, template, {'$1': duration})
        return exp.replace('$1', to_local_digits(duration, site.code))
    return to_local_digits(string, site.code)


def str2size(string: str) -> tuple[int, str]:
    """Return a size for a shorthand size.

    Accepts a string defining a size::

      1337 - 1337 bytes
      150K - 150 kilobytes
      2M - 2 megabytes

    :Returns: a tuple ``(size, unit)``, where ``size`` is an integer and
        unit is ``'B'`` (bytes) or ``'T'`` (threads).
    """
    match = re.fullmatch(r'(\d{1,3}(?: \d{3})+|\d+) *([BkKMT]?)', string)
    if not match:
        raise MalformedConfigError(f"Couldn't parse size: {string}")
    val, unit = (int(match[1].replace(' ', '')), match[2])
    if unit == 'M':
        val *= 1024
        unit = 'K'
    if unit in ('K', 'k'):
        val *= 1024
    if unit != 'T':
        unit = 'B'
    return val, unit


def template_title_regex(tpl_page: pywikibot.Page) -> re.Pattern:
    """Return a regex that matches to variations of the template title.

    It supports the transcluding variant as well as localized namespaces
    and case-insensitivity depending on the namespace.

    :param tpl_page: The template page
    :type tpl_page: pywikibot.page.Page
    """
    ns = tpl_page.site.namespaces[tpl_page.namespace()]
    marker = '?' if ns.id == 10 else ''
    title = tpl_page.title(with_ns=False)
    title = case_escape(ns.case, title)

    return re.compile(r'(?:(?:{}):){}{}'.format('|'.join(ns), marker, title))


def calc_md5_hexdigest(txt, salt) -> str:
    """Return md5 hexdigest computed from text and salt."""
    s = md5()
    s.update(salt.encode('utf-8'))
    s.update(b'\n')
    s.update(txt.encode('utf8'))
    s.update(b'\n')
    return s.hexdigest()


class DiscussionThread:

    """An object representing a discussion thread on a page.

    It represents something that is of the form::

        == Title of thread ==

        Thread content here. ~~~~
        :Reply, etc. ~~~~
    """

    def __init__(self, title: str, timestripper: TimeStripper) -> None:
        """Initializer."""
        self.title = title
        self.ts = timestripper
        self.code = self.ts.site.code
        self.content = ''
        self.timestamp = None

    def __repr__(self) -> str:
        """Return a string representation."""
        return '{}("{}",{} bytes)'.format(self.__class__.__name__, self.title,
                                          len(self.content.encode('utf-8')))

    def feed_line(self, line: str) -> None:
        """Add a line to the content and find the newest timestamp."""
        if not self.content and not line:
            return

        self.content += line + '\n'
        timestamp = self.ts.timestripper(line)

        if not self.timestamp:  # first time
            self.timestamp = timestamp

        if timestamp:
            self.timestamp = max(self.timestamp, timestamp)

    def size(self) -> int:
        """Return size of discussion thread.

        Note that the result is NOT equal to that of
        len(self.to_text()). This method counts bytes, rather than
        codepoints (characters). This corresponds to MediaWiki's
        definition of page size.
        """
        return len(self.title.encode('utf-8')) + len(
            self.content.encode('utf-8')) + 12

    def to_text(self) -> str:
        """Return wikitext discussion thread."""
        return f'== {self.title} ==\n\n{self.content}'


class DiscussionPage(pywikibot.Page):

    """A class that represents a single page of discussion threads.

    Feed threads to it and run an update() afterwards.
    """

    def __init__(self, source, archiver, params=None, keep=False) -> None:
        """Initializer."""
        super().__init__(source)
        self.archiver = archiver
        # for testing purposes we allow archiver to be None and we are able
        # to create the a DiscussionPage in this way:
        # >>> import pywikibot as py
        # >>> from scripts.archivebot import DiscussionPage
        # >>> d = DiscussionPage(py.Page(py.Site(), <talk page name>), None)
        self.params = params
        self.keep = keep
        self.full = False
        self.archived_threads = 0
        if archiver is None:
            self.timestripper = TimeStripper(self.site)
        else:
            self.timestripper = self.archiver.timestripper

    def __getattr__(self, name):
        """Lazy load page if archives, header or threads attribute is missing.

        .. versionadded:: 8.1
        """
        if name in ('archives', 'header', 'threads'):
            self.load_page()
        return self.__getattribute__(name)

    @staticmethod
    def max(
        ts1: pywikibot.Timestamp | None,
        ts2: pywikibot.Timestamp | None
    ) -> pywikibot.Timestamp | None:
        """Calculate the maximum of two timestamps but allow None as value.

        .. versionadded:: 7.6
        """
        if ts1 is None:
            return ts2
        if ts2 is None:
            return ts1
        return max(ts1, ts2)

    def get_header_template(self) -> str:
        """Return a localized archive header template from Wikibase.

        This method looks up a localized archive header template by
        checking a predefined list of Wikidata item IDs that correspond
        to commonly used archive header templates. It returns the first
        matching template found on the local wiki via the site’s
        Wikibase repository.

        If no such localized template is found, it falls back to the
        default ``{{talkarchive}}`` template.

        .. versionadded:: 10.2

        .. versionchanged:: 10.3
           Returns ``{{talkarchive}}`` by default if no localized
           template is found.

        .. caution::
           The default should be avoided where possible. It is
           recommended to explicitly set the ``archiveheader`` parameter
           in the bot's configuration template instead.
        """
        for item in ARCHIVE_HEADER:
            tpl = self.site.page_from_repository(item)
            if tpl:
                return f'{{{{{tpl.title(with_ns=False)}}}}}'

        return '{{talkarchive}}'

    def load_page(self) -> None:
        """Load the page to be archived and break it up into threads.

        .. versionchanged:: 7.6
           If `-keep` option is given run through all threads and set
           the current timestamp to the previous if the current is lower.
        .. versionchanged:: 7.7
           Load unsigned threads using timestamp of the next thread.
        """
        self.header = ''
        self.threads = []
        self.archives = {}
        try:
            text = self.get()
        except NoPageError:
            self.header = self.archiver.get_attr('archiveheader',
                                                 self.get_header_template())
            if self.params:
                self.header = self.header % self.params
            return

        # Exclude unsupported headings (h1, h3, etc):
        # adding the marker will make them ignored by extract_sections()
        marker = findmarker(text)
        text = re.sub(r'^((=|={3,})[^=])', marker + r'\1', text, flags=re.M)

        # Find threads, avoid archiving categories or interwiki
        header, threads, footer = extract_sections(text, self.site)
        header = header.replace(marker, '')
        if header and footer:
            self.header = f'{header.rstrip()}\n\n{footer}\n\n'
        else:
            self.header = header + footer

        for thread in threads:
            cur_thread = DiscussionThread(thread.heading, self.timestripper)
            # remove heading line
            _, *lines = thread.content.replace(marker, '').splitlines()
            for line in lines:
                cur_thread.feed_line(line)
            self.threads.append(cur_thread)

        # add latter timestamp to predecessor if it is None
        for last, prev in pairwise(reversed(self.threads)):
            if not prev.timestamp:
                prev.timestamp = last.timestamp

        if self.keep:
            # set the timestamp to the previous if the current is lower
            for first, second in pairwise(self.threads):
                second.timestamp = self.max(first.timestamp, second.timestamp)

        # This extra info is not desirable when run under the unittest
        # framework, which may be run either directly or via setup.py
        if pywikibot.calledModuleName() not in ('archivebot_tests', 'pytest',
                                                'setup', 'unittest'):
            self.archiver.info(
                f'{len(self.threads)} thread(s) found on {self}')

    def is_full(self, max_archive_size: tuple[int, str]) -> bool:
        """Check whether archive size exceeded."""
        if self.full:
            return True

        size, unit = max_archive_size
        self_size = self.size()
        if (unit == 'B' and self_size >= size
            or unit == 'T' and len(self.threads) >= size
                or self_size > self.archiver.maxsize):
            self.full = True  # note: this is one-way flag
        return self.full

    def feed_thread(self, thread: DiscussionThread,
                    max_archive_size: tuple[int, str]) -> bool:
        """Append a new thread to the archive."""
        self.threads.append(thread)
        self.archived_threads += 1
        return self.is_full(max_archive_size)

    def size(self) -> int:
        """Return size of talk page threads.

        Note that this method counts bytes, rather than codepoints
        (characters). This corresponds to MediaWiki's definition
        of page size.

        .. versionchanged:: 7.6
           return 0 if archive page neither exists nor has threads
           (:phab:`T313886`).
        """
        if not (self.exists() or self.threads):
            return 0

        return len(self.header.encode('utf-8')) + sum(t.size()
                                                      for t in self.threads)

    def update(self,
               summary, *,
               sort_threads: bool = False,
               asynchronous: bool = False) -> None:
        """Recombine threads and save page.

        .. versionchanged:: 10.0
           the *asynchronous* parameter was added.
        """
        if sort_threads:
            self.archiver.info('Sorting threads...')
            self.threads.sort(key=lambda t: t.timestamp)
        newtext = self.header.strip() + '\n\n'  # Fix trailing newlines
        for t in self.threads:
            newtext += t.to_text()
        if self.full:
            summary += ' ' + i18n.twtranslate(self.site.code,
                                              'archivebot-archive-full')
        self.text = newtext
        self.save(summary, asynchronous=asynchronous)


class PageArchiver:

    """A class that encapsulates all archiving methods."""

    algo = 'none'

    def __init__(self, page, template, salt: str, force: bool = False,
                 keep: bool = False, sort: bool = False,
                 asynchronous: bool = False) -> None:
        """Initializer.

        .. versionchanged:: 10.0
           The *asynchronous* parameter was added.

        :param page: a page object to be archived
        :type page: :py:obj:`pywikibot.Page`
        :param template: a template with configuration settings
        :type template: :py:obj:`pywikibot.Page`
        :param salt: salt value
        :param force: override security value
        :param asynchronous: asynchronous processing activated
        """
        self.attributes = OrderedDict([
            ('archive', ['', False]),
            ('algo', ['old(24h)', False]),
            ('counter', ['1', False]),
            ('maxarchivesize', ['200K', False]),
        ])
        self.salt = salt
        self.force = force
        self.sort = sort
        self.site = page.site
        self.tpl = template
        self.timestripper = TimeStripper(site=self.site)

        # read maxarticlesize
        # keep a gap of 1 KB not to block later changes
        self.maxsize = self.site.siteinfo['maxarticlesize'] - 1024

        self.page = DiscussionPage(page, self, keep=keep)
        self.comment_params = {
            'from': self.page.title(),
        }
        self.now = datetime.datetime.now(datetime.timezone.utc)
        self.archives = {}
        self.archived_threads = 0
        self.month_num2orig_names = {}
        for n, (long, short) in enumerate(self.site.months_names, start=1):
            self.month_num2orig_names[n] = {'long': long, 'short': short}
        self.asynchronous = asynchronous
        self.output = []
        self.load_config()

    def info(self, msg: str = '') -> None:
        """Forward text to cache if asynchronous is activated.

        .. versionadded:: 10.0
        """
        if self.asynchronous:
            self.output.append(msg)
        else:
            pywikibot.info(msg)

    def flush(self) -> None:
        """Flush the cache.

        .. versionadded:: 10.0
        """
        pywikibot.info('\n'.join(self.output))
        self.output.clear()

    def get_attr(self, attr, default='') -> Any:
        """Get an archiver attribute."""
        return self.attributes.get(attr, [default])[0]

    def set_attr(self, attr, value, out: bool = True) -> None:
        """Set an archiver attribute."""
        if attr == 'archive':
            value = value.replace('_', ' ')
        elif attr == 'maxarchivesize':
            size, unit = str2size(value)
            if unit == 'B' and size > self.maxsize:
                value = f'{self.maxsize // 1024} K'
                warn('Siteinfo "maxarticlesize" exceeded. Decreasing '
                     '"maxarchivesize" to ' + value,
                     ResourceWarning, stacklevel=2)
        self.attributes[attr] = [value, out]

    def saveables(self) -> list[str]:
        """Return a list of saveable attributes."""
        return [a for a in self.attributes if self.attributes[a][1]
                and a != 'maxage']

    def attr2text(self) -> str:
        """Return a template with archiver saveable attributes."""
        return '{{%s\n%s\n}}' \
               % (self.tpl.title(with_ns=self.tpl.namespace() != 10),
                  '\n'.join(f'|{a} = {self.get_attr(a)}'
                            for a in self.saveables()))

    def key_ok(self) -> bool:
        """Return whether key is valid."""
        hexdigest = calc_md5_hexdigest(self.page.title(), self.salt)
        return self.get_attr('key') == hexdigest

    def load_config(self) -> None:
        """Load and validate archiver template."""
        for tpl, params in self.page.raw_extracted_templates:
            try:  # Check tpl name before comparing; it might be invalid.
                tpl_page = pywikibot.Page(self.site, tpl, ns=10)
                tpl_page.title()
            except Error:
                continue

            if tpl_page == self.tpl:
                for item, value in params.items():
                    self.set_attr(item, value)
                break
        else:
            raise MissingConfigError('Missing or malformed template')

        for field in ('algo', 'archive'):
            if not self.get_attr(field, ''):
                raise MissingConfigError(
                    f'Missing argument {field!r} in template')

    def should_archive_thread(self, thread: DiscussionThread
                              ) -> tuple[str, str] | None:
        """Check whether a thread has to be archived.

        :return: the archivation reason as a tuple of localization args
        """
        # Archived by timestamp
        algo = self.get_attr('algo')
        re_t = re.fullmatch(r'old\((.*)\)', algo)
        if re_t:
            if not thread.timestamp:
                return None
            # TODO: handle unsigned
            try:
                maxage = str2timedelta(re_t[1], thread.timestamp)
            except ValueError as e:
                raise MalformedConfigError(e) from None
            if self.now - thread.timestamp > maxage:
                duration = str2localized_duration(self.site, re_t[1])
                return ('duration', duration)
        # TODO: handle marked with template
        return None

    def get_archive_page(self, title: str, params=None) -> DiscussionPage:
        """Return the page for archiving.

        If it doesn't exist yet, create and cache it. Also check for
        security violations.
        """
        if title not in self.archives:
            page_title = self.page.title()
            archive_link = pywikibot.Link(title, self.site)
            if not (title.startswith(page_title + '/') or self.force
                    or self.key_ok()):
                raise ArchiveSecurityError(
                    f'Archive page {archive_link} does not start with page '
                    f'title ({page_title})!'
                )
            self.archives[title] = DiscussionPage(archive_link, self, params)

        return self.archives[title]

    def get_params(self, timestamp, counter: int) -> dict:
        """Make params for archiving template."""
        lang = self.site.lang
        params = {
            'counter': counter,
            'year': timestamp.year,
            'isoyear': timestamp.isocalendar()[0],
            'isoweek': timestamp.isocalendar()[1],
            'semester': int(ceil(timestamp.month / 6)),
            'quarter': int(ceil(timestamp.month / 3)),
            'month': timestamp.month,
            'week': int(time.strftime('%W', timestamp.timetuple())),
        }
        params.update({'local' + key: to_local_digits(value, lang)
                       for key, value in params.items()})
        monthnames = self.month_num2orig_names[timestamp.month]
        params['monthname'] = monthnames['long']
        params['monthnameshort'] = monthnames['short']
        return params

    def preload_pages(self, counter: int, thread, pattern) -> None:
        """Preload pages if counter matters."""
        if counter < 25:
            return

        for c in range(counter):
            params = self.get_params(thread.timestamp, c + 1)
            self.get_archive_page(pattern % params, params)
        list(self.site.preloadpages(self.archives.values()))

    def analyze_page(self) -> set[tuple[str, str]]:
        """Analyze DiscussionPage."""
        max_size = self.get_attr('maxarchivesize')
        max_arch_size = str2size(max_size)
        if not max_arch_size[0]:
            raise MalformedConfigError(f'invalid maxarchivesize {max_size!r}')

        counter = int(self.get_attr('counter', '1'))
        pattern = self.get_attr('archive')

        keep_threads = []
        threads_per_archive = defaultdict(list)
        whys = set()
        fields = self.get_params(self.now, 0).keys()  # dummy parameters
        regex = re.compile(r'%(\((?:{})\))d'.format('|'.join(fields)))
        stringpattern = regex.sub(r'%\1s', pattern)
        for i, thread in enumerate(self.page.threads):
            # TODO: Make an option so that unstamped (unsigned) posts get
            # archived.
            why = self.should_archive_thread(thread)
            if not why or why[0] != 'duration':
                keep_threads.append(i)
                continue
            params = self.get_params(thread.timestamp, counter)
            # this is actually just a dummy key to group the threads by
            # "era" regardless of the counter and deal with it later
            try:
                key = pattern % params
            except TypeError as e:
                if 'a real number is required' not in str(e):
                    raise MalformedConfigError(e)

                pywikibot.error(e)
                self.info(
                    fill('<<lightblue>>Use string format field like '
                         '%(localfield)s instead of %(localfield)d. '
                         'Trying to solve it...'))
                self.info()
                pattern = stringpattern
                key = pattern % params

            threads_per_archive[key].append((i, thread))
            whys.add(why)  # FIXME: we don't know if we ever archive anything

        params = self.get_params(self.now, counter)
        aux_params = self.get_params(self.now, counter + 1)
        counter_matters = (pattern % params) != (pattern % aux_params)

        # we need to start with the oldest archive since that is
        # the one the saved counter applies to, so sort the groups
        # by the oldest timestamp
        groups = sorted(threads_per_archive.values(),
                        key=lambda group: min(t.timestamp for _, t in group))

        era_change = False
        for group in groups:
            # We will reset counter IFF:
            # 1. it matters (AND)
            # 2. "era" (year, month, etc.) changes (AND)
            # 3. there is something to put to the new archive.
            counter_found = False
            for i, thread in group:
                threads_left = len(self.page.threads) - self.archived_threads
                if threads_left <= int(self.get_attr('minthreadsleft', 5)):
                    keep_threads.append(i)
                    continue  # Because there's too little threads left.

                if era_change:
                    era_change = False
                    counter = 1

                params = self.get_params(thread.timestamp, counter)
                archive = self.get_archive_page(pattern % params, params)

                if counter_matters:

                    self.preload_pages(counter, thread, pattern)
                    while not counter_found and counter > 1 \
                            and not archive.exists():
                        # This may happen when either:
                        # 1. a previous version of the bot run and reset
                        #    the counter without archiving anything
                        #    (number #3 above)
                        # 2. era changed between runs.
                        # Decrease the counter.
                        counter -= 1
                        params = self.get_params(thread.timestamp, counter)
                        archive = self.get_archive_page(
                            pattern % params, params)

                    # There are only non existing pages found by countdown
                    counter_found = True

                    while archive.is_full(max_arch_size):
                        counter += 1
                        params = self.get_params(thread.timestamp, counter)
                        archive = self.get_archive_page(
                            pattern % params, params)

                archive.feed_thread(thread, max_arch_size)
                self.archived_threads += 1

            if counter_matters:
                era_change = True

        if self.archived_threads:
            self.page.threads = [self.page.threads[i]
                                 for i in sorted(keep_threads)]
            self.set_attr('counter', str(counter))
            return whys
        return set()

    def run(self) -> None:
        """Process a single DiscussionPage object.

        .. versionchanged:: 10.0
           save the talk page in asynchronous mode if ``-async`` option
           was given but archive pages are saved in synchronous mode.
        """
        if not self.page.botMayEdit():
            return

        whys = self.analyze_page()
        mintoarchive = int(self.get_attr('minthreadstoarchive', 2))
        if self.archived_threads < mintoarchive:
            # We might not want to archive a measly few threads
            # (lowers edit frequency)
            var = 'threads are' if self.archived_threads > 1 else 'thread is'
            if self.archived_threads:
                self.info(f'Only {self.archived_threads} {var} old enough, '
                          f'{mintoarchive} required. Skipping')
            else:
                self.info('No thread is old enough. Skipping')
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

            self.info(f'Archiving {self.archived_threads} thread(s).')
            # Save the archives first (so that bugs don't cause a loss of data)
            for archive in self.archives.values():
                count = archive.archived_threads
                if not count:
                    continue
                self.comment_params['count'] = count
                comment = i18n.twtranslate(self.site.code,
                                           'archivebot-archive-summary',
                                           self.comment_params)
                archive.update(comment, sort_threads=self.sort)

            # Save the page itself
            self.page.header = rx.sub(self.attr2text(), self.page.header)
            self.comment_params['count'] = self.archived_threads
            comma = self.site.mediawiki_message('comma-separator')
            self.comment_params['archives'] = comma.join(
                a.title(as_link=True) for a in self.archives.values()
                if a.archived_threads > 0
            )
            # Find out the reasons and return them localized
            translated_whys = set()
            for why, arg in whys:
                # Archived by timestamp
                if why == 'duration':
                    translated_whys.add(
                        i18n.twtranslate(self.site.code,
                                         'archivebot-older-than',
                                         {'duration': arg,
                                          'count': self.archived_threads}))
                # TODO: handle unsigned or archived by template
            self.comment_params['why'] = comma.join(translated_whys)
            comment = i18n.twtranslate(self.site.code,
                                       'archivebot-page-summary',
                                       self.comment_params)
            self.page.update(comment, asynchronous=self.asynchronous)


def process_page(page, *args: Any, asynchronous: bool = False) -> bool:
    """Call PageArchiver for a single page.

    :return: Return True to continue with the next page, False to break
        the loop.

    .. versionadded:: 7.6
    .. versionchanged:: 7.7
       pass an unspecified number of arguments to the bot using ``*args``
    .. versionchanged:: 10.0
       *asynchronous* parameter was added.
    """
    global outlock
    if not page.exists():
        pywikibot.info(f'{page} does not exist, skipping...')
        return True

    # Catching exceptions, so that errors in one page do not bail out
    # the entire process
    try:
        archiver = PageArchiver(page, *args, asynchronous)
        archiver.info(f'\n\n>>> <<lightpurple>>{page}<<default>> <<<')
        archiver.run()
    except ArchiveBotSiteConfigError as e:
        # no stack trace for errors originated by pages on-site
        pywikibot.error(f'Missing or malformed template in page {page}: {e}')
    except Exception:
        pywikibot.exception(f'Error occurred while processing page {page}')
    except KeyboardInterrupt:
        pywikibot.info('\nUser quit bot run...')
        return False
    else:
        with outlock:
            archiver.flush()
    return True


def show_md5_key(calc, salt, site) -> bool:
    """Show calculated MD5 hexdigest."""
    if not calc:
        return False

    if not salt:
        pywikibot.bot.suggest_help(missing_parameters=['-salt'])
    else:
        page = pywikibot.Page(site, calc)
        if page.exists():
            calc = page.title()
        else:
            pywikibot.info(
                f'NOTE: the specified page "{calc}" does not (yet) exist.')
        pywikibot.info(f'key = {calc_md5_hexdigest(calc, salt)}')
    return True


def main(*args: str) -> None:
    """Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
    """
    def signal_handler(signum, frame) -> None:
        pywikibot.info('\n<<lightyellow>>User quit bot run...')
        exiting.set()

    global outlock
    exiting = threading.Event()
    outlock = threading.Lock()
    filename = None
    pagename = None
    namespace = None
    salt = ''
    force = False
    calc = None
    keep = False
    sort = False
    asynchronous = False
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
            namespace = int(value)
        elif option == 'keep':
            keep = True
        elif option == 'sort':
            sort = True
        elif option == 'async':
            asynchronous = True

    site = pywikibot.Site()

    if show_md5_key(calc, salt, site):
        return

    if not templates:
        templates = ['User:MiszaBot/config']
        pywikibot.info('No template was specified, using default '
                       f'{{{{{templates[0]}}}}}.')

    if asynchronous:
        signal.signal(signal.SIGINT, signal_handler)
        context = BoundedPoolExecutor('ThreadPoolExecutor')
    else:
        context = nullcontext()

    for template_name in templates:
        tmpl = pywikibot.Page(site, template_name, ns=10)
        if filename:
            with open(filename) as f:
                gen = [pywikibot.Page(site, line, ns=10) for line in f]
        elif pagename:
            gen = [pywikibot.Page(site, pagename, ns=namespace or 3)]
        else:

            ns = [str(namespace)] if namespace is not None else []
            pywikibot.info(
                f'Fetching {template_name} template transclusions...')
            gen = tmpl.getReferences(only_template_inclusion=True,
                                     follow_redirects=False,
                                     namespaces=ns,
                                     content=True)

        botargs = tmpl, salt, force, keep, sort
        botkwargs = {'asynchronous': asynchronous}
        with context as executor:
            for pg in gen:
                if asynchronous:
                    executor.submit(process_page, pg, *botargs, **botkwargs)

                    if exiting.is_set():
                        pywikibot.info(
                            '<<lightyellow>>Canceling pending Futures...')
                        executor.shutdown(cancel_futures=True)
                        break

                elif not process_page(pg, *botargs, **botkwargs):
                    break


if __name__ == '__main__':
    start = datetime.datetime.now()
    main()
    pywikibot.info('\nExecution time: '
                   f'{(datetime.datetime.now() - start).seconds} seconds')
