"""Time handling module."""
#
# (C) Pywikibot team, 2009-2022
#
# Distributed under the terms of the MIT license.
#
import datetime
import re
from typing import Type, Union

from pywikibot.tools import classproperty

__all__ = ['Timestamp']


class Timestamp(datetime.datetime):

    """Class for handling MediaWiki timestamps.

    This inherits from datetime.datetime, so it can use all of the methods
    and operations of a datetime object. To ensure that the results of any
    operation are also a Timestamp object, be sure to use only Timestamp
    objects (and datetime.timedeltas) in any operation.

    Use Timestamp.fromISOformat() and Timestamp.fromtimestampformat() to
    create Timestamp objects from MediaWiki string formats.
    As these constructors are typically used to create objects using data
    passed provided by site and page methods, some of which return a Timestamp
    when previously they returned a MediaWiki string representation, these
    methods also accept a Timestamp object, in which case they return a clone.

    Alternatively, Timestamp.set_timestamp() can create Timestamp objects from
    Timestamp, datetime.datetime object, or strings compliant with ISO8601,
    MW, or POSIX formats.

    Use Site.server_time() for the current time; this is more reliable
    than using Timestamp.utcnow().
    """

    mediawikiTSFormat = '%Y%m%d%H%M%S'  # noqa: N815
    _ISO8601Format_new = '{0:+05d}-{1:02d}-{2:02d}T{3:02d}:{4:02d}:{5:02d}Z'

    @classmethod
    def set_timestamp(cls: Type['Timestamp'],
                      ts: Union[str, datetime.datetime, 'Timestamp']
                      ) -> 'Timestamp':
        """Set Timestamp from input object.

        ts is converted to a datetime naive object representing UTC time.
        String shall be compliant with:
        - Mediwiki timestamp format: YYYYMMDDHHMMSS
        - ISO8601 format: YYYY-MM-DD[T ]HH:MM:SS[Z|±HH[MM[SS[.ffffff]]]]
        - POSIX format: seconds from Unix epoch S{1,13}[.ffffff]]

        :param ts: Timestamp, datetime.datetime or str
        :return: Timestamp object
        :raises ValuError: conversion failed
        """
        if isinstance(ts, cls):
            return ts
        if isinstance(ts, datetime.datetime):
            return cls._from_datetime(ts)
        if isinstance(ts, str):
            return cls._from_string(ts)

    @staticmethod
    def _from_datetime(dt: datetime.datetime) -> 'Timestamp':
        """Convert a datetime.datetime timestamp to a Timestamp object."""
        return Timestamp(dt.year, dt.month, dt.day, dt.hour,
                         dt.minute, dt.second, dt.microsecond,
                         dt.tzinfo)

    @classmethod
    def _from_mw(cls: Type['Timestamp'], timestr: str) -> 'Timestamp':
        """Convert a string in MW format to a Timestamp object.

        Mediwiki timestamp format: YYYYMMDDHHMMSS
        """
        RE_MW = r'\d{14}$'  # noqa: N806
        m = re.match(RE_MW, timestr)

        if not m:
            msg = "time data '{timestr}' does not match MW format."
            raise ValueError(msg.format(timestr=timestr))

        return cls.strptime(timestr, cls.mediawikiTSFormat)

    @classmethod
    def _from_iso8601(cls: Type['Timestamp'], timestr: str) -> 'Timestamp':
        """Convert a string in ISO8601 format to a Timestamp object.

        ISO8601 format:
        - YYYY-MM-DD[T ]HH:MM:SS[[.,]ffffff][Z|±HH[MM[SS[.ffffff]]]]
        """
        RE_ISO8601 = (r'(?:\d{4}-\d{2}-\d{2})(?P<sep>[T ])'  # noqa: N806
                      r'(?:\d{2}:\d{2}:\d{2})(?P<u>[.,]\d{1,6})?'
                      r'(?P<tz>Z|[+\-]\d{2}:?\d{,2})?$'
                      )
        m = re.match(RE_ISO8601, timestr)

        if not m:
            msg = "time data '{timestr}' does not match ISO8601 format."
            raise ValueError(msg.format(timestr=timestr))

        strpfmt = '%Y-%m-%d{sep}%H:%M:%S'.format(sep=m.group('sep'))
        strpstr = timestr[:19]

        if m.group('u'):
            strpfmt += '.%f'
            strpstr += m.group('u').replace(',', '.')  # .ljust(7, '0')

        if m.group('tz'):
            if m.group('tz') == 'Z':
                strpfmt += 'Z'
                strpstr += 'Z'
            else:
                strpfmt += '%z'
                # strptime wants HHMM, without ':'
                strpstr += (m.group('tz').replace(':', '')).ljust(5, '0')

        ts = cls.strptime(strpstr, strpfmt)
        if ts.tzinfo is not None:
            ts = ts.astimezone(datetime.timezone.utc).replace(tzinfo=None)
            # why pytest in py35/py37 fails without this?
            ts = cls._from_datetime(ts)

        return ts

    @classmethod
    def _from_posix(cls: Type['Timestamp'], timestr: str) -> 'Timestamp':
        """Convert a string in POSIX format to a Timestamp object.

        POSIX format: SECONDS[.ffffff]]
        """
        RE_POSIX = r'(?P<S>-?\d{1,13})(?:\.(?P<u>\d{1,6}))?$'  # noqa: N806
        m = re.match(RE_POSIX, timestr)

        if not m:
            msg = "time data '{timestr}' does not match POSIX format."
            raise ValueError(msg.format(timestr=timestr))

        sec = int(m.group('S'))
        usec = m.group('u')
        usec = int(usec.ljust(6, '0')) if usec else 0
        if sec < 0 and usec > 0:
            sec = sec - 1
            usec = 1000000 - usec

        ts = (cls(1970, 1, 1)
              + datetime.timedelta(seconds=sec, microseconds=usec))
        return ts

    @classmethod
    def _from_string(cls: Type['Timestamp'], timestr: str) -> 'Timestamp':
        """Convert a string to a Timestamp object."""
        handlers = [
            cls._from_mw,
            cls._from_iso8601,
            cls._from_posix,
        ]

        for handler in handlers:
            try:
                return handler(timestr)
            except ValueError:
                continue

        msg = "time data '{timestr}' does not match any format."
        raise ValueError(msg.format(timestr=timestr))

    def clone(self) -> datetime.datetime:
        """Clone this instance."""
        return self.replace(microsecond=self.microsecond)

    @classproperty
    def ISO8601Format(cls: Type['Timestamp']) -> str:  # noqa: N802
        """ISO8601 format string class property for compatibility purpose."""
        return cls._ISO8601Format()

    @classmethod
    def _ISO8601Format(cls: Type['Timestamp'],  # noqa: N802
                       sep: str = 'T') -> str:
        """ISO8601 format string.

        :param sep: one-character separator, placed between the date and time
        :return: ISO8601 format string
        """
        assert len(sep) == 1
        return '%Y-%m-%d{}%H:%M:%SZ'.format(sep)

    @classmethod
    def fromISOformat(cls: Type['Timestamp'],  # noqa: N802
                      ts: Union[str, 'Timestamp'],
                      sep: str = 'T') -> 'Timestamp':
        """Convert an ISO 8601 timestamp to a Timestamp object.

        :param ts: ISO 8601 timestamp or a Timestamp object already
        :param sep: one-character separator, placed between the date and time
        :return: Timestamp object
        """
        # If inadvertently passed a Timestamp object, use replace()
        # to create a clone.
        if isinstance(ts, cls):
            return ts.clone()
        _ts = '{pre}{sep}{post}'.format(pre=ts[:10], sep=sep, post=ts[11:])
        return cls._from_iso8601(_ts)

    @classmethod
    def fromtimestampformat(cls: Type['Timestamp'], ts: Union[str, 'Timestamp']
                            ) -> 'Timestamp':
        """Convert a MediaWiki internal timestamp to a Timestamp object."""
        # If inadvertently passed a Timestamp object, use replace()
        # to create a clone.
        if isinstance(ts, cls):
            return ts.clone()
        if len(ts) == 8:  # year, month and day are given only
            ts += '000000'
        return cls._from_mw(ts)

    def isoformat(self, sep: str = 'T') -> str:  # type: ignore[override]
        """
        Convert object to an ISO 8601 timestamp accepted by MediaWiki.

        datetime.datetime.isoformat does not postfix the ISO formatted date
        with a 'Z' unless a timezone is included, which causes MediaWiki
        ~1.19 and earlier to fail.
        """
        return self.strftime(self._ISO8601Format(sep))

    def totimestampformat(self) -> str:
        """Convert object to a MediaWiki internal timestamp."""
        return self.strftime(self.mediawikiTSFormat)

    def posix_timestamp(self) -> float:
        """
        Convert object to a POSIX timestamp.

        See Note in datetime.timestamp().
        """
        return self.replace(tzinfo=datetime.timezone.utc).timestamp()

    def posix_timestamp_format(self) -> str:
        """Convert object to a POSIX timestamp format."""
        return '{ts:.6f}'.format(ts=self.posix_timestamp())

    def __str__(self) -> str:
        """Return a string format recognized by the API."""
        return self.isoformat()

    def __add__(self, other: datetime.timedelta) -> 'Timestamp':
        """Perform addition, returning a Timestamp instead of datetime."""
        newdt = super().__add__(other)
        if isinstance(newdt, datetime.datetime):
            return self._from_datetime(newdt)
        return newdt

    def __sub__(self, other: datetime.timedelta  # type: ignore[override]
                ) -> 'Timestamp':
        """Perform subtraction, returning a Timestamp instead of datetime."""
        newdt = super().__sub__(other)
        if isinstance(newdt, datetime.datetime):
            return self._from_datetime(newdt)
        return newdt
