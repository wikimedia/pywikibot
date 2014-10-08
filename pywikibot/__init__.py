# -*- coding: utf-8  -*-
"""The initialization file for the Pywikibot framework."""
#
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
__release__ = '2.0b2'
__version__ = '$Id$'

import datetime
import difflib
import math
import re
import sys
import threading
import json

if sys.version_info[0] == 2:
    from Queue import Queue
else:
    from queue import Queue
    long = int

# Use pywikibot. prefix for all in-package imports; this is to prevent
# confusion with similarly-named modules in version 1 framework, for users
# who want to continue using both

from pywikibot import config2 as config
from pywikibot.bot import (
    output, warning, error, critical, debug, stdout, exception,
    input, inputChoice, handleArgs, showHelp, ui, log,
    calledModuleName, Bot, WikidataBot, QuitKeyboardInterrupt,
)
from pywikibot.exceptions import (
    Error, InvalidTitle, BadTitle, NoPage, SectionError,
    NoSuchSite, NoUsername, UserBlocked,
    PageRelatedError, IsRedirectPage, IsNotRedirectPage,
    PageSaveRelatedError, PageNotSaved, OtherPageSaveError,
    LockedPage, CascadeLockedPage, LockedNoPage,
    EditConflict, PageDeletedConflict, PageCreatedConflict,
    ServerError, FatalServerError, Server504Error,
    CaptchaError, SpamfilterError, CircularRedirect,
    WikiBaseError, CoordinateGlobeUnknownException,
)
from pywikibot.tools import UnicodeMixin, redirect_func
from pywikibot.i18n import translate
from pywikibot.data.api import UploadWarning
import pywikibot.textlib as textlib
import pywikibot.tools

textlib_methods = (
    'unescape', 'replaceExcept', 'removeDisabledParts', 'removeHTMLParts',
    'isDisabled', 'interwikiFormat', 'interwikiSort',
    'getLanguageLinks', 'replaceLanguageLinks',
    'removeLanguageLinks', 'removeLanguageLinksAndSeparator',
    'getCategoryLinks', 'categoryFormat', 'replaceCategoryLinks',
    'removeCategoryLinks', 'removeCategoryLinksAndSeparator',
    'replaceCategoryInPlace', 'compileLinkR', 'extract_templates_and_params',
)

# pep257 doesn't understand when the first entry is on the next line
__all__ = ('config', 'ui', 'UnicodeMixin', 'translate',
           'Page', 'FilePage', 'Category', 'Link', 'User',
           'ItemPage', 'PropertyPage', 'Claim', 'TimeStripper',
           'html2unicode', 'url2unicode', 'unicode2html',
           'stdout', 'output', 'warning', 'error', 'critical', 'debug',
           'exception',
           'input', 'inputChoice', 'handleArgs', 'showHelp', 'ui', 'log',
           'calledModuleName', 'Bot', 'WikidataBot',
           'Error', 'InvalidTitle', 'BadTitle', 'NoPage', 'SectionError',
           'NoSuchSite', 'NoUsername', 'UserBlocked',
           'PageRelatedError', 'IsRedirectPage', 'IsNotRedirectPage',
           'PageSaveRelatedError', 'PageNotSaved', 'OtherPageSaveError',
           'LockedPage', 'CascadeLockedPage', 'LockedNoPage',
           'EditConflict', 'PageDeletedConflict', 'PageCreatedConflict',
           'UploadWarning',
           'ServerError', 'FatalServerError', 'Server504Error',
           'CaptchaError', 'SpamfilterError', 'CircularRedirect',
           'WikiBaseError', 'CoordinateGlobeUnknownException',
           'QuitKeyboardInterrupt',
           )
# flake8 is unable to detect concatenation in the same operation
# like:
# ) + textlib_methods
# pep257 also doesn't support __all__ multiple times in a document
# so instead use this trick
globals()['__all__'] = globals()['__all__'] + textlib_methods

for _name in textlib_methods:
    target = getattr(textlib, _name)
    wrapped_func = redirect_func(target)
    globals()[_name] = wrapped_func


deprecated = redirect_func(pywikibot.tools.deprecated)
deprecate_arg = redirect_func(pywikibot.tools.deprecate_arg)


