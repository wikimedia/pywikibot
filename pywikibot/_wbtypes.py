"""Wikibase data type classes."""
#
# (C) Pywikibot team, 2013-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import abc
import datetime
import json
import math
import re
from collections.abc import Mapping
from contextlib import suppress
from decimal import Decimal
from typing import TYPE_CHECKING, Any, cast

import pywikibot
from pywikibot import exceptions
from pywikibot.backports import Iterator
from pywikibot.time import Timestamp
from pywikibot.tools import (
    deprecated_signature,
    issue_deprecation_warning,
    remove_last_args,
)


if TYPE_CHECKING:
    from typing import Union

    from pywikibot.site import APISite, BaseSite, DataSite

    ItemPageStrNoneType = Union[str, pywikibot.ItemPage, None]
    ToDecimalType = Union[int, float, str, Decimal, None]


__all__ = (
    'Coordinate',
    'WbGeoShape',
    'WbMonolingualText',
    'WbQuantity',
    'WbTabularData',
    'WbTime',
    'WbUnknown',
)


class WbRepresentation(abc.ABC):

    """Abstract class for Wikibase representations."""

    _items: tuple[str, ...]

    @abc.abstractmethod
    def __init__(self) -> None:
        """Initializer."""
        raise NotImplementedError

    @abc.abstractmethod
    def toWikibase(self) -> Any:
        """Convert representation to JSON for the Wikibase API."""
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def fromWikibase(
        cls,
        data: dict[str, Any],
        site: DataSite | None = None,
    ) -> WbRepresentation:
        """Create a representation object based on JSON from Wikibase API."""
        raise NotImplementedError

    def __str__(self) -> str:
        return json.dumps(
            self.toWikibase(),
            indent=4,
            sort_keys=True,
            separators=(',', ': ')
        )

    def __repr__(self) -> str:
        """String representation of this object.

        .. versionchanged:: 10.4
           Parameters are shown as representations instead of plain
           strings.

        :meta public:
        """
        assert isinstance(self._items, tuple)
        assert all(isinstance(item, str) for item in self._items)

        attrs = ', '.join(f'{attr}={getattr(self, attr)!r}'
                          for attr in self._items)
        return f'{type(self).__name__}({attrs})'

    def __eq__(self, other: object) -> bool:
        if isinstance(other, self.__class__):
            return self.toWikibase() == other.toWikibase()

        return NotImplemented

    def __hash__(self) -> int:
        return hash(json.dumps(self.toWikibase(), sort_keys=True))


