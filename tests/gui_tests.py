#!/usr/bin/env python3
"""Tests for the Tk UI."""
#
# (C) Pywikibot team, 2008-2025
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import os
import sys
import unittest
from contextlib import suppress

import pywikibot
from tests.aspects import TestCase, require_modules


class TestTkdialog(TestCase):

    """Test Tkdialog."""

    net = True

    def test_tk_dialog(self) -> None:
        """Test Tk dialog."""
        desc = 'foo'
        filename = 'MP_sounds.png'
        image = f'tests/data/images/{filename}'
        box = Tkdialog(desc, image, filename)
        # skip after ~100 ms
        box.root.after(100, box.skip_file)
        description, name, skip = box.show_dialog()
        self.assertEqual(description, desc)
        self.assertEqual(name, filename)
        self.assertTrue(skip)


class TestTkinter(TestCase):

    """Test Tkinter."""

    family = 'wikipedia'
    code = 'en'

    def test_tkinter(self) -> None:
        """Test Tkinter window."""
        root = tkinter.Tk()
        root.resizable(width=tkinter.FALSE, height=tkinter.FALSE)
        root.title('pywikibot GUI')
        page = pywikibot.Page(self.site, 'Main Page')
        content = page.get()
        myapp = EditBoxWindow(root)
        root.after(100, myapp.pressedOK)
        text = myapp.edit(content, highlight=page.title())
        self.assertIsNotNone(text)
        self.assertIn('Main Page', text)


@require_modules('PIL')
def setUpModule() -> None:
    """Skip tests if tkinter or PIL is not installed.

    .. versionchanged:: 7.7
       skip test if ``PYWIKIBOT_TEST_GUI`` environment variable is not
       set.
    .. versionchanged:: 9.5
       :envvar:`PYWIKIBOT_TEST_GUI` environment variable was removed.
       ``pytest`` with ``pytest-xvfb `` extension is required for this
       tests on github actions.
    """
    if os.environ.get('GITHUB_ACTIONS'):
        skip = True
        if 'pytest' in sys.modules:
            with suppress(ModuleNotFoundError):
                import pytest_xvfb  # noqa: F401
                skip = False

        if skip:
            raise unittest.SkipTest('Tkinter tests must run with pytest and '
                                    'needs pytest-xvfb extension')

    global EditBoxWindow, Tkdialog, tkinter

    # pypy3 has a tkinter module which just raises importError if _tkinter
    # is not installed; thus require_modules does not work for it.
    # pypy3.10 has a version mismatch, see T380732.
    try:
        import tkinter
    except ImportError as e:
        raise unittest.SkipTest(e)

    try:
        dialog = tkinter.Tk()
    except RuntimeError as e:  # pragma: no cover
        raise unittest.SkipTest(f'Skipping due to T380732 - {e}')
    dialog.destroy()

    from pywikibot.userinterfaces.gui import EditBoxWindow, Tkdialog


if __name__ == '__main__':
    with suppress(SystemExit):
        unittest.main()