class Timestamp(datetime.datetime):

    """Class for handling MediaWiki timestamps.

    This inherits from datetime.datetime, so it can use all of the methods
    and operations of a datetime object.  To ensure that the results of any
    operation are also a Timestamp object, be sure to use only Timestamp
    objects (and datetime.timedeltas) in any operation.

    Use Timestamp.fromISOformat() and Timestamp.fromtimestampformat() to
    create Timestamp objects from MediaWiki string formats.

    Use Site.getcurrenttime() for the current time; this is more reliable
    than using Timestamp.utcnow().

    """

    mediawikiTSFormat = "%Y%m%d%H%M%S"
    ISO8601Format = "%Y-%m-%dT%H:%M:%SZ"

    @classmethod
    def fromISOformat(cls, ts):
        """Convert an ISO 8601 timestamp to a Timestamp object."""
        return cls.strptime(ts, cls.ISO8601Format)

    @classmethod
    def fromtimestampformat(cls, ts):
        """Convert a MediaWiki internal timestamp to a Timestamp object."""
        return cls.strptime(ts, cls.mediawikiTSFormat)

    def toISOformat(self):
        """Convert object to an ISO 8601 timestamp."""
        return self.strftime(self.ISO8601Format)

    def totimestampformat(self):
        """Convert object to a MediaWiki internal timestamp."""
        return self.strftime(self.mediawikiTSFormat)

    def __str__(self):
        """Return a string format recognized by the API."""
        return self.toISOformat()

    def __add__(self, other):
        newdt = datetime.datetime.__add__(self, other)
        if isinstance(newdt, datetime.datetime):
            return Timestamp(newdt.year, newdt.month, newdt.day, newdt.hour,
                             newdt.minute, newdt.second, newdt.microsecond,
                             newdt.tzinfo)
        else:
            return newdt

    def __sub__(self, other):
        newdt = datetime.datetime.__sub__(self, other)
        if isinstance(newdt, datetime.datetime):
            return Timestamp(newdt.year, newdt.month, newdt.day, newdt.hour,
                             newdt.minute, newdt.second, newdt.microsecond,
                             newdt.tzinfo)
        else:
            return newdt


class Coordinate(object):

    """
    Class for handling and storing Coordinates.

    For now its just being used for DataSite, but
    in the future we can use it for the GeoData extension.
    """

    def __init__(self, lat, lon, alt=None, precision=None, globe='earth',
                 typ="", name="", dim=None, site=None, entity=''):
        """
        Represent a geo coordinate.

        @param lat: Latitude
        @type lat: float
        @param lon: Longitude
        @type lon: float
        @param alt: Altitute? TODO FIXME
        @param precision: precision
        @type precision: float
        @param globe: Which globe the point is on
        @type globe: str
        @param typ: The type of coordinate point
        @type typ: str
        @param name: The name
        @type name: str
        @param dim: Dimension (in meters)
        @type dim: int
        @param entity: The URL entity of a Wikibase item
        @type entity: str
        """
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self._precision = precision
        if globe:
            globe = globe.lower()
        self.globe = globe
        self._entity = entity
        self.type = typ
        self.name = name
        self._dim = dim
        if not site:
            self.site = Site().data_repository()
        else:
            self.site = site

    def __repr__(self):
        string = 'Coordinate(%s, %s' % (self.lat, self.lon)
        if self.globe != 'earth':
            string += ', globe="%s"' % self.globe
        string += ')'
        return string

    @property
    def entity(self):
        if self._entity:
            return self._entity
        return self.site.globes()[self.globe]

    def toWikibase(self):
        """
        Export the data to a JSON object for the Wikibase API.

        FIXME: Should this be in the DataSite object?
        """
        if self.globe not in self.site.globes():
            raise CoordinateGlobeUnknownException(
                u"%s is not supported in Wikibase yet."
                % self.globe)
        return {'latitude': self.lat,
                'longitude': self.lon,
                'altitude': self.alt,
                'globe': self.entity,
                'precision': self.precision,
                }

    @staticmethod
    def fromWikibase(data, site):
        """Constructor to create an object from Wikibase's JSON output."""
        globes = {}
        for k in site.globes():
            globes[site.globes()[k]] = k

        globekey = data['globe']
        if globekey:
            globe = globes.get(data['globe'])
        else:
            # Default to earth or should we use None here?
            globe = 'earth'

        return Coordinate(data['latitude'], data['longitude'],
                          data['altitude'], data['precision'],
                          globe, site=site, entity=data['globe'])

    @property
    def precision(self):
        u"""
        Return the precision of the geo coordinate.

        The biggest error (in degrees) will be given by the longitudinal error;
        the same error in meters becomes larger (in degrees) further up north.
        We can thus ignore the latitudinal error.

        The longitudinal can be derived as follows:

        In small angle approximation (and thus in radians):

        Δλ ≈ Δpos / r_φ, where r_φ is the radius of earth at the given latitude.
        Δλ is the error in longitude.

            r_φ = r cos φ, where r is the radius of earth, φ the latitude

        Therefore:
        precision = math.degrees(self._dim/(radius*math.cos(math.radians(self.lat))))
        """
        if not self._precision:
            radius = 6378137  # TODO: Support other globes
            self._precision = math.degrees(
                self._dim / (radius * math.cos(math.radians(self.lat))))
        return self._precision

    def precisionToDim(self):
        """Convert precision from Wikibase to GeoData's dim."""
        raise NotImplementedError


