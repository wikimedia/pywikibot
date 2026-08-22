#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for :mod:`editor` module."""
from __future__ import annotations

import os
import unittest
from contextlib import suppress
from unittest.mock import patch

from pywikibot import config, editor
from tests.aspects import TestCase


class EditorTestCase(TestCase):

    """Test for editor.Texteditor."""

    net = False

    def setUp(self):
        """Save editor setting."""
        self.old_editor = config.editor

    def tearDown(self):
        """Restore editor setting."""
        config.editor = self.old_editor

    def test_editor_default(self):
        """Test editor with default config setting."""
        te = editor.TextEditor()
        self.assertEqual(te.editor, '')

    def test_editor_true(self):
        """Test editor with config.editor set to True."""
        config.editor = True
        te = editor.TextEditor()
        self.assertEqual(te.editor, '')

    def test_editor_false(self):
        """Test editor with config.editor set to False."""
        config.editor = False
        te = editor.TextEditor()
        self.assertEqual(te.editor, 'break' if editor.OSWIN32 else 'true')

    def test_editor_editor(self):
        """Test editor with config.editor set to True."""
        config.editor = 'custom_editor'
        te = editor.TextEditor()
        self.assertEqual(te.editor, 'custom_editor')

    def test_descriptor_closed_before_editor(self):
        """Test that the temporary descriptor is closed before editing."""
        config.editor = 'custom_editor'
        real_mkstemp = editor.tempfile.mkstemp
        handle = -1

        def mkstemp(*args, **kwargs):
            nonlocal handle
            handle, filename = real_mkstemp(*args, **kwargs)
            return handle, filename

        def run(*args, **kwargs):
            with self.assertRaises(OSError):
                os.fstat(handle)

        with patch.object(editor.tempfile, 'mkstemp', side_effect=mkstemp):
            with patch.object(editor.subprocess, 'run', side_effect=run):
                self.assertIsNone(editor.TextEditor().edit('text'))


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
