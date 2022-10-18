"""Objects representing API upload to MediaWiki site."""
#
# (C) Pywikibot team, 2009-2022
#
# Distributed under the terms of the MIT license.
#
import mimetypes
import os
from collections.abc import Iterable
from typing import Optional
from warnings import warn

import pywikibot
from pywikibot.exceptions import APIError, Error, UploadError
from pywikibot.tools import compute_file_hash


__all__ = ('Uploader', )


class Uploader:

    """Uploader class to upload a file to the wiki.

    .. versionadded:: 7.1

    :param site: The current site to work on
    :param filepage: a FilePage object from which the wiki-name of the
        file will be obtained.
    :param source_filename: path to the file to be uploaded
    :param source_url: URL of the file to be uploaded
    :param comment: Edit summary; if this is not provided, then
        filepage.text will be used. An empty summary is not permitted.
        This may also serve as the initial page text (see below).
    :param text: Initial page text; if this is not set, then
        filepage.text will be used, or comment.
    :param watch: If true, add filepage to the bot user's watchlist
    :param chunk_size: The chunk size in bytes for chunked uploading
        (see :api:`Upload#Chunked_uploading`). It will only upload in
        chunks, if the chunk size is positive but lower than the file
        size.
    :param asynchronous: Make potentially large file operations
        asynchronous on the server side when possible.
    :param ignore_warnings: It may be a static boolean, a callable
        returning a boolean or an iterable. The callable gets a list of
        UploadError instances and the iterable should contain the warning
        codes for which an equivalent callable would return True if all
        UploadError codes are in thet list. If the result is False it'll
        not continue uploading the file and otherwise disable any warning
        and reattempt to upload the file.

        .. note:: If report_success is True or None it'll raise an
           UploadError exception if the static boolean is False.
    :type ignore_warnings: bool or callable or iterable of str
    :param report_success: If the upload was successful it'll print a
        success message and if ignore_warnings is set to False it'll
        raise an UploadError if a warning occurred. If it's None
        (default) it'll be True if ignore_warnings is a bool and False
        otherwise. If it's True or None ignore_warnings must be a bool.
    """

    upload_warnings = {
        # map API warning codes to user error messages
        # {msg} will be replaced by message string from API response
        'duplicate-archive':
            'The file is a duplicate of a deleted file {msg}.',
        'was-deleted': 'The file {msg} was previously deleted.',
        'empty-file': 'File {msg} is empty.',
        'exists': 'File {msg} already exists.',
        'duplicate': 'Uploaded file is a duplicate of {msg}.',
        'badfilename': 'Target filename is invalid.',
        'filetype-unwanted-type': 'File {msg} type is unwanted type.',
        'exists-normalized':
            'File exists with different extension as {msg!r}.',
        'bad-prefix': 'Target filename has a bad prefix {msg}.',
        'page-exists':
            'Target filename exists but with a different file {msg}.',

        # API-returned message string will be timestamps, not much use here
        'no-change': 'The upload is an exact duplicate of the current version '
                     'of this file.',
        'duplicate-version': 'The upload is an exact duplicate of older '
                             'version(s) of this file.',
    }

    def __init__(self,
                 site: 'pywikibot.site.APISite',
                 filepage: 'pywikibot.FilePage',
                 *,
                 source_filename: Optional[str] = None,
                 source_url: Optional[str] = None,
                 comment: Optional[str] = None,
                 text: Optional[str] = None,
                 watch: bool = False,
                 chunk_size: int = 0,
                 asynchronous: bool = False,
                 ignore_warnings=False,
                 report_success: Optional[bool] = None) -> None:
        """Initializer."""
        self.site = site
        self.filepage = filepage
        self.comment = comment
        self.text = text
        self.watch = watch
        self.ignore_warnings = ignore_warnings
        self.chunk_size = chunk_size
        self.asynchronous = asynchronous
        self.report_success = report_success

        if source_filename and source_url:
            raise ValueError('APISite.upload: must provide either '
                             'source_filename or source_url, not both.')

        self.filename = source_filename
        self.url = source_url

    def upload(self) -> bool:
        """Check for required parameters to upload and run the job.

        :return: Whether the upload was successful.
        """
        if self.comment is None:
            self.comment = self.filepage.text
        if not self.comment:
            raise ValueError('APISite.upload: cannot upload file without '
                             'a summary/description.')

        if self.text is None:
            self.text = self.filepage.text
        if not self.text:
            self.text = self.comment

        return self._upload(self.ignore_warnings, self.report_success)

    @classmethod
    def create_warnings_list(cls, response, file_key):
        """Create a list of upload errors."""
        return [UploadError(warning,
                            cls.upload_warnings.get(warning, '{msg}')
                            .format(msg=data),
                            file_key,
                            response['offset'])
                for warning, data in response['warnings'].items()]

    def _upload(self, ignore_warnings, report_success,
                file_key=None, offset=0) -> bool:
        """Recursive Upload method.

        :param file_key: Reuses an already uploaded file using the
            filekey. If None (default) it will upload the file.
        :param offset: When file_key is not None this can be an integer
            to continue a previously canceled chunked upload. If False
            it treats that as a finished upload. If True it requests the
            stash info from the server to determine the offset. By
            default starts at 0.
        :return: Whether the upload was successful.
        """
        # An offset != 0 doesn't make sense without a file key
        assert offset == 0 or file_key is not None

        if report_success is None:
            report_success = isinstance(ignore_warnings, bool)
        if report_success is True and not isinstance(ignore_warnings, bool):
            raise ValueError('report_success may only be set to True when '
                             'ignore_warnings is a boolean')
        if isinstance(ignore_warnings, Iterable):
            ignored_warnings = ignore_warnings

            def ignore_warnings(warnings):
                return all(w.code in ignored_warnings for w in warnings)

        ignore_all_warnings = not callable(ignore_warnings) and ignore_warnings

        token = self.site.tokens['csrf']
        result = None
        file_page_title = self.filepage.title(with_ns=False)
        file_size = None

        # make sure file actually exists
        if self.filename:
            if os.path.isfile(self.filename):
                file_size = os.path.getsize(self.filename)
            elif offset is not False:
                raise ValueError("File '{}' does not exist."
                                 .format(self.filename))

        # Verify the stash when a file key and offset is given:
        # requests the SHA1 and file size uploaded and compares it to
        # the local file. Also verify that offset is matching the
        # file size if the offset is an int. If offset is False if
        # verifies that the file size match with the local file.
        verify_stash = False
        if self.filename and file_key:
            assert offset is False or file_size is not None
            verify_stash = True
            if (offset is not False and offset is not True
                    and offset > file_size):
                raise ValueError(
                    'For the file key "{}" the offset was set to {} '
                    'while the file is only {} bytes large.'
                    .format(file_key, offset, file_size))

        if verify_stash or offset is True:
            if not file_key:
                raise ValueError('Without a file key it cannot request the '
                                 'stash information')
            if not self.filename:
                raise ValueError('Can request stash information only when '
                                 'using a file name.')
            props = ['size']
            if verify_stash:
                props += ['sha1']
            stash_info = self.site.stash_info(file_key, props)
            if offset is True:
                offset = stash_info['size']
            elif offset is False:
                if file_size != stash_info['size']:
                    raise ValueError(
                        'For the file key "{}" the server reported a size '
                        '{} while the file size is {}'
                        .format(file_key, stash_info['size'], file_size))
            elif offset is not False and offset != stash_info['size']:
                raise ValueError(
                    'For the file key "{}" the server reported a size {} '
                    'while the offset was {}'
                    .format(file_key, stash_info['size'], offset))

            if verify_stash:
                # The SHA1 was also requested so calculate and compare it
                assert 'sha1' in stash_info, \
                    f'sha1 not in stash info: {stash_info}'
                sha1 = compute_file_hash(self.filename, bytes_to_read=offset)
                if sha1 != stash_info['sha1']:
                    raise ValueError(
                        'The SHA1 of {} bytes of the stashed "{}" is {} '
                        'while the local file is {}'
                        .format(offset, file_key, stash_info['sha1'], sha1))

        assert offset is not True
        if file_key and file_size is None:
            assert offset is False

        data = {}
        if file_key and offset is False or offset == file_size:
            pywikibot.log('Reused already upload file using filekey "{}"'
                          .format(file_key))
            # TODO: Use sessionkey instead of filekey if necessary
            final_request = self.site._request(
                parameters={
                    'action': 'upload',
                    'token': token,
                    'filename': file_page_title,
                    'comment': self.comment,
                    'text': self.text,
                    'async': self.asynchronous,
                    'filekey': file_key
                })

        elif self.filename:
            # TODO: Dummy value to allow also Unicode names, see bug T75661
            mime_filename = 'FAKE-NAME'
            # upload local file
            throttle = True
            filesize = os.path.getsize(self.filename)
            chunked_upload = 0 < self.chunk_size < filesize
            with open(self.filename, 'rb') as f:
                final_request = self.site._request(
                    throttle=throttle, parameters={
                        'action': 'upload', 'token': token, 'text': self.text,
                        'filename': file_page_title, 'comment': self.comment})
                if chunked_upload:
                    if offset > 0:
                        pywikibot.log('Continuing upload from byte {}'
                                      .format(offset))
                    poll = False
                    while True:

                        if poll:
                            # run a poll; not possible in first iteration
                            assert file_key
                            req = self.site.simple_request(
                                action='upload',
                                token=token,
                                filekey=file_key,
                                checkstatus=True)
                        else:
                            f.seek(offset)
                            chunk = f.read(self.chunk_size)
                            # workaround (hack) for T132676
                            # append another '\r' so that one is the payload
                            # and the second is used for newline when mangled
                            # by email package.
                            if (len(chunk) < self.chunk_size
                                    or (offset + len(chunk)) == filesize
                                    and chunk[-1] == b'\r'[0]):
                                chunk += b'\r'

                            mime_params = {
                                'chunk': (chunk,
                                          ('application', 'octet-stream'),
                                          {'filename': mime_filename})
                            }
                            req = self.site._request(
                                throttle=throttle,
                                mime=mime_params,
                                parameters={
                                    'action': 'upload',
                                    'token': token,
                                    'stash': True,
                                    'filesize': filesize,
                                    'offset': offset,
                                    'filename': file_page_title,
                                    'async': self.asynchronous,
                                    'ignorewarnings': ignore_all_warnings})

                            if file_key:
                                req['filekey'] = file_key

                        try:
                            data = req.submit()['upload']
                        except APIError as error:
                            # TODO: catch and process foreseeable errors
                            if error.code == 'stashfailed' \
                                    and 'offset' in error.other:
                                # TODO: Ask MediaWiki to change this
                                # ambiguous error code.

                                new_offset = int(error.other['offset'])
                                # If the offset returned from the server
                                # (the offset it expects now) is equal to
                                # the offset we sent it, there must be
                                # something else that prevented the upload,
                                # instead of simple offset mismatch. This
                                # also prevents infinite loops when we
                                # upload the same chunk again and again,
                                # every time ApiError.
                                if offset != new_offset:
                                    pywikibot.log(
                                        'Old offset: {}; Returned '
                                        'offset: {}; Chunk size: {}'
                                        .format(offset, new_offset,
                                                len(chunk)))
                                    pywikibot.warning('Attempting to correct '
                                                      'automatically from '
                                                      'offset mismatch error.')
                                    offset = new_offset
                                    continue
                            raise error
                        if 'nochange' in data:  # in simulation mode
                            break

                        # Polls may not contain file key in response
                        file_key = data.get('filekey', file_key)
                        if data['result'] == 'Warning':
                            assert ('warnings' in data
                                    and not ignore_all_warnings)
                            if callable(ignore_warnings):
                                restart = False
                                if 'offset' not in data:
                                    # This is a result of a warning in the
                                    # first chunk. The chunk is not actually
                                    # stashed so upload must be restarted if
                                    # the warning is allowed.
                                    # T112416 and T112405#1637544
                                    restart = True
                                    data['offset'] = True
                                if ignore_warnings(self.create_warnings_list(
                                        data, file_key)):
                                    # Future warnings of this run
                                    # can be ignored
                                    if restart:
                                        return self._upload(
                                            ignore_warnings=True,
                                            report_success=False
                                        )

                                    ignore_warnings = True
                                    ignore_all_warnings = True
                                    offset = data['offset']
                                    continue
                                return False
                            result = data
                            result.setdefault('offset', 0)
                            break

                        if data['result'] == 'Continue':
                            throttle = False
                            if 'offset' in data:
                                new_offset = int(data['offset'])
                                if offset + len(chunk) != new_offset:
                                    pywikibot.log('Old offset: {}; Returned '
                                                  'offset: {}; Chunk size: {}'
                                                  .format(offset,
                                                          new_offset,
                                                          len(chunk)))
                                    pywikibot.warning('Unexpected offset.')
                                offset = new_offset
                            else:
                                pywikibot.warning('Offset was not supplied.')
                                offset += len(chunk)
                        elif data['result'] == 'Poll':
                            poll = True
                            pywikibot.log('Waiting for server to '
                                          'assemble chunks.')
                        elif data['result'] == 'Success':  # finished
                            pywikibot.log('Finished uploading last chunk.')
                            final_request['filekey'] = file_key
                            final_request['async'] = self.asynchronous
                            break
                        else:
                            raise Error('Unrecognized result: {result}'
                                        .format_map(data))

                else:  # not chunked upload
                    if file_key:
                        final_request['filekey'] = file_key
                    else:
                        file_contents = f.read()
                        filetype = (mimetypes.guess_type(self.filename)[0]
                                    or 'application/octet-stream')
                        final_request.mime = {
                            'file': (file_contents, filetype.split('/'),
                                     {'filename': mime_filename})
                        }
        else:
            # upload by URL
            if not self.site.has_right('upload_by_url'):
                raise Error(
                    "User '{}' is not authorized to upload by URL on site {}."
                    .format(self.site.user(), self))
            final_request = self.site.simple_request(
                action='upload', filename=file_page_title, url=self.url,
                comment=self.comment, text=self.text, token=token)

        return self.submit(final_request, result, data.get('result'),
                           ignore_warnings, ignore_all_warnings,
                           report_success, file_key)

    def submit(self, request, result, data_result: Optional[str],
               ignore_warnings, ignore_all_warnings, report_success,
               file_key) -> bool:
        """Submit request and return whether upload was successful."""
        # some warning keys have been changed
        warning_keys = {
            'nochange': 'no-change',
            'duplicateversions': 'duplicate-version',
            'emptyfile': 'empty-file',
        }

        token = request['token']
        while True:
            if not result:
                request['watch'] = self.watch
                request['ignorewarnings'] = ignore_all_warnings
                result = request.submit()['upload']
                pywikibot.debug(result)

            if 'result' not in result:
                raise Error(f'Upload: unrecognized response: {result}')

            if result['result'] == 'Warning':
                assert 'warnings' in result and not ignore_all_warnings

                if self.filename:
                    if 'filekey' in result:
                        file_key = result['filekey']
                    elif 'sessionkey' in result:
                        # TODO: Probably needs to be reflected in the API call
                        # above
                        file_key = result['sessionkey']
                        pywikibot.warning(
                            'Using sessionkey instead of filekey.')
                    else:
                        file_key = None
                        pywikibot.warning('No filekey defined.')
                else:
                    file_key = None

                if not report_success:
                    result.setdefault('offset', bool(self.filename))
                    offset = result['offset'] if self.filename else False
                    if ignore_warnings(self.create_warnings_list(result,
                                                                 file_key)):
                        return self._upload(ignore_warnings=True,
                                            report_success=False,
                                            file_key=file_key,
                                            offset=offset)
                    return False

                if len(result['warnings']) > 1:
                    warn('The upload returned {} warnings: {}'
                         .format(len(result['warnings']),
                                 ', '.join(result['warnings'])),
                         UserWarning, 3)
                warning = list(result['warnings'].keys())[0]
                message = result['warnings'][warning]
                warning = warning_keys.get(warning, warning)
                raise UploadError(warning,
                                  self.upload_warnings[warning]
                                  .format(msg=message),
                                  file_key=file_key,
                                  offset=result.get('offset', False))

            if result['result'] == 'Poll':
                # Polling is meaningless without a file key
                assert file_key
                pywikibot.log('Waiting for upload to be published.')
                result = None
                request = self.site.simple_request(
                    action='upload',
                    token=token,
                    filekey=file_key,
                    checkstatus=True)
                continue

            if result['result'] == 'Success':
                if report_success:
                    pywikibot.info('Upload successful.')
                # If we receive a nochange, that would mean we're in simulation
                # mode, don't attempt to access imageinfo
                if 'nochange' not in result:
                    self.filepage._load_file_revisions([result['imageinfo']])
                return True

            raise Error('Unrecognized result: {}'
                        .format(data_result or result['result']))