class Coordinate(WbRepresentation):

    """Class for handling and storing Coordinates."""

    _items = ('lat', 'lon', 'entity')

    @deprecated_signature(since='10.4.0')
    def __init__(
        self,
        lat: float,
        lon: float,
        *,
        alt: float | None = None,
        precision: float | None = None,
        globe: str | None = None,
        typ: str = '',
        name: str = '',
        dim: int | None = None,
        site: DataSite | None = None,
        globe_item: ItemPageStrNoneType = None,
        primary: bool = False
    ) -> None:
        """Represent a geo coordinate.

        .. versionchanged:: 10.4
           The parameters after `lat` and `lon` are now keyword-only.

        :param lat: Latitude coordinate
        :param lon: Longitude coordinate
        :param alt: Altitude in meters
        :param precision: Precision of the coordinate
        :param globe: The globe the coordinate is on (e.g. 'earth')
        :param typ: Type of coordinate point
        :param name: Name associated with the coordinate
        :param dim: Dimension in meters used for precision calculation
        :param site: The Wikibase site instance
        :param globe_item: Wikibase item or entity URI for the globe;
            takes precedence over *globe*
        :param primary: Indicates if this is a primary coordinate set
            (default: False)
        """
        self.lat = lat
        self.lon = lon
        self.alt = alt
        self._precision = precision
        self._entity = globe_item
        self.type = typ
        self.name = name
        self._dim = dim
        self.site = site or pywikibot.Site().data_repository()
        self.primary = primary

        if globe:
            globe = globe.lower()
        elif not globe_item:
            globe = self.site.default_globe()
        self.globe = globe

    @property
    def entity(self) -> str:
        """Return the entity URI of the globe.

        :raises CoordinateGlobeUnknownError: the globe is not supported
            by Wikibase
        """
        if not self._entity:
            if self.globe not in self.site.globes():
                raise exceptions.CoordinateGlobeUnknownError(
                    f'{self.globe} is not supported in Wikibase yet.')

            return self.site.globes()[self.globe]

        if isinstance(self._entity, pywikibot.ItemPage):
            return self._entity.concept_uri()

        return self._entity

    def toWikibase(self) -> dict[str, Any]:
        """Export the data to a JSON object for the Wikibase API.

        :return: Wikibase JSON representation of the coordinate
        """
        return {
            'latitude': self.lat,
            'longitude': self.lon,
            'altitude': self.alt,
            'globe': self.entity,
            'precision': self.precision,
        }

    @classmethod
    def fromWikibase(cls, data: dict[str, Any],
                     site: DataSite | None = None) -> Coordinate:
        """Create an object from Wikibase's JSON output.

        :param data: Wikibase JSON data
        :param site: The Wikibase site instance
        :return: Coordinate instance
        """
        site = site or pywikibot.Site().data_repository()
        globe = None

        if data.get('globe'):
            globes = {entity: name for name, entity in site.globes().items()}
            globe = globes.get(data['globe'])

        return cls(
            data['latitude'],
            data['longitude'],
            alt=data.get('altitude'),
            precision=data.get('precision'),
            globe=globe,
            site=site,
            globe_item=data.get('globe')
        )

    @property
    def precision(self) -> float | None:
        """Return the precision of the geo coordinate.

        The precision is calculated if the Coordinate does not have a
        precision, and self._dim is set.

        When no precision and no self._dim exists, None is returned.

        The biggest error (in degrees) will be given by the longitudinal
        error; the same error in meters becomes larger (in degrees)
        further up north. We can thus ignore the latitudinal error.

        The longitudinal can be derived as follows:

        In small angle approximation (and thus in radians):

        :math:`M{Δλ ≈ Δpos / r_φ}`, where :math:`r_φ` is the radius of
        earth at the given latitude. :math:`Δλ` is the error in
        longitude.

        :math:`M{r_φ = r cos(φ)}`, where :math:`r` is the radius of
        earth, :math:`φ` the latitude

        Therefore:

        .. code-block:: python

           precision = math.degrees(
               self._dim / (radius * math.cos(math.radians(self.lat))))

        :return: precision in degrees or None
        """
        if self._precision is not None:
            return self._precision

        if self._dim is None:
            return None

        radius = 6378137  # Earth radius in meters (TODO: support other globes)
        with suppress(ZeroDivisionError):
            self._precision = math.degrees(
                self._dim / (radius * math.cos(math.radians(self.lat))))

        return self._precision

    @precision.setter
    def precision(self, value: float) -> None:
        """Set the precision value.

        :param value: precision in degrees
        """
        self._precision = value

    def precisionToDim(self) -> int | None:
        """Convert precision from Wikibase to GeoData's dim.

        dim is calculated if the Coordinate doesn't have a dimension, and
        precision is set. When neither dim nor precision are set, ValueError
        is thrown.

        Carrying on from the earlier derivation of precision, since

        .. code-block:: python

           precision = math.degrees(
               dim / (radius * math.cos(math.radians(self.lat))))

        we get:

        .. code-block:: python

           dim = math.radians(
               precision) * radius * math.cos(math.radians(self.lat))

        But this is not valid, since it returns a float value for dim which is
        an integer. We must round it off to the nearest integer.

        Therefore:

        .. code-block:: python

           dim = int(round(math.radians(
               precision)*radius*math.cos(math.radians(self.lat))))

        :return: dimension in meters
        :raises ValueError: if neither dim nor precision is set
        """
        if self._dim is not None:
            return self._dim

        if self._precision is None:
            raise ValueError('No values set for dim or precision')

        radius = 6378137
        self._dim = int(
            round(
                math.radians(self._precision) * radius * math.cos(
                    math.radians(self.lat))
            )
        )
        return self._dim

    @deprecated_signature(since='10.4.0')
    def get_globe_item(self, repo: DataSite | None = None, *,
                       lazy_load: bool = False) -> pywikibot.ItemPage:
        """Return the ItemPage corresponding to the globe.

        .. note:: The globe need not be in the same data repository as
           the Coordinate itself.

        A successful lookup is stored as an internal value to avoid the
        need for repeated lookups.

        .. versionchanged:: 10.4
           The *lazy_load* parameter is now keyword-only.

        :param repo: the Wikibase site for the globe, if different from
            that provided with the Coordinate
        :param lazy_load: Do not raise :exc:`exceptions.NoPageError` if
            ItemPage does not exist
        :return: pywikibot.ItemPage of the globe
        """
        if isinstance(self._entity, pywikibot.ItemPage):
            return self._entity

        repo = repo or self.site
        return pywikibot.ItemPage.from_entity_uri(repo, self.entity, lazy_load)


class _Precision(Mapping):

    """Wrapper for WbTime.PRECISION to deprecate 'millenia' key."""

    PRECISION = {
        '1000000000': 0,
        '100000000': 1,
        '10000000': 2,
        '1000000': 3,
        '100000': 4,
        '10000': 5,
        'millennium': 6,
        'century': 7,
        'decade': 8,
        'year': 9,
        'month': 10,
        'day': 11,
        'hour': 12,
        'minute': 13,
        'second': 14,
    }

    def __getitem__(self, key: str) -> int:
        if key == 'millenia':
            issue_deprecation_warning(
                f'{key!r} key for precision', "'millennium'", since='10.0.0')
            return self.PRECISION['millennium']

        return self.PRECISION[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self.PRECISION)

    def __len__(self) -> int:
        return len(self.PRECISION)


