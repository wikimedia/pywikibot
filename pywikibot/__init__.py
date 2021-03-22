"""The initialization file for the Pywikibot framework."""
#
# (C) Pywikibot team, 2008-2021
#
# Distributed under the terms of the MIT license.
#
import atexit
import datetime
import inspect
import math
import re
import threading
import time
from contextlib import suppress
from decimal import Decimal
from queue import Queue
from typing import Optional, Union
from urllib.parse import urlparse
from warnings import warn

from pywikibot import config as _config
from pywikibot import exceptions
from pywikibot.__metadata__ import (
    __copyright__,
    __description__,
    __download_url__,
    __license__,
    __maintainer__,
    __maintainer_email__,
    __name__,
    __url__,
    __version__,
)
from pywikibot._wbtypes import WbRepresentation as _WbRepresentation
from pywikibot.backports import cache, removesuffix
from pywikibot.bot import (
    Bot,
    CurrentPageBot,
    WikidataBot,
    calledModuleName,
    handle_args,
    input,
    input_choice,
    input_yn,
    show_help,
    ui,
)
from pywikibot.diff import PatchManager
from pywikibot.exceptions import (
    DEPRECATED_EXCEPTIONS,
    CoordinateGlobeUnknownError,
)
from pywikibot.family import AutoFamily, Family
from pywikibot.i18n import translate
from pywikibot.logging import (
    critical,
    debug,
    error,
    exception,
    log,
    output,
    stdout,
    warning,
)
from pywikibot.site import APISite, BaseSite, ClosedSite, DataSite
from pywikibot.tools import (
    ModuleDeprecationWrapper as _ModuleDeprecationWrapper,
)
from pywikibot.tools import classproperty
from pywikibot.tools import deprecate_arg as _deprecate_arg
from pywikibot.tools import normalize_username
from pywikibot.tools.formatter import color_format


