#!/usr/bin/env python3
#
# (C) Pywikibot team, 2014-2026
#
# Distributed under the terms of the MIT license.
#
"""Site upload tests."""
from __future__ import annotations

import unittest
from contextlib import suppress

import pywikibot
from pywikibot.site._upload import Uploader
from pywikibot.tools import compute_file_hash
from tests import join_images_path
from tests.aspects import TestCase
from tests.utils import DryRequest, DrySite


class _Request(DryRequest):

    """Dry upload request returning scripted responses."""

    def __init__(self, site, parameters, *, throttle=True, mime=None) -> None:
        super().__init__(site=site, parameters=parameters,
                         throttle=throttle, mime=mime)
        self.submitted = False

    def submit(self):
        """Return the next scripted response."""
        self.submitted = True
        response = self.site.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class _TokenWallet:

    """Return a distinct token for each upload attempt."""

    def __init__(self) -> None:
        self.calls = 0

    def __getitem__(self, key):
        assert key == 'csrf'
        self.calls += 1
        return f'token-{self.calls}'


class _Site(DrySite):

    """Dry site recording upload requests."""

    def __init__(self, responses, stash_info=None) -> None:
        super().__init__('test', 'wikipedia', 'UploadTest')
        self._userinfo = {
            'id': 1,
            'name': 'UploadTest',
            'rights': ['upload_by_url'],
        }
        self.responses = list(responses)
        self.requests = []
        self.stash_calls = []
        self._tokens = _TokenWallet()
        self._stash_info = stash_info

    def _request(self, *, throttle=True, parameters, mime=None):
        request = _Request(
            self, parameters, throttle=throttle, mime=mime)
        self.requests.append(request)
        return request

    def simple_request(self, **parameters):
        request = _Request(self, parameters)
        self.requests.append(request)
        return request

    def stash_info(self, file_key, props):
        self.stash_calls.append((file_key, props))
        return self._stash_info


class _FilePage:

    """FilePage test double recording revision loading."""

    text = 'description'

    def __init__(self) -> None:
        self.revisions = None

    def title(self, *, with_ns, with_section):
        assert not with_ns and not with_section
        return 'Test.png'

    def _load_file_revisions(self, revisions) -> None:
        self.revisions = revisions


