"""Objects representing MediaWiki File pages.

This module includes objects:

* FilePage: A subclass of Page representing a file description page
* FileInfo: a structure holding imageinfo of latest revision of FilePage
"""
#
# (C) Pywikibot team, 2008-2023
#
# Distributed under the terms of the MIT license.
#
import os.path
from http import HTTPStatus

import pywikibot
from pywikibot.comms import http
from pywikibot.exceptions import NoPageError
from pywikibot.page._page import Page
from pywikibot.tools import compute_file_hash, deprecated


__all__ = (
    'FileInfo',
    'FilePage',
)


class FilePage(Page):

    """
    A subclass of Page representing a file description page.

    Supports the same interface as Page, with some added methods.
    """

    def __init__(self, source, title: str = '') -> None:
        """Initializer."""
        self._file_revisions = {}  # dictionary to cache File history.
        super().__init__(source, title, 6)
        if self.namespace() != 6:
            raise ValueError("'{}' is not in the file namespace!"
                             .format(self.title()))

    def _load_file_revisions(self, imageinfo) -> None:
        for file_rev in imageinfo:
            # filemissing in API response indicates most fields are missing
            # see https://gerrit.wikimedia.org/r/c/mediawiki/core/+/533482/
            if 'filemissing' in file_rev:
                pywikibot.warning("File '{}' contains missing revisions"
                                  .format(self.title()))
                continue
            file_revision = FileInfo(file_rev)
            self._file_revisions[file_revision.timestamp] = file_revision

    @property
    def latest_file_info(self):
        """
        Retrieve and store information of latest Image rev. of FilePage.

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
        """
        Retrieve and store information of oldest Image rev. of FilePage.

        At the same time, the whole history of Image is fetched and cached in
        self._file_revisions

        :return: instance of FileInfo()
        """
        if not self._file_revisions:
            self.site.loadimageinfo(self, history=True)
        oldest_ts = min(self._file_revisions)
        return self._file_revisions[oldest_ts]

    def get_file_history(self) -> dict:
        """
        Return the file's version history.

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
            path = '{}/index.php?title={}'.format(self.site.scriptpath(),
                                                  self.title(as_url=True))
            self._imagePageHtml = http.request(self.site, path).text
        return self._imagePageHtml

    def get_file_url(self, url_width=None, url_height=None,
                     url_param=None) -> str:
        """
        Return the url or the thumburl of the file described on this page.

        Fetch the information if not available.

        Once retrieved, thumburl information will also be accessible as
        latest_file_info attributes, named as in [1]:
        - url, thumburl, thumbwidth and thumbheight

        Parameters correspond to iiprops in:
        [1] :api:`Imageinfo`

        Parameters validation and error handling left to the API call.

        :param url_width: see iiurlwidth in [1]
        :param url_height: see iiurlheigth in [1]
        :param url_param: see iiurlparam in [1]
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

    @deprecated('using_pages', since='7.4.0')
    def usingPages(self, **kwargs):  # noqa: N802
        """Yield Pages on which the file is displayed.

        .. deprecated:: 7.4.0
           Use :meth:`using_pages` instead.
        """
        return self.using_pages(**kwargs)

    @property
    def file_is_used(self) -> bool:
        """Check whether the file is used at this site.

        .. versionadded:: 7.1
        """
        return bool(list(self.using_pages(total=1)))

    def upload(self, source: str, **kwargs) -> bool:
        """
        Upload this file to the wiki.

        keyword arguments are from site.upload() method.

        :param source: Path or URL to the file to be uploaded.

        :keyword comment: Edit summary; if this is not provided, then
            filepage.text will be used. An empty summary is not permitted.
            This may also serve as the initial page text (see below).
        :keyword text: Initial page text; if this is not set, then
            filepage.text will be used, or comment.
        :keyword watch: If true, add filepage to the bot user's watchlist
        :keyword ignore_warnings: It may be a static boolean, a callable
            returning a boolean or an iterable. The callable gets a list of
            UploadError instances and the iterable should contain the warning
            codes for which an equivalent callable would return True if all
            UploadError codes are in thet list. If the result is False it'll
            not continue uploading the file and otherwise disable any warning
            and reattempt to upload the file.

            .. note:: NOTE: If report_success is True or None it'll
               raise an UploadError exception if the static boolean is
               False.
        :type ignore_warnings: bool or callable or iterable of str
        :keyword chunk_size: The chunk size in bytesfor chunked
            uploading (see :api:`Upload#Chunked_uploading`). It will
            only upload in chunks, if the chunk size is positive but
            lower than the file size.
        :type chunk_size: int
        :keyword report_success: If the upload was successful it'll print a
            success message and if ignore_warnings is set to False it'll
            raise an UploadError if a warning occurred. If it's
            None (default) it'll be True if ignore_warnings is a bool and False
            otherwise. If it's True or None ignore_warnings must be a bool.
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

    def download(self, filename=None, chunk_size=100 * 1024, revision=None):
        """
        Download to filename file of FilePage.

        :param filename: filename where to save file:
            None: self.title(as_filename=True, with_ns=False)
            will be used
            str: provided filename will be used.
        :type filename: None or str
        :param chunk_size: the size of each chunk to be received and
            written to file.
        :type chunk_size: int
        :param revision: file revision to download:
            None: self.latest_file_info will be used
            FileInfo: provided revision will be used.
        :type revision: None or FileInfo
        :return: True if download is successful, False otherwise.
        :raise IOError: if filename cannot be written for any reason.
        """
        if filename is None:
            filename = self.title(as_filename=True, with_ns=False)

        filename = os.path.expanduser(filename)

        if revision is None:
            revision = self.latest_file_info

        req = http.fetch(revision.url, stream=True)
        if req.status_code == HTTPStatus.OK:
            try:
                with open(filename, 'wb') as f:
                    for chunk in req.iter_content(chunk_size):
                        f.write(chunk)
            except OSError as e:
                raise e

            sha1 = compute_file_hash(filename)
            return sha1 == revision.sha1
        pywikibot.warning(
            'Unsuccessful request ({}): {}'
            .format(req.status_code, req.url))
        return False

    def globalusage(self, total=None):
        """
        Iterate all global usage for this page.

        .. seealso:: :meth:`using_pages`

        :param total: iterate no more than this number of pages in total
        :return: a generator that yields Pages also on sites different from
            self.site.
        :rtype: generator
        """
        return self.site.globalusage(self, total=total)

    def data_item(self):
        """
        Convenience function to get the associated Wikibase item of the file.

        If WikibaseMediaInfo extension is available (e.g. on Commons),
        the method returns the associated mediainfo entity. Otherwise,
        it falls back to behavior of BasePage.data_item.

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

    """
    A structure holding imageinfo of latest rev. of FilePage.

    All keys of API imageinfo dictionary are mapped to FileInfo attributes.
    Attributes can be retrieved both as self['key'] or self.key.

    Following attributes will be returned:
        - timestamp, user, comment, url, size, sha1, mime, metadata
        - archivename (not for latest revision)

    see :meth:`Site.loadimageinfo()
    <pywikibot.site._apisite.APISite.loadimageinfo>` for details.

    .. note:: timestamp will be casted to :func:`pywikibot.Timestamp`.

    .. versionchanged:: 7.7
       raises KeyError instead of AttributeError if FileInfo is used as
       Mapping.
    """

    def __init__(self, file_revision) -> None:
        """Initiate the class using the dict from ``APISite.loadimageinfo``."""
        self.__dict__.update(file_revision)
        self.timestamp = pywikibot.Timestamp.fromISOformat(self.timestamp)

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
