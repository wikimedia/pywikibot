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
from __future__ import annotations

import re


try:
    from defusedxml.ElementTree import ParseError, iterparse
except ImportError:
    from xml.etree.ElementTree import iterparse, ParseError

from pywikibot.backports import Callable, Type
from pywikibot.tools import (
    issue_deprecation_warning,
    open_archive,
)


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
    .. versionchanged:: 9.0
        `allrevisions` parameter deprecated due to :phab:`T340804`
        `revisions` parameter introduced as replacement

    Usage example:

    >>> from pywikibot import xmlreader
    >>> name = 'tests/data/xml/article-pear.xml'
    >>> dump = xmlreader.XmlDump(name, revisions='all')
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
    :param revisions: which of four methods to use to parse the dump:
        * `first_found` (whichever revision is the first element)
        * `latest` (most recent revision, by largest `revisionid`)
        * `earliest` (first revision, by smallest `revisionid`)
        * `all` (all revisions for each page)
        Default: `first_found`
    """

    def __init__(self, filename, *,
                 allrevisions: bool | str = None,
                 # when allrevisions removed, revisions can default to 'latest'
                 revisions: str = 'first_found',
                 on_error: None | (
                     Callable[[Type[BaseException]], None]) = None) -> None:
        """Initializer."""
        self.filename = filename
        self.on_error = on_error

        self.rev_actions = {
            'first_found': self._parse_only_first_found,
            'latest': self._parse_only_latest,
            'earliest': self._parse_only_earliest,
            'all': self._parse_all,
        }

        if allrevisions:
            issue_deprecation_warning(
                'allrevisions=True',
                "revisions='all'",
                since='9.0.0')
            revisions = 'all'
        elif revisions == 'first_found':
            issue_deprecation_warning(
                'allrevisions=False returns first revision found,'
                " usually earliest. For most recent, use revisions='latest'. "
                "For oldest, use revisions='earliest',"
                "'allrevisions'",
                since='9.0.0')

        if revisions not in self.rev_actions:
            actions = str(list(self.rev_actions.keys())).strip('[]')
            raise ValueError(f"'revisions' must be one of {actions}.")

        self._parse = self.rev_actions.get(revisions)

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

    def _parse_only_first_found(self, event, elem):
        """
        Deprecated parser that yields the first revision found.

        Documentation had wrongly indicated it returned the latest revision.
        :phab: `T340804`
        """
        if event == 'end' and elem.tag == f'{{{self.uri}}}page':
            self._headers(elem)
            revision = elem.find(f'{{{self.uri}}}revision')
            yield self._create_revision(revision)
            elem.clear()
            self.root.clear()

    def _parse_only_latest(self, event, elem):
        """Parser that yields only the latest revision."""
        if event == 'end' and elem.tag == f'{{{self.uri}}}page':
            self._headers(elem)
            latest_revision = None
            latest_revisionid = 0
            for revision in elem.findall(f'{{{self.uri}}}revision'):
                revisionid = int(revision.findtext(f'{{{self.uri}}}id'))
                if latest_revision is None or revisionid > latest_revisionid:
                    latest_revision = revision
                    latest_revisionid = revisionid
            if latest_revision is not None:
                yield self._create_revision(latest_revision)
            elem.clear()
            self.root.clear()

    def _parse_only_earliest(self, event, elem):
        """Parser that yields only the earliest revision."""
        if event == 'end' and elem.tag == f'{{{self.uri}}}page':
            self._headers(elem)
            earliest_revision = None
            earliest_revisionid = float('inf')  # Initialize positive infinity
            for revision in elem.findall(f'{{{self.uri}}}revision'):
                revisionid = int(revision.findtext(f'{{{self.uri}}}id'))
                if revisionid < earliest_revisionid:
                    earliest_revisionid = revisionid
                    earliest_revision = revision
            if earliest_revision is not None:
                yield self._create_revision(earliest_revision)
            elem.clear()
            self.root.clear()

    def _parse_all(self, event, elem):
        """Parser that yields all revisions."""
        if event == 'end' and elem.tag == f'{{{self.uri}}}page':
            self._headers(elem)
            for revision in elem.findall(f'{{{self.uri}}}revision'):
                yield self._create_revision(revision)
            elem.clear()
            self.root.clear()

    def _headers(self, elem) -> None:
        """Extract headers from XML chunk."""
        self.title = elem.findtext(f'{{{self.uri}}}title')
        self.ns = elem.findtext(f'{{{self.uri}}}ns')
        self.pageid = elem.findtext(f'{{{self.uri}}}id')
        self.restrictions = elem.findtext(f'{{{self.uri}}}restrictions')
        self.isredirect = elem.findtext(f'{{{self.uri}}}redirect') is not None
        self.editRestriction, self.moveRestriction = parseRestrictions(
            self.restrictions)

    def _create_revision(self, revision):
        """Create a single revision."""
        revisionid = revision.findtext(f'{{{self.uri}}}id')
        timestamp = revision.findtext(f'{{{self.uri}}}timestamp')
        comment = revision.findtext(f'{{{self.uri}}}comment')
        contributor = revision.find(f'{{{self.uri}}}contributor')
        ipeditor = contributor.findtext(f'{{{self.uri}}}ip')
        username = ipeditor or contributor.findtext(f'{{{self.uri}}}username')
        # could get comment, minor as well
        text = revision.findtext(f'{{{self.uri}}}text')
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