#!/usr/bin/python3
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

.. seealso:: Python :python:`datetime.date.isocalendar
   <library/datetime.html#datetime.date.isocalendar>`,
   https://webspace.science.uu.nl/~gent0113/calendar/isocalendar.htm

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
# (C) Pywikibot team, 2006-2022
#
# Distributed under the terms of the MIT license.
#
import datetime
import locale
import math
import os
import re
import time
import types
from collections import OrderedDict, defaultdict
from hashlib import md5
from math import ceil
from typing import Any, Optional, Pattern
from warnings import warn

import pywikibot
from pywikibot import i18n
from pywikibot.backports import List, Set, Tuple
from pywikibot.date import apply_month_delta
from pywikibot.exceptions import Error, NoPageError
from pywikibot.textlib import (
    TimeStripper,
    case_escape,
    extract_sections,
    findmarker,
    to_local_digits,
)


ShouldArchive = Tuple[str, str]
Size = Tuple[int, str]

ZERO = datetime.timedelta(0)

MW_KEYS = types.MappingProxyType({
    's': 'seconds',
    'h': 'hours',
    'd': 'days',
    'w': 'weeks',
    'y': 'years',
    # 'months' and 'minutes' were removed because confusion outweighs merit
})


class ArchiveBotSiteConfigError(Error):

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


