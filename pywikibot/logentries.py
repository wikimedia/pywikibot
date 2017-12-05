# -*- coding: utf-8 -*-
"""Objects representing Mediawiki log entries."""
#
# (C) Pywikibot team, 2007-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import sys

import pywikibot
from pywikibot.exceptions import Error
from pywikibot.tools import deprecated, classproperty

if sys.version_info[0] > 2:
    basestring = (str, )

_logger = "wiki"


class LogDict(dict):

    """
    Simple custom dict that raises a custom KeyError when a key is missing.

    It also logs debugging information when a key is missing.
    """

    def __missing__(self, key):
        """Debug when the key is missing."""
        pywikibot.debug(u"API log entry received:\n" + repr(self),
                        _logger)
        raise KeyError("Log entry (%s) has no '%s' key" % (self._type, key))


class LogEntry(object):

    """Generic log entry."""

    # Log type expected. None for every type, or one of the (letype) str :
    # block/patrol/etc...
    # Overridden in subclasses.
    _expectedType = None

    def __init__(self, apidata, site):
        """Initialize object from a logevent dict returned by MW API."""
        self.data = LogDict(apidata)
        self.site = site
        if self._expectedType is not None and self._expectedType != self.type():
            raise Error("Wrong log type! Expecting %s, received %s instead."
                        % (self._expectedType, self.type()))
        self.data._type = self.type()

    def __repr__(self):
        """Return a string representation of LogEntry object."""
        return '<{0}({1}, logid={2})>'.format(type(self).__name__,
                                              self.site.sitename, self.logid())

    def __hash__(self):
        """Combine site and logid as the hash."""
        return self.logid() ^ hash(self.site)

    def __eq__(self, other):
        """Compare if self is equal to other."""
        if not isinstance(other, LogEntry):
            pywikibot.debug("'{0}' cannot be compared with '{1}'"
                            .format(type(self).__name__, type(other).__name__),
                            _logger)
            return False
        return self.logid() == other.logid() and self.site == other.site

    def __ne__(self, other):
        """Compare if self is not equal to other."""
        return not self == other

    @property
    def _params(self):
        """
        Additional data for some log entry types.

        @rtype: dict or None
        """
        if 'params' in self.data:
            return self.data['params']
        else:  # try old mw style preceding mw 1.19
            return self.data[self._expectedType]

    def logid(self):
        """Return the id of the log entry."""
        return self.data['logid']

    def pageid(self):
        """Return the log id of the page handled by this log entry."""
        return self.data['pageid']

    def ns(self):
        """Return the namespace id of the page handled by this log entry."""
        return self.data['ns']

    @deprecated('page()')
    def title(self):
        """
        DEPRECATED: Alias for page().

        This is going to be replaced by just returning the title as a string
        instead of a Page instance.
        """
        return self.page()

    def page(self):
        """
        Page on which action was performed.

        @note: title may be missing in data dict e.g. by oversight action to
               hide the title. In that case a KeyError exception will raise

        @rtype: pywikibot.Page
        @raise: KeyError: title was missing from log entry
        """
        if not hasattr(self, '_page'):
            self._page = pywikibot.Page(self.site, self.data['title'])
        return self._page

    def type(self):
        """The type of thie logentry."""
        return self.data['type']

    def action(self):
        """The action of this log entry."""
        return self.data['action']

    def user(self):
        """Return the user name doing this action."""
        # TODO use specific User class ?
        return self.data['user']

    def timestamp(self):
        """Timestamp object corresponding to event timestamp."""
        if not hasattr(self, '_timestamp'):
            self._timestamp = pywikibot.Timestamp.fromISOformat(
                self.data['timestamp'])
        return self._timestamp

    def comment(self):
        """Return the logentry's comment."""
        return self.data['comment']


class UserTargetLogEntry(LogEntry):

    """A log entry whose target is a user page."""

    def page(self):
        """Return the target user.

        This returns a User object instead of the Page object returned by the
        superclass method.

        @return: target user
        @rtype: pywikibot.User
        """
        if not hasattr(self, '_page'):
            self._page = pywikibot.User(super(UserTargetLogEntry, self).page())
        return self._page


