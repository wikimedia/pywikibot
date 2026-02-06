#!/usr/bin/env python3
"""Tests for exceptions."""
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

from pywikibot.exceptions import Error
from pywikibot.tools import PYTHON_VERSION
from tests.aspects import TestCase


class TestExceptionAddNote(TestCase):

    """Test Error.add_note() backport logic."""

    net = False

    def test_add_note(self):
        """Test that add_note appends text to the exception string."""
        e = Error('Original Message')
        e.add_note('Note 1')
        e.add_note('Note 2')

        # Check that notes are stored internally (all versions)
        # In Py3.11+ this is native; in <3.11 it is our backport.
        self.assertTrue(hasattr(e, '__notes__'))
        self.assertEqual(e.__notes__, ['Note 1', 'Note 2'])

        # Check string representation
        # Case A: Python < 3.11 (Backport)
        # We expect the note to be baked into str(e)
        if PYTHON_VERSION < (3, 11):
            expected = 'Original Message\nNote 1\nNote 2'
            self.assertEqual(str(e), expected)

        # Case B: Python 3.11+ (Native)
        # We expect str(e) to ONLY be the message.
        # The traceback printer handles the notes separately.
        else:
            self.assertEqual(str(e), 'Original Message')