def str2localized_duration(site, string: str) -> str:
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
    return to_local_digits(string, site.code)


def str2time(string: str, timestamp=None) -> datetime.timedelta:
    """
    Return a timedelta for a shorthand duration.

    :param string: a string defining a time period:

    Examples::

        300s - 300 seconds
        36h - 36 hours
        7d - 7 days
        2w - 2 weeks (14 days)
        1y - 1 year

    :param timestamp: a timestamp to calculate a more accurate duration offset
        used by years
    :type timestamp: datetime.datetime
    :return: the corresponding timedelta object
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
            'Unrecognized parameter in template: {}'.format(string))

    if timestamp:
        return apply_month_delta(
            timestamp.date(), month_delta=duration) - timestamp.date()
    return datetime.timedelta(days=days)


def checkstr(string: str) -> Tuple[str, str]:
    """
    Return the key and duration extracted from the string.

    :param string: a string defining a time period

    Examples::

        300s - 300 seconds
        36h - 36 hours
        7d - 7 days
        2w - 2 weeks (14 days)
        1y - 1 year

    :return: key and duration extracted form the string
    """
    if len(string) < 2:
        raise MalformedConfigError('Time period should be a numeric value '
                                   'followed by its qualifier')

    key, duration = string[-1], string[:-1]

    if key not in MW_KEYS:
        raise MalformedConfigError('Time period qualifier is unrecognized: {}'
                                   .format(string))
    if not duration.isdigit():
        raise MalformedConfigError("Time period's duration should be "
                                   'numeric: {}'.format(string))

    return key, duration


def str2size(string: str) -> Size:
    """
    Return a size for a shorthand size.

    Accepts a string defining a size::

      1337 - 1337 bytes
      150K - 150 kilobytes
      2M - 2 megabytes

    :Returns: a tuple ``(size, unit)``, where ``size`` is an integer and
        unit is ``'B'`` (bytes) or ``'T'`` (threads).
    """
    match = re.fullmatch(r'(\d{1,3}(?: \d{3})+|\d+) *([BkKMT]?)', string)
    if not match:
        raise MalformedConfigError("Couldn't parse size: {}".format(string))
    val, unit = (int(match.group(1).replace(' ', '')), match.group(2))
    if unit == 'M':
        val *= 1024
        unit = 'K'
    if unit in ('K', 'k'):
        val *= 1024
    if unit != 'T':
        unit = 'B'
    return val, unit


def template_title_regex(tpl_page: pywikibot.Page) -> Pattern:
    """
    Return a regex that matches to variations of the template title.

    It supports the transcluding variant as well as localized namespaces and
    case-insensitivity depending on the namespace.

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


