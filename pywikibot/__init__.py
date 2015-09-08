# -*- coding: utf-8  -*-
"""The initialization file for the Pywikibot framework."""
#
# (C) Pywikibot team, 2008-2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__release__ = '2.0b3'
__version__ = '$Id$'
__url__ = 'https://www.mediawiki.org/wiki/Special:MyLanguage/Manual:Pywikibot'

import datetime
import math
import re
import sys
import threading
import json

if sys.version_info[0] > 2:
    from queue import Queue
    long = int
else:
    from Queue import Queue

from warnings import warn

# Use pywikibot. prefix for all in-package imports; this is to prevent
# confusion with similarly-named modules in version 1 framework, for users
# who want to continue using both

from pywikibot import config2 as config
from pywikibot.bot import (
    output, warning, error, critical, debug, stdout, exception,
    input, input_choice, input_yn, inputChoice, handle_args, showHelp, ui, log,
    calledModuleName, Bot, CurrentPageBot, WikidataBot,
    # the following are flagged as deprecated on usage
    handleArgs,
)
from pywikibot.exceptions import (
    Error, InvalidTitle, BadTitle, NoPage, NoMoveTarget, SectionError,
    SiteDefinitionError, NoSuchSite, UnknownSite, UnknownFamily,
    UnknownExtension,
    NoUsername, UserBlocked,
    PageRelatedError, IsRedirectPage, IsNotRedirectPage,
    PageSaveRelatedError, PageNotSaved, OtherPageSaveError,
    LockedPage, CascadeLockedPage, LockedNoPage, NoCreateError,
    EditConflict, PageDeletedConflict, PageCreatedConflict,
    ServerError, FatalServerError, Server504Error,
    CaptchaError, SpamfilterError, CircularRedirect, InterwikiRedirectPage,
    WikiBaseError, CoordinateGlobeUnknownException,
)
from pywikibot.tools import PY2, UnicodeMixin, redirect_func
from pywikibot.i18n import translate
from pywikibot.data.api import UploadWarning
from pywikibot.diff import PatchManager
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
    'TimeStripper',
)

__all__ = (
    'config', 'ui', 'UnicodeMixin', 'translate',
    'Page', 'FilePage', 'Category', 'Link', 'User',
    'ItemPage', 'PropertyPage', 'Claim',
    'html2unicode', 'url2unicode', 'unicode2html',
    'stdout', 'output', 'warning', 'error', 'critical', 'debug',
    'exception', 'input_choice', 'input', 'input_yn', 'inputChoice',
    'handle_args', 'handleArgs', 'showHelp', 'ui', 'log',
    'calledModuleName', 'Bot', 'CurrentPageBot', 'WikidataBot',
    'Error', 'InvalidTitle', 'BadTitle', 'NoPage', 'NoMoveTarget',
    'SectionError',
    'SiteDefinitionError', 'NoSuchSite', 'UnknownSite', 'UnknownFamily',
    'UnknownExtension',
    'NoUsername', 'UserBlocked', 'UserActionRefuse',
    'PageRelatedError', 'IsRedirectPage', 'IsNotRedirectPage',
    'PageSaveRelatedError', 'PageNotSaved', 'OtherPageSaveError',
    'LockedPage', 'CascadeLockedPage', 'LockedNoPage', 'NoCreateError',
    'EditConflict', 'PageDeletedConflict', 'PageCreatedConflict',
    'UploadWarning',
    'ServerError', 'FatalServerError', 'Server504Error',
    'CaptchaError', 'SpamfilterError', 'CircularRedirect',
    'InterwikiRedirectPage',
    'WikiBaseError', 'CoordinateGlobeUnknownException',
    'QuitKeyboardInterrupt',
)
__all__ += textlib_methods

