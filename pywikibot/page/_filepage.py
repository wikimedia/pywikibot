"""Objects representing MediaWiki File pages.

This module includes objects:

* FilePage: A subclass of Page representing a file description page
* FileInfo: a structure holding imageinfo of latest revision of FilePage
"""
#
# (C) Pywikibot team, 2008-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from http import HTTPStatus
from os import PathLike
from pathlib import Path
from urllib.parse import urlparse

import pywikibot
from pywikibot.backports import Iterable
from pywikibot.comms import http
from pywikibot.exceptions import NoPageError
from pywikibot.page._page import Page
from pywikibot.tools import compute_file_hash


__all__ = (
    'FileInfo',
    'FilePage',
)


class FilePage(Page):

    """A subclass of Page representing a file description page.

    Supports the same interface as Page except *ns*; some added methods.
    """

    def __init__(self, source, title: str = '', *,
                 ignore_extension: bool = False) -> None:
        """Initializer.

        .. versionchanged:: 8.4
           Check for valid extensions.
        .. versionchanged:: 9.3
           Added the optional *ignore_extension* parameter.
        .. versionchanged:: 9.6
           Show a warning if *ignore_extension* was set and the
           extension is invalid.
        .. seealso::
           :meth:`Site.file_extensions
           <pywikibot.site._apisite.APISite.file_extensions>`

        :param source: the source of the page
        :type source: pywikibot.page.BaseLink (or subclass),
            pywikibot.page.Page (or subclass), or pywikibot.page.Site
        :param title: normalized title of the page; required if source is a
            Site, ignored otherwise
        :param ignore_extension: prevent extension check
        :raises ValueError: Either the title is not in the file
            namespace or does not have a valid extension and
            *ignore_extension* was not set.
        """
        self._file_revisions = {}  # dictionary to cache File history.
        super().__init__(source, title, 6)
        if self.namespace() != 6:
            raise ValueError(f"'{self.title()}' is not in the file namespace!")

        title = self.title(with_ns=False, with_section=False)
        _, sep, extension = title.rpartition('.')
        if not sep or extension.lower() not in self.site.file_extensions:
            msg = (f'{title!r} does not have a valid extension\n'
                   f'({", ".join(self.site.file_extensions)}).')
            if not ignore_extension:
                raise ValueError(msg)

            pywikibot.warning(msg)

    def _load_file_revisions(self, imageinfo) -> None:
        """Save a file revision of FilePage (a FileInfo object) in local cache.

        Metadata shall be added lazily to the revision already present
        in cache.
        """
        for file_rev in imageinfo:
            # filemissing in API response indicates most fields are missing
            # see https://gerrit.wikimedia.org/r/c/mediawiki/core/+/533482/
            if 'filemissing' in file_rev:
                pywikibot.warning(
                    f"File '{self.title()}' contains missing revisions")
                continue

            ts_key = pywikibot.Timestamp.fromISOformat(file_rev['timestamp'])
            file_revision = self._file_revisions.setdefault(
                ts_key, FileInfo(file_rev, self))

            # add new imageinfo attributes since last request.
            file_revision.update(file_rev)

    @property
    def latest_file_info(self):
        """Retrieve and store information of latest Image rev. of FilePage.

        At the same time, the whole history of Image is fetched and cached in
        self._file_revisions

        :return: instance of FileInfo()
        """
        if not self._file_revisions:
            self.site.loadimageinfo(self, history=True)
        latest_ts = max(self._file_revisions)
        return self._file_revisions[latest_ts]

    @property
    def oldest_file_info(self):
        """Retrieve and store information of oldest Image rev. of FilePage.

        At the same time, the whole history of Image is fetched and cached in
        self._file_revisions

        :return: instance of FileInfo()
        """
        if not self._file_revisions:
            self.site.loadimageinfo(self, history=True)
        oldest_ts = min(self._file_revisions)
        return self._file_revisions[oldest_ts]

    def get_file_info(self, ts) -> dict:
        """Retrieve and store information of a specific Image rev. of FilePage.

        This function will load also metadata.
        It is also used as a helper in FileInfo to load metadata lazily.

        .. versionadded:: 8.6

        :param ts: timestamp of the Image rev. to retrieve

        :return: instance of FileInfo()
        """
        self.site.loadimageinfo(self, history=False, timestamp=ts)
        return self._file_revisions[ts]

    def get_file_history(self) -> dict:
        """Return the file's version history.

        :return: dictionary with:
            key: timestamp of the entry
            value: instance of FileInfo()
        """
        if not self._file_revisions:
            self.site.loadimageinfo(self, history=True)
        return self._file_revisions

    def getImagePageHtml(self) -> str:  # noqa: N802
        """Download the file page, and return the HTML, as a string.

        Caches the HTML code, so that if you run this method twice on the
        same FilePage object, the page will only be downloaded once.
        """
        if not hasattr(self, '_imagePageHtml'):
            path = (f'{self.site.scriptpath()}/index.php?'
                    f'title={self.title(as_url=True)}')
            self._imagePageHtml = http.request(self.site, path).text
        return self._imagePageHtml

    def get_file_url(self,
                     url_width: int | None = None,
                     url_height: int | None = None,
                     url_param: str | None = None) -> str:
        """Return the url or the thumburl of the file described on this page.

        Fetch the information if not available.

        Once retrieved, file information will also be accessible as
        :attr:`latest_file_info` attributes, named as in :api:`Imageinfo`.
        If *url_width*, *url_height* or *url_param* is given, additional
        properties ``thumbwidth``, ``thumbheight``, ``thumburl`` and
        ``responsiveUrls`` are provided.

        .. note:: Parameters validation and error handling left to the
           API call.
        .. seealso::

           * :meth:`APISite.loadimageinfo()
             <pywikibot.site._apisite.APISite.loadimageinfo>`
           * :api:`Imageinfo`

        :param url_width: get info for a thumbnail with given width
        :param url_height: get info for a thumbnail with given height
        :param url_param:  get info for a thumbnail with given param
        :return: latest file url or thumburl
        """
        # Plain url is requested.
        if url_width is None and url_height is None and url_param is None:
            return self.latest_file_info.url

        # Thumburl is requested.
        self.site.loadimageinfo(self, history=not self._file_revisions,
                                url_width=url_width, url_height=url_height,
                                url_param=url_param)
        return self.latest_file_info.thumburl

    def file_is_shared(self) -> bool:
        """Check if the file is stored on any known shared repository.

        .. versionchanged:: 7.0
           return False if file does not exist on shared image repository
           instead raising NoPageError.
        """
        # as of now, the only known repositories are commons and wikitravel
        # TODO: put the URLs to family file
        if not self.site.has_image_repository:
            return False

        try:
            info = self.latest_file_info
        except NoPageError:
            return False

        if 'wikitravel_shared' in self.site.shared_image_repository():
            return info.url.startswith('https://wikitravel.org/upload/shared/')

        # default to commons
        return info.url.startswith(
            'https://upload.wikimedia.org/wikipedia/commons/')

    def getFileVersionHistoryTable(self) -> str:  # noqa: N802
        """Return the version history in the form of a wiki table."""
        lines = []
        for info in self.get_file_history().values():
            dimension = '{width}×{height} px ({size} bytes)'.format(
                **info.__dict__)
            lines.append('| {timestamp} || {user} || {dimension} |'
                         '| <nowiki>{comment}</nowiki>'
                         .format(dimension=dimension, **info.__dict__))
        return ('{| class="wikitable"\n'
                '! {{int:filehist-datetime}} || {{int:filehist-user}} |'
                '| {{int:filehist-dimensions}} || {{int:filehist-comment}}\n'
                '|-\n%s\n|}\n' % '\n|-\n'.join(lines))

    def using_pages(self, **kwargs):
        """Yield Pages on which the file is displayed.

        For parameters refer
        :meth:`APISite.imageusage()
        <pywikibot.site._generators.GeneratorsMixin.imageusage>`

        Usage example:

        >>> site = pywikibot.Site('wikipedia:test')
        >>> file = pywikibot.FilePage(site, 'Pywikibot MW gear icon.svg')
        >>> used = list(file.using_pages(total=10))
        >>> len(used)
        2
        >>> used[0].title()
        'Pywikibot'

        .. seealso:: :meth:`globalusage`
        .. versionchanged:: 7.2
           all parameters from :meth:`APISite.imageusage()
           <pywikibot.site._generators.GeneratorsMixin.imageusage>`
           are available.
        .. versionchanged:: 7.4
           renamed from :meth:`usingPages`.
        """
        return self.site.imageusage(self, **kwargs)

    @property
    def file_is_used(self) -> bool:
        """Check whether the file is used at this site.

        .. versionadded:: 7.1
        """
        return bool(list(self.using_pages(total=1)))

    def upload(self, source: str, **kwargs) -> bool:
        """Upload this file to the wiki.

        keyword arguments are from site.upload() method.

        :param source: Path or URL to the file to be uploaded.

        :keyword comment: Edit summary; if this is not provided, then
            filepage.text will be used. An empty summary is not
            permitted. This may also serve as the initial page text (see
            below).
        :keyword text: Initial page text; if this is not set, then
            filepage.text will be used, or comment.
        :keyword watch: If true, add filepage to the bot user's
            watchlist
        :keyword ignore_warnings: It may be a static boolean, a callable
            returning a boolean or an iterable. The callable gets a list
            of UploadError instances and the iterable should contain the
            warning codes for which an equivalent callable would return
            True if all UploadError codes are in that list. If the
            result is False it'll not continue uploading the file and
            otherwise disable any warning and reattempt to upload the
            file.

            .. note:: NOTE: If report_success is True or None it'll
               raise an UploadError exception if the static boolean is
               False.
        :type ignore_warnings: bool or callable or iterable of str
        :keyword chunk_size: The chunk size in bytesfor chunked
            uploading (see :api:`Upload#Chunked_uploading`). It will
            only upload in chunks, if the chunk size is positive but
            lower than the file size.
        :type chunk_size: int
        :keyword report_success: If the upload was successful it'll
            print a success message and if ignore_warnings is set to
            False it'll raise an UploadError if a warning occurred. If
            it's None (default) it'll be True if ignore_warnings is a
            bool and False otherwise. If it's True or None
            ignore_warnings must be a bool.
        :return: It returns True if the upload was successful and False
            otherwise.
        """
        filename = url = None
        if '://' in source:
            url = source
        else:
            filename = source
        return self.site.upload(self, source_filename=filename, source_url=url,
                                **kwargs)

    def download(self,
                 filename: str | PathLike | Iterable[str] | None = None,
                 chunk_size: int = 100 * 1024,
                 revision: FileInfo | None = None, *,
                 url_width: int | None = None,
                 url_height: int | None = None,
                 url_param: str | None = None) -> bool:
        """Download to filename file of FilePage.

        **Usage examples:**

        Download an image:

        >>> site = pywikibot.Site('wikipedia:test')
        >>> file = pywikibot.FilePage(site, 'Pywikibot MW gear icon.svg')
        >>> file.download()
        True

        Pywikibot_MW_gear_icon.svg was downloaded.

        Download a thumbnail:

        >>> file.download(url_param='120px')
        True

        The suffix has changed and Pywikibot_MW_gear_icon.png was
        downloaded.

        .. versionadded:: 8.2
           *url_width*, *url_height* and *url_param* parameters.
        .. versionchanged:: 8.2
           *filename* argument may be also a path-like object or an
           iterable of path segments.
        .. note:: filename suffix is adjusted if target url's suffix is
           different which may be the case if a thumbnail is loaded.
        .. warning:: If a file already exists, it will be overridden
           without further notes.
        .. seealso:: :api:`Imageinfo` for new parameters

        :param filename: filename where to save file. If ``None``,
            ``self.title(as_filename=True, with_ns=False)`` will be used.
            If an Iterable is specified the items will be used as path
            segments. To specify the user directory path you have to use
            either ``~`` or ``~user`` as first path segment e.g. ``~/foo``
            or ``('~', 'foo')`` as filename. If only the user directory
            specifier is given, the title is used as filename like for
            None. If the suffix is missing or different from url (which
            can happen if a *url_width*, *url_height* or *url_param*
            argument is given), the file suffix is adjusted.
        :param chunk_size: the size of each chunk to be received and
            written to file.
        :param revision: file revision to download. If None
            :attr:`latest_file_info` will be used; otherwise provided
            revision will be used.
        :param url_width: download thumbnail with given width
        :param url_height: download thumbnail with given height
        :param url_param:  download thumbnail with given param
        :return: True if download is successful, False otherwise.
        :raise IOError: if filename cannot be written for any reason.
        """
        if not filename:
            path = Path()
        elif isinstance(filename, (str, PathLike)):
            path = Path(filename)
        else:
            path = Path(*filename)

        if path.stem in ('', '~', '~user'):
            path = path / self.title(as_filename=True, with_ns=False)

        thumb = bool(url_width or url_height or url_param)
        if thumb or revision is None:
            url = self.get_file_url(url_width, url_height, url_param)
            revision = self.latest_file_info
        else:
            url = revision.url

        # adjust suffix
        path = path.with_suffix(Path(urlparse(url).path).suffix)
        # adjust user path
        path = path.expanduser()
        req = http.fetch(url, stream=True)
        if req.status_code == HTTPStatus.OK:
            with open(path, 'wb') as f:
                for chunk in req.iter_content(chunk_size):
                    f.write(chunk)

            return thumb or compute_file_hash(path) == revision.sha1

        pywikibot.warning(
            f'Unsuccessful request ({req.status_code}): {req.url}')
        return False

    def globalusage(self, total=None):
        """Iterate all global usage for this page.

        .. seealso:: :meth:`using_pages`

        :param total: iterate no more than this number of pages in total
        :return: a generator that yields Pages also on sites different from
            self.site.
        :rtype: generator
        """
        return self.site.globalusage(self, total=total)

    def data_item(self):
        """Function to get the associated Wikibase item of the file.

        If WikibaseMediaInfo extension is available (e.g., on Commons),
        the method returns the associated mediainfo entity. Otherwise,
        it falls back to the behavior of :meth:`BasePage.data_item`.

        .. versionadded:: 6.5

        :rtype: pywikibot.page.WikibaseEntity
        """
        if self.site.has_extension('WikibaseMediaInfo'):
            if not hasattr(self, '_item'):
                self._item = pywikibot.MediaInfo(self.site)
                self._item._file = self
            return self._item

        return super().data_item()


