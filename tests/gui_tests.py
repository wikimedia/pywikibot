#!/usr/bin/env python3
"""Tests for the Tk UI."""
#
# (C) Pywikibot team, 2008-2023
#
# Distributed under the terms of the MIT license.
#
import os
import unittest
from contextlib import suppress

import pywikibot
from tests.aspects import DefaultSiteTestCase, TestCase, require_modules


class TestTkdialog(TestCase):

    """Test Tkdialog."""

    net = True

    def test_tk_dialog(self):
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


class TestTkinter(DefaultSiteTestCase):

    """Test Tkinter."""

    net = True

    def test_tkinter(self):
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


@require_modules('tkinter')
@require_modules('PIL')
def setUpModule():
    """Skip tests if tkinter or PIL is not installed.

    Also skip test if ``PYWIKIBOT_TEST_GUI`` environment variable is not
    set. Otherwise import modules and run tests.
    """
    if os.environ.get('PYWIKIBOT_TEST_GUI', '0') != '1':
        raise unittest.SkipTest('Tkinter tests are not enabled. '
                                '(set PYWIKIBOT_TEST_GUI=1 to enable)')

    global EditBoxWindow, Tkdialog, tkinter
    import tkinter

    from pywikibot.userinterfaces.gui import EditBoxWindow, Tkdialog


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