__all__ = (
    '__copyright__', '__description__', '__download_url__', '__license__',
    '__maintainer__', '__maintainer_email__', '__name__',
    '__url__', '__version__',
    'Bot', 'calledModuleName', 'CaptchaError', 'CascadeLockedPage',
    'Category', 'CircularRedirect', 'Claim', 'Coordinate',
    'CoordinateGlobeUnknownException', 'critical', 'CurrentPageBot', 'debug',
    'EditConflict', 'error', 'Error', 'exception', 'FatalServerError',
    'FilePage', 'handle_args', 'html2unicode', 'input', 'input_choice',
    'input_yn', 'InterwikiRedirectPage', 'InvalidTitle', 'IsNotRedirectPage',
    'IsRedirectPage', 'ItemPage', 'Link', 'LockedNoPage', 'LockedPage', 'log',
    'NoCreateError', 'NoMoveTarget', 'NoPage', 'NoUsername',
    'NoWikibaseEntity', 'OtherPageSaveError', 'output', 'Page',
    'PageCreatedConflict', 'PageDeletedConflict', 'PageRelatedError',
    'PageSaveRelatedError', 'PropertyPage', 'SectionError', 'Server414Error',
    'Server504Error', 'ServerError', 'showDiff', 'show_help', 'Site',
    'SiteDefinitionError', 'SiteLink', 'SpamblacklistError', 'stdout',
    'Timestamp', 'TitleblacklistError', 'translate', 'ui', 'unicode2html',
    'UnknownExtension', 'UnknownFamily', 'UnknownSite', 'UnsupportedPage',
    'UploadWarning', 'url2unicode', 'User', 'warning', 'WbGeoShape',
    'WbMonolingualText', 'WbQuantity', 'WbTabularData', 'WbTime', 'WbUnknown',
    'WikiBaseError', 'WikidataBot',
)


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

    Use Site.server_time() for the current time; this is more reliable
    than using Timestamp.utcnow().
    """

    mediawikiTSFormat = '%Y%m%d%H%M%S'
    _ISO8601Format_new = '{0:+05d}-{1:02d}-{2:02d}T{3:02d}:{4:02d}:{5:02d}Z'

    def clone(self):
        """Clone this instance."""
        return self.replace(microsecond=self.microsecond)

    @classproperty
    def ISO8601Format(cls):
        """ISO8601 format string class property for compatibility purpose."""
        return cls._ISO8601Format()

    @classmethod
    def _ISO8601Format(cls, sep: str = 'T') -> str:
        """ISO8601 format string.

        :param sep: one-character separator, placed between the date and time
        :return: ISO8601 format string
        """
        assert len(sep) == 1
        return '%Y-%m-%d{}%H:%M:%SZ'.format(sep)

    @classmethod
    def fromISOformat(cls, ts, sep: str = 'T'):
        """Convert an ISO 8601 timestamp to a Timestamp object.

        :param ts: ISO 8601 timestamp or a Timestamp object already
        :type ts: str or Timestamp
        :param sep: one-character separator, placed between the date and time
        :return: Timestamp object
        :rtype: Timestamp
        """
        # If inadvertently passed a Timestamp object, use replace()
        # to create a clone.
        if isinstance(ts, cls):
            return ts.clone()
        return cls.strptime(ts, cls._ISO8601Format(sep))

    @classmethod
    def fromtimestampformat(cls, ts):
        """Convert a MediaWiki internal timestamp to a Timestamp object."""
        # If inadvertently passed a Timestamp object, use replace()
        # to create a clone.
        if isinstance(ts, cls):
            return ts.clone()
        if len(ts) == 8:  # year, month and day are given only
            ts += '000'
        return cls.strptime(ts, cls.mediawikiTSFormat)

    def isoformat(self, sep='T'):
        """
        Convert object to an ISO 8601 timestamp accepted by MediaWiki.

        datetime.datetime.isoformat does not postfix the ISO formatted date
        with a 'Z' unless a timezone is included, which causes MediaWiki
        ~1.19 and earlier to fail.
        """
        return self.strftime(self._ISO8601Format(sep))

    def totimestampformat(self):
        """Convert object to a MediaWiki internal timestamp."""
        return self.strftime(self.mediawikiTSFormat)

    def __str__(self):
        """Return a string format recognized by the API."""
        return self.isoformat()

    def __add__(self, other):
        """Perform addition, returning a Timestamp instead of datetime."""
        newdt = super().__add__(other)
        if isinstance(newdt, datetime.datetime):
            return Timestamp(newdt.year, newdt.month, newdt.day, newdt.hour,
                             newdt.minute, newdt.second, newdt.microsecond,
                             newdt.tzinfo)
        return newdt

    def __sub__(self, other):
        """Perform subtraction, returning a Timestamp instead of datetime."""
        newdt = super().__sub__(other)
        if isinstance(newdt, datetime.datetime):
            return Timestamp(newdt.year, newdt.month, newdt.day, newdt.hour,
                             newdt.minute, newdt.second, newdt.microsecond,
                             newdt.tzinfo)
        return newdt


class Coordinate(_WbRepresentation):

    """Class for handling and storing Coordinates."""

    _items = ('lat', 'lon', 'entity')

    @_deprecate_arg('entity', 'globe_item')
    def __init__(self, lat: float, lon: float, alt=None,
                 precision: Optional[float] = None,
                 globe: Optional[str] = None, typ: str = '',
                 name: str = '', dim: Optional[int] = None,
                 site: Optional[DataSite] = None, globe_item=None,
                 primary: bool = False):
        """
        Represent a geo coordinate.

        :param lat: Latitude
        :param lon: Longitude
        :param alt: Altitude? TODO FIXME
        :param precision: precision
        :param globe: Which globe the point is on
        :param typ: The type of coordinate point
        :param name: The name
        :param dim: Dimension (in meters)
        :param site: The Wikibase site
        :param globe_item: The Wikibase item for the globe, or the entity URI
                           of this Wikibase item. Takes precedence over 'globe'
                           if present.
        :type globe_item: pywikibot.ItemPage or str
        :param primary: True for a primary set of coordinates
        """
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self._precision = precision
        self._entity = globe_item
        self.type = typ
        self.name = name
        self._dim = dim
        self.site = site or Site().data_repository()
        self.primary = primary

        if globe:
            globe = globe.lower()
        elif not globe_item:
            globe = self.site.default_globe()
        self.globe = globe

    @property
    def entity(self):
        """Return the entity uri of the globe."""
        if not self._entity:
            if self.globe not in self.site.globes():
                raise CoordinateGlobeUnknownError(
                    '{} is not supported in Wikibase yet.'
                    .format(self.globe))
            return self.site.globes()[self.globe]

        if isinstance(self._entity, ItemPage):
            return self._entity.concept_uri()

        return self._entity

    def toWikibase(self) -> dict:
        """
        Export the data to a JSON object for the Wikibase API.

        FIXME: Should this be in the DataSite object?

        :return: Wikibase JSON
        """
        return {'latitude': self.lat,
                'longitude': self.lon,
                'altitude': self.alt,
                'globe': self.entity,
                'precision': self.precision,
                }

    @classmethod
    def fromWikibase(cls, data: dict, site: DataSite):
        """
        Constructor to create an object from Wikibase's JSON output.

        :param data: Wikibase JSON
        :param site: The Wikibase site
        :rtype: Coordinate
        """
        globe = None

        if data['globe']:
            globes = {}
            for name, entity in site.globes().items():
                globes[entity] = name

            globe = globes.get(data['globe'])

        return cls(data['latitude'], data['longitude'],
                   data['altitude'], data['precision'],
                   globe, site=site, globe_item=data['globe'])

    @property
    def precision(self) -> Optional[float]:
        """
        Return the precision of the geo coordinate.

        The precision is calculated if the Coordinate does not have a
        precision, and self._dim is set.

        When no precision and no self._dim exists, None is returned.

        The biggest error (in degrees) will be given by the longitudinal error;
        the same error in meters becomes larger (in degrees) further up north.
        We can thus ignore the latitudinal error.

        The longitudinal can be derived as follows:

        In small angle approximation (and thus in radians):

        M{Δλ ≈ Δpos / r_φ}, where r_φ is the radius of earth at the given
        latitude.
        Δλ is the error in longitude.

        M{r_φ = r cos φ}, where r is the radius of earth, φ the latitude

        Therefore::

            precision = math.degrees(
                self._dim/(radius*math.cos(math.radians(self.lat))))
        """
        if self._dim is None and self._precision is None:
            return None
        if self._precision is None and self._dim is not None:
            radius = 6378137  # TODO: Support other globes
            self._precision = math.degrees(
                self._dim / (radius * math.cos(math.radians(self.lat))))
        return self._precision

    @precision.setter
    def precision(self, value):
        self._precision = value

    def precisionToDim(self) -> Optional[int]:
        """
        Convert precision from Wikibase to GeoData's dim and return the latter.

        dim is calculated if the Coordinate doesn't have a dimension, and
        precision is set. When neither dim nor precision are set, ValueError
        is thrown.

        Carrying on from the earlier derivation of precision, since
        precision = math.degrees(dim/(radius*math.cos(math.radians(self.lat))))
        we get::

            dim = math.radians(
                precision)*radius*math.cos(math.radians(self.lat))

        But this is not valid, since it returns a float value for dim which is
        an integer. We must round it off to the nearest integer.

        Therefore::

            dim = int(round(math.radians(
                precision)*radius*math.cos(math.radians(self.lat))))
        """
        if self._dim is None and self._precision is None:
            raise ValueError('No values set for dim or precision')
        if self._dim is None and self._precision is not None:
            radius = 6378137
            self._dim = int(
                round(
                    math.radians(self._precision) * radius * math.cos(
                        math.radians(self.lat))
                )
            )
        return self._dim

    def get_globe_item(self, repo: Optional[DataSite] = None,
                       lazy_load: bool = False):
        """
        Return the ItemPage corresponding to the globe.

        Note that the globe need not be in the same data repository as the
        Coordinate itself.

        A successful lookup is stored as an internal value to avoid the need
        for repeated lookups.

        :param repo: the Wikibase site for the globe, if different from that
            provided with the Coordinate.
        :param lazy_load: Do not raise NoPage if ItemPage does not exist.
        :return: pywikibot.ItemPage
        """
        if isinstance(self._entity, ItemPage):
            return self._entity

        repo = repo or self.site
        return ItemPage.from_entity_uri(repo, self.entity, lazy_load)


class WbTime(_WbRepresentation):

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

    _items = ('year', 'month', 'day', 'hour', 'minute', 'second',
              'precision', 'before', 'after', 'timezone', 'calendarmodel')

    def __init__(self,
                 year: Optional[int] = None,
                 month: Optional[int] = None,
                 day: Optional[int] = None,
                 hour: Optional[int] = None,
                 minute: Optional[int] = None,
                 second: Optional[int] = None,
                 precision: Union[int, str, None] = None,
                 before: int = 0,
                 after: int = 0,
                 timezone: int = 0,
                 calendarmodel: Optional[str] = None,
                 site: Optional[DataSite] = None):
        """Create a new WbTime object.

        The precision can be set by the Wikibase int value (0-14) or by a human
        readable string, e.g., 'hour'. If no precision is given, it is set
        according to the given time units.

        Timezone information is given in three different ways depending on the
        time:

        * Times after the implementation of UTC (1972): as an offset from UTC
          in minutes;
        * Times before the implementation of UTC: the offset of the time zone
          from universal time;
        * Before the implementation of time zones: The longitude of the place
          of the event, in the range −180° to 180°, multiplied by 4 to convert
          to minutes.

        :param year: The year as a signed integer of between 1 and 16 digits.
        :param month: Month
        :param day: Day
        :param hour: Hour
        :param minute: Minute
        :param second: Second
        :param precision: The unit of the precision of the time.
        :param before: Number of units after the given time it could be, if
            uncertain. The unit is given by the precision.
        :param after: Number of units before the given time it could be, if
            uncertain. The unit is given by the precision.
        :param timezone: Timezone information in minutes.
        :param calendarmodel: URI identifying the calendar model
        :param site: The Wikibase site
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
        self.year = year
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
                if site is None:
                    raise ValueError('Site {} has no data repository'
                                     .format(Site()))
            calendarmodel = site.calendarmodel()
        self.calendarmodel = calendarmodel

        # if precision is given it overwrites the autodetection above
        if precision is not None:
            if (isinstance(precision, int)
                    and precision in self.PRECISION.values()):
                self.precision = precision
            elif precision in self.PRECISION:
                self.precision = self.PRECISION[precision]
            else:
                raise ValueError('Invalid precision: "{}"'.format(precision))

    @classmethod
    def fromTimestr(cls,
                    datetimestr: str,
                    precision: Union[int, str] = 14,
                    before: int = 0,
                    after: int = 0,
                    timezone: int = 0,
                    calendarmodel: Optional[str] = None,
                    site: Optional[DataSite] = None):
        """Create a new WbTime object from a UTC date/time string.

        The timestamp differs from ISO 8601 in that:

        * The year is always signed and having between 1 and 16 digits;
        * The month, day and time are zero if they are unknown;
        * The Z is discarded since time zone is determined from the timezone
          param.

        :param datetimestr: Timestamp in a format resembling ISO 8601,
            e.g. +2013-01-01T00:00:00Z
        :param precision: The unit of the precision of the time.
        :param before: Number of units after the given time it could be, if
            uncertain. The unit is given by the precision.
        :param after: Number of units before the given time it could be, if
            uncertain. The unit is given by the precision.
        :param timezone: Timezone information in minutes.
        :param calendarmodel: URI identifying the calendar model
        :param site: The Wikibase site
        :rtype: pywikibot.WbTime
        """
        match = re.match(r'([-+]?\d+)-(\d+)-(\d+)T(\d+):(\d+):(\d+)Z',
                         datetimestr)
        if not match:
            raise ValueError("Invalid format: '{}'".format(datetimestr))
        t = match.groups()
        return cls(int(t[0]), int(t[1]), int(t[2]),
                   int(t[3]), int(t[4]), int(t[5]),
                   precision, before, after, timezone, calendarmodel, site)

    @classmethod
    def fromTimestamp(cls, timestamp, precision: Union[int, str] = 14,
                      before: int = 0, after: int = 0,
                      timezone: int = 0, calendarmodel: Optional[str] = None,
                      site: Optional[DataSite] = None):
        """
        Create a new WbTime object from a pywikibot.Timestamp.

        :param timestamp: Timestamp
        :type timestamp: pywikibot.Timestamp
        :param precision: The unit of the precision of the time.
        :param before: Number of units after the given time it could be, if
            uncertain. The unit is given by the precision.
        :param after: Number of units before the given time it could be, if
            uncertain. The unit is given by the precision.
        :param timezone: Timezone information in minutes.
        :param calendarmodel: URI identifying the calendar model
        :param site: The Wikibase site
        :rtype: pywikibot.WbTime
        """
        return cls.fromTimestr(timestamp.isoformat(), precision=precision,
                               before=before, after=after,
                               timezone=timezone, calendarmodel=calendarmodel,
                               site=site)

    def toTimestr(self, force_iso: bool = False) -> str:
        """
        Convert the data to a UTC date/time string.

        See fromTimestr() for differences between output with and without
        force_iso.

        :param force_iso: whether the output should be forced to ISO 8601
        :return: Timestamp in a format resembling ISO 8601
        """
        if force_iso:
            return Timestamp._ISO8601Format_new.format(
                self.year, max(1, self.month), max(1, self.day),
                self.hour, self.minute, self.second)
        return self.FORMATSTR.format(self.year, self.month, self.day,
                                     self.hour, self.minute, self.second)

    def toTimestamp(self) -> Timestamp:
        """
        Convert the data to a pywikibot.Timestamp.

        :raises ValueError: instance value cannot be represented using
            Timestamp
        """
        if self.year <= 0:
            raise ValueError('You cannot turn BC dates into a Timestamp')
        return Timestamp.fromISOformat(
            self.toTimestr(force_iso=True).lstrip('+'))

    def toWikibase(self) -> dict:
        """
        Convert the data to a JSON object for the Wikibase API.

        :return: Wikibase JSON
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
    def fromWikibase(cls, wb: dict, site: Optional[DataSite] = None):
        """
        Create a WbTime from the JSON data given by the Wikibase API.

        :param wb: Wikibase JSON
        :param site: The Wikibase site
        :rtype: pywikibot.WbTime
        """
        return cls.fromTimestr(wb['time'], wb['precision'],
                               wb['before'], wb['after'],
                               wb['timezone'], wb['calendarmodel'], site)


class WbQuantity(_WbRepresentation):

    """A Wikibase quantity representation."""

    _items = ('amount', 'upperBound', 'lowerBound', 'unit')

    @staticmethod
    def _require_errors(site: DataSite) -> bool:
        """
        Check if Wikibase site is so old it requires error bounds to be given.

        If no site item is supplied it raises a warning and returns True.

        :param site: The Wikibase site
        """
        if not site:
            warning(
                "WbQuantity now expects a 'site' parameter. This is needed to "
                'ensure correct handling of error bounds.')
            return False
        return site.mw_version < '1.29.0-wmf.2'

    @staticmethod
    def _todecimal(value: str) -> Optional[Decimal]:
        """
        Convert a string to a Decimal for use in WbQuantity.

        None value is returned as is.

        :param value: decimal number to convert
        """
        if isinstance(value, Decimal):
            return value
        if value is None:
            return None
        return Decimal(str(value))

    @staticmethod
    def _fromdecimal(value: Decimal) -> Optional[str]:
        """
        Convert a Decimal to a string representation suitable for WikiBase.

        None value is returned as is.

        :param value: decimal number to convert
        """
        if value is None:
            return None
        return format(value, '+g')

    def __init__(self, amount, unit=None, error=None,
                 site: Optional[DataSite] = None):
        """
        Create a new WbQuantity object.

        :param amount: number representing this quantity
        :type amount: str or Decimal. Other types are accepted, and
            converted via str to Decimal.
        :param unit: the Wikibase item for the unit or the entity URI of this
            Wikibase item.
        :type unit: pywikibot.ItemPage, str or None
        :param error: the uncertainty of the amount (e.g. ±1)
        :type error: same as amount, or tuple of two values, where the first
            value is the upper error and the second is the lower error value.
        :param site: The Wikibase site
        """
        if amount is None:
            raise ValueError('no amount given')

        self.amount = self._todecimal(amount)
        self._unit = unit
        self.site = site or Site().data_repository()

        # also allow entity URIs to be provided via unit parameter
        if isinstance(unit, str) \
           and unit.partition('://')[0] not in ('http', 'https'):
            raise ValueError("'unit' must be an ItemPage or entity uri.")

        if error is None and not self._require_errors(site):
            self.upperBound = self.lowerBound = None
        else:
            if error is None:
                upperError = lowerError = Decimal(0)
            elif isinstance(error, tuple):
                upperError = self._todecimal(error[0])
                lowerError = self._todecimal(error[1])
            else:
                upperError = lowerError = self._todecimal(error)

            self.upperBound = self.amount + upperError
            self.lowerBound = self.amount - lowerError

    @property
    def unit(self):
        """Return _unit's entity uri or '1' if _unit is None."""
        if isinstance(self._unit, ItemPage):
            return self._unit.concept_uri()
        return self._unit or '1'

    def get_unit_item(self, repo: Optional[DataSite] = None,
                      lazy_load: bool = False):
        """
        Return the ItemPage corresponding to the unit.

        Note that the unit need not be in the same data repository as the
        WbQuantity itself.

        A successful lookup is stored as an internal value to avoid the need
        for repeated lookups.

        :param repo: the Wikibase site for the unit, if different from that
            provided with the WbQuantity.
        :param lazy_load: Do not raise NoPage if ItemPage does not exist.
        :return: pywikibot.ItemPage
        """
        if not isinstance(self._unit, str):
            return self._unit

        repo = repo or self.site
        self._unit = ItemPage.from_entity_uri(repo, self._unit, lazy_load)
        return self._unit

    def toWikibase(self) -> dict:
        """
        Convert the data to a JSON object for the Wikibase API.

        :return: Wikibase JSON
        """
        json = {'amount': self._fromdecimal(self.amount),
                'upperBound': self._fromdecimal(self.upperBound),
                'lowerBound': self._fromdecimal(self.lowerBound),
                'unit': self.unit
                }
        return json

    @classmethod
    def fromWikibase(cls, wb: dict, site: Optional[DataSite] = None):
        """
        Create a WbQuantity from the JSON data given by the Wikibase API.

        :param wb: Wikibase JSON
        :param site: The Wikibase site
        :rtype: pywikibot.WbQuantity
        """
        amount = cls._todecimal(wb['amount'])
        upperBound = cls._todecimal(wb.get('upperBound'))
        lowerBound = cls._todecimal(wb.get('lowerBound'))
        bounds_provided = (upperBound is not None and lowerBound is not None)
        error = None
        if bounds_provided or cls._require_errors(site):
            error = (upperBound - amount, amount - lowerBound)
        if wb['unit'] == '1':
            unit = None
        else:
            unit = wb['unit']
        return cls(amount, unit, error, site)


