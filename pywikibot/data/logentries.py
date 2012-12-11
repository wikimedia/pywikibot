# -*- coding: utf-8  -*-
"""
Objects representing Mediawiki log entries
"""
#
# (C) Pywikipedia bot team, 2007-12
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

from pywikibot.exceptions import *
import pywikibot

_logger = "wiki"


class LogDict(dict):
    """
    Simple custom dictionary that raises a custom KeyError and logs
    debugging information when a key is missing
    """
    def __missing__(self, key):
        pywikibot.debug(u"API log entry received:\n" + repr(self),
                        _logger)
        raise KeyError("Log entry has no '%s' key" % key, key)


class LogEntry(object):
    """Generic log entry"""

    # Log type expected. None for every type, or one of the (letype) str :
    # block/patrol/etc...
    # Overriden in subclasses.
    _expectedType = None

    def __init__(self, apidata):
        """Initialize object from a logevent dict returned by MW API"""
        self.data = LogDict(apidata)
        if self._expectedType is not None and self._expectedType != self.type():
            raise Error("Wrong log type! Expecting %s, received %s instead."
                        % (self._expectedType, self.type()))

    def __hash__(self):
        return self.logid()

    def logid(self):
        return self.data['logid']

    def pageid(self):
        return self.data['pageid']

    def ns(self):
        return self.data['ns']

    def title(self):
        """Page on which action was performed"""
        if not hasattr(self, '_title'):
            self._title = pywikibot.Page(pywikibot.Link(self.data['title']))
        return self._title

    def type(self):
        return self.data['type']

    def action(self):
        return self.data['action']

    def user(self):
        #TODO use specific User class ?
        return self.data['user']

    def timestamp(self):
        """Timestamp object corresponding to event timestamp"""
        if not hasattr(self, '_timestamp'):
            self._timestamp = pywikibot.Timestamp.fromISOformat(
                                            self.data['timestamp'])
        return self._timestamp

    def comment(self):
        return self.data['comment']


class BlockEntry(LogEntry):
    _expectedType = 'block'
    def __init__(self, apidata):
        super(BlockEntry, self).__init__(apidata)
        # see http://en.wikipedia.org/w/api.php?action=query&list=logevents&letype=block&lelimit=1&lestart=2009-03-04T00:35:07Z :
        # When an autoblock is removed, the "title" field is not a page title
        # ( https://bugzilla.wikimedia.org/show_bug.cgi?id=17781 )
        pos = self.data['title'].find('#')
        self.isAutoblockRemoval = pos > 0
        if self.isAutoblockRemoval:
            self._blockid = int(self.data['title'][pos+1:])

    def title(self):
        """
        * Returns the Page object of username or IP
           if this block action targets a username or IP.
        * Returns the blockid if this log reflects the removal of an autoblock
        """
        #TODO what for IP ranges ?
        if self.isAutoblockRemoval:
            return self._blockid
        else:
            return super(BlockEntry, self).title()

    def isAutoblockRemoval(self):
        return self.isAutoblockRemoval

    def _getBlockDetails(self):
        try:
            return self.data['block']
        except KeyError:
            # No 'block' key means this is an unblocking log entry
            if self.action() == 'unblock':
                raise Error("action='unblock': this log entry has no block details such as flags, duration, or expiry!")
            raise

    def flags(self):
        """
        Returns a list of (str) flags associated with the block entry.
        Raises an Error if the entry is an unblocking log entry
        """
        if hasattr(self, '_flags'):
            return self._flags
        self._flags = self._getBlockDetails()['flags'].split(',')
        return self._flags

    def duration(self):
        """
        Returns a datetime.timedelta representing the block duration,
        or None if block is indefinite
        Raises an Error if the entry is an unblocking log entry
        """
        if hasattr(self, '_duration'):
            return self._duration
        if self._getBlockDetails()['duration'] == 'indefinite':
            self._duration = None
        else:
            # Doing the difference is easier than parsing the string
            self._duration = self.expiry() - self.timestamp()
        return self._duration

    def expiry(self):
        """
        Returns a Timestamp representing the block expiry date
        Raises an Error if the entry is an unblocking log entry
        """
        if hasattr(self, '_expiry'):
            return self._expiry
        self._expiry = pywikibot.Timestamp.fromISOformat(
                                    self._getBlockDetails()['expiry'])
        return self._expiry


class ProtectEntry(LogEntry):
    _expectedType = 'protect'

class RightsEntry(LogEntry):
    _expectedType = 'rights'

class DeleteEntry(LogEntry):
    _expectedType = 'delete'

class UploadEntry(LogEntry):
    _expectedType = 'upload'


class MoveEntry(LogEntry):
    _expectedType = 'move'

    def new_ns(self):
        return self.data['move']['new_ns']

    def new_title(self):
        """Page object of the new title"""
        if not hasattr(self, '_new_title'):
            self._new_title = pywikibot.Page(pywikibot.Link(
                                self.data['move']['new_title']))
        return self._new_title

    def suppressedredirect(self):
        """
        Returns True if no redirect was created from the old title
        to the new title during the move
        """
        # Introduced in MW r47901
        return 'suppressedredirect' in self.data['move']


class ImportEntry(LogEntry):
    _expectedType = 'import'

class PatrolEntry(LogEntry):
    _expectedType = 'patrol'

class NewUsersEntry(LogEntry):
    _expectedType = 'newusers'

#TODO entries for merge,suppress,makebot,gblblock,renameuser,globalauth,gblrights ?


class LogEntryFactory(object):
    """
    LogEntry Factory

    Only available method is create()
    """
    _logtypes = {
        'block':BlockEntry,
        'protect':ProtectEntry,
        'rights':RightsEntry,
        'delete':DeleteEntry,
        'upload':UploadEntry,
        'move':MoveEntry,
        'import':ImportEntry,
        'patrol':PatrolEntry,
        'newusers':NewUsersEntry
    }

    def __init__(self, logtype=None):
        """
        @param logtype: The log type of the log entries, if known in advance.
                        If None, the Factory will fetch the log entry from
                        the data to create each object.
        @type logtype: (letype) str : move/block/patrol/etc...
        """
        if logtype is None:
            self._creator = self._createFromData
        else:
            # Bind a Class object to self._creator:
            # When called, it will initialize a new object of that class
            self._creator = LogEntryFactory._getEntryClass(logtype)

    def create(self, logdata):
        """
        Instantiates the LogEntry object representing logdata
        @param logdata: <item> returned by the api
        @type logdata: dict

        @return LogEntry object representing logdata
        """
        return self._creator(logdata)

    @staticmethod
    def _getEntryClass(logtype):
        """
        Returns the class corresponding to the @logtype string parameter.
        Returns LogEntry if logtype is unknown or not supported
        """
        try:
            return LogEntryFactory._logtypes[logtype]
        except KeyError:
            return LogEntry

    def _createFromData(self, logdata):
        """
        Checks for logtype from data, and creates the correct LogEntry
        """
        try:
            logtype = logdata['type']
            return LogEntryFactory._getEntryClass(logtype)(logdata)
        except KeyError:
            pywikibot.debug(u"API log entry received:\n" + logdata,
                            _logger)
            raise Error("Log entry has no 'type' key")
