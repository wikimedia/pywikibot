#
# (C) Pywikibot team, 2009-2026
#
# Distributed under the terms of the MIT license.
#
"""Objects representing API upload to MediaWiki sites."""
from __future__ import annotations

import mimetypes
import os
from collections.abc import Iterable
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any
from warnings import warn

import pywikibot
from pywikibot.exceptions import APIError, Error, UploadError
from pywikibot.tools import compute_file_hash, deprecated_args


__all__ = ('Uploader', )


class _UploadStage(Enum):

    """Stages of an upload attempt."""

    PREPARE = auto()
    RECOVER_STASH = auto()
    TRANSFER = auto()
    POLL_TRANSFER = auto()
    FINALIZE = auto()
    POLL_PUBLICATION = auto()


class _ResumeMode(Enum):

    """Ways to resume an upload from the server stash."""

    FRESH = auto()
    DISCOVER_OFFSET = auto()
    AT_OFFSET = auto()
    COMPLETE_STASH = auto()


@dataclass
class _UploadState:

    """Mutable progress for one upload invocation."""

    ignore_warnings: Any
    ignore_all_warnings: bool
    report_success: bool | None
    stage: _UploadStage = _UploadStage.PREPARE
    resume_mode: _ResumeMode = _ResumeMode.FRESH
    file_key: str | None = None
    offset: int = 0
    file_size: int | None = None
    token: str | None = None
    file_page_title: str | None = None
    request: Any = None
    response: dict[str, Any] | None = None
    data_result: str | None = None
    throttle: bool = True