class WbMonolingualText(_WbRepresentation):
    """A Wikibase monolingual text representation."""

    _items = ('text', 'language')

    def __init__(self, text: str, language: str):
        """
        Create a new WbMonolingualText object.

        :param text: text string
        :param language: language code of the string
        """
        if not text or not language:
            raise ValueError('text and language cannot be empty')
        self.text = text
        self.language = language

    def toWikibase(self) -> dict:
        """
        Convert the data to a JSON object for the Wikibase API.

        :return: Wikibase JSON
        """
        json = {'text': self.text,
                'language': self.language
                }
        return json

    @classmethod
    def fromWikibase(cls, wb: dict):
        """
        Create a WbMonolingualText from the JSON data given by Wikibase API.

        :param wb: Wikibase JSON
        :rtype: pywikibot.WbMonolingualText
        """
        return cls(wb['text'], wb['language'])


class _WbDataPage(_WbRepresentation):
    """
    A Wikibase representation for data pages.

    A temporary implementation until T162336 has been resolved.

    Note that this class cannot be used directly
    """

    _items = ('page', )

    @classmethod
    def _get_data_site(cls, repo_site: DataSite) -> APISite:
        """
        Return the site serving as a repository for a given data type.

        Must be implemented in the extended class.

        :param repo_site: The Wikibase site
        """
        raise NotImplementedError

    @classmethod
    def _get_type_specifics(cls, site: DataSite) -> dict:
        """
        Return the specifics for a given data type.

        Must be implemented in the extended class.

        The dict should have three keys:

        * ending: str, required filetype-like ending in page titles.
        * label: str, describing the data type for use in error messages.
        * data_site: APISite, site serving as a repository for
            the given data type.

        :param site: The Wikibase site
        """
        raise NotImplementedError

    @staticmethod
    def _validate(page, data_site, ending: str, label: str):
        """
        Validate the provided page against general and type specific rules.

        :param page: Page containing the data.
        :type page: pywikibot.Page
        :param data_site: The site serving as a repository for the given
            data type.
        :type data_site: APISite
        :param ending: Required filetype-like ending in page titles.
            E.g. '.map'
        :param label: Label describing the data type in error messages.
        """
        if not isinstance(page, Page):
            raise ValueError(
                'Page {} must be a pywikibot.Page object not a {}.'
                .format(page, type(page)))

        # validate page exists
        if not page.exists():
            raise ValueError('Page {} must exist.'.format(page))

        # validate page is on the right site, and that site supports the type
        if not data_site:
            raise ValueError(
                'The provided site does not support {}.'.format(label))
        if page.site != data_site:
            raise ValueError(
                'Page must be on the {} repository site.'.format(label))

        # validate page title fulfills hard-coded Wikibase requirement
        # pcre regexp: '/^Data:[^\\[\\]#\\\:{|}]+\.map$/u' for geo-shape
        # pcre regexp: '/^Data:[^\\[\\]#\\\:{|}]+\.tab$/u' for tabular-data
        # As we have already checked for existence the following simplified
        # check should be enough.
        if not page.title().startswith('Data:') \
           or not page.title().endswith(ending):
            raise ValueError(
                "Page must be in 'Data:' namespace and end in '{}' "
                'for {}.'.format(ending, label))

    def __init__(self, page, site: Optional[DataSite] = None):
        """
        Create a new _WbDataPage object.

        :param page: page containing the data
        :type page: pywikibot.Page
        :param site: The Wikibase site
        """
        site = site or Site().data_repository()
        specifics = type(self)._get_type_specifics(site)
        _WbDataPage._validate(page, specifics['data_site'],
                              specifics['ending'], specifics['label'])
        self.page = page

    def __hash__(self):
        """Override super.hash() as toWikibase is a string for _WbDataPage."""
        return hash(self.toWikibase())

    def toWikibase(self) -> str:
        """
        Convert the data to the value required by the Wikibase API.

        :return: title of the data page incl. namespace
        """
        return self.page.title()

    @classmethod
    def fromWikibase(cls, page_name: str, site: DataSite):
        """
        Create a _WbDataPage from the JSON data given by the Wikibase API.

        :param page_name: page name from Wikibase value
        :param site: The Wikibase site
        :rtype: pywikibot._WbDataPage
        """
        data_site = cls._get_data_site(site)
        page = Page(data_site, page_name)
        return cls(page, site)