class TestUploaderStateTransitions(TestCase):

    """Offline tests for upload state transitions."""

    net = False

    source = join_images_path('MP_sounds.png')

    @staticmethod
    def _success():
        return {
            'upload': {
                'result': 'Success',
                'imageinfo': {'timestamp': '2026-08-14T00:00:00Z'},
            },
        }

    def _uploader(self, responses, callback, *, stash_info=None):
        site = _Site(responses, stash_info)
        page = _FilePage()
        uploader = Uploader(
            site, page, source_filename=self.source,
            comment='upload test', chunk_size=1024,
            ignore_warnings=callback)
        return uploader, site, page

    def test_first_chunk_warning_restarts_upload(self) -> None:
        """Test accepting an unstashed warning starts a new attempt."""
        seen = []
        responses = [
            {'upload': {
                'result': 'Warning',
                'warnings': {'exists': 'Test.png'},
                'filekey': 'unused-key',
            }},
            {'upload': {
                'result': 'Continue', 'offset': 1024,
                'filekey': 'second-key',
            }},
            {'upload': {'result': 'Success', 'filekey': 'second-key'}},
            self._success(),
        ]

        def callback(warnings):
            seen.extend(warnings)
            return True

        uploader, site, page = self._uploader(responses, callback)

        self.assertTrue(uploader.upload())
        chunks = [request for request in site.requests
                  if request.get('stash')]
        self.assertEqual([request['offset'] for request in chunks],
                         [[0], [0], [1024]])
        self.assertEqual([request['ignorewarnings'] for request in chunks],
                         [[False], [True], [True]])
        self.assertEqual(site.tokens.calls, 2)
        self.assertIsEmpty(site.stash_calls)
        self.assertEqual(seen[0].file_key, 'unused-key')
        self.assertIs(seen[0].offset, True)
        self.assertIsNotNone(page.revisions)

    def test_chunk_warning_continues_current_attempt(self) -> None:
        """Test an accepted stashed chunk warning continues directly."""
        responses = [
            {'upload': {
                'result': 'Warning', 'offset': 1024,
                'warnings': {'exists': 'Test.png'},
                'filekey': 'upload-key',
            }},
            {'upload': {'result': 'Success', 'filekey': 'upload-key'}},
            self._success(),
        ]
        uploader, site, _ = self._uploader(
            responses, lambda warnings: True)

        self.assertTrue(uploader.upload())
        chunks = [request for request in site.requests
                  if request.get('stash')]
        self.assertEqual([request['offset'] for request in chunks],
                         [[0], [1024]])
        self.assertEqual(site.tokens.calls, 1)
        self.assertIsEmpty(site.stash_calls)

    def test_final_warning_recovers_stash(self) -> None:
        """Test accepting a final warning validates and reuses its stash."""
        sha1 = compute_file_hash(self.source)
        for response_offset in (None, 1276):
            warning = {
                'result': 'Warning',
                'warnings': {'exists': 'Test.png'},
                'filekey': 'upload-key',
            }
            if response_offset is not None:
                warning['offset'] = response_offset
            responses = [{'upload': warning}, self._success()]
            stash_info = {'size': 1276, 'sha1': sha1}

            with self.subTest(offset=response_offset):
                uploader, site, _ = self._uploader(
                    responses, lambda warnings: True,
                    stash_info=stash_info)
                uploader.chunk_size = 0

                self.assertTrue(uploader.upload())
                self.assertEqual(site.tokens.calls, 2)
                self.assertEqual(
                    site.stash_calls,
                    [('upload-key', ['size', 'sha1'])])
                submitted = [request for request in site.requests
                             if request.submitted]
                self.assertNotIn('filekey', submitted[0])
                self.assertEqual(submitted[1]['filekey'], ['upload-key'])

    def test_transfer_and_publication_polling(self) -> None:
        """Test transfer and publication polling remain distinct."""
        responses = [
            {'upload': {'result': 'Poll', 'filekey': 'upload-key'}},
            {'upload': {'result': 'Continue', 'offset': 1024}},
            {'upload': {'result': 'Success'}},
            {'upload': {'result': 'Poll'}},
            self._success(),
        ]
        uploader, site, _ = self._uploader(
            responses, lambda warnings: True)

        self.assertTrue(uploader.upload())
        polls = [request for request in site.requests
                 if request.get('checkstatus')]
        self.assertLength(polls, 3)
        self.assertTrue(all(request['filekey'] == ['upload-key']
                            for request in polls))

    def test_url_warning_restarts_without_stash(self) -> None:
        """Test accepting a URL warning starts a fresh URL request."""
        responses = [
            {'upload': {
                'result': 'Warning',
                'warnings': {'exists': 'Test.png'},
            }},
            self._success(),
        ]
        site = _Site(responses)
        page = _FilePage()
        uploader = Uploader(
            site, page, source_url='https://example.invalid/Test.png',
            comment='upload test', ignore_warnings=lambda warnings: True)

        self.assertTrue(uploader.upload())
        submitted = [request for request in site.requests
                     if request.submitted]
        self.assertLength(submitted, 2)
        self.assertEqual([request['ignorewarnings'] for request in submitted],
                         [[False], [True]])
        self.assertEqual(site.tokens.calls, 2)
        self.assertIsEmpty(site.stash_calls)

    def test_submit_compatibility(self) -> None:
        """Test the existing submit entry point uses the state driver."""
        site = _Site([self._success()])
        page = _FilePage()
        uploader = Uploader(
            site, page, source_url='https://example.invalid/Test.png',
            comment='upload test')
        request = site.simple_request(action='upload', token='token')

        self.assertTrue(uploader.submit(
            request, None, None, False, False, False, None))
        self.assertIsNotNone(page.revisions)