class TZoneUTC(datetime.tzinfo):

    """Class building a UTC tzinfo object."""

    def utcoffset(self, dt) -> datetime.timedelta:
        """Subclass implementation, return timedelta(0)."""
        return ZERO

    def tzname(self, dt) -> str:
        """Subclass implementation."""
        return 'UTC'

    def dst(self, dt) -> datetime.timedelta:
        """Subclass implementation, return timedelta(0)."""
        return ZERO

    def __repr__(self) -> str:
        """Return a string representation."""
        return '{}()'.format(self.__class__.__name__)


class DiscussionThread:

    """
    An object representing a discussion thread on a page.

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
        """
        Return size of discussion thread.

        Note that the result is NOT equal to that of
        len(self.to_text()). This method counts bytes, rather than
        codepoints (characters). This corresponds to MediaWiki's
        definition of page size.
        """
        return len(self.title.encode('utf-8')) + len(
            self.content.encode('utf-8')) + 12

    def to_text(self) -> str:
        """Return wikitext discussion thread."""
        return '== {} ==\n\n{}'.format(self.title, self.content)


class DiscussionPage(pywikibot.Page):

    """
    A class that represents a single page of discussion threads.

    Feed threads to it and run an update() afterwards.
    """

    def __init__(self, source, archiver, params=None) -> None:
        """Initializer."""
        super().__init__(source)
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
        try:
            self.load_page()
        except NoPageError:
            self.header = archiver.get_attr('archiveheader',
                                            i18n.twtranslate(
                                                self.site.code,
                                                'archivebot-archiveheader'))
            if self.params:
                self.header = self.header % self.params

    def load_page(self) -> None:
        """Load the page to be archived and break it up into threads."""
        self.header = ''
        self.threads = []
        self.archives = {}
        self.archived_threads = 0

        # Exclude unsupported headings (h1, h3, etc):
        # adding the marker will make them ignored by extract_sections()
        text = self.get()
        marker = findmarker(text)
        text = re.sub(r'^((=|={3,})[^=])', marker + r'\1', text, flags=re.M)

        # Find threads, avoid archiving categories or interwiki
        header, threads, footer = extract_sections(text, self.site)
        header = header.replace(marker, '')
        if header and footer:
            self.header = '\n\n'.join((header.rstrip(), footer, ''))
        else:
            self.header = header + footer
        for thread_heading, thread_content in threads:
            cur_thread = DiscussionThread(thread_heading.strip('= '),
                                          self.timestripper)
            # remove heading line
            _, *lines = thread_content.replace(marker, '').splitlines()
            for line in lines:
                cur_thread.feed_line(line)
            self.threads.append(cur_thread)

        # This extra info is not desirable when run under the unittest
        # framework, which may be run either directly or via setup.py
        if pywikibot.calledModuleName() not in ['archivebot_tests', 'setup']:
            pywikibot.output('{} thread(s) found on {}'
                             .format(len(self.threads), self))

    def is_full(self, max_archive_size: Size) -> bool:
        """Check whether archive size exceeded."""
        size, unit = max_archive_size
        if (self.size() > self.archiver.maxsize
            or unit == 'B' and self.size() >= size
                or unit == 'T' and len(self.threads) >= size):
            self.full = True  # xxx: this is one-way flag
        return self.full

    def feed_thread(self, thread: DiscussionThread,
                    max_archive_size: Size) -> bool:
        """Append a new thread to the archive."""
        self.threads.append(thread)
        self.archived_threads += 1
        return self.is_full(max_archive_size)

    def size(self) -> int:
        """
        Return size of talk page threads.

        Note that this method counts bytes, rather than codepoints
        (characters). This corresponds to MediaWiki's definition
        of page size.
        """
        return len(self.header.encode('utf-8')) + sum(t.size()
                                                      for t in self.threads)

    def update(self, summary, sort_threads: bool = False) -> None:
        """Recombine threads and save page."""
        if sort_threads:
            pywikibot.output('Sorting threads...')
            self.threads.sort(key=lambda t: t.timestamp)
        newtext = self.header.strip() + '\n\n'  # Fix trailing newlines
        for t in self.threads:
            newtext += t.to_text()
        if self.full:
            summary += ' ' + i18n.twtranslate(self.site.code,
                                              'archivebot-archive-full')
        self.text = newtext
        self.save(summary)


class PageArchiver:

    """A class that encapsulates all archiving methods."""

    algo = 'none'

    def __init__(self, page, template, salt: str, force: bool = False) -> None:
        """Initializer.

        :param page: a page object to be archived
        :type page: :py:obj:`pywikibot.Page`
        :param template: a template with configuration settings
        :type template: :py:obj:`pywikibot.Page`
        :param salt: salt value
        :param force: override security value
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

        # read maxarticlesize
        try:
            # keep a gap of 1 KB not to block later changes
            self.maxsize = self.site.siteinfo['maxarticlesize'] - 1024
        except KeyError:  # mw < 1.28
            self.maxsize = 2096128  # 2 MB - 1 KB gap

        self.page = DiscussionPage(page, self)
        self.load_config()
        self.comment_params = {
            'from': self.page.title(),
        }
        self.now = datetime.datetime.utcnow().replace(tzinfo=TZoneUTC())
        self.archives = {}
        self.archived_threads = 0
        self.month_num2orig_names = {}
        for n, (long, short) in enumerate(self.site.months_names, start=1):
            self.month_num2orig_names[n] = {'long': long, 'short': short}

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
                value = '{} K'.format(self.maxsize // 1024)
                warn('Siteinfo "maxarticlesize" exceeded. Decreasing '
                     '"maxarchivesize" to ' + value,
                     ResourceWarning, stacklevel=2)
        self.attributes[attr] = [value, out]

    def saveables(self) -> List[str]:
        """Return a list of saveable attributes."""
        return [a for a in self.attributes if self.attributes[a][1]
                and a != 'maxage']

    def attr2text(self) -> str:
        """Return a template with archiver saveable attributes."""
        return '{{%s\n%s\n}}' \
               % (self.tpl.title(with_ns=(self.tpl.namespace() != 10)),
                  '\n'.join('|{} = {}'.format(a, self.get_attr(a))
                            for a in self.saveables()))

    def key_ok(self) -> bool:
        """Return whether key is valid."""
        hexdigest = calc_md5_hexdigest(self.page.title(), self.salt)
        return self.get_attr('key') == hexdigest

    def load_config(self) -> None:
        """Load and validate archiver template."""
        pywikibot.output('Looking for: {{{{{}}}}} in {}'.format(
            self.tpl.title(), self.page))
        for tpl, params in self.page.raw_extracted_templates:
            try:  # Check tpl name before comparing; it might be invalid.
                tpl_page = pywikibot.Page(self.site, tpl, ns=10)
                tpl_page.title()
            except Error:
                continue
            if tpl_page == self.tpl:
                for item, value in params.items():
                    self.set_attr(item.strip(), value.strip())
                break
        else:
            raise MissingConfigError('Missing or malformed template')
        if not self.get_attr('algo', ''):
            raise MissingConfigError('Missing argument "algo" in template')
        if not self.get_attr('archive', ''):
            raise MissingConfigError('Missing argument "archive" in template')

    def should_archive_thread(self, thread: DiscussionThread
                              ) -> Optional[ShouldArchive]:
        """
        Check whether a thread has to be archived.

        :return: the archivation reason as a tuple of localization args
        """
        # Archived by timestamp
        algo = self.get_attr('algo')
        re_t = re.fullmatch(r'old\((.*)\)', algo)
        if re_t:
            if not thread.timestamp:
                return None
            # TODO: handle unsigned
            maxage = str2time(re_t.group(1), thread.timestamp)
            if self.now - thread.timestamp > maxage:
                duration = str2localized_duration(self.site, re_t.group(1))
                return ('duration', duration)
        # TODO: handle marked with template
        return None

    def get_archive_page(self, title: str, params=None) -> DiscussionPage:
        """
        Return the page for archiving.

        If it doesn't exist yet, create and cache it.
        Also check for security violations.
        """
        page_title = self.page.title()
        archive = pywikibot.Page(self.site, title)
        if not (self.force or title.startswith(page_title + '/')
                or self.key_ok()):
            raise ArchiveSecurityError(
                'Archive page {} does not start with page title ({})!'
                .format(archive, page_title))
        if title not in self.archives:
            self.archives[title] = DiscussionPage(archive, self, params)
        return self.archives[title]

    def get_params(self, timestamp, counter: int) -> dict:
        """Make params for archiving template."""
        lang = self.site.lang
        return {
            'counter': to_local_digits(counter, lang),
            'year': to_local_digits(timestamp.year, lang),
            'isoyear': to_local_digits(timestamp.isocalendar()[0], lang),
            'isoweek': to_local_digits(timestamp.isocalendar()[1], lang),
            'semester': to_local_digits(int(ceil(timestamp.month / 6)), lang),
            'quarter': to_local_digits(int(ceil(timestamp.month / 3)), lang),
            'month': to_local_digits(timestamp.month, lang),
            'monthname': self.month_num2orig_names[timestamp.month]['long'],
            'monthnameshort': self.month_num2orig_names[
                timestamp.month]['short'],
            'week': to_local_digits(
                int(time.strftime('%W', timestamp.timetuple())), lang),
        }

    def analyze_page(self) -> Set[ShouldArchive]:
        """Analyze DiscussionPage."""
        max_arch_size = str2size(self.get_attr('maxarchivesize'))
        counter = int(self.get_attr('counter', '1'))
        pattern = self.get_attr('archive')

        keep_threads = []
        threads_per_archive = defaultdict(list)
        whys = set()
        pywikibot.output('Processing {} threads'
                         .format(len(self.page.threads)))
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
            key = pattern % params
            threads_per_archive[key].append((i, thread))
            whys.add(why)  # xxx: we don't know if we ever archive anything

        params = self.get_params(self.now, counter)
        aux_params = self.get_params(self.now, counter + 1)
        counter_matters = (pattern % params) != (pattern % aux_params)
        del params, aux_params

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
                    while counter > 1 and not archive.exists():
                        # This may happen when either:
                        # 1. a previous version of the bot run and reset
                        #    the counter without archiving anything
                        #    (number #3 above)
                        # 2. era changed between runs.
                        # Decrease the counter.
                        # TODO: This can be VERY slow, use preloading
                        # or binary search.
                        counter -= 1
                        params = self.get_params(thread.timestamp, counter)
                        archive = self.get_archive_page(
                            pattern % params, params)
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

            pywikibot.output('Archiving {} thread(s).'
                             .format(self.archived_threads))
            # Save the archives first (so that bugs don't cause a loss of data)
            for _title, archive in sorted(self.archives.items()):
                count = archive.archived_threads
                if count == 0:
                    continue
                self.comment_params['count'] = count
                comment = i18n.twtranslate(self.site.code,
                                           'archivebot-archive-summary',
                                           self.comment_params)
                archive.update(comment)

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
            self.page.update(comment)


def main(*args: str) -> None:
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    :param args: command line arguments
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
            return
        page = pywikibot.Page(site, calc)
        if page.exists():
            calc = page.title()
        else:
            pywikibot.output(
                'NOTE: the specified page "{}" does not (yet) exist.'
                .format(calc))
        pywikibot.output('key = {}'.format(calc_md5_hexdigest(calc, salt)))
        return

    if not templates:
        pywikibot.bot.suggest_help(
            additional_text='No template was specified.')
        return

    for template_name in templates:
        pagelist = []
        tmpl = pywikibot.Page(site, template_name, ns=10)
        if not filename and not pagename:
            if namespace is not None:
                ns = [str(namespace)]
            else:
                ns = []
            pywikibot.output('Fetching template transclusions...')
            pagelist.extend(tmpl.getReferences(only_template_inclusion=True,
                                               follow_redirects=False,
                                               namespaces=ns))
        if filename:
            with open(filename) as f:
                for pg in f.readlines():
                    pagelist.append(pywikibot.Page(site, pg, ns=10))
        if pagename:
            pagelist.append(pywikibot.Page(site, pagename, ns=3))
        pagelist.sort()
        for pg in pagelist:
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
                pywikibot.exception('Error occurred while processing page {}'
                                    .format(pg))


if __name__ == '__main__':
    main()