class WbTime(WbRepresentation):

    """A Wikibase time representation.

    Make a WbTime object from the current time:

    .. code-block:: python

        current_ts = pywikibot.Timestamp.now()
        wbtime = pywikibot.WbTime.fromTimestamp(current_ts)

    For converting python datetime objects to WbTime objects, see
    :class:`pywikibot.Timestamp` and :meth:`fromTimestamp`.
    """

    month: int
    day: int
    hour: int
    minute: int
    second: int

    PRECISION = _Precision()

    FORMATSTR = '{0:+012d}-{1:02d}-{2:02d}T{3:02d}:{4:02d}:{5:02d}Z'

    _items = ('year', 'month', 'day', 'hour', 'minute', 'second',
              'precision', 'before', 'after', 'timezone', 'calendarmodel')

    _month_offset = {
        1: 0,
        2: 31,  # Jan -> Feb: 31 days
        3: 59,  # Feb -> Mar: 28 days, plus 31 days in Jan -> Feb
        4: 90,  # Mar -> Apr: 31 days, plus 59 days in Jan -> Mar
        5: 120,  # Apr -> May: 30 days, plus 90 days in Jan -> Apr
        6: 151,  # May -> Jun: 31 days, plus 120 days in Jan -> May
        7: 181,  # Jun -> Jul: 30 days, plus 151 days in Jan -> Jun
        8: 212,  # Jul -> Aug: 31 days, plus 181 days in Jan -> Jul
        9: 243,  # Aug -> Sep: 31 days, plus 212 days in Jan -> Aug
        10: 273,  # Sep -> Oct: 30 days, plus 243 days in Jan -> Sep
        11: 304,  # Oct -> Nov: 31 days, plus 273 days in Jan -> Oct
        12: 334,  # Nov -> Dec: 30 days, plus 304 days in Jan -> Nov
    }

    _timestr_re = re.compile(
        r'([-+]?\d{1,16})-(\d{2})-(\d{2})T(\d{2}):(\d{2}):(\d{2})Z')

    @deprecated_signature(since='10.4.0')
    def __init__(
        self,
        year: int,
        month: int | None = None,
        day: int | None = None,
        hour: int | None = None,
        minute: int | None = None,
        second: int | None = None,
        *,
        precision: int | str | None = None,
        before: int = 0,
        after: int = 0,
        timezone: int = 0,
        calendarmodel: str | None = None,
        site: DataSite | None = None
    ) -> None:
        """Create a new WbTime object.

        The precision can be set by the Wikibase int value (0-14) or by
        a human readable string, e.g., ``hour``. If no precision is
        given, it is set according to the given time units.

        Timezone information is given in three different ways depending
        on the time:

        * Times after the implementation of UTC (1972): as an offset
          from UTC in minutes;
        * Times before the implementation of UTC: the offset of the time
          zone from universal time;
        * Before the implementation of time zones: The longitude of the
          place of the event, in the range −180° to 180°, multiplied by
          4 to convert to minutes.

        .. note::  **Comparison information:** When using the greater
           than or equal to operator, or the less than or equal to
           operator, two different time objects with the same UTC time
           after factoring in timezones are considered equal. However,
           the equality operator will return false if the timezone is
           different.

        .. deprecated:: 10.0
           *precision* value 'millenia' is deprecated; 'millennium' must
           be used instead.

        .. versionchanged:: 10.4
           The parameters except timestamp values are now keyword-only.
           A TypeError is raised if *year* is not an int. Previously, a
           ValueError was raised if *year* was None.

        :param year: The year as a signed integer of between 1 and 16
            digits.
        :param month: Month of the timestamp, if it exists.
        :param day: Day of the timestamp, if it exists.
        :param hour: Hour of the timestamp, if it exists.
        :param minute: Minute of the timestamp, if it exists.
        :param second: Second of the timestamp, if it exists.
        :param precision: The unit of the precision of the time. Must be
            either an int in range 0 - 14 or one of '1000000000',
            '100000000', '10000000', '1000000', '100000', '10000',
            'millennium', 'century', 'decade', 'year', month', 'day',
            'hour', 'minute' or 'second'.
        :param before: Number of units after the given time it could be,
            if uncertain. The unit is given by the precision.
        :param after: Number of units before the given time it could be,
            if uncertain. The unit is given by the precision.
        :param timezone: Timezone information in minutes.
        :param calendarmodel: URI identifying the calendar model.
        :param site: The Wikibase site. If not provided, retrieves the
            data repository from the default site from user-config.py.
            Only used if calendarmodel is not given.
        :raises TypeError: Invalid *year* type.
        :raises ValueError: Invalid *precision* or *site* or default
            site has no data repository.
        """
        if not isinstance(year, int):
            raise TypeError(f'year must be an int, not {type(year).__name__}')

        units = [
            ('month', month, 1),
            ('day', day, 1),
            ('hour', hour, 0),
            ('minute', minute, 0),
            ('second', second, 0),
        ]

        # set unit attribute values
        self.year = year
        for unit, value, default in units:
            setattr(self, unit, value if value is not None else default)

        if precision is None:
            # Autodetection of precision based on the passed time values
            prec = self.PRECISION['year']

            for unit, value, _ in units:
                if value is not None:
                    prec = self.PRECISION[unit]
        else:
            # explicit precision is given
            if (isinstance(precision, int)
                    and precision in self.PRECISION.values()):
                prec = precision
            elif isinstance(precision, str) and precision in self.PRECISION:
                prec = self.PRECISION[cast(str, precision)]
            else:
                raise ValueError(f'Invalid precision: "{precision}"')

        self.precision = prec
        self.after = after
        self.before = before
        self.timezone = timezone
        if calendarmodel is None:
            site = site or pywikibot.Site().data_repository()
            if site is None:
                raise ValueError(
                    f'Site {pywikibot.Site()} has no data repository')
            calendarmodel = site.calendarmodel()

        self.calendarmodel = calendarmodel

    def _getSecondsAdjusted(self) -> int:
        """Return an internal representation of the time object as seconds.

        The value adjusts itself for timezones. It is not compatible
        with before/after.

        This value should *only* be used for comparisons, and its value
        may change without warning.

        .. versionadded:: 8.0

        :return: An integer roughly representing the number of seconds
            since January 1, 0000 AD, adjusted for leap years.
        """
        # This function ignores leap seconds. Since it is not required
        # to correlate to an actual UNIX timestamp, this is acceptable.

        # We are always required to have a year.
        elapsed_seconds = int(self.year * 365.25 * 24 * 60 * 60)
        if self.month > 1:
            elapsed_seconds += self._month_offset[self.month] * 24 * 60 * 60
            # The greogrian calendar
            if (self.calendarmodel == 'http://www.wikidata.org/entity/Q1985727'
                and (self.year % 400 == 0
                     or (self.year % 4 == 0 and self.year % 100 != 0)
                     and self.month > 2)):
                elapsed_seconds += 24 * 60 * 60  # Leap year
            # The julian calendar
            if (self.calendarmodel == 'http://www.wikidata.org/entity/Q1985786'
                    and self.year % 4 == 0 and self.month > 2):
                elapsed_seconds += 24 * 60 * 60
        if self.day > 1:
            # Days start at 1, not 0.
            elapsed_seconds += (self.day - 1) * 24 * 60 * 60
        elapsed_seconds += self.hour * 60 * 60
        elapsed_seconds += self.minute * 60
        elapsed_seconds += self.second
        if self.timezone is not None:
            # See T325866
            elapsed_seconds -= self.timezone * 60
        return elapsed_seconds

    def __lt__(self, other: object) -> bool:
        """Compare if self is less than other.

        .. versionadded:: 8.0
        """
        if isinstance(other, WbTime):
            return self._getSecondsAdjusted() < other._getSecondsAdjusted()
        return NotImplemented

    def __le__(self, other: object) -> bool:
        """Compare if self is less equals other.

        .. versionadded:: 8.0
        """
        if isinstance(other, WbTime):
            return self._getSecondsAdjusted() <= other._getSecondsAdjusted()
        return NotImplemented

    def __gt__(self, other: object) -> bool:
        """Compare if self is greater than other.

        .. versionadded:: 8.0
        """
        if isinstance(other, WbTime):
            return self._getSecondsAdjusted() > other._getSecondsAdjusted()
        return NotImplemented

    def __ge__(self, other: object) -> bool:
        """Compare if self is greater equals other.

        .. versionadded:: 8.0
        """
        if isinstance(other, WbTime):
            return self._getSecondsAdjusted() >= other._getSecondsAdjusted()
        return NotImplemented

    def equal_instant(self, other: WbTime) -> bool:
        """Checks if the two times represent the same instant in time.

        This is different from the equality operator, which will return false
        for two times that are the same number of UTC seconds, but with
        different timezone information.

        For example, a time with at 10:00 UTC-5 would return false if checked
        with == with a time at 15:00 UTC, but would return true with
        this method.

        .. versionadded:: 9.0
        """
        return self._getSecondsAdjusted() == other._getSecondsAdjusted()

    @classmethod
    @deprecated_signature(since='10.4.0')
    def fromTimestr(
        cls,
        datetimestr: str,
        *,
        precision: int | str = 14,
        before: int = 0,
        after: int = 0,
        timezone: int = 0,
        calendarmodel: str | None = None,
        site: DataSite | None = None
    ) -> WbTime:
        """Create a new WbTime object from a UTC date/time string.

        The timestamp format must match a string resembling ISO 8601
        with the following constraints:

        - Year is signed and can have between 1 and 16 digits.
        - Month, day, hour, minute and second are always two digits.
          They may be zero.
        - Time is always in UTC and ends with ``Z``.
        - Example: ``+0000000000123456-01-01T00:00:00Z``.

        .. versionchanged:: 10.4
           The parameters except *datetimestr* are now keyword-only.

        :param datetimestr: Timestamp string to parse
        :param precision: The unit of the precision of the time. Defaults
            to 14 (second).
        :param before: Number of units after the given time it could be,
            if uncertain. The unit is given by the precision.
        :param after: Number of units before the given time it could be,
            if uncertain. The unit is given by the precision.
        :param timezone: Timezone offset in minutes.
        :param calendarmodel: URI identifying the calendar model.
        :param site: The Wikibase site. If not provided, retrieves the
            data repository from the default site from user-config.py.
            Only used if calendarmodel is not given.
        :raises ValueError: If the string does not match the expected
            format.
        """
        match = cls._timestr_re.match(datetimestr)
        if not match:
            raise ValueError(f"Invalid format: '{datetimestr}'")

        t = match.groups()
        return cls(int(t[0]), int(t[1]), int(t[2]),
                   int(t[3]), int(t[4]), int(t[5]),
                   precision=precision, before=before, after=after,
                   timezone=timezone, calendarmodel=calendarmodel, site=site)

    @classmethod
    @deprecated_signature(since='10.4.0')
    def fromTimestamp(
        cls,
        timestamp: Timestamp,
        *,
        precision: int | str = 14,
        before: int = 0,
        after: int = 0,
        timezone: int = 0,
        calendarmodel: str | None = None,
        site: DataSite | None = None,
        copy_timezone: bool = False
    ) -> WbTime:
        """Create a new WbTime object from a pywikibot.Timestamp.

        .. versionchanged:: 8.0
           Added *copy_timezone* parameter.
        .. versionchanged:: 10.4
           The parameters except *timestamp* are now keyword-only.


        :param timestamp: Timestamp
        :param precision: The unit of the precision of the time.
            Defaults to 14 (second).
        :param before: Number of units after the given time it could be,
            if uncertain. The unit is given by the precision.
        :param after: Number of units before the given time it could be,
            if uncertain. The unit is given by the precision.
        :param timezone: Timezone information in minutes.
        :param calendarmodel: URI identifying the calendar model.
        :param site: The Wikibase site. If not provided, retrieves the
            data repository from the default site from user-config.py.
            Only used if calendarmodel is not given.
        :param copy_timezone: Whether to copy the timezone from the
            timestamp if it has timezone information. Defaults to False
            to maintain backwards compatibility. If a timezone is given,
            timezone information is discarded.
        """
        if not timezone and timestamp.tzinfo and copy_timezone:
            timezone = int(timestamp.utcoffset().total_seconds() / 60)
        return cls.fromTimestr(timestamp.isoformat(), precision=precision,
                               before=before, after=after, timezone=timezone,
                               calendarmodel=calendarmodel, site=site)

    @staticmethod
    def _normalize_millennium(year: int) -> int:
        """Round the given year to the start of its millennium.

        The rounding is performed towards positive infinity for positive
        years and towards negative infinity for negative years.

        .. versionadded:: 10.4

        :param year: The year as an integer.
        :return: The first year of the millennium containing the given
            year.
        """
        # For negative years, floor rounds away from zero to correctly handle
        # BCE dates. For positive years, ceil rounds up to the next
        # millennium/century.
        year_float = year / 1000
        if year_float < 0:
            year = math.floor(year_float)
        else:
            year = math.ceil(year_float)
        return year * 1000

    @staticmethod
    def _normalize_century(year: int) -> int:
        """Round the given year to the start of its century.

        The rounding is performed towards positive infinity for positive
        years and towards negative infinity for negative years.

        .. versionadded:: 10.4

        :param year: The year as an integer.
        :return: The first year of the century containing the given year.
        """
        # For century, -1301 is the same century as -1400 but not -1401.
        # Similar for 1901 and 2000 vs 2001.
        year_float = year / 100
        if year_float < 0:
            year = math.floor(year_float)
        else:
            year = math.ceil(year_float)
        return year * 100

    @staticmethod
    def _normalize_decade(year: int) -> int:
        """Round the given year down to the start of its decade.

        Unlike millennium or century normalization, this always
        truncates towards zero.

        .. versionadded:: 10.4

        :param year: The year as an integer.
        :return: The first year of the decade containing the given year.
        """
        # For decade, -1340 is the same decade as -1349 but not -1350.
        # Similar for 2010 and 2019 vs 2020
        year_float = year / 10
        year = math.trunc(year_float)
        return year * 10

    @staticmethod
    def _normalize_power_of_ten(year: int, precision: int) -> int:
        """Round the year to the given power-of-ten precision.

        This is used for very coarse historical precision levels, where
        the time unit represents a power-of-ten number of years.

        .. versionadded:: 10.4

        :param year: The year as an integer.
        :param precision: The precision level (Wikibase int value).
        :return: The normalized year rounded to the nearest matching
            power-of-ten boundary.
        """
        # Wikidata rounds the number based on the first non-decimal digit.
        # Python's round function will round -15.5 to -16, and +15.5 to +16
        # so we don't need to do anything complicated like the other
        # examples.
        power_of_10 = 10 ** (9 - precision)
        return round(year / power_of_10) * power_of_10

    def normalize(self) -> WbTime:
        """Normalizes the WbTime object to account for precision.

        Normalization is needed because WbTime objects can have hidden
        values that affect naive comparisons, such as an object set to
        a precision of YEAR but containing a month and day value.

        This function returns a new normalized object and does not do
        any modification in place.

        Normalization will delete timezone information if the precision
        is less than or equal to DAY.

        .. note:: Normalized WbTime objects can only be compared to
           other normalized WbTime objects of the same precision.
           Normalization might make a WbTime object that was less than
           another WbTime object before normalization, greater than it
           after normalization, or vice versa.
        """
        year = self.year
        for prec in 'millennium', 'century', 'decade':
            if self.precision == self.PRECISION[prec]:
                handler = getattr(self, '_normalize_' + prec)
                year = handler(year)
                break
        else:
            lower = self.PRECISION['1000000000']
            upper = self.PRECISION['10000']
            if lower <= self.precision <= upper:
                year = self._normalize_power_of_ten(year, self.precision)

        kwargs = {
            'precision': self.precision,
            'before': self.before,
            'after': self.after,
            'calendarmodel': self.calendarmodel,
            'year': year
        }

        for prec in 'month', 'day', 'hour', 'minute', 'second':
            if self.precision >= self.PRECISION[prec]:
                kwargs[prec] = getattr(self, prec)
                if prec == 'hour':
                    # Add timezone, see T326693
                    kwargs['timezone'] = self.timezone

        return type(self)(**kwargs)

    @remove_last_args(['normalize'])  # since 8.2.0
    def toTimestr(self, force_iso: bool = False) -> str:
        """Convert the data to a UTC date/time string.

        .. seealso:: :meth:`fromTimestr` for differences between output
           with and without *force_iso* parameter.

        .. versionchanged:: 8.0
           *normalize* parameter was added.
        .. versionchanged:: 8.2
           *normalize* parameter was removed due to :phab:`T340495` and
           :phab:`T57755`

        :param force_iso: whether the output should be forced to ISO 8601
        :return: Timestamp in a format resembling ISO 8601
        """
        if force_iso:
            return Timestamp._ISO8601Format_new.format(
                self.year, max(1, self.month), max(1, self.day),
                self.hour, self.minute, self.second)
        return self.FORMATSTR.format(self.year, self.month, self.day,
                                     self.hour, self.minute, self.second)

    def toTimestamp(self, timezone_aware: bool = False) -> Timestamp:
        """Convert the data to a pywikibot.Timestamp.

        .. versionchanged:: 8.0.1
           *timezone_aware* parameter was added.

        :param timezone_aware: Whether the timezone should be passed to
            the Timestamp object.
        :raises ValueError: instance value cannot be represented using
            Timestamp
        """
        if self.year <= 0:
            raise ValueError('You cannot turn BC dates into a Timestamp')
        ts = Timestamp.fromISOformat(
            self.toTimestr(force_iso=True).lstrip('+'))
        if timezone_aware:
            ts = ts.replace(tzinfo=datetime.timezone(
                datetime.timedelta(minutes=self.timezone)))
        return ts

    @remove_last_args(['normalize'])  # since 8.2.0
    def toWikibase(self) -> dict[str, Any]:
        """Convert the data to a JSON object for the Wikibase API.

        .. versionchanged:: 8.0
           *normalize* parameter was added.
        .. versionchanged:: 8.2
           *normalize* parameter was removed due to :phab:`T340495` and
           :phab:`T57755`

        :return: Wikibase JSON
        """
        return {
            'time': self.toTimestr(),
            'precision': self.precision,
            'after': self.after,
            'before': self.before,
            'timezone': self.timezone,
            'calendarmodel': self.calendarmodel,
        }

    @classmethod
    def fromWikibase(cls, data: dict[str, Any],
                     site: DataSite | None = None) -> WbTime:
        """Create a WbTime from the JSON data given by the Wikibase API.

        :param data: Wikibase JSON
        :param site: The Wikibase site. If not provided, retrieves the
            data repository from the default site from user-config.py.
        """
        return cls.fromTimestr(
            data['time'],
            precision=data['precision'],
            before=data['before'],
            after=data['after'],
            timezone=data['timezone'],
            calendarmodel=data['calendarmodel'],
            site=site
        )