class WbGeoShape(_WbDataPage):
    """A Wikibase geo-shape representation."""

    @classmethod
    def _get_data_site(cls, site: DataSite) -> APISite:
        """
        Return the site serving as a geo-shape repository.

        :param site: The Wikibase site
        """
        return site.geo_shape_repository()

    @classmethod
    def _get_type_specifics(cls, site: DataSite) -> dict:
        """
        Return the specifics for WbGeoShape.

        :param site: The Wikibase site
        """
        specifics = {
            'ending': '.map',
            'label': 'geo-shape',
            'data_site': cls._get_data_site(site)
        }
        return specifics


class WbTabularData(_WbDataPage):
    """A Wikibase tabular-data representation."""

    @classmethod
    def _get_data_site(cls, site: DataSite) -> APISite:
        """
        Return the site serving as a tabular-data repository.

        :param site: The Wikibase site
        """
        return site.tabular_data_repository()

    @classmethod
    def _get_type_specifics(cls, site: DataSite) -> dict:
        """
        Return the specifics for WbTabularData.

        :param site: The Wikibase site
        """
        specifics = {
            'ending': '.tab',
            'label': 'tabular-data',
            'data_site': cls._get_data_site(site)
        }
        return specifics


class WbUnknown(_WbRepresentation):
    """
    A Wikibase representation for unknown data type.

    This will prevent the bot from breaking completely when a new type
    is introduced.

    This data type is just a json container

    *New in version 3.0.*
    """

    _items = ('json',)

    def __init__(self, json):
        """
        Create a new WbUnknown object.

        :param json: Wikibase JSON
        """
        self.json = json

    def toWikibase(self) -> dict:
        """
        Return the JSON object for the Wikibase API.

        :return: Wikibase JSON
        """
        return self.json

    @classmethod
    def fromWikibase(cls, json: dict):
        """
        Create a WbUnknown from the JSON data given by the Wikibase API.

        :param json: Wikibase JSON
        :rtype: pywikibot.WbUnknown
        """
        return cls(json)