class BlockEntry(LogEntry):

    """
    Block or unblock log entry.

    It might contain a block or unblock depending on the action. The duration,
    expiry and flags are not available on unblock log entries.
    """

    _expectedType = 'block'

    def __init__(self, apidata, site):
        """Constructor."""
        super(BlockEntry, self).__init__(apidata, site)
        # When an autoblock is removed, the "title" field is not a page title
        # See bug T19781
        pos = self.data['title'].find('#')
        self.isAutoblockRemoval = pos > 0
        if self.isAutoblockRemoval:
            self._blockid = int(self.data['title'][pos + 1:])

    def page(self):
        """
        Return the blocked account or IP.

        @return: the Page object of username or IP if this block action
            targets a username or IP, or the blockid if this log reflects
            the removal of an autoblock
        @rtype: pywikibot.Page or int
        """
        # TODO what for IP ranges ?
        if self.isAutoblockRemoval:
            return self._blockid
        else:
            return super(BlockEntry, self).page()

    def flags(self):
        """
        Return a list of (str) flags associated with the block entry.

        It raises an Error if the entry is an unblocking log entry.

        @rtype: list of flag strings
        """
        if self.action() == 'unblock':
            return []
        if not hasattr(self, '_flags'):
            self._flags = self._params['flags']
            # pre mw 1.19 returned a delimited string.
            if isinstance(self._flags, basestring):
                if self._flags:
                    self._flags = self._flags.split(',')
                else:
                    self._flags = []
        return self._flags

    def duration(self):
        """
        Return a datetime.timedelta representing the block duration.

        @return: datetime.timedelta, or None if block is indefinite.
        """
        if not hasattr(self, '_duration'):
            if self.expiry() is None:
                self._duration = None
            else:
                # Doing the difference is easier than parsing the string
                self._duration = self.expiry() - self.timestamp()
        return self._duration

    def expiry(self):
        """
        Return a Timestamp representing the block expiry date.

        @rtype: pywikibot.Timestamp or None
        """
        if not hasattr(self, '_expiry'):
            details = self._params.get('expiry')
            if details:
                self._expiry = pywikibot.Timestamp.fromISOformat(details)
            else:
                self._expiry = None  # for infinite blocks
        return self._expiry


class ProtectEntry(LogEntry):

    """Protection log entry."""

    _expectedType = 'protect'


class RightsEntry(LogEntry):

    """Rights log entry."""

    _expectedType = 'rights'

    @property
    def oldgroups(self):
        """Return old rights groups."""
        if 'old' in self._params:  # old mw style
            return self._params['old'].split(',') if self._params['old'] else []
        return self._params['oldgroups']

    @property
    def newgroups(self):
        """Return new rights groups."""
        if 'new' in self._params:  # old mw style
            return self._params['new'].split(',') if self._params['new'] else []
        return self._params['newgroups']


class DeleteEntry(LogEntry):

    """Deletion log entry."""

    _expectedType = 'delete'


class UploadEntry(LogEntry):

    """Upload log entry."""

    _expectedType = 'upload'

    def page(self):
        """
        Return FilePage on which action was performed.

        Note: title may be missing in data dict e.g. by oversight action to
              hide the title. In that case a KeyError exception will raise

        @rtype: pywikibot.FilePage
        @raise: KeyError: title was missing from log entry
        """
        if not hasattr(self, '_page'):
            self._page = pywikibot.FilePage(self.site, self.data['title'])
        return self._page


class MoveEntry(LogEntry):

    """Move log entry."""

    _expectedType = 'move'

    @deprecated('target_ns.id')
    def new_ns(self):
        """Return namespace id of target page."""
        return self.target_ns.id

    @property
    def target_ns(self):
        """Return namespace object of target page."""
        # key has been changed in mw 1.19
        return self.site.namespaces[self._params['target_ns']
                                    if 'target_ns' in self._params
                                    else self._params['new_ns']]

    @deprecated('target_page')
    def new_title(self):
        """Return page object of the new title."""
        return self.target_page

    @property
    def target_title(self):
        """Return the target title."""
        # key has been changed in mw 1.19
        return (self._params['target_title']
                if 'target_title' in self._params
                else self._params['new_title'])

    @property
    def target_page(self):
        """Return target page object."""
        if not hasattr(self, '_target_page'):
            self._target_page = pywikibot.Page(self.site, self.target_title)
        return self._target_page

    def suppressedredirect(self):
        """
        Return True if no redirect was created during the move.

        @rtype: bool
        """
        # Introduced in MW r47901
        return 'suppressedredirect' in self._params