class WbQuantity(WbRepresentation):

    """A Wikibase quantity representation."""

    _items = ('amount', 'upperBound', 'lowerBound', 'unit')

    @staticmethod
    def _todecimal(value: ToDecimalType) -> Decimal | None:
        """Convert a string to a Decimal for use in WbQuantity.

        None value is returned as is.

        :param value: decimal number to convert
        """
        if isinstance(value, Decimal):
            return value
        if value is None:
            return None
        return Decimal(str(value))

    @staticmethod
    def _fromdecimal(value: Decimal | None) -> str | None:
        """Convert a Decimal to a string representation suitable for WikiBase.

        None value is returned as is.

        :param value: decimal number to convert
        """
        return format(value, '+g') if value is not None else None

    def __init__(
        self, amount: ToDecimalType,
        unit: ItemPageStrNoneType = None,
        error: ToDecimalType | tuple[ToDecimalType, ToDecimalType] = None,
        site: DataSite | None = None,
    ) -> None:
        """Create a new WbQuantity object.

        :param amount: number representing this quantity
        :param unit: the Wikibase item for the unit or the entity URI of
            this Wikibase item.
        :param error: the uncertainty of the amount (e.g. ±1)
        :param site: The Wikibase site
        """
        if amount is None:
            raise ValueError('no amount given')

        self.amount = self._todecimal(amount)
        self._unit = unit
        self.site = site or pywikibot.Site().data_repository()

        # also allow entity URIs to be provided via unit parameter
        if isinstance(unit, str) \
           and not unit.startswith(('http://', 'https://')):
            raise ValueError("'unit' must be an ItemPage or entity uri.")

        if error is None:
            self.upperBound = self.lowerBound = None
        else:
            if isinstance(error, tuple):
                upper_error = self._todecimal(error[0])
                lower_error = self._todecimal(error[1])
            else:
                upper_error = lower_error = self._todecimal(error)

            assert upper_error is not None and lower_error is not None
            assert self.amount is not None

            self.upperBound = self.amount + upper_error
            self.lowerBound = self.amount - lower_error

    @property
    def unit(self) -> str:
        """Return _unit's entity uri or '1' if _unit is None."""
        if isinstance(self._unit, pywikibot.ItemPage):
            return self._unit.concept_uri()
        return self._unit or '1'

    def get_unit_item(self, repo: DataSite | None = None,
                      lazy_load: bool = False) -> pywikibot.ItemPage:
        """Return the ItemPage corresponding to the unit.

        Note that the unit need not be in the same data repository as
        the WbQuantity itself.

        A successful lookup is stored as an internal value to avoid the
        need for repeated lookups.

        :param repo: the Wikibase site for the unit, if different from
            that provided with the WbQuantity.
        :param lazy_load: Do not raise NoPage if ItemPage does not
            exist.
        :return: pywikibot.ItemPage
        """
        if not isinstance(self._unit, str):
            return self._unit

        repo = repo or self.site
        self._unit = pywikibot.ItemPage.from_entity_uri(
            repo, self._unit, lazy_load)
        return self._unit

    def toWikibase(self) -> dict[str, Any]:
        """Convert the data to a JSON object for the Wikibase API.

        :return: Wikibase JSON
        """
        return {
            'amount': self._fromdecimal(self.amount),
            'upperBound': self._fromdecimal(self.upperBound),
            'lowerBound': self._fromdecimal(self.lowerBound),
            'unit': self.unit,
        }

    @classmethod
    def fromWikibase(cls, data: dict[str, Any],
                     site: DataSite | None = None) -> WbQuantity:
        """Create a WbQuantity from the JSON data given by the Wikibase API.

        :param data: Wikibase JSON
        :param site: The Wikibase site
        """
        amount = cls._todecimal(data['amount'])
        upper_bound = cls._todecimal(data.get('upperBound'))
        lower_bound = cls._todecimal(data.get('lowerBound'))
        bounds_provided = (upper_bound is not None and lower_bound is not None)
        error = None
        if bounds_provided:
            error = (upper_bound - amount, amount - lower_bound)
        unit = None if data['unit'] == '1' else data['unit']
        return cls(amount, unit, error, site)