class TestUpload(TestCase):

    """Test cases for upload."""

    write = True

    family = 'wikipedia'
    code = 'test'

    sounds_png = join_images_path('MP_sounds.png')
    arrow_png = join_images_path('1rightarrow.png')

    @unittest.expectedFailure  # T367319
    def test_png(self) -> None:
        """Test uploading a png using Site.upload."""
        page = pywikibot.FilePage(self.site, 'MP_sounds-pwb.png')
        self.site.upload(page, source_filename=self.sounds_png,
                         comment='pywikibot test',
                         ignore_warnings=True)

    @unittest.expectedFailure  # T367320
    def test_png_chunked(self) -> None:
        """Test uploading a png in two chunks using Site.upload."""
        page = pywikibot.FilePage(self.site, 'MP_sounds-pwb-chunked.png')
        self.site.upload(page, source_filename=self.sounds_png,
                         comment='pywikibot test',
                         ignore_warnings=True, chunk_size=1024)

    def _init_upload(self, chunk_size) -> None:
        """Do an initial upload causing an abort because of warnings."""
        def warn_callback(warnings) -> None:
            """A simple callback not automatically finishing the upload."""
            self.assertCountEqual([w.code for w in warnings], expected_warns)
            # by now we know there are only two but just make sure
            self.assertLength(warnings, expected_warns)
            self.assertIn(len(expected_warns), [1, 2])
            if len(expected_warns) == 2:
                self.assertEqual(warnings[0].file_key, warnings[1].file_key)
                self.assertEqual(warnings[0].offset, warnings[1].offset)
            self._file_key = warnings[0].file_key
            self._offset = warnings[0].offset

        expected_warns = ['exists'] if chunk_size else ['duplicate', 'exists']

        # First upload the warning with warnings enabled
        page = pywikibot.FilePage(self.site, 'MP_sounds-pwb.png')
        self.assertNotHasAttr(self, '_file_key')
        self.site.upload(page, source_filename=self.sounds_png,
                         comment='pywikibot test', chunk_size=chunk_size,
                         ignore_warnings=warn_callback)

        # Check that the warning happened and it's cached
        self.assertHasAttr(self, '_file_key')
        self.assertIs(self._offset, True)
        self.assertRegex(self._file_key, r'[0-9a-z]+.[0-9a-z]+.\d+.png')
        self._verify_stash()

    def _verify_stash(self) -> None:
        info = self.site.stash_info(self._file_key, ['size', 'sha1'])
        if info['size'] == 1024:
            self.assertEqual('3503db342c8dfb0a38db0682b7370ddd271fa163',
                             info['sha1'])
        else:
            self.assertEqual('0408a0f6a5e057e701f3aed96b0d1fb913c3d9d0',
                             info['sha1'])

    def _finish_upload(self, chunk_size, file_name) -> None:
        """Finish the upload."""
        # Finish/continue upload with the given file key
        page = pywikibot.FilePage(self.site, 'MP_sounds-pwb.png')
        self.site.upload(page, source_filename=file_name,
                         comment='pywikibot test', chunk_size=chunk_size,
                         ignore_warnings=True, report_success=False)

    def _test_continue_filekey(self, chunk_size) -> None:
        """Test uploading a chunk first and finish in a separate upload."""
        self._init_upload(chunk_size)
        self._finish_upload(chunk_size, self.sounds_png)

        # Check if it's still cached
        with self.assertAPIError('siiinvalidsessiondata') as cm:
            self.site.stash_info(self._file_key)
        self.assertStartsWith(cm.exception.info, 'File not found')

    @unittest.expectedFailure  # T367314
    def test_continue_filekey_once(self) -> None:
        """Test continuing to upload a file without using chunked mode."""
        self._test_continue_filekey(0)

    @unittest.expectedFailure  # T133288
    def test_continue_filekey_chunked(self) -> None:
        """Test continuing to upload a file with using chunked mode."""
        self._test_continue_filekey(1024)

    @unittest.expectedFailure  # T367321
    def test_sha1_mismatch(self) -> None:
        """Test trying to continue with a different file."""
        self._init_upload(1024)
        with self.assertRaises(ValueError) as cm:
            self._finish_upload(1024, self.arrow_png)
        self.assertEqual(
            str(cm.exception),
            f'The SHA1 of 1024 bytes of the stashed "{self._file_key}" is '
            '3503db342c8dfb0a38db0682b7370ddd271fa163 while the local file is '
            '3dd334f11aa1e780d636416dc0649b96b67588b6')
        self._verify_stash()

    @unittest.expectedFailure  # T367316
    def test_offset_mismatch(self) -> None:
        """Test trying to continue with a different offset."""
        self._init_upload(1024)
        self._offset = 0
        with self.assertRaises(ValueError) as cm:
            self._finish_upload(1024, self.sounds_png)
        self.assertEqual(
            str(cm.exception),
            f'For the file key "{self._file_key}" the server reported a size'
            ' 1024 while the offset was 0'
        )
        self._verify_stash()

    @unittest.expectedFailure  # T367317
    def test_offset_oversize(self) -> None:
        """Test trying to continue with an offset which is to large."""
        self._init_upload(1024)
        self._offset = 2000
        with self.assertRaises(ValueError) as cm:
            self._finish_upload(1024, self.sounds_png)
        self.assertEqual(
            str(cm.exception),
            f'For the file key "{self._file_key}" the offset was set to 2000'
            ' while the file is only 1276 bytes large.'
        )
        self._verify_stash()


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