_sites = {}


@cache
def _code_fam_from_url(url: str, name: Optional[str] = None):
    """Set url to cache and get code and family from cache.

    Site helper method.
    :param url: The site URL to get code and family
    :param name: A family name used by AutoFamily
    """
    matched_sites = []
    # Iterate through all families and look, which does apply to
    # the given URL
    for fam in _config.family_files:
        family = Family.load(fam)
        code = family.from_url(url)
        if code is not None:
            matched_sites.append((code, family))

    if not matched_sites:
        if not name:  # create a name from url
            name = urlparse(url).netloc.split('.')[-2]
            name = removesuffix(name, 'wiki')
        family = AutoFamily(name, url)
        matched_sites.append((family.code, family))

    if len(matched_sites) > 1:
        warning('Found multiple matches for URL "{}": {} (use first)'
                .format(url, ', '.join(str(s) for s in matched_sites)))
    return matched_sites[0]


@_deprecate_arg('sysop', True)
def Site(code: Optional[str] = None, fam=None, user: Optional[str] = None, *,
         interface=None,
         url: Optional[str] = None) -> Union[APISite, DataSite, ClosedSite]:
    """A factory method to obtain a Site object.

    Site objects are cached and reused by this method.

    By default rely on config settings. These defaults may all be overridden
    using the method parameters.

    Creating the default site using config.mylang and config.family::

        site = pywikibot.Site()

    Override default site code::

        site = pywikibot.Site('fr')

    Override default family::

        site = pywikibot.Site(family='wikisource')

    Setting a specific site::

        site = pywikibot.Site('fr', 'wikisource')

    which is equal to::

        site = pywikibot.Site('wikisource:fr')

    :Note: An already created site is cached an a new variable points to
        the same object if interface, family, code and user are equal:

    >>> import pywikibot
    >>> site_1 = pywikibot.Site('wikisource:fr')
    >>> site_2 = pywikibot.Site('fr', 'wikisource')
    >>> site_1 is site_2
    True
    >>> site_1
    APISite("fr", "wikisource")

    ``APISite`` is the default interface. Refer :py:obj:`pywikibot.site` for
    other interface types.

    **Never create a site object via interface class directly.**
    Always use this factory method.

    :param code: language code (override config.mylang)
        code may also be a sitename like 'wikipedia:test'
    :param fam: family name or object (override config.family)
    :type fam: str or pywikibot.family.Family
    :param user: bot user name to use on this site (override config.usernames)
    :param interface: site class or name of class in :py:obj:`pywikibot.site`
        (override config.site_interface)
    :type interface: subclass of :py:obj:`pywikibot.site.BaseSite` or string
    :param url: Instead of code and fam, does try to get a Site based on the
        URL. Still requires that the family supporting that URL exists.
    :raises ValueError: URL and pair of code and family given
    :raises ValueError: Invalid interface name
    """
    _logger = 'wiki'

    if url:
        # Either code and fam or url with optional fam for AutoFamily name
        if code:
            raise ValueError(
                'URL to the wiki OR a pair of code and family name '
                'should be provided')
        code, fam = _code_fam_from_url(url, fam)
    elif code and ':' in code:
        if fam:
            raise ValueError(
                'sitename OR a pair of code and family name '
                'should be provided')
        fam, _, code = code.partition(':')
    else:
        # Fallback to config defaults
        code = code or _config.mylang
        fam = fam or _config.family

    if not isinstance(fam, Family):
        fam = Family.load(fam)

    interface = interface or fam.interface(code)

    # config.usernames is initialised with a defaultdict for each family name
    family_name = str(fam)

    code_to_user = {}
    if '*' in _config.usernames:  # T253127: usernames is a defaultdict
        code_to_user = _config.usernames['*'].copy()
    code_to_user.update(_config.usernames[family_name])
    user = user or code_to_user.get(code) or code_to_user.get('*')

    if not isinstance(interface, type):
        # If it isn't a class, assume it is a string
        try:
            tmp = __import__('pywikibot.site', fromlist=[interface])
        except ImportError:
            raise ValueError('Invalid interface name: {}'.format(interface))
        else:
            interface = getattr(tmp, interface)

    if not issubclass(interface, BaseSite):
        warning('Site called with interface={}'.format(interface.__name__))

    user = normalize_username(user)
    key = '{}:{}:{}:{}'.format(interface.__name__, fam, code, user)
    if key not in _sites or not isinstance(_sites[key], interface):
        _sites[key] = interface(code=code, fam=fam, user=user)
        debug("Instantiated {} object '{}'"
              .format(interface.__name__, _sites[key]), _logger)

        if _sites[key].code != code:
            warn('Site {} instantiated using different code "{}"'
                 .format(_sites[key], code), UserWarning, 2)

    return _sites[key]