class FileInfo:

    """A structure holding imageinfo of latest rev. of FilePage.

    All keys of API imageinfo dictionary are mapped to FileInfo attributes.
    Attributes can be retrieved both as self['key'] or self.key.

    Following attributes will be returned:
        - timestamp, user, comment, url, size, sha1, mime, metadata (lazily)
        - archivename (not for latest revision)

    see :meth:`Site.loadimageinfo()
    <pywikibot.site._apisite.APISite.loadimageinfo>` for details.

    .. note:: timestamp will be casted to :func:`pywikibot.Timestamp`.

    .. versionchanged:: 7.7
       raises KeyError instead of AttributeError if FileInfo is used as
       Mapping.
    .. versionchanged:: 8.6
       Metadata are loaded lazily.
       Added *filepage* parameter.
    """

    def __init__(self, file_revision, filepage) -> None:
        """Initiate the class using the dict from ``APISite.loadimageinfo``."""
        self.filepage = filepage
        self._metadata = None
        self.update(file_revision)

    def update(self, file_revision):
        """Update FileInfo with new values.

        .. versionadded:: 8.6
        """
        for k, v in file_revision.items():
            if k == 'timestamp':
                v = pywikibot.Timestamp.fromISOformat(v)
            setattr(self, k, v)

    def __getitem__(self, key):
        """Give access to class values by key."""
        try:
            result = getattr(self, key)
        except AttributeError as e:
            raise KeyError(str(e).replace('attribute', 'key')) from None
        return result

    def __repr__(self) -> str:
        """Return a more complete string representation."""
        return repr(self.__dict__)

    def __eq__(self, other) -> bool:
        """Test if two FileInfo objects are equal."""
        return self.__dict__ == other.__dict__

    @property
    def metadata(self):
        """Return metadata.

        .. versionadded:: 8.6
        """
        if self._metadata is None:
            self.filepage.get_file_info(self.timestamp)
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        """Set metadata.

        .. versionadded:: 8.6
        """
        self._metadata = value