class WbTime(object):

    """A Wikibase time representation."""

    PRECISION = {'1000000000': 0,
                 '100000000': 1,
                 '10000000': 2,
                 '1000000': 3,
                 '100000': 4,
                 '10000': 5,
                 'millenia': 6,
                 'century': 7,
                 'decade': 8,
                 'year': 9,
                 'month': 10,
                 'day': 11,
                 'hour': 12,
                 'minute': 13,
                 'second': 14
                 }

    FORMATSTR = '{0:+012d}-{1:02d}-{2:02d}T{3:02d}:{4:02d}:{5:02d}Z'

    def __init__(self, year=None, month=None, day=None,
                 hour=None, minute=None, second=None,
                 precision=None, before=0, after=0,
                 timezone=0, calendarmodel=None, site=None):
        """
        Create a new WbTime object.

        The precision can be set by the Wikibase int value (0-14) or by a human
        readable string, e.g., 'hour'. If no precision is given, it is set
        according to the given time units.
        """
        if year is None:
            raise ValueError('no year given')
        self.precision = self.PRECISION['second']
        if second is None:
            self.precision = self.PRECISION['minute']
            second = 0
        if minute is None:
            self.precision = self.PRECISION['hour']
            minute = 0
        if hour is None:
            self.precision = self.PRECISION['day']
            hour = 0
        if day is None:
            self.precision = self.PRECISION['month']
            day = 1
        if month is None:
            self.precision = self.PRECISION['year']
            month = 1
        self.year = long(year)
        self.month = month
        self.day = day
        self.hour = hour
        self.minute = minute
        self.second = second
        self.after = after
        self.before = before
        self.timezone = timezone
        if calendarmodel is None:
            if site is None:
                site = Site().data_repository()
            calendarmodel = site.calendarmodel()
        self.calendarmodel = calendarmodel

        # if precision is given it overwrites the autodetection above
        if precision is not None:
            if (isinstance(precision, int) and
                    precision in self.PRECISION.values()):
                self.precision = precision
            elif precision in self.PRECISION:
                self.precision = self.PRECISION[precision]
            else:
                raise ValueError('Invalid precision: "%s"' % precision)

    @staticmethod
    def fromTimestr(datetimestr, precision=14, before=0, after=0, timezone=0,
                    calendarmodel=None, site=None):
        match = re.match('([-+]?\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)Z',
                         datetimestr)
        if not match:
            raise ValueError(u"Invalid format: '%s'" % datetimestr)
        t = match.groups()
        return WbTime(long(t[0]), int(t[1]), int(t[2]),
                      int(t[3]), int(t[4]), int(t[5]),
                      precision, before, after, timezone, calendarmodel, site)

    def toTimestr(self):
        """
        Convert the data to a UTC date/time string.

        @return: str
        """
        return self.FORMATSTR.format(self.year, self.month, self.day,
                                     self.hour, self.minute, self.second)

    def toWikibase(self):
        """
        Convert the data to a JSON object for the Wikibase API.

        @return: dict
        """
        json = {'time': self.toTimestr(),
                'precision': self.precision,
                'after': self.after,
                'before': self.before,
                'timezone': self.timezone,
                'calendarmodel': self.calendarmodel
                }
        return json

    @staticmethod
    def fromWikibase(ts):
        return WbTime.fromTimestr(ts[u'time'], ts[u'precision'],
                                  ts[u'before'], ts[u'after'],
                                  ts[u'timezone'], ts[u'calendarmodel'])

    def __str__(self):
        return json.dumps(self.toWikibase(), indent=4, sort_keys=True,
                          separators=(',', ': '))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return u"WbTime(year=%(year)d, month=%(month)d, day=%(day)d, " \
            u"hour=%(hour)d, minute=%(minute)d, second=%(second)d, " \
            u"precision=%(precision)d, before=%(before)d, after=%(after)d, " \
            u"timezone=%(timezone)d, calendarmodel='%(calendarmodel)s')" \
            % self.__dict__


