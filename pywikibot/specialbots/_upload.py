"""Special bot library containing UploadRobot.

Do not import classes directly from here but from specialbots.
"""
#
# (C) Pywikibot team, 2003-2022
#
# Distributed under the terms of the MIT license.
#
import os
import tempfile
from contextlib import suppress
from http import HTTPStatus
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlparse

import requests

import pywikibot
import pywikibot.comms.http as http
from pywikibot import config
from pywikibot.backports import List
from pywikibot.bot import BaseBot, QuitKeyboardInterrupt
from pywikibot.exceptions import APIError, FatalServerError, NoPageError


class UploadRobot(BaseBot):

    """Upload bot."""

    def __init__(self, url: Union[List[str], str], *,
                 url_encoding=None,
                 description: str = '',
                 use_filename=None,
                 keep_filename: bool = False,
                 verify_description: bool = True,
                 ignore_warning: Union[bool, list] = False,
                 target_site=None,
                 aborts: Union[bool, list, None] = None,
                 chunk_size: int = 0,
                 asynchronous: bool = False,
                 summary: Optional[str] = None,
                 filename_prefix: Optional[str] = None,
                 force_if_shared: bool = False,
                 **kwargs) -> None:
        """Initializer.

        .. versionchanged:: 6.2
           asynchronous upload is used if *asynchronous* parameter is set

        .. versionchanged:: 6.4
           *force_if_shared* parameter was added

        :param url: path to url or local file, or list of urls or paths
            to local files.
        :param description: Description of file for its page. If multiple files
            are uploading the same description is used for every file.
        :type description: str
        :param use_filename: Specify title of the file's page. If multiple
            files are uploading it asks to change the name for second, third,
            etc. files, otherwise the last file will overwrite the other.
        :param keep_filename: Set to True to keep original names of urls and
            files, otherwise it will ask to enter a name for each file.
        :param summary: Summary of the upload
        :param verify_description: Set to True to proofread the description.
        :param ignore_warning: Set this to True to upload even if another file
            would be overwritten or another mistake would be risked. Set it to
            an array of warning codes to selectively ignore specific warnings.
        :param target_site: Set the site to upload to. If target site is not
            given it's taken from user config file (user_config.py).
        :type target_site: object
        :param aborts: List of the warning types to abort upload on. Set to
            True to abort on any warning.
        :param chunk_size: Upload the file in chunks (more overhead, but
            restartable) specified in bytes. If no value is specified the file
            will be uploaded as whole.
        :param asynchronous: Make potentially large file operations
            asynchronous on the server side when possible.
        :param filename_prefix: Specify prefix for the title of every
            file's page.
        :param force_if_shared: Upload the file even if it's currently
            shared to the target site (e.g. when moving from Commons to another
            wiki)
        :keyword always: Disables any input, requires that either
            ignore_warning or aborts are set to True and that the
            description is also set. It overwrites verify_description to
            False and keep_filename to True.
        :type always: bool
        """
        super().__init__(**kwargs)
        if self.opt.always:
            if ignore_warning is not True and aborts is not True:
                raise ValueError(
                    'When always is set to True, '
                    'ignore_warning or aborts must be set to True.')
            if not description:
                raise ValueError(
                    'When always is set to True, the description must be set.')

        self.url = [url] if isinstance(url, str) else url
        self.url_encoding = url_encoding
        self.description = description
        self.use_filename = use_filename
        self.keep_filename = keep_filename or self.opt.always
        self.verify_description = verify_description and not self.opt.always
        self.ignore_warning = ignore_warning
        self.aborts = aborts or []
        self.chunk_size = chunk_size
        self.asynchronous = asynchronous
        self.summary = summary
        self.filename_prefix = filename_prefix
        self.force_if_shared = force_if_shared

        if config.upload_to_commons:
            default_site = pywikibot.Site('commons')
        else:
            default_site = pywikibot.Site()
        self.target_site = target_site or default_site

    def read_file_content(self, file_url: str):
        """Return name of temp file in which remote file is saved."""
        pywikibot.info('Reading file ' + file_url)

        handle, tempname = tempfile.mkstemp()
        path = Path(tempname)
        size = 0

        dt_gen = (el for el in (15, 30, 45, 60, 120, 180, 240, 300))
        while True:
            file_len = path.stat().st_size
            if file_len:
                pywikibot.info('Download resumed.')
                headers = {'Range': f'bytes={file_len}-'}
            else:
                headers = {}

            with open(path, 'ab') as fd:
                os.lseek(handle, file_len, 0)
                try:
                    response = http.fetch(file_url, stream=True,
                                          headers=headers)
                    response.raise_for_status()

                    # get download info, if available
                    # Note: this is not enough to exclude pages
                    #       e.g. 'application/json' is also not a media
                    if 'text/' in response.headers['Content-Type']:
                        raise FatalServerError('The requested URL was not '
                                               'found on server.')
                    size = max(size,
                               int(response.headers.get('Content-Length', 0)))

                    # stream content to temp file (in chunks of 1Mb)
                    for chunk in response.iter_content(chunk_size=1024 * 1024):
                        fd.write(chunk)

                # raised from connection lost during response.iter_content()
                except requests.ConnectionError:
                    fd.flush()
                    pywikibot.info('Connection closed at byte {}'
                                   .format(path.stat().st_size))
                # raised from response.raise_for_status()
                except requests.HTTPError as e:
                    # exit criteria if size is not available
                    # error on last iteration is OK, we're requesting
                    #    {'Range': 'bytes=file_len-'}
                    err = HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE
                    if response.status_code == err and path.stat().st_size:
                        break
                    raise FatalServerError(str(e)) from e

            if size and size == path.stat().st_size:
                break
            try:
                dt = next(dt_gen)
                pywikibot.info(f'Sleeping for {dt} seconds ...')
                pywikibot.sleep(dt)
            except StopIteration:
                raise FatalServerError('Download failed, too many retries!')

        pywikibot.info(f'Downloaded {path.stat().st_size} bytes')
        return tempname

    def _handle_warning(self, warning: str) -> Optional[bool]:
        """Return whether the warning cause an abort or be ignored.

        :param warning: The warning name
        :return: False if this warning should cause an abort, True if it should
            be ignored or None if this warning has no default handler.
        """
        if self.aborts is not True and warning in self.aborts:
            return False
        if self.ignore_warning is True or (self.ignore_warning is not False
                                           and warning in self.ignore_warning):
            return True
        return None if self.aborts is not True else False

    def _handle_warnings(self, warnings):
        messages = '\n'.join('{0.code}: {0.info}'.format(warning)
                             for warning in sorted(warnings,
                                                   key=lambda w: w.code))
        if len(warnings) > 1:
            messages = '\n' + messages
        pywikibot.info('We got the following warning(s): ' + messages)
        answer = True
        for warning in warnings:
            this_answer = self._handle_warning(warning.code)
            if this_answer is False:
                answer = False
                break
            if this_answer is None:
                answer = None
        if answer is None:
            answer = pywikibot.input_yn('Do you want to ignore?',
                                        default=False, automatic_quit=False)
        return answer

    def process_filename(self, file_url):
        """Return base filename portion of file_url."""
        # Isolate the pure name
        filename = file_url
        # Filename may be either a URL or a local file path
        if '://' in filename:
            # extract the path portion of the URL
            filename = urlparse(filename).path
        filename = os.path.basename(filename)
        if self.use_filename:
            filename = self.use_filename
        if self.filename_prefix:
            filename = self.filename_prefix + filename
        if not self.keep_filename:
            pywikibot.info(
                '\nThe filename on the target wiki will default to: {}\n'
                .format(filename))
            assert not self.opt.always
            newfn = pywikibot.input(
                'Enter a better name, or press enter to accept:')
            if newfn != '':
                filename = newfn
        # FIXME: these 2 belong somewhere else, presumably in family
        # forbidden characters are handled by pywikibot/page.py
        forbidden = ':*/\\'  # to be extended
        try:
            allowed_formats = self.target_site.siteinfo.get(
                'fileextensions', get_default=False)
        except KeyError:
            allowed_formats = []
        else:
            allowed_formats = [item['ext'] for item in allowed_formats]

        # ask until it's valid
        first_check = True
        while True:
            if not first_check:
                if self.opt.always:
                    filename = None
                else:
                    filename = pywikibot.input('Enter a better name, or press '
                                               'enter to skip the file:')
                if not filename:
                    return None

            first_check = False
            ext = os.path.splitext(filename)[1].lower().strip('.')
            # are any chars in forbidden also in filename?
            invalid = set(forbidden) & set(filename)
            if invalid:
                c = ''.join(invalid)
                pywikibot.info(
                    f'Invalid character(s): {c}. Please try again')
                continue

            if allowed_formats and ext not in allowed_formats:
                if self.opt.always:
                    pywikibot.info('File format is not one of [{}]'
                                   .format(' '.join(allowed_formats)))
                    continue

                if not pywikibot.input_yn(
                        'File format is not one of [{}], but {!r}. Continue?'
                        .format(' '.join(allowed_formats), ext),
                        default=False):
                    continue

            potential_file_page = pywikibot.FilePage(self.target_site,
                                                     filename)
            if potential_file_page.exists():
                overwrite = self._handle_warning('exists')
                if overwrite is False:
                    pywikibot.info(
                        'File exists and you asked to abort. Skipping.')
                    return None

                if potential_file_page.has_permission():
                    if overwrite is None:
                        overwrite = not pywikibot.input_yn(
                            'File with name {} already exists. '
                            'Would you like to change the name? '
                            '(Otherwise file will be overwritten.)'
                            .format(filename), default=True,
                            automatic_quit=False)
                    if not overwrite:
                        continue
                    break

                pywikibot.info(f'File with name {filename} already exists and '
                               f'cannot be overwritten.')
                continue

            with suppress(NoPageError):
                if (not self.force_if_shared
                        and potential_file_page.file_is_shared()):
                    pywikibot.info(
                        f'File with name {filename} already exists in shared '
                        f'repository and cannot be overwritten.')
                    continue
            break

        # A proper description for the submission.
        # Empty descriptions are not accepted.
        if self.description:
            pywikibot.info(
                f'The suggested description is:\n{self.description}')

        while not self.description or self.verify_description:
            if not self.description:
                pywikibot.info('<<lightred>>It is not possible to upload a '
                               'file without a description.')
            assert not self.opt.always
            # if no description, ask if user want to add one or quit,
            # and loop until one is filled.
            # if self.verify_description, ask if user want to change it
            # or continue.
            if self.description:
                question = 'Do you want to change this description?'
            else:
                question = 'No description was given. Add one?'
            if pywikibot.input_yn(question, default=not self.description,
                                  automatic_quit=self.description):
                from pywikibot import editor as editarticle
                editor = editarticle.TextEditor()
                try:
                    new_description = editor.edit(self.description)
                except ImportError:
                    raise
                except Exception as e:
                    pywikibot.error(e)
                    continue
                # if user saved / didn't press Cancel
                if new_description:
                    self.description = new_description
            elif not self.description:
                raise QuitKeyboardInterrupt
            self.verify_description = False

        return filename

    def abort_on_warn(self, warn_code):
        """Determine if the warning message should cause an abort."""
        return self.aborts is True or warn_code in self.aborts

    def ignore_on_warn(self, warn_code: str):
        """
        Determine if the warning message should be ignored.

        :param warn_code: The warning message
        """
        return self.ignore_warning is True or warn_code in self.ignore_warning

    def upload_file(self, file_url):
        """
        Upload the image at file_url to the target wiki.

        .. seealso:: :api:`Upload`

        Return the filename that was used to upload the image.
        If the upload fails, ask the user whether to try again or not.
        If the user chooses not to retry, return None.

        .. versionchanged:: 7.0
           If 'copyuploadbaddomain' API error occurred in first step,
           download the file and upload it afterwards
        """
        filename = self.process_filename(file_url)
        if not filename:
            return None

        site = self.target_site
        imagepage = pywikibot.FilePage(site, filename)  # normalizes filename
        imagepage.text = self.description

        pywikibot.info(f'Uploading file to {site}...')

        ignore_warnings = self.ignore_warning is True or self._handle_warnings

        download = False
        while True:
            if '://' in file_url \
               and (not site.has_right('upload_by_url') or download):
                try:
                    file_url = self.read_file_content(file_url)
                except FatalServerError as e:
                    pywikibot.error(e)
                    return None

            try:
                success = imagepage.upload(file_url,
                                           ignore_warnings=ignore_warnings,
                                           chunk_size=self.chunk_size,
                                           asynchronous=self.asynchronous,
                                           comment=self.summary)
            except APIError as error:
                if error.code == 'uploaddisabled':
                    pywikibot.error(
                        'Upload error: Local file uploads are disabled on {}.'
                        .format(site))
                elif error.code == 'copyuploadbaddomain' and not download \
                        and '://' in file_url:
                    pywikibot.error(error)
                    pywikibot.info('Downloading the file and retry...')
                    download = True
                    continue
                else:
                    pywikibot.exception('Upload error: ')
            except Exception:
                pywikibot.exception('Upload error: ')
            else:
                if success:
                    # No warning, upload complete.
                    pywikibot.info(f'Upload of {filename} successful.')
                    self.counter['upload'] += 1
                    return filename  # data['filename']
                pywikibot.info('Upload aborted.')
            break

        return None

    def skip_run(self) -> bool:
        """Check whether processing is to be skipped."""
        # early check that upload is enabled
        if self.target_site.is_uploaddisabled():
            pywikibot.error(
                'Upload error: Local file uploads are disabled on {}.'
                .format(self.target_site))
            return True

        # early check that user has proper rights to upload
        self.target_site.login()
        if not self.target_site.has_right('upload'):
            pywikibot.error(
                "User '{}' does not have upload rights on site {}."
                .format(self.target_site.user(), self.target_site))
            return True

        return False

    def run(self):
        """Run bot."""
        if self.skip_run():
            return
        try:
            for file_url in self.url:
                self.upload_file(file_url)
                self.counter['read'] += 1
        except QuitKeyboardInterrupt:
            pywikibot.info('\nUser quit {} bot run...'
                           .format(self.__class__.__name__))
        except KeyboardInterrupt:
            if config.verbose_output:
                raise

            pywikibot.info('\nKeyboardInterrupt during {} bot run...'
                           .format(self.__class__.__name__))
        finally:
            self.exit()