class Uploader:

    """Uploader class to upload a file to the wiki.

    .. version-added:: 7.1

    :param site: The current site to work on
    :param filepage: a FilePage object from which the wiki-name of the
        file will be obtained.
    :param source_filename: path to the file to be uploaded
    :param source_url: URL of the file to be uploaded
    :param summary: Edit summary; if this is not provided, then
        filepage.text will be used. An empty summary is not permitted.
        This may also serve as the initial page text (see below).
    :param text: Initial page text; if this is not set, then
        filepage.text will be used, or summary.
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
        UploadError codes are in that list. If the result is False it'll
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

    @deprecated_args(comment='summary')  # since 11.8.0
    def __init__(self,
                 site: pywikibot.site.APISite,
                 filepage: pywikibot.FilePage,
                 *,
                 source_filename: str | None = None,
                 source_url: str | None = None,
                 summary: str | None = None,
                 text: str | None = None,
                 watch: bool = False,
                 chunk_size: int = 0,
                 asynchronous: bool = False,
                 ignore_warnings=False,
                 report_success: bool | None = None) -> None:
        """Initializer.

        .. version-changed:: 11.8
           The *comment* parameter was renamed to *summary*.
        """
        self.site = site
        self.filepage = filepage
        self.comment = summary
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
        """Upload the file using explicit state transitions."""
        state = self._new_state(ignore_warnings, report_success)
        self._restart_upload(state, file_key, offset)
        return self._run_upload(state)

    def _new_state(self, ignore_warnings, report_success) -> _UploadState:
        """Normalize upload options and create its initial state."""
        if report_success is None:
            report_success = isinstance(ignore_warnings, bool)
        if report_success is True and not isinstance(ignore_warnings, bool):
            raise ValueError('report_success may only be set to True when '
                             'ignore_warnings is a boolean')
        if isinstance(ignore_warnings, Iterable):
            ignored_warnings = ignore_warnings

            def ignore_warnings(warnings):
                return all(w.code in ignored_warnings for w in warnings)

        ignore_all_warnings = (
            not callable(ignore_warnings) and ignore_warnings)
        return _UploadState(ignore_warnings, ignore_all_warnings,
                            report_success)

    def _run_upload(self, state: _UploadState) -> bool:
        """Run upload stages until the upload completes or aborts."""
        while True:
            if state.stage is _UploadStage.PREPARE:
                self._prepare_upload(state)
            elif state.stage is _UploadStage.RECOVER_STASH:
                self._recover_stash(state)
            elif state.stage in {
                    _UploadStage.TRANSFER,
                    _UploadStage.POLL_TRANSFER,
            }:
                outcome = self._transfer_chunks(state)
                if outcome is not None:
                    return outcome
            elif state.stage in {
                    _UploadStage.FINALIZE,
                    _UploadStage.POLL_PUBLICATION,
            }:
                outcome = self._finalize_upload(state)
                if outcome is not None:
                    return outcome
            else:  # pragma: no cover - all stages are handled above
                raise AssertionError(f'Unknown upload stage: {state.stage}')

    def _prepare_upload(self, state: _UploadState) -> None:
        """Prepare one fresh or resumed upload attempt."""
        state.token = self.site.tokens['csrf']
        state.file_page_title = self.filepage.title(
            with_ns=False,
            with_section=False,
        )
        state.file_size = None
        state.request = None
        state.response = None
        state.data_result = None
        state.throttle = True

        if self.filename:
            if os.path.isfile(self.filename):
                state.file_size = os.path.getsize(self.filename)
            elif state.resume_mode is not _ResumeMode.COMPLETE_STASH:
                raise ValueError(f"File '{self.filename}' does not exist.")

        if self.filename and state.file_key:
            self._validate_resume_offset(state)
            state.stage = _UploadStage.RECOVER_STASH
        else:
            self._prepare_request(state)

    def _validate_resume_offset(self, state: _UploadState) -> None:
        """Validate a client-provided resume offset."""
        assert (state.resume_mode is _ResumeMode.COMPLETE_STASH
                or state.file_size is not None)
        file_size = state.file_size
        if (state.resume_mode is _ResumeMode.AT_OFFSET
                and file_size is not None
                and state.offset > file_size):
            raise ValueError(
                f'For the file key "{state.file_key}" the offset was set to '
                f'{state.offset} while the file is only '
                f'{file_size} bytes large.'
            )

    def _recover_stash(self, state: _UploadState) -> None:
        """Validate a server stash and select its next stage."""
        if not state.file_key:
            raise ValueError('Without a file key it cannot request the '
                             'stash information')
        if not self.filename:
            raise ValueError('Can request stash information only when '
                             'using a file name.')

        stash_info = self.site.stash_info(
            state.file_key, ['size', 'sha1'])
        if state.resume_mode is _ResumeMode.DISCOVER_OFFSET:
            state.offset = stash_info['size']
        elif state.resume_mode is _ResumeMode.COMPLETE_STASH:
            if state.file_size != stash_info['size']:
                raise ValueError(
                    f'For the file key "{state.file_key}" the server reported '
                    f'a size {stash_info["size"]} while the file size is '
                    f'{state.file_size}')
            assert state.file_size is not None
            state.offset = state.file_size
        elif state.offset != stash_info['size']:
            raise ValueError(
                f'For the file key "{state.file_key}" the server reported '
                f'a size {stash_info["size"]} while the offset was '
                f'{state.offset}')

        assert 'sha1' in stash_info, f'sha1 not in stash info: {stash_info}'
        sha1 = compute_file_hash(
            self.filename,
            bytes_to_read=(
                None if state.resume_mode is _ResumeMode.COMPLETE_STASH
                else state.offset))
        if sha1 != stash_info['sha1']:
            raise ValueError(
                f'The SHA1 of {state.offset} bytes of the stashed '
                f'"{state.file_key}" is {stash_info["sha1"]} '
                f'while the local file is {sha1}')

        self._prepare_request(state)

    def _prepare_request(self, state: _UploadState) -> None:
        """Build an upload request or select chunk transfer."""
        reuse_stash = (
            bool(state.file_key)
            and state.resume_mode is _ResumeMode.COMPLETE_STASH
        ) or state.offset == state.file_size
        if reuse_stash:
            pywikibot.log(
                'Reused already upload file using filekey '
                f'"{state.file_key}"')
            # TODO: Use sessionkey instead of filekey if necessary
            state.request = self.site._request(parameters={
                'action': 'upload',
                'token': state.token,
                'filename': state.file_page_title,
                'comment': self.comment,
                'text': self.text,
                'async': self.asynchronous,
                'filekey': state.file_key,
            })
            state.stage = _UploadStage.FINALIZE
            return

        if self.filename:
            self._prepare_file_request(state)
            return

        if not self.site.has_right('upload_by_url'):
            raise Error(f"User '{self.site.user()}' is not authorized to "
                        f'upload by URL on site {self}.')
        state.request = self.site.simple_request(
            action='upload', filename=state.file_page_title, url=self.url,
            comment=self.comment, text=self.text, token=state.token)
        state.stage = _UploadStage.FINALIZE

    def _prepare_file_request(self, state: _UploadState) -> None:
        """Build a local-file request and select its transfer mode."""
        assert self.filename is not None
        state.file_size = os.path.getsize(self.filename)
        state.request = self.site._request(
            throttle=state.throttle,
            parameters={
                'action': 'upload',
                'token': state.token,
                'text': self.text,
                'filename': state.file_page_title,
                'comment': self.comment,
            })
        if 0 < self.chunk_size < state.file_size:
            state.stage = _UploadStage.TRANSFER
            return

        if state.file_key:
            state.request['filekey'] = state.file_key
        else:
            # TODO: Dummy value to allow Unicode names, see T75661
            with open(self.filename, 'rb') as f:
                file_contents = f.read()
            filetype = (mimetypes.guess_type(self.filename)[0]
                        or 'application/octet-stream')
            state.request.mime = {
                'file': (file_contents, filetype.split('/'),
                         {'filename': 'FAKE-NAME'})
            }
        state.stage = _UploadStage.FINALIZE

    def _transfer_chunks(self, state: _UploadState) -> bool | None:
        """Transfer chunks until another upload stage is required."""
        assert self.filename is not None
        if state.offset > 0:
            pywikibot.log(f'Continuing upload from byte {state.offset}')

        chunk = b''
        with open(self.filename, 'rb') as f:
            while state.stage in {
                    _UploadStage.TRANSFER,
                    _UploadStage.POLL_TRANSFER,
            }:
                request, new_chunk = self._next_chunk_request(state, f)
                if new_chunk is not None:
                    chunk = new_chunk
                try:
                    data = request.submit()['upload']
                except APIError as error:
                    if self._correct_stash_offset(error, state, chunk):
                        continue
                    raise

                outcome = self._handle_chunk_response(state, data, chunk)
                if outcome is not None:
                    return outcome
        return None

    def _next_chunk_request(self, state: _UploadState, file_obj):
        """Create the next chunk-transfer or polling request."""
        if state.stage is _UploadStage.POLL_TRANSFER:
            assert state.file_key
            return self.site.simple_request(
                action='upload', token=state.token,
                filekey=state.file_key, checkstatus=True), None

        file_obj.seek(state.offset)
        chunk = file_obj.read(self.chunk_size)
        # Workaround for T132676: append another carriage return so that
        # one remains in the payload if the email package mangles it.
        if (len(chunk) < self.chunk_size
                or (state.offset + len(chunk)) == state.file_size
                and chunk[-1] == b'\r'[0]):
            chunk += b'\r'
        request = self.site._request(
            throttle=state.throttle,
            mime={
                'chunk': (chunk, ('application', 'octet-stream'),
                          {'filename': 'FAKE-NAME'}),
            },
            parameters={
                'action': 'upload',
                'token': state.token,
                'stash': True,
                'filesize': state.file_size,
                'offset': state.offset,
                'filename': state.file_page_title,
                'async': self.asynchronous,
                'ignorewarnings': state.ignore_all_warnings,
            })
        if state.file_key:
            request['filekey'] = state.file_key
        return request, chunk

    @staticmethod
    def _correct_stash_offset(error, state: _UploadState, chunk) -> bool:
        """Correct a mismatched stash offset when the server supplies one."""
        if error.code != 'stashfailed' or 'offset' not in error.other:
            return False
        new_offset = int(error.other['offset'])
        if state.offset == new_offset:
            return False
        pywikibot.log(
            f'Old offset: {state.offset}; Returned offset: {new_offset}; '
            f'Chunk size: {len(chunk)}')
        pywikibot.warning('Attempting to correct automatically from '
                          'offset mismatch error.')
        state.offset = new_offset
        return True

    def _handle_chunk_response(self, state: _UploadState, data,
                               chunk) -> bool | None:
        """Apply a chunk response and select the next stage."""
        state.data_result = data.get('result')
        if 'nochange' in data:  # in simulation mode
            state.stage = _UploadStage.FINALIZE
            return None

        # Polls may not contain a file key in the response.
        state.file_key = data.get('filekey', state.file_key)
        if data['result'] == 'Warning':
            return self._handle_chunk_warning(state, data)
        if data['result'] == 'Continue':
            self._continue_chunk(state, data, chunk)
        elif data['result'] == 'Poll':
            state.stage = _UploadStage.POLL_TRANSFER
            pywikibot.log('Waiting for server to assemble chunks.')
        elif data['result'] == 'Success':
            pywikibot.log('Finished uploading last chunk.')
            state.request['filekey'] = state.file_key
            state.request['async'] = self.asynchronous
            state.stage = _UploadStage.FINALIZE
        else:
            raise Error('Unrecognized result: {result}'.format_map(data))
        return None

    def _handle_chunk_warning(self, state: _UploadState,
                              data) -> bool | None:
        """Resolve a warning returned while transferring chunks."""
        assert 'warnings' in data and not state.ignore_all_warnings
        if not callable(state.ignore_warnings):
            state.response = data
            state.response.setdefault('offset', 0)
            state.stage = _UploadStage.FINALIZE
            return None

        restart = 'offset' not in data
        if restart:
            # A first-chunk warning has no stashed data to continue.
            # See T112416 and T112405#1637544.
            data['offset'] = True
        warnings = self.create_warnings_list(data, state.file_key)
        if not state.ignore_warnings(warnings):
            return False

        self._ignore_future_warnings(state)
        if restart:
            self._restart_upload(state)
        else:
            state.offset = data['offset']
        return None

    @staticmethod
    def _continue_chunk(state: _UploadState, data, chunk) -> None:
        """Advance state after a successful chunk transfer."""
        state.throttle = False
        if 'offset' in data:
            new_offset = int(data['offset'])
            if state.offset + len(chunk) != new_offset:
                pywikibot.log(
                    f'Old offset: {state.offset}; Returned offset: '
                    f'{new_offset}; Chunk size: {len(chunk)}')
                pywikibot.warning('Unexpected offset.')
            state.offset = new_offset
        else:
            pywikibot.warning('Offset was not supplied.')
            state.offset += len(chunk)

    @staticmethod
    def _ignore_future_warnings(state: _UploadState) -> None:
        """Ignore any warnings after the callback accepts them."""
        state.ignore_warnings = True
        state.ignore_all_warnings = True
        state.report_success = False

    def _restart_upload(self, state: _UploadState, file_key=None,
                        offset=0) -> None:
        """Start a new attempt with explicit resume information."""
        assert offset == 0 or file_key is not None
        state.stage = _UploadStage.PREPARE
        state.file_key = file_key
        state.offset = 0
        if not self.filename:
            state.resume_mode = _ResumeMode.FRESH
        elif offset is True:
            state.resume_mode = _ResumeMode.DISCOVER_OFFSET
        elif offset is False:
            state.resume_mode = _ResumeMode.COMPLETE_STASH
        elif file_key:
            state.resume_mode = _ResumeMode.AT_OFFSET
            state.offset = offset
        else:
            state.resume_mode = _ResumeMode.FRESH
        state.request = None
        state.response = None
        state.data_result = None

    def _finalize_upload(self, state: _UploadState) -> bool | None:
        """Submit or poll the final publication request."""
        assert state.request is not None
        if not state.response:
            state.request['watch'] = self.watch
            state.request['ignorewarnings'] = state.ignore_all_warnings
            state.response = state.request.submit()['upload']
            pywikibot.debug(state.response)

        if 'result' not in state.response:
            raise Error(
                f'Upload: unrecognized response: {state.response}')
        if state.response['result'] == 'Warning':
            return self._handle_final_warning(state)
        if state.response['result'] == 'Poll':
            self._poll_publication(state)
            return None
        if state.response['result'] == 'Success':
            return self._complete_upload(state)
        raise Error(
            'Unrecognized result: '
            f"{state.data_result or state.response['result']}")

    def _handle_final_warning(self, state: _UploadState) -> bool | None:
        """Resolve a warning returned during final publication."""
        result = state.response
        assert result is not None
        assert 'warnings' in result and not state.ignore_all_warnings
        warnings = result['warnings']
        self._update_warning_file_key(state, result)

        if not state.report_success:
            result.setdefault('offset', bool(self.filename))
            offset = result['offset'] if self.filename else False
            warning_list = self.create_warnings_list(
                result, state.file_key)
            if state.ignore_warnings(warning_list):
                self._ignore_future_warnings(state)
                self._restart_upload(state, state.file_key, offset)
                return None
            return False

        if len(warnings) > 1:
            warn(f'The upload returned {len(warnings)} warnings: '
                 f'{", ".join(warnings)}', UserWarning, 3)
        warning, message = next(iter(warnings.items()))
        warning_keys = {
            'nochange': 'no-change',
            'duplicateversions': 'duplicate-version',
            'emptyfile': 'empty-file',
        }
        warning = warning_keys.get(warning, warning)
        raise UploadError(warning,
                          self.upload_warnings[warning].format(msg=message),
                          file_key=state.file_key,
                          offset=result.get('offset', False))

    def _update_warning_file_key(self, state: _UploadState, result) -> None:
        """Update the file key supplied with a final warning."""
        if not self.filename:
            state.file_key = None
        elif 'filekey' in result:
            state.file_key = result['filekey']
        elif 'sessionkey' in result:
            # TODO: Reflect sessionkey in the API call above if necessary.
            state.file_key = result['sessionkey']
            pywikibot.warning('Using sessionkey instead of filekey.')
        else:
            state.file_key = None
            pywikibot.warning('No filekey defined.')

    def _poll_publication(self, state: _UploadState) -> None:
        """Prepare a status request for asynchronous publication."""
        assert state.file_key
        pywikibot.log('Waiting for upload to be published.')
        state.response = None
        state.request = self.site.simple_request(
            action='upload', token=state.token,
            filekey=state.file_key, checkstatus=True)
        state.stage = _UploadStage.POLL_PUBLICATION

    def _complete_upload(self, state: _UploadState) -> bool:
        """Record a successful upload and return its result."""
        result = state.response
        assert result is not None
        if state.report_success:
            pywikibot.info('Upload successful.')
        if 'nochange' not in result:
            self.filepage._load_file_revisions([result['imageinfo']])
        return True

    def submit(self, request, result, data_result: str | None,
               ignore_warnings, ignore_all_warnings, report_success,
               file_key) -> bool:
        """Submit request and return whether upload was successful.

        This compatibility entry point starts the state machine at final
        publication. New upload orchestration uses private stage helpers.
        """
        state = _UploadState(
            ignore_warnings,
            ignore_all_warnings,
            report_success,
            stage=_UploadStage.FINALIZE,
            file_key=file_key,
            token=request['token'],
            request=request,
            response=result,
            data_result=data_result,
        )
        return self._run_upload(state)
