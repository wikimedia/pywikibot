"""XML reading module.

Each XmlEntry object represents a page, as read from an XML source

The XmlDump class reads a pages_current XML dump (like the ones offered on
https://dumps.wikimedia.org/backup-index.html) and offers a generator over
XmlEntry objects which can be used by other bots.

.. versionchanged:: 7.7
   *defusedxml* is used in favour of *xml.etree* if present to prevent
   vulnerable XML attacks. *defusedxml* 0.7.1 or higher is recommended.
"""
#
# (C) Pywikibot team, 2005-2023
#
# Distributed under the terms of the MIT license.
#
import re
from typing import Optional


try:
    from defusedxml.ElementTree import ParseError, iterparse
except ImportError:
    from xml.etree.ElementTree import iterparse, ParseError

from pywikibot.backports import Callable, Type
from pywikibot.tools import open_archive


def parseRestrictions(restrictions):
    """
    Parse the characters within a restrictions tag.

    Returns strings representing user groups allowed to edit and
    to move a page, where None means there are no restrictions.
    """
    if not restrictions:
        return None, None
    editRestriction = None
    moveRestriction = None
    editLockMatch = re.search('edit=([^:]*)', restrictions)
    if editLockMatch:
        editRestriction = editLockMatch[1]
    moveLockMatch = re.search('move=([^:]*)', restrictions)
    if moveLockMatch:
        moveRestriction = moveLockMatch[1]
    if restrictions == 'sysop':
        editRestriction = 'sysop'
        moveRestriction = 'sysop'
    return editRestriction, moveRestriction


class XmlEntry:

    """Represent a page."""

    def __init__(self, title, ns, id, text, username, ipedit, timestamp,
                 editRestriction, moveRestriction, revisionid, comment,
                 redirect) -> None:
        """Initializer."""
        # TODO: there are more tags we can read.
        self.title = title
        self.ns = ns
        self.id = id
        self.text = text
        self.username = username.strip()
        self.ipedit = ipedit
        self.timestamp = timestamp
        self.editRestriction = editRestriction
        self.moveRestriction = moveRestriction
        self.revisionid = revisionid
        self.comment = comment
        self.isredirect = redirect


class XmlDump:

    """Represents an XML dump file.

    Reads the local file at initialization,
    parses it, and offers access to the resulting XmlEntries via a generator.

    .. versionadded:: 7.2
       the `on_error` parameter
    .. versionchanged:: 7.2
       `allrevisions` parameter must be given as keyword parameter

    Usage example:

    >>> from pywikibot import xmlreader
    >>> name = 'tests/data/xml/article-pear.xml'
    >>> dump = xmlreader.XmlDump(name, allrevisions=True)
    >>> for elem in dump.parse():
    ...     print(elem.title, elem.revisionid)
    ...
    ...
    Pear 185185
    Pear 185241
    Pear 185408
    Pear 188924
    >>>

    :param allrevisions: boolean
        If True, parse all revisions instead of only the latest one.
        Default: False.
    :param on_error: a callable which is invoked within :meth:`parse`
        method when a ParseError occurs. The exception is passed to this
        callable. Otherwise the exception is raised.
    """

    def __init__(self, filename, *,
                 allrevisions: bool = False,
                 on_error: Optional[
                     Callable[[Type[BaseException]], None]] = None) -> None:
        """Initializer."""
        self.filename = filename
        self.on_error = on_error
        if allrevisions:
            self._parse = self._parse_all
        else:
            self._parse = self._parse_only_latest

    def parse(self):
        """Generator using ElementTree iterparse function.

        .. versionchanged:: 7.2
           if a ParseError occurs it can be handled by the callable
           given with `on_error` parameter of this instance.
        """
        with open_archive(self.filename) as source:
            context = iterparse(source, events=('start', 'end', 'start-ns'))
            self.root = None
            while True:
                try:
                    event, elem = next(context)
                except StopIteration:
                    return
                except ParseError as e:
                    if self.on_error:
                        self.on_error(e)
                        continue
                    raise

                if event == 'start-ns' and elem[0] == '':
                    self.uri = elem[1]
                    continue
                if event == 'start' and self.root is None:
                    self.root = elem
                    continue
                yield from self._parse(event, elem)

    def _parse_only_latest(self, event, elem):
        """Parser that yields only the latest revision."""
        if event == 'end' and elem.tag == '{%s}page' % self.uri:
            self._headers(elem)
            revision = elem.find('{%s}revision' % self.uri)
            yield self._create_revision(revision)
            elem.clear()
            self.root.clear()

    def _parse_all(self, event, elem):
        """Parser that yields all revisions."""
        if event == 'start' and elem.tag == '{%s}page' % self.uri:
            self._headers(elem)
        if event == 'end' and elem.tag == '{%s}revision' % self.uri:
            yield self._create_revision(elem)
            elem.clear()
            self.root.clear()

    def _headers(self, elem) -> None:
        """Extract headers from XML chunk."""
        self.title = elem.findtext('{%s}title' % self.uri)
        self.ns = elem.findtext('{%s}ns' % self.uri)
        self.pageid = elem.findtext('{%s}id' % self.uri)
        self.restrictions = elem.findtext('{%s}restrictions' % self.uri)
        self.isredirect = elem.findtext('{%s}redirect' % self.uri) is not None
        self.editRestriction, self.moveRestriction = parseRestrictions(
            self.restrictions)

    def _create_revision(self, revision):
        """Create a Single revision."""
        revisionid = revision.findtext('{%s}id' % self.uri)
        timestamp = revision.findtext('{%s}timestamp' % self.uri)
        comment = revision.findtext('{%s}comment' % self.uri)
        contributor = revision.find('{%s}contributor' % self.uri)
        ipeditor = contributor.findtext('{%s}ip' % self.uri)
        username = ipeditor or contributor.findtext('{%s}username' % self.uri)
        # could get comment, minor as well
        text = revision.findtext('{%s}text' % self.uri)
        return XmlEntry(title=self.title,
                        ns=self.ns,
                        id=self.pageid,
                        text=text or '',
                        username=username or '',  # username might be deleted
                        ipedit=bool(ipeditor),
                        timestamp=timestamp,
                        editRestriction=self.editRestriction,
                        moveRestriction=self.moveRestriction,
                        revisionid=revisionid,
                        comment=comment,
                        redirect=self.isredirect
                        )
