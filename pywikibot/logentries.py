"""Objects representing MediaWiki log entries."""
#
# (C) Pywikibot team, 2007-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import datetime
from collections import UserDict
from typing import Any

import pywikibot
from pywikibot.exceptions import Error, HiddenKeyError
from pywikibot.tools import cached


class LogEntry(UserDict):

    """Generic log entry.

    LogEntry parameters may be retrieved by the corresponding method
    or the LogEntry key. The following statements are equivalent:

    action = logentry.action()
    action = logentry['action']
    action = logentry.data['action']
    """

    # Log type expected. None for every type, or one of the (letype) str :
    # block/patrol/etc...
    # Overridden in subclasses.
    _expected_type: str | None = None

    def __init__(self, apidata: dict[str, Any],
                 site: pywikibot.site.BaseSite) -> None:
        """Initialize object from a logevent dict returned by MW API."""
        super().__init__(apidata)
        self.site = site
        expected_type = self._expected_type
        if expected_type is not None and expected_type != self.type():
            raise Error(f'Wrong log type! Expecting {expected_type}, received '
                        f'{self.type()} instead.')

    def __missing__(self, key: str) -> None:
        """Debug when the key is missing.

        HiddenKeyError is raised when the user does not have permission.
        KeyError is raised otherwise.

        It also logs debugging information when a key is missing.
        """
        pywikibot.debug(f'API log entry received:\n{self!r}')
        hidden = {
            'actionhidden': [
                'action', 'logpage', 'ns', 'pageid', 'params', 'title',
            ],
            'commenthidden': ['comment'],
            'userhidden': ['user'],
        }
        for hidden_key, hidden_types in hidden.items():
            if hidden_key in self and key in hidden_types:
                raise HiddenKeyError(
                    f'Log entry ({self["type"]}) has a hidden {key!r} key and'
                    " you don't have permission to view it due to "
                    f'{hidden_key!r}'
                )

        raise KeyError(f"Log entry ({self['type']}) has no {key!r} key")

    def __repr__(self) -> str:
        """Return a string representation of LogEntry object."""
        return (f'<{type(self).__name__}({self.site.sitename}, '
                f'logid={self.logid()})>')

    def __hash__(self) -> int:
        """Combine site and logid as the hash."""
        return self.logid() ^ hash(self.site)

    def __eq__(self, other: Any) -> bool:
        """Compare if self is equal to other."""
        if not isinstance(other, LogEntry):
            pywikibot.debug(f"'{type(self).__name__}' cannot be compared with "
                            f"'{type(other).__name__}'")
            return False

        return self.logid() == other.logid() and self.site == other.site

    def __getattr__(self, item: str) -> Any:
        """Return several items from dict used as methods."""
        if item in ('action', 'comment', 'logid', 'ns', 'pageid', 'type',
                    'user'):  # TODO use specific User class for 'user'?
            return lambda: self[item]

        return super().__getattribute__(item)

    @property
    def params(self) -> dict[str, Any]:
        """Additional data for some log entry types.

        .. versionadded:: 9.4
           private *_param* attribute became a public property
        """
        return self.get('params', {})

    @cached
    def page(self) -> int | pywikibot.page.Page:
        """Page on which action was performed.

        :return: page on action was performed
        """
        return pywikibot.Page(self.site, self['title'])

    @cached
    def timestamp(self) -> pywikibot.Timestamp:
        """Timestamp object corresponding to event timestamp."""
        return pywikibot.Timestamp.fromISOformat(self['timestamp'])


class OtherLogEntry(LogEntry):

    """A log entry class for unspecified log events."""


class UserTargetLogEntry(LogEntry):

    """A log entry whose target is a user page."""

    @cached
    def page(self) -> pywikibot.page.User:
        """Return the target user.

        This returns a User object instead of the Page object returned by the
        superclass method.

        :return: target user
        """
        return pywikibot.User(self.site, self['title'])


class BlockEntry(LogEntry):

    """Block or unblock log entry.

    It might contain a block or unblock depending on the action. The duration,
    expiry and flags are not available on unblock log entries.
    """

    _expected_type = 'block'

    def __init__(self, apidata: dict[str, Any],
                 site: pywikibot.site.BaseSite) -> None:
        """Initializer."""
        super().__init__(apidata, site)
        # When an autoblock is removed, the "title" field is not a page title
        # See bug T19781
        pos = self.get('title', '').find('#')
        self.isAutoblockRemoval = pos > 0
        if self.isAutoblockRemoval:
            self._blockid = int(self['title'][pos + 1:])

    def page(self) -> int | pywikibot.page.Page:
        """Return the blocked account or IP.

        :return: the Page object of username or IP if this block action
            targets a username or IP, or the blockid if this log reflects
            the removal of an autoblock
        """
        # TODO what for IP ranges ?
        if self.isAutoblockRemoval:
            return self._blockid

        return super().page()

    @cached
    def flags(self) -> list[str]:
        """Return a list of (str) flags associated with the block entry.

        It raises an Error if the entry is an unblocking log entry.

        :return: list of flags strings
        """
        if self.action() == 'unblock':
            return []

        return self.params.get('flags', [])

    @cached
    def duration(self) -> datetime.timedelta | None:
        """Return a datetime.timedelta representing the block duration.

        :return: datetime.timedelta, or None if block is indefinite.
        """
        # Doing the difference is easier than parsing the string
        return (self.expiry() - self.timestamp()
                if self.expiry() is not None else None)

    @cached
    def expiry(self) -> pywikibot.Timestamp | None:
        """Return a Timestamp representing the block expiry date."""
        details = self.params.get('expiry')
        return pywikibot.Timestamp.fromISOformat(details) if details else None


