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
# (C) Pywikibot team, 2005-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import NamedTuple
from xml.etree.ElementTree import Element


try:
    from defusedxml.ElementTree import ParseError, iterparse
except ImportError:
    from xml.etree.ElementTree import iterparse, ParseError

from pywikibot.backports import Callable, Iterator
from pywikibot.tools import (
    ModuleDeprecationWrapper,
    issue_deprecation_warning,
    open_archive,
)


@dataclass
class XmlEntry:

    """Represent a page."""

    # TODO: there are more tags we can read.
    title: str
    ns: str
    id: str
    text: str
    username: str
    ipedit: bool
    timestamp: str
    editRestriction: str  # noqa: N815
    moveRestriction: str  # noqa: N815
    revisionid: str
    comment: str
    isredirect: bool


class Headers(NamedTuple):

    """Represent the common info of a page.

    .. versionadded:: 9.0
    """

    title: str
    ns: str
    pageid: str
    isredirect: bool
    edit_restriction: str
    move_restriction: str


class RawRev(NamedTuple):

    """Represent a raw revision.

    .. versionadded:: 9.0
    """

    headers: Headers
    revision: Element
    revid: int


class XmlDump:

    """Represents an XML dump file.

    Reads the local file at initialization,
    parses it, and offers access to the resulting XmlEntries via a generator.

    .. versionadded:: 7.2
       the `on_error` parameter
    .. versionchanged:: 7.2
       `allrevisions` parameter must be given as keyword parameter
    .. versionchanged:: 9.0
       `allrevisions` parameter is deprecated due to :phab:`T340804`,
       `revisions` parameter was introduced as replacement.
       `root` attribute was removed.

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

    def __init__(
        self,
        filename,
        *,
        allrevisions: bool | str | None = None,
        # when allrevisions removed, revisions can default to 'latest'
        revisions: str = 'first_found',
        on_error: Callable[[ParseError], None] | None = None,
    ) -> None:
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

        self._parse = self.rev_actions[revisions]
        self.uri = None

    def parse(self) -> Iterator[XmlEntry]:
        """Generator using ElementTree iterparse function.

        .. versionchanged:: 7.2
           if a ParseError occurs it can be handled by the callable
           given with `on_error` parameter of this instance.
        """
        with open_archive(self.filename) as source:
            context = iterparse(source, events=('start', 'end', 'start-ns'))
            root = None

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
                    self.uri = f'{{{elem[1]}}}'
                    continue

                # get the root element
                if event == 'start' and root is None:
                    root = elem

                if not (event == 'end' and elem.tag == f'{self.uri}page'):
                    continue

                yield from self._parse(elem)

                # clear references in the root, to allow garbage collection.
                elem.clear()
                root.clear()

    def _parse_only_first_found(self, elem: Element) -> Iterator[XmlEntry]:
        """Parser that yields the first revision found.

        .. versionadded:: 9.0
        """
        raw_revs = self._fetch_revs(elem)
        try:
            raw_rev = next(raw_revs)
            yield self._create_revision(raw_rev.headers, raw_rev.revision)
        except StopIteration:
            return

    def _parse_only_latest(self, elem: Element) -> Iterator[XmlEntry]:
        """Parser that yields only the latest revision."""
        raw_revs = self._fetch_revs(elem, with_id=True)
        raw_rev = max(raw_revs, default=None, key=lambda rev: rev.revid)
        if raw_rev is not None:
            yield self._create_revision(raw_rev.headers, raw_rev.revision)

    def _parse_only_earliest(self, elem: Element) -> Iterator[XmlEntry]:
        """Parser that yields only the earliest revision.

        .. versionadded:: 9.0
        """
        raw_revs = self._fetch_revs(elem, with_id=True)
        raw_rev = min(raw_revs, default=None, key=lambda rev: rev.revid)
        if raw_rev is not None:
            yield self._create_revision(raw_rev.headers, raw_rev.revision)

    def _parse_all(self, elem: Element) -> Iterator[XmlEntry]:
        """Parser that yields all revisions."""
        raw_revs = self._fetch_revs(elem)
        for raw_rev in raw_revs:
            yield self._create_revision(raw_rev.headers, raw_rev.revision)

    def _fetch_revs(self, elem: Element, with_id=False) -> Iterator[RawRev]:
        """Yield all revisions in a page.

        .. versionadded:: 9.0
        """
        uri = self.uri
        headers = self._headers(elem)
        for revision in elem.findall(f'{uri}revision'):
            revid = int(revision.findtext(f'{uri}id')) if with_id else 0
            yield RawRev(headers, revision, revid)

    @staticmethod
    def parse_restrictions(restrictions: str) -> tuple[str | None, str | None]:
        """Parse the characters within a restrictions tag.

        Returns strings representing user groups allowed to edit and
        to move a page, where None means there are no restrictions.

        .. versionadded:: 9.0
           replaces deprecated ``parseRestrictions`` function.
        """
        if not restrictions:
            return None, None

        edit_restriction, move_restriction = None, None

        edit_lock_match = re.search('edit=([^:]*)', restrictions)
        if edit_lock_match:
            edit_restriction = edit_lock_match[1]

        move_lock_match = re.search('move=([^:]*)', restrictions)
        if move_lock_match:
            move_restriction = move_lock_match[1]

        if restrictions == 'sysop':
            edit_restriction = 'sysop'
            move_restriction = 'sysop'

        return edit_restriction, move_restriction

    def _headers(self, elem: Element) -> Headers:
        """Extract headers from XML chunk."""
        uri = self.uri
        edit_restriction, move_restriction = self.parse_restrictions(
            elem.findtext(f'{uri}restrictions')
        )

        headers = Headers(
            title=elem.findtext(f'{uri}title'),
            ns=elem.findtext(f'{uri}ns'),
            pageid=elem.findtext(f'{uri}id'),
            isredirect=elem.findtext(f'{uri}redirect') is not None,
            edit_restriction=edit_restriction,
            move_restriction=move_restriction,
        )

        return headers

    def _create_revision(
            self, headers: Headers, revision: Element
    ) -> XmlEntry:
        """Create a Single revision."""
        uri = self.uri
        contributor = revision.find(f'{uri}contributor')
        ip_editor = contributor.findtext(f'{uri}ip')
        username = ip_editor or contributor.findtext(f'{uri}username')
        username = username or ''  # username might be deleted

        xml_entry = XmlEntry(
            title=headers.title,
            ns=headers.ns,
            id=headers.pageid,
            editRestriction=headers.edit_restriction,
            moveRestriction=headers.move_restriction,
            isredirect=headers.isredirect,
            text=revision.findtext(f'{uri}text'),
            username=username,
            ipedit=bool(ip_editor),
            timestamp=revision.findtext(f'{uri}timestamp'),
            revisionid=revision.findtext(f'{uri}id'),
            comment=revision.findtext(f'{uri}comment'),
            # could get comment, minor as well
        )

        return xml_entry


wrapper = ModuleDeprecationWrapper(__name__)
wrapper.add_deprecated_attr(
    'parseRestrictions',
    XmlDump.parse_restrictions,
    replacement_name='pywikibot.xmlreader.XmlDump.parseRestrictions',
    since='9.0.0')