class WbQuantity(object):

    """A Wikibase quantity representation."""

    def __init__(self, amount, unit=None, error=None):
        u"""
        Create a new WbQuantity object.

        @param amount: number representing this quantity
        @type amount: float
        @param unit: not used (only unit-less quantities are supported)
        @param error: the uncertainty of the amount (e.g. ±1)
        @type error: float, or tuple of two floats, where the first value is
                     the upper error and the second is the lower error value.
        """
        if amount is None:
            raise ValueError('no amount given')
        if unit is not None and unit != '1':
            raise NotImplementedError(
                'Currently only unit-less quantities are supported')
        if unit is None:
            unit = '1'
        self.amount = amount
        self.unit = unit
        upperError = lowerError = 0
        if isinstance(error, tuple):
            upperError, lowerError = error
        elif error is not None:
            upperError = lowerError = error
        self.upperBound = self.amount + upperError
        self.lowerBound = self.amount - lowerError

    def toWikibase(self):
        """Convert the data to a JSON object for the Wikibase API."""
        json = {'amount': self.amount,
                'upperBound': self.upperBound,
                'lowerBound': self.lowerBound,
                'unit': self.unit
                }
        return json

    @staticmethod
    def fromWikibase(wb):
        """
        Create a WbQuanity from the JSON data given by the Wikibase API.

        @param wb: Wikibase JSON
        """
        amount = eval(wb['amount'])
        upperBound = eval(wb['upperBound'])
        lowerBound = eval(wb['lowerBound'])
        error = (upperBound - amount, amount - lowerBound)
        return WbQuantity(amount, wb['unit'], error)

    def __str__(self):
        return json.dumps(self.toWikibase(), indent=4, sort_keys=True,
                          separators=(',', ': '))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return (u"WbQuantity(amount=%(amount)s, upperBound=%(upperBound)s, "
                u"lowerBound=%(lowerBound)s, unit=%(unit)s)" % self.__dict__)


_sites = {}


def Site(code=None, fam=None, user=None, sysop=None, interface=None):
    """A factory method to obtain a Site object.

    Site objects are cached and reused by this method.

    By default rely on config settings. These defaults may all be overriden
    using the method parameters.

    @param code: language code (override config.mylang)
    @type code: string
    @param fam: family name or object (override config.family)
    @type fam: string or Family
    @param user: bot user name to use on this site (override config.usernames)
    @type user: unicode
    @param sysop: sysop user to use on this site (override config.sysopnames)
    @type sysop: unicode
    @param interface: site interface (override config.site_interface)
    @type interface: string
    """
    _logger = "wiki"

    # Fallback to config defaults
    code = code or config.mylang
    fam = fam or config.family
    interface = interface or config.site_interface

    # config.usernames is initialised with a dict for each family name
    family_name = str(fam)
    if family_name in config.usernames:
        user = user or config.usernames[family_name].get(code) \
            or config.usernames[family_name].get('*')
        sysop = sysop or config.sysopnames[family_name].get(code) \
            or config.sysopnames[family_name].get('*')

    try:
        tmp = __import__('pywikibot.site', fromlist=[interface])
        __Site = getattr(tmp, interface)
    except ImportError:
        raise ValueError("Invalid interface name '%(interface)s'" % locals())
    key = '%s:%s:%s:%s' % (interface, fam, code, user)
    if key not in _sites or not isinstance(_sites[key], __Site):
        _sites[key] = __Site(code=code, fam=fam, user=user, sysop=sysop)
        debug(u"Instantiating Site object '%(site)s'"
                        % {'site': _sites[key]}, _logger)
    return _sites[key]


# alias for backwards-compability
getSite = pywikibot.tools.redirect_func(Site, old_name='getSite')


from .page import (
    Page,
    FilePage,
    Category,
    Link,
    User,
    ItemPage,
    PropertyPage,
    Claim,
)
from .page import html2unicode, url2unicode, unicode2html


link_regex = re.compile(r'\[\[(?P<title>[^\]|[<>{}]*)(\|.*?)?\]\]')


@pywikibot.tools.deprecated("comment parameter for page saving method")
def setAction(s):
    """Set a summary to use for changed page submissions."""
    config.default_edit_summary = s


