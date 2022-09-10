#!/usr/bin/python3
"""Tests for the Tk UI."""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import os
import unittest
from contextlib import suppress

import pywikibot
from tests.aspects import DefaultSiteTestCase, TestCase, require_modules


class TkinterTestsBase(TestCase):

    """TestCase base for Tkinter tests."""

    net = True

    @classmethod
    def setUpClass(cls):
        """Set virtual display environment."""
        super().setUpClass()
        cls.env = os.environ.get('DISPLAY')
        os.environ['DISPLAY'] = ':1.0'

    @classmethod
    def tearDownClass(cls):
        """Restore the display environment value."""
        if not cls.env:
            del os.environ['DISPLAY']
        else:
            os.environ['DISPLAY'] = cls.env
        super().tearDownClass()


class TestTkdialog(TkinterTestsBase):

    """Test Tkdialog."""

    def test_tk_dialog(self):
        """Test Tk dialog."""
        desc = 'foo'
        image = 'tests/data/images/MP_sounds.png'
        filename = image.rsplit('/', 1)[1]
        box = Tkdialog(desc, image, filename)
        # skip after ~100 ms
        box.root.after(100, box.skip_file)
        description, name, skip = box.show_dialog()
        self.assertEqual(description, desc)
        self.assertEqual(name, filename)
        self.assertTrue(skip)


class TestTkinter(TkinterTestsBase, DefaultSiteTestCase):

    """Test Tkinter."""

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

    Otherwise import modules.
    """
    global EditBoxWindow, Tkdialog, tkinter
    import tkinter
    from pywikibot.userinterfaces.gui import EditBoxWindow, Tkdialog


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