# These imports depend on Wb* classes above.
from pywikibot.page import (  # noqa: E402
    Category,
    Claim,
    FilePage,
    ItemPage,
    Link,
    Page,
    PropertyPage,
    SiteLink,
    User,
    html2unicode,
    url2unicode,
)


link_regex = re.compile(r'\[\[(?P<title>[^\]|[<>{}]*)(\|.*?)?\]\]')


def showDiff(oldtext, newtext, context=0):
    """
    Output a string showing the differences between oldtext and newtext.

    The differences are highlighted (only on compatible systems) to show which
    changes were made.
    """
    PatchManager(oldtext, newtext, context=context).print_hunks()


# Throttle and thread handling


def sleep(secs):
    """Suspend execution of the current thread for the given number of seconds.

    Drop this process from the throttle log if wait time is greater than
    30 seconds.
    """
    if secs >= 30:
        stopme()
    time.sleep(secs)


def stopme():
    """
    Drop this process from the throttle log, after pending threads finish.

    Can be called manually if desired. Does not clean async_manager.
    This should be run when a bot does not interact with the Wiki, or
    when it has stopped doing so. After a bot has run stopme() it will
    not slow down other bots any more.
    """
    _flush(False)


def _flush(stop=True):
    """
    Drop this process from the throttle log, after pending threads finish.

    Wait for the page-putter to flush its queue. Also drop this process from
    the throttle log. Called automatically at Python exit.
    """
    _logger = 'wiki'

    debug('_flush() called', _logger)

    def remaining():
        remainingPages = page_put_queue.qsize()
        if stop:
            # -1 because we added a None element to stop the queue
            remainingPages -= 1

        remainingSeconds = datetime.timedelta(
            seconds=round(remainingPages * _config.put_throttle))
        return (remainingPages, remainingSeconds)

    if stop:
        # None task element leaves async_manager
        page_put_queue.put((None, [], {}))

    num, sec = remaining()
    if num > 0 and sec.total_seconds() > _config.noisysleep:
        output(color_format(
            '{lightblue}Waiting for {num} pages to be put. '
            'Estimated time remaining: {sec}{default}', num=num, sec=sec))

    if _putthread is not threading.current_thread():
        while (_putthread.is_alive()
               and (page_put_queue.qsize() > 0
                    or page_put_queue_busy.qsize() > 0)):
            try:
                _putthread.join(1)
            except KeyboardInterrupt:
                if input_yn('There are {} pages remaining in the queue. '
                            'Estimated time remaining: {}\nReally exit?'
                            .format(*remaining()),
                            default=False, automatic_quit=False):
                    break

    # only need one drop() call because all throttles use the same global pid
    with suppress(IndexError):
        list(_sites.values())[0].throttle.drop()
        log('Dropped throttle(s).')


