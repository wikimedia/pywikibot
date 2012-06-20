# -*- coding: utf-8  -*-

"""
Each XmlEntry object represents a page, as read from an XML source

The XmlDump class reads a pages_current XML dump (like the ones offered on
http://download.wikimedia.org/wikipedia/de/) and offers a generator over
XmlEntry objects which can be used by other bots.
"""
#
# (C) Pywikipedia bot team, 2005-2012
#
# Distributed under the terms of the MIT license.
#
__version__='$Id$'
#

import threading
import codecs, re
from xml.etree.cElementTree import iterparse
import pywikibot

def parseRestrictions(restrictions):
    """
    Parses the characters within a restrictions tag and returns
    strings representing user groups allowed to edit and to move
    a page, where None means there are no restrictions.
    """
    if not restrictions:
        return None, None
    editRestriction = None
    moveRestriction = None
    editLockMatch = re.search('edit=([^:]*)', restrictions)
    if editLockMatch:
        editRestriction = editLockMatch.group(1)
    moveLockMatch = re.search('move=([^:]*)', restrictions)
    if moveLockMatch:
        moveRestriction = moveLockMatch.group(1)
    if restrictions == 'sysop':
        editRestriction = 'sysop'
        moveRestriction = 'sysop'
    return editRestriction, moveRestriction


class XmlEntry:
    """
    Represents a page.
    """
    def __init__(self, title, ns, id, text, username, ipedit, timestamp,
                 editRestriction, moveRestriction, revisionid, comment,
                 redirect):
        # TODO: there are more tags we can read.
        self.title = title
        self.ns = ns
        self.id =id
        self.text = text
        self.username = username.strip()
        self.ipedit = ipedit
        self.timestamp = timestamp
        self.editRestriction = editRestriction
        self.moveRestriction = moveRestriction
        self.revisionid = revisionid
        self.comment = comment
        self.isredirect = redirect


class XmlParserThread(threading.Thread):
    """
    This XML parser will run as a single thread. This allows the XmlDump
    generator to yield pages before the parser has finished reading the
    entire dump.

    There surely are more elegant ways to do this.
    """
    def __init__(self, filename, handler):
        threading.Thread.__init__(self)
        self.filename = filename
        self.handler = handler

    def run(self):
        xml.sax.parse(self.filename, self.handler)


class XmlDump(object):
    """
    Represents an XML dump file. Reads the local file at initialization,
    parses it, and offers access to the resulting XmlEntries via a generator.

    @param allrevisions: boolean
        If True, parse all revisions instead of only the latest one.
        Default: False.
    """
    def __init__(self, filename, allrevisions=False):
        self.filename = filename
        if allrevisions:
            self._parse = self._parse_all
        else:
            self._parse = self._parse_only_latest

    def parse(self):
        """Generator using cElementTree iterparse function"""
        if self.filename.endswith('.bz2'):
            import bz2
            source = bz2.BZ2File(self.filename)
        elif self.filename.endswith('.gz'):
            import gzip
            source = gzip.open(self.filename)
        elif self.filename.endswith('.7z'):
            import subprocess
            source = subprocess.Popen('7za e -bd -so %s 2>/dev/null'
                                      % self.filename,
                                      shell=True,
                                      stdout=subprocess.PIPE,
                                      bufsize=65535).stdout
        else:
            # assume it's an uncompressed XML file
            source = open(self.filename)
        context = iterparse(source, events=("start", "end", "start-ns"))
        self.root = None

        for event, elem in context:
            if event == "start-ns" and elem[0] == "":
                self.uri = elem[1]
                continue
            if event == "start" and self.root is None:
                self.root = elem
                continue
            for rev in self._parse(event, elem):
                yield rev

    def _parse_only_latest(self, event, elem):
        """Parser that yields only the latest revision"""
        if event == "end" and elem.tag == "{%s}page" % self.uri:
            self._headers(elem)
            revision = elem.find("{%s}revision" % self.uri)
            yield self._create_revision(revision)
            elem.clear()
            self.root.clear()

    def _parse_all(self, event, elem):
        """Parser that yields all revisions"""
        if event == "start" and elem.tag == "{%s}page" % self.uri:
            self._headers(elem)
        if event == "end" and elem.tag == "{%s}revision" % self.uri:
            yield self._create_revision(elem)
            elem.clear()
            self.root.clear()

    def _headers(self, elem):
        self.title = elem.findtext("{%s}title" % self.uri)
        self.ns = elem.findtext("{%s}ns" % self.uri)
        self.pageid = elem.findtext("{%s}id" % self.uri)
        self.restrictions = elem.findtext("{%s}restrictions" % self.uri)
        self.isredirect = elem.findtext("{%s}redirect" % self.uri) is not None
        self.editRestriction, self.moveRestriction \
                              = parseRestrictions(self.restrictions)


    def _create_revision(self, revision):
        """Creates a Single revision"""
        revisionid = revision.findtext("{%s}id" % self.uri)
        timestamp = revision.findtext("{%s}timestamp" % self.uri)
        comment = revision.findtext("{%s}comment" % self.uri)
        contributor = revision.find("{%s}contributor" % self.uri)
        ipeditor = contributor.findtext("{%s}ip" % self.uri)
        username = ipeditor or contributor.findtext("{%s}username" % self.uri)
        # could get comment, minor as well
        text = revision.findtext("{%s}text" % self.uri)
        return XmlEntry(title=self.title,
                        ns=self.ns,
                        id=self.pageid,
                        text=text or u'',
                        username=username or u'', #username might be deleted
                        ipedit=bool(ipeditor),
                        timestamp=timestamp,
                        editRestriction=self.editRestriction,
                        moveRestriction=self.moveRestriction,
                        revisionid=revisionid,
                        comment=comment,
                        redirect=self.isredirect
                       )