def showDiff(oldtext, newtext):
    """
    Output a string showing the differences between oldtext and newtext.

    The differences are highlighted (only on compatible systems) to show which
    changes were made.
    """
    # This is probably not portable to non-terminal interfaces....
    # For information on difflib, see http://pydoc.org/2.1/difflib.html
    color = {
        '+': 'lightgreen',
        '-': 'lightred',
    }
    diff = u''
    colors = []
    # This will store the last line beginning with + or -.
    lastline = None
    # For testing purposes only: show original, uncolored diff
    #     for line in difflib.ndiff(oldtext.splitlines(), newtext.splitlines()):
    #         print line
    for line in difflib.ndiff(oldtext.splitlines(), newtext.splitlines()):
        if line.startswith('?'):
            # initialize color vector with None, which means default color
            lastcolors = [None for c in lastline]
            # colorize the + or - sign
            lastcolors[0] = color[lastline[0]]
            # colorize changed parts in red or green
            for i in range(min(len(line), len(lastline))):
                if line[i] != ' ':
                    lastcolors[i] = color[lastline[0]]
            diff += lastline + '\n'
            # append one None (default color) for the newline character
            colors += lastcolors + [None]
        elif lastline:
            diff += lastline + '\n'
            # colorize the + or - sign only
            lastcolors = [None for c in lastline]
            lastcolors[0] = color[lastline[0]]
            colors += lastcolors + [None]
        lastline = None
        if line[0] in ('+', '-'):
            lastline = line
    # there might be one + or - line left that wasn't followed by a ? line.
    if lastline:
        diff += lastline + '\n'
        # colorize the + or - sign only
        lastcolors = [None for c in lastline]
        lastcolors[0] = color[lastline[0]]
        colors += lastcolors + [None]

    result = u''
    lastcolor = None
    for i in range(len(diff)):
        if colors[i] != lastcolor:
            if lastcolor is None:
                result += '\03{%s}' % colors[i]
            else:
                result += '\03{default}'
        lastcolor = colors[i]
        result += diff[i]
    output(result)


# Throttle and thread handling

stopped = False


def stopme():
    """Drop this process from the throttle log, after pending threads finish.

    Can be called manually if desired, but if not, will be called automatically
    at Python exit.

    """
    global stopped
    _logger = "wiki"

    if not stopped:
        debug(u"stopme() called", _logger)

        def remaining():
            remainingPages = page_put_queue.qsize() - 1
            # -1 because we added a None element to stop the queue

            remainingSeconds = datetime.timedelta(
                seconds=(remainingPages * config.put_throttle))
            return (remainingPages, remainingSeconds)

        page_put_queue.put((None, [], {}))
        stopped = True

        if page_put_queue.qsize() > 1:
            num, sec = remaining()
            format_values = dict(num=num, sec=sec)
            output(u'\03{lightblue}'
                   u'Waiting for %(num)i pages to be put. '
                   u'Estimated time remaining: %(sec)s'
                   u'\03{default}' % format_values)

        while(_putthread.isAlive()):
            try:
                _putthread.join(1)
            except KeyboardInterrupt:
                answer = inputChoice(u"""\
There are %i pages remaining in the queue. Estimated time remaining: %s
Really exit?""" % remaining(),
                    ['yes', 'no'], ['y', 'N'], 'N')
                if answer == 'y':
                    return

    # only need one drop() call because all throttles use the same global pid
    try:
        list(_sites.values())[0].throttle.drop()
        log(u"Dropped throttle(s).")
    except IndexError:
        pass

import atexit
atexit.register(stopme)


# Create a separate thread for asynchronous page saves (and other requests)
def async_manager():
    """Daemon; take requests from the queue and execute them in background."""
    while True:
        (request, args, kwargs) = page_put_queue.get()
        if request is None:
            break
        request(*args, **kwargs)


def async_request(request, *args, **kwargs):
    """Put a request on the queue, and start the daemon if necessary."""
    if not _putthread.isAlive():
        try:
            page_put_queue.mutex.acquire()
            try:
                _putthread.start()
            except (AssertionError, RuntimeError):
                pass
        finally:
            page_put_queue.mutex.release()
    page_put_queue.put((request, args, kwargs))

# queue to hold pending requests
page_put_queue = Queue(config.max_queue_size)
# set up the background thread
_putthread = threading.Thread(target=async_manager)
# identification for debugging purposes
_putthread.setName('Put-Thread')
_putthread.setDaemon(True)

wrapper = pywikibot.tools.ModuleDeprecationWrapper(__name__)
wrapper._add_deprecated_attr('ImagePage', FilePage)