atexit.register(_flush)


# Create a separate thread for asynchronous page saves (and other requests)
def async_manager():
    """Daemon; take requests from the queue and execute them in background."""
    while True:
        (request, args, kwargs) = page_put_queue.get()
        page_put_queue_busy.put(None)
        if request is None:
            break
        request(*args, **kwargs)
        page_put_queue.task_done()
        page_put_queue_busy.get()


def async_request(request, *args, **kwargs):
    """Put a request on the queue, and start the daemon if necessary."""
    if not _putthread.is_alive():
        try:
            page_put_queue.mutex.acquire()
            with suppress(AssertionError, RuntimeError):
                _putthread.start()
        finally:
            page_put_queue.mutex.release()
    page_put_queue.put((request, args, kwargs))


# queue to hold pending requests
page_put_queue = Queue(_config.max_queue_size)
# queue to signal that async_manager is working on a request. See T147178.
page_put_queue_busy = Queue(_config.max_queue_size)
# set up the background thread
_putthread = threading.Thread(target=async_manager)
# identification for debugging purposes
_putthread.setName('Put-Thread')
_putthread.setDaemon(True)

wrapper = _ModuleDeprecationWrapper(__name__)
wrapper.add_deprecated_attr('config2', replacement_name='pywikibot.config',
                            since='20210426', future_warning=True)
