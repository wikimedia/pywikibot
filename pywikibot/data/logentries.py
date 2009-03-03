# -*- coding: utf-8  -*-
"""
Objects representing Mediawiki log entries
"""
#
# (C) Pywikipedia bot team, 2007-08
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'

from pywikibot.exceptions import *
import pywikibot
from pywikibot import date
  
class LogDict(dict):
    """Simple custom dictionary that raises a custom Error instead of a KeyError"""
    def __missing__(self, key):
        pywikibot.output(u"API log entry received:\n" + repr(self),
                         level=pywikibot.DEBUG)
        raise Error("Log entry has no '%s' key" % key)

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
            raise Error("Wrong log type! Expecting %s, received %s instead." \
                        % (self._expectedType, self.type()))
     
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
        """datetime object corresponding to event timestamp"""
        if not hasattr(self, '_timestamp'):
            self._timestamp = date.ISO2datetime(self.data['timestamp'])
        return self._timestamp

    def comment(self):
        return self.data['comment']

class BlockEntry(LogEntry):
    _expectedType = 'block'

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

class ImportEntry(LogEntry):
    _expectedType = 'import'

class PatrolEntry(LogEntry):
    _expectedType = 'patrol'

class NewUsersEntry(LogEntry):
    _expectedType = 'newusers'

#TODO entries for merge,suppress,makebot,gblblock,renameuser,globalauth,gblrights ?


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

def _getEntryClass(logtype):
    """
    Returns the class corresponding to the @logtype string parameter.
    Returns LogEntry if logtype is unknown or not supported
    """
    try:
        return _logtypes[logtype]
    except KeyError:
        return LogEntry

class LogEntryFactory(object):
    """
    LogEntry Factory

    Only available method is create()
    """
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
            self._creator = _getEntryClass(logtype)

    def create(self, logdata):
        """
        Instantiates the LogEntry object representing logdata
        @param logdata: <item> returned by the api
        @type logdata: dict

        @return LogEntry object representing logdata
        """
        return self._creator(logdata)

    def _createFromData(self, logdata):
        """
        Checks for logtype from data, and creates the correct LogEntry
        """
        try:
            logtype = logdata['type'] 
            return _getEntryClass(logtype)(logdata)
        except KeyError:
            pywikibot.output(u"API log entry received:\n" + logdata,
                              level=pywikibot.DEBUG)
            raise Error("Log entry has no 'type' key")