class ImportEntry(LogEntry):

    """Import log entry."""

    _expectedType = 'import'


class PatrolEntry(LogEntry):

    """Patrol log entry."""

    _expectedType = 'patrol'

    @property
    def current_id(self):
        """Return the current id."""
        # key has been changed in mw 1.19; try the new mw style first
        # sometimes it returns strs sometimes ints
        return int(self._params['curid']
                   if 'curid' in self._params else self._params['cur'])

    @property
    def previous_id(self):
        """Return the previous id."""
        # key has been changed in mw 1.19; try the new mw style first
        # sometimes it returns strs sometimes ints
        return int(self._params['previd']
                   if 'previd' in self._params else self._params['prev'])

    @property
    def auto(self):
        """Return auto patrolled."""
        return 'auto' in self._params and self._params['auto'] != 0


class NewUsersEntry(LogEntry):

    """New user log entry."""

    _expectedType = 'newusers'


class ThanksEntry(UserTargetLogEntry):

    """Thanks log entry."""

    _expectedType = 'thanks'

# TODO entries for merge,suppress,makebot,gblblock,renameuser,globalauth,gblrights ?


class LogEntryFactory(object):

    """
    LogEntry Factory.

    Only available method is create()
    """

    logtypes = {
        'block': BlockEntry,
        'protect': ProtectEntry,
        'rights': RightsEntry,
        'delete': DeleteEntry,
        'upload': UploadEntry,
        'move': MoveEntry,
        'import': ImportEntry,
        'patrol': PatrolEntry,
        'newusers': NewUsersEntry,
        'thanks': ThanksEntry,
    }

    def __init__(self, site, logtype=None):
        """
        Constructor.

        @param site: The site on which the log entries are created.
        @type site: BaseSite
        @param logtype: The log type of the log entries, if known in advance.
                        If None, the Factory will fetch the log entry from
                        the data to create each object.
        @type logtype: (letype) str : move/block/patrol/etc...
        """
        self._site = site
        if logtype is None:
            self._creator = self._createFromData
        else:
            # Bind a Class object to self._creator:
            # When called, it will initialize a new object of that class
            logclass = LogEntryFactory._getEntryClass(logtype)
            self._creator = lambda data: logclass(data, self._site)

    @classproperty
    @deprecated('LogEntryFactory.logtypes')
    def _logtypes(cls):  # noqa: N805
        """DEPRECATED LogEntryFactory class attribute of log types."""
        return cls.logtypes

    def create(self, logdata):
        """
        Instantiate the LogEntry object representing logdata.

        @param logdata: <item> returned by the api
        @type logdata: dict

        @return: LogEntry object representing logdata
        """
        return self._creator(logdata)

    @classmethod
    def _getEntryClass(cls, logtype):
        """
        Return the class corresponding to the @logtype string parameter.

        @return: specified subclass of LogEntry, or LogEntry
        @rtype: class
        """
        try:
            return cls.logtypes[logtype]
        except KeyError:
            pywikibot.warning(
                'Log entry key {0} is not known.'.format(logtype))
            return LogEntry

    def _createFromData(self, logdata):
        """
        Check for logtype from data, and creates the correct LogEntry.

        @param logdata: log entry data
        @type logdata: dict
        @rtype: LogEntry
        """
        try:
            logtype = logdata['type']
        except KeyError:
            pywikibot.debug('API log entry received:\n{0}'.format(logdata),
                            _logger)
            raise Error("Log entry has no 'type' key")
        return LogEntryFactory._getEntryClass(logtype)(logdata, self._site)