wrapper.add_deprecated_attr('__release__', __version__,
                            replacement_name='pywikibot.__version__',
                            since='20200707')
wrapper.add_deprecated_attr('showHelp', show_help,
                            since='20200705', future_warning=True)
wrapper.add_deprecated_attr(
    'unicode2html', replacement_name='pywikibot.tools.chars.string2html',
    since='6.2.0', future_warning=True)

# This module aliases many (but not all) pywikibot.exception classes and one
# from pywikibot.data.api. Use of these aliases is deprecated. When removed
# we can drop them from both our import and __all__ listing.

EXCEPTION_CLASSES = {
    n for n, _ in inspect.getmembers(exceptions, inspect.isclass)
}

EXCEPTION_CLASSES.add('UploadWarning')
EXCEPTION_CLASSES.update(DEPRECATED_EXCEPTIONS.keys())

for name in __all__:
    if name in EXCEPTION_CLASSES:
        if name in DEPRECATED_EXCEPTIONS:
            replacement = DEPRECATED_EXCEPTIONS[name]
        elif name == 'UploadWarning':
            replacement = 'UploadError'
        else:
            replacement = name

        wrapper.add_deprecated_attr(
            name,
            replacement_name='pywikibot.exceptions.{}'.format(replacement),
            since='20210424', future_warning=True
        )