class WbMonolingualText(WbRepresentation):

    """A Wikibase monolingual text representation."""

    _items = ('text', 'language')

    def __init__(self, text: str, language: str) -> None:
        """Create a new WbMonolingualText object.

        :param text: text string
        :param language: language code of the string
        """
        if not text or not language:
            raise ValueError('text and language cannot be empty')
        self.text = text
        self.language = language

    def toWikibase(self) -> dict[str, Any]:
        """Convert the data to a JSON object for the Wikibase API.

        :return: Wikibase JSON
        """
        return {
            'text': self.text,
            'language': self.language,
        }

    @classmethod
    def fromWikibase(cls, data: dict[str, Any],
                     site: DataSite | None = None) -> WbMonolingualText:
        """Create a WbMonolingualText from the JSON data given by Wikibase API.

        :param data: Wikibase JSON
        :param site: The Wikibase site
        """
        return cls(data['text'], data['language'])


class WbDataPage(WbRepresentation):

    """An abstract Wikibase representation for data pages.

    .. warning:: Perhaps a temporary implementation until :phab:`T162336`
       has been resolved.
    .. note:: that this class cannot be used directly.
    """

    _items = ('page', )

    @classmethod
    @abc.abstractmethod
    def _get_data_site(cls, repo_site: DataSite) -> APISite:
        """Return the site serving as a repository for a given data type.

        .. note:: implemented in the extended class.

        :param repo_site: The Wikibase site
        """
        raise NotImplementedError

    @classmethod
    @abc.abstractmethod
    def _get_type_specifics(cls, site: DataSite) -> dict[str, Any]:
        """Return the specifics for a given data type.

        .. note:: Must be implemented in the extended class.

        The dict should have three keys:

        * ending: str, required filetype-like ending in page titles.
        * label: str, describing the data type for use in error messages.
        * data_site: APISite, site serving as a repository for
          the given data type.

        :param site: The Wikibase site
        """
        raise NotImplementedError

    @staticmethod
    def _validate(page: pywikibot.Page, data_site: BaseSite, ending: str,
                  label: str) -> None:
        """Validate the provided page against general and type specific rules.

        :param page: Page containing the data.
        :param data_site: The site serving as a repository for the given
            data type.
        :param ending: Required filetype-like ending in page titles.
            E.g. '.map'
        :param label: Label describing the data type in error messages.
        """
        if not isinstance(page, pywikibot.Page):
            raise ValueError(f'Page {page} must be a pywikibot.Page object '
                             f'not a {type(page)}.')

        # validate page exists
        if not page.exists():
            raise ValueError(f'Page {page} must exist.')

        # validate page is on the right site, and that site supports the type
        if not data_site:
            raise ValueError(
                f'The provided site does not support {label}.')
        if page.site != data_site:
            raise ValueError(
                f'Page must be on the {label} repository site.')

        # validate page title fulfills hard-coded Wikibase requirement
        # pcre regexp: '/^Data:[^\\[\\]#\\\:{|}]+\.map$/u' for geo-shape
        # pcre regexp: '/^Data:[^\\[\\]#\\\:{|}]+\.tab$/u' for tabular-data
        # As we have already checked for existence the following simplified
        # check should be enough.
        if not page.title().startswith('Data:') \
           or not page.title().endswith(ending):
            raise ValueError(f"Page must be in 'Data:' namespace and end in "
                             f"'{ending}' for {label}.")

    def __init__(self,
                 page: pywikibot.Page,
                 site: DataSite | None = None) -> None:
        """Create a new WbDataPage object.

        :param page: page containing the data
        :param site: The Wikibase site
        """
        site = site or page.site.data_repository()
        specifics = type(self)._get_type_specifics(site)
        WbDataPage._validate(page, specifics['data_site'], specifics['ending'],
                             specifics['label'])
        self.page = page

    def __hash__(self) -> int:
        """Override super.hash() as toWikibase is a string for WbDataPage."""
        return hash(self.toWikibase())

    def toWikibase(self) -> str:
        """Convert the data to the value required by the Wikibase API.

        :return: title of the data page incl. namespace
        """
        return self.page.title()

    @classmethod
    def fromWikibase(cls, page_name: str, site: DataSite | None) -> WbDataPage:
        """Create a WbDataPage from the JSON data given by the Wikibase API.

        :param page_name: page name from Wikibase value
        :param site: The Wikibase site
        """
        # TODO: This method signature does not match our parent class (which
        # takes a dictionary argument rather than a string). We should either
        # change this method's signature or rename this method.

        data_site = cls._get_data_site(site)
        page = pywikibot.Page(data_site, page_name)
        return cls(page, site)


