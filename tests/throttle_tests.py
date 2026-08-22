#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Test cases for the :mod:`throttle` module."""
from __future__ import annotations

import tempfile
from pathlib import Path

from pywikibot.throttle import ProcEntry, Throttle
from tests.aspects import TestCase


class ThrottleTestCase(TestCase):

    """Test throttle process file handling."""

    net = False

    def test_process_file_roundtrip(self) -> None:
        """Test that process entries are written in canonical order."""
        processes = [
            ProcEntry('c', 2, 30, 'site-b'),
            ProcEntry('b', 1, 20, 'site-b'),
            ProcEntry('a', 1, 10, 'site-a'),
        ]
        expected = sorted(processes, key=lambda p: (p.pid, p.site))

        with tempfile.TemporaryDirectory() as directory:
            throttle = object.__new__(Throttle)
            throttle.ctrlfilename = Path(directory) / 'throttle.ctrl'
            throttle._write_file(iter(processes))

            self.assertEqual(list(throttle._read_file()), expected)