if PY2:
    # T111615: Python 2 requires __all__ is bytes
    globals()['__all__'] = tuple(bytes(item) for item in __all__)

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
    As these constructors are typically used to create objects using data
    passed provided by site and page methods, some of which return a Timestamp
    when previously they returned a MediaWiki string representation, these
    methods also accept a Timestamp object, in which case they return a clone.

    Use Site.getcurrenttime() for the current time; this is more reliable
    than using Timestamp.utcnow().

    """

    mediawikiTSFormat = "%Y%m%d%H%M%S"
    ISO8601Format = "%Y-%m-%dT%H:%M:%SZ"

    def clone(self):
        """Clone this instance."""
        return self.replace(microsecond=self.microsecond)

    @classmethod
    def fromISOformat(cls, ts):
        """Convert an ISO 8601 timestamp to a Timestamp object."""
        # If inadvertantly passed a Timestamp object, use replace()
        # to create a clone.
        if isinstance(ts, cls):
            return ts.clone()
        return cls.strptime(ts, cls.ISO8601Format)

    @classmethod
    def fromtimestampformat(cls, ts):
        """Convert a MediaWiki internal timestamp to a Timestamp object."""
        # If inadvertantly passed a Timestamp object, use replace()
        # to create a clone.
        if isinstance(ts, cls):
            return ts.clone()
        return cls.strptime(ts, cls.mediawikiTSFormat)

    def isoformat(self):
        """
        Convert object to an ISO 8601 timestamp accepted by MediaWiki.

        datetime.datetime.isoformat does not postfix the ISO formatted date
        with a 'Z' unless a timezone is included, which causes MediaWiki
        ~1.19 and earlier to fail.
        """
        return self.strftime(self.ISO8601Format)

    toISOformat = redirect_func(isoformat, old_name='toISOformat',
                                class_name='Timestamp')

    def totimestampformat(self):
        """Convert object to a MediaWiki internal timestamp."""
        return self.strftime(self.mediawikiTSFormat)

    def __str__(self):
        """Return a string format recognized by the API."""
        return self.isoformat()

    def __add__(self, other):
        """Perform addition, returning a Timestamp instead of datetime."""
        newdt = super(Timestamp, self).__add__(other)
        if isinstance(newdt, datetime.datetime):
            return Timestamp(newdt.year, newdt.month, newdt.day, newdt.hour,
                             newdt.minute, newdt.second, newdt.microsecond,
                             newdt.tzinfo)
        else:
            return newdt

    def __sub__(self, other):
        """Perform substraction, returning a Timestamp instead of datetime."""
        newdt = super(Timestamp, self).__sub__(other)
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

    @classmethod
    def fromWikibase(cls, data, site):
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

        return cls(data['latitude'], data['longitude'],
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

        M{Δλ ≈ Δpos / r_φ}, where r_φ is the radius of earth at the given latitude.
        Δλ is the error in longitude.

        M{r_φ = r cos φ}, where r is the radius of earth, φ the latitude

        Therefore::
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

    @classmethod
    def fromTimestr(cls, datetimestr, precision=14, before=0, after=0,
                    timezone=0, calendarmodel=None, site=None):
        match = re.match(r'([-+]?\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)Z',
                         datetimestr)
        if not match:
            raise ValueError(u"Invalid format: '%s'" % datetimestr)
        t = match.groups()
        return cls(long(t[0]), int(t[1]), int(t[2]),
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

    @classmethod
    def fromWikibase(cls, ts):
        return cls.fromTimestr(ts[u'time'], ts[u'precision'],
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

    @classmethod
    def fromWikibase(cls, wb):
        """
        Create a WbQuanity from the JSON data given by the Wikibase API.

        @param wb: Wikibase JSON
        """
        amount = eval(wb['amount'])
        upperBound = eval(wb['upperBound'])
        lowerBound = eval(wb['lowerBound'])
        error = (upperBound - amount, amount - lowerBound)
        return cls(amount, wb['unit'], error)

    def __str__(self):
        return json.dumps(self.toWikibase(), indent=4, sort_keys=True,
                          separators=(',', ': '))

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def __repr__(self):
        return (u"WbQuantity(amount=%(amount)s, upperBound=%(upperBound)s, "
                u"lowerBound=%(lowerBound)s, unit=%(unit)s)" % self.__dict__)


_sites = {}
_url_cache = {}  # The code/fam pair for each URL


def Site(code=None, fam=None, user=None, sysop=None, interface=None, url=None):
    """A factory method to obtain a Site object.

    Site objects are cached and reused by this method.

    By default rely on config settings. These defaults may all be overridden
    using the method parameters.

    @param code: language code (override config.mylang)
    @type code: string
    @param fam: family name or object (override config.family)
    @type fam: string or Family
    @param user: bot user name to use on this site (override config.usernames)
    @type user: unicode
    @param sysop: sysop user to use on this site (override config.sysopnames)
    @type sysop: unicode
    @param interface: site class or name of class in pywikibot.site
        (override config.site_interface)
    @type interface: subclass of L{pywikibot.site.BaseSite} or string
    @param url: Instead of code and fam, does try to get a Site based on the
        URL. Still requires that the family supporting that URL exists.
    @type url: string
    """
    # Either code and fam or only url
    if url and (code or fam):
        raise ValueError('URL to the wiki OR a pair of code and family name '
                         'should be provided')
    _logger = "wiki"

    if url:
        if url not in _url_cache:
            matched_sites = []
            # Iterate through all families and look, which does apply to
            # the given URL
            for fam in config.family_files:
                family = pywikibot.family.Family.load(fam)
                code = family.from_url(url)
                if code is not None:
                    matched_sites += [(code, fam)]

            if matched_sites:
                if len(matched_sites) > 1:
                    pywikibot.warning(
                        'Found multiple matches for URL "{0}": {1} (use first)'
                        .format(url, ', '.join(str(s) for s in matched_sites)))
                _url_cache[url] = matched_sites[0]
            else:
                # TODO: As soon as AutoFamily is ready, try and use an
                #       AutoFamily
                _url_cache[url] = None

        cached = _url_cache[url]
        if cached:
            code = cached[0]
            fam = cached[1]
        else:
            raise SiteDefinitionError("Unknown URL '{0}'.".format(url))
    else:
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

    if not isinstance(interface, type):
        # If it isnt a class, assume it is a string
        try:
            tmp = __import__('pywikibot.site', fromlist=[interface])
            interface = getattr(tmp, interface)
        except ImportError:
            raise ValueError("Invalid interface name '%(interface)s'" % locals())

    if not issubclass(interface, pywikibot.site.BaseSite):
        warning('Site called with interface=%s' % interface.__name__)

    user = pywikibot.tools.normalize_username(user)
    key = '%s:%s:%s:%s' % (interface.__name__, fam, code, user)
    if key not in _sites or not isinstance(_sites[key], interface):
        _sites[key] = interface(code=code, fam=fam, user=user, sysop=sysop)
        debug(u"Instantiated %s object '%s'"
              % (interface.__name__, _sites[key]), _logger)

        if _sites[key].code != code:
            warn('Site %s instantiated using different code "%s"'
                 % (_sites[key], code), UserWarning, 2)

    return _sites[key]


# alias for backwards-compability
getSite = pywikibot.tools.redirect_func(Site, old_name='getSite')


from pywikibot.page import (
    Page,
    FilePage,
    Category,
    Link,
    User,
    ItemPage,
    PropertyPage,
    Claim,
)
from pywikibot.page import html2unicode, url2unicode, unicode2html


link_regex = re.compile(r'\[\[(?P<title>[^\]|[<>{}]*)(\|.*?)?\]\]')


@pywikibot.tools.deprecated("comment parameter for page saving method")
def setAction(s):
    """Set a summary to use for changed page submissions."""
    config.default_edit_summary = s


def showDiff(oldtext, newtext, context=0):
    """
    Output a string showing the differences between oldtext and newtext.

    The differences are highlighted (only on compatible systems) to show which
    changes were made.
    """
    PatchManager(oldtext, newtext, context=context).print_hunks()


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
                if input_yn('There are %i pages remaining in the queue. '
                            'Estimated time remaining: %s\nReally exit?'
                            % remaining(), default=False, automatic_quit=False):
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
        page_put_queue.task_done()


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
wrapper._add_deprecated_attr(
    'PageNotFound', pywikibot.exceptions.DeprecatedPageNotFoundError,
    warning_message=('{0}.{1} is deprecated, and no longer '
                     'used by pywikibot; use http.fetch() instead.'))
wrapper._add_deprecated_attr(
    'UserActionRefuse', pywikibot.exceptions._EmailUserError,
    warning_message='UserActionRefuse is deprecated; '
                    'use UserRightsError and/or NotEmailableError')
wrapper._add_deprecated_attr(
    'QuitKeyboardInterrupt', pywikibot.bot.QuitKeyboardInterrupt,
    warning_message='pywikibot.QuitKeyboardInterrupt is deprecated; '
                    'use pywikibot.bot.QuitKeyboardInterrupt instead')