class WbGeoShape(WbDataPage):

    """A Wikibase geo-shape representation."""

    @classmethod
    def _get_data_site(cls, site: DataSite) -> APISite:
        """Return the site serving as a geo-shape repository.

        :param site: The Wikibase site
        """
        return site.geo_shape_repository()

    @classmethod
    def _get_type_specifics(cls, site: DataSite) -> dict[str, Any]:
        """Return the specifics for WbGeoShape.

        :param site: The Wikibase site
        """
        return {
            'ending': '.map',
            'label': 'geo-shape',
            'data_site': cls._get_data_site(site),
        }


class WbTabularData(WbDataPage):

    """A Wikibase tabular-data representation."""

    @classmethod
    def _get_data_site(cls, site: DataSite) -> APISite:
        """Return the site serving as a tabular-data repository.

        :param site: The Wikibase site
        """
        return site.tabular_data_repository()

    @classmethod
    def _get_type_specifics(cls, site: DataSite) -> dict[str, Any]:
        """Return the specifics for WbTabularData.

        :param site: The Wikibase site
        """
        return {
            'ending': '.tab',
            'label': 'tabular-data',
            'data_site': cls._get_data_site(site),
        }


class WbUnknown(WbRepresentation):

    """A Wikibase representation for unknown data type.

    This will prevent the bot from breaking completely when a new type
    is introduced.

    This data type is just a json container

    .. versionadded:: 3.0
    .. versionchanged:: 9.4
       *warning* parameter was added
    """

    _items = ('json',)

    def __init__(self, json: dict[str, Any], warning: str = '') -> None:
        """Create a new WbUnknown object.

        :param json: Wikibase JSON
        :param warning: a warning message which is shown once if
            :meth:`toWikibase` is called
        """
        self.json = json
        self.warning = warning

    def toWikibase(self) -> dict[str, Any]:
        """Return the JSON object for the Wikibase API.

        .. versionchanged:: 9.4
           a waning message given by the warning attribute is shown once.

        :return: Wikibase JSON
        """
        if self.warning:
            pywikibot.warning(self.warning)
            self.warning = ''
        return self.json

    @classmethod
    def fromWikibase(cls, data: dict[str, Any],
                     site: DataSite | None = None) -> WbUnknown:
        """Create a WbUnknown from the JSON data given by the Wikibase API.

        :param data: Wikibase JSON
        :param site: The Wikibase site
        """
        return cls(data)