class RightsEntry(LogEntry):

    """Rights log entry."""

    _expected_type = 'rights'

    @property
    def oldgroups(self) -> list[str]:
        """Return old rights groups.

        .. versionchanged:: 7.5
           No longer raise KeyError if `oldgroups` does not exists or
           LogEntry has no additional data e.g. due to hidden data and
           insufficient rights.
        """
        return self.params.get('oldgroups', [])

    @property
    def newgroups(self) -> list[str]:
        """Return new rights groups.

        .. versionchanged:: 7.5
           No longer raise KeyError if `oldgroups` does not exists or
           LogEntry has no additional data e.g. due to hidden data and
           insufficient rights.
        """
        return self.params.get('newgroups', [])


class UploadEntry(LogEntry):

    """Upload log entry."""

    _expected_type = 'upload'

    @cached
    def page(self) -> pywikibot.page.FilePage:
        """Return FilePage on which action was performed."""
        return pywikibot.FilePage(self.site, self['title'])


class MoveEntry(LogEntry):

    """Move log entry."""

    _expected_type = 'move'

    @property
    def target_ns(self) -> pywikibot.site._namespace.Namespace:
        """Return namespace object of target page."""
        return self.site.namespaces[self.params['target_ns']]

    @property
    def target_title(self) -> str:
        """Return the target title."""
        return self.params['target_title']

    @property
    @cached
    def target_page(self) -> pywikibot.page.Page:
        """Return target page object."""
        return pywikibot.Page(self.site, self.target_title)

    def suppressedredirect(self) -> bool:
        """Return True if no redirect was created during the move."""
        # Introduced in MW r47901
        return 'suppressedredirect' in self.params


class PatrolEntry(LogEntry):

    """Patrol log entry."""

    _expected_type = 'patrol'

    @property
    def current_id(self) -> int:
        """Return the current id."""
        return int(self.params['curid'])

    @property
    def previous_id(self) -> int:
        """Return the previous id."""
        return int(self.params['previd'])

    @property
    def auto(self) -> bool:
        """Return auto patrolled."""
        return 'auto' in self.params and self.params['auto'] != 0


class LogEntryFactory:

    """LogEntry Factory.

    Only available method is create()
    """

    _logtypes = {
        'block': BlockEntry,
        'rights': RightsEntry,
        'upload': UploadEntry,
        'move': MoveEntry,
        'patrol': PatrolEntry,
    }

    def __init__(self, site: pywikibot.site.BaseSite,
                 logtype: str | None = None) -> None:
        """Initializer.

        :param site: The site on which the log entries are created.
        :param logtype: The log type of the log entries, if known in advance.
                        If None, the Factory will fetch the log entry from
                        the data to create each object.
        """
        self._site = site
        if logtype is None:
            self._creator = self._create_from_data
        else:
            # Bind a Class object to self._creator:
            # When called, it will initialize a new object of that class
            logclass = self.get_valid_entry_class(logtype)
            self._creator = lambda data: logclass(data, self._site)

    def create(self, logdata: dict[str, Any]) -> LogEntry:
        """Instantiate the LogEntry object representing logdata.

        :param logdata: <item> returned by the api

        :return: LogEntry object representing logdata
        """
        return self._creator(logdata)

    def get_valid_entry_class(self, logtype: str) -> LogEntry:
        """Return the class corresponding to the @logtype string parameter.

        :return: specified subclass of LogEntry
        :raise KeyError: logtype is not valid
        """
        if logtype not in self._site.logtypes:
            raise KeyError(f'{logtype} is not a valid logtype')

        return LogEntryFactory.get_entry_class(logtype)

    @classmethod
    def get_entry_class(cls, logtype: str) -> LogEntry:
        """Return the class corresponding to the @logtype string parameter.

        :return: specified subclass of LogEntry

        .. note:: this class method cannot verify whether the given logtype
           already exits for a given site; to verify use Site.logtypes
           or use the get_valid_entry_class instance method instead.
        """
        if logtype not in cls._logtypes:
            if logtype is None:
                cls._logtypes[logtype] = OtherLogEntry
            else:
                if logtype in ('newusers', 'thanks'):
                    bases = (UserTargetLogEntry, OtherLogEntry)
                else:
                    bases = (OtherLogEntry,)
                cls._logtypes[logtype] = type(
                    f'{logtype.capitalize()}Entry',
                    bases,
                    {
                        '__doc__': f'{logtype.capitalize()} log entry',
                        '_expected_type': logtype,
                    },
                )
        return cls._logtypes[logtype]

    def _create_from_data(self, logdata: dict[str, Any]) -> LogEntry:
        """Check for logtype from data, and creates the correct LogEntry.

        :param logdata: log entry data
        """
        try:
            logtype = logdata['type']
        except KeyError:
            pywikibot.debug(f'API log entry received:\n{logdata}')
            raise Error("Log entry has no 'type' key")

        return LogEntryFactory.get_entry_class(logtype)(logdata, self._site)


# For backward compatibility
ProtectEntry = LogEntryFactory.get_entry_class('protect')
DeleteEntry = LogEntryFactory.get_entry_class('delete')
ImportEntry = LogEntryFactory.get_entry_class('import')
NewUsersEntry = LogEntryFactory.get_entry_class('newusers')
ThanksEntry = LogEntryFactory.get_entry_class('thanks')
