#!/usr/bin/env python3
"""
Site upload test.

These tests write to the wiki.
"""
#
# (C) Pywikibot team, 2014-2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import unittest
from contextlib import suppress

import pywikibot
from tests import join_images_path
from tests.aspects import TestCase


class TestUpload(TestCase):

    """Test cases for upload."""

    write = True

    family = 'wikipedia'
    code = 'test'

    sounds_png = join_images_path('MP_sounds.png')
    arrow_png = join_images_path('1rightarrow.png')

    @unittest.expectedFailure  # T367319
    def test_png(self):
        """Test uploading a png using Site.upload."""
        page = pywikibot.FilePage(self.site, 'MP_sounds-pwb.png')
        self.site.upload(page, source_filename=self.sounds_png,
                         comment='pywikibot test',
                         ignore_warnings=True)

    @unittest.expectedFailure  # T367320
    def test_png_chunked(self):
        """Test uploading a png in two chunks using Site.upload."""
        page = pywikibot.FilePage(self.site, 'MP_sounds-pwb-chunked.png')
        self.site.upload(page, source_filename=self.sounds_png,
                         comment='pywikibot test',
                         ignore_warnings=True, chunk_size=1024)

    def _init_upload(self, chunk_size):
        """Do an initial upload causing an abort because of warnings."""
        def warn_callback(warnings):
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
        self.assertFalse(hasattr(self, '_file_key'))
        self.site.upload(page, source_filename=self.sounds_png,
                         comment='pywikibot test', chunk_size=chunk_size,
                         ignore_warnings=warn_callback)

        # Check that the warning happened and it's cached
        self.assertTrue(hasattr(self, '_file_key'))
        self.assertIs(self._offset, True)
        self.assertRegex(self._file_key, r'[0-9a-z]+.[0-9a-z]+.\d+.png')
        self._verify_stash()

    def _verify_stash(self):
        info = self.site.stash_info(self._file_key, ['size', 'sha1'])
        if info['size'] == 1024:
            self.assertEqual('3503db342c8dfb0a38db0682b7370ddd271fa163',
                             info['sha1'])
        else:
            self.assertEqual('0408a0f6a5e057e701f3aed96b0d1fb913c3d9d0',
                             info['sha1'])

    def _finish_upload(self, chunk_size, file_name):
        """Finish the upload."""
        # Finish/continue upload with the given file key
        page = pywikibot.FilePage(self.site, 'MP_sounds-pwb.png')
        self.site.upload(page, source_filename=file_name,
                         comment='pywikibot test', chunk_size=chunk_size,
                         ignore_warnings=True, report_success=False)

    def _test_continue_filekey(self, chunk_size):
        """Test uploading a chunk first and finish in a separate upload."""
        self._init_upload(chunk_size)
        self._finish_upload(chunk_size, self.sounds_png)

        # Check if it's still cached
        with self.assertAPIError('siiinvalidsessiondata') as cm:
            self.site.stash_info(self._file_key)
        self.assertTrue(cm.exception.info.startswith('File not found'),
                        f'info ({cm.exception.info}) did not start with '
                        '"File not found"')

    @unittest.expectedFailure  # T367314
    def test_continue_filekey_once(self):
        """Test continuing to upload a file without using chunked mode."""
        self._test_continue_filekey(0)

    @unittest.expectedFailure  # T133288
    def test_continue_filekey_chunked(self):
        """Test continuing to upload a file with using chunked mode."""
        self._test_continue_filekey(1024)

    @unittest.expectedFailure  # T367321
    def test_sha1_missmatch(self):
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
    def test_offset_missmatch(self):
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
    def test_offset_oversize(self):
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
