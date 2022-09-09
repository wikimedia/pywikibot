#!/usr/bin/python3
"""Tests for the Tk UI."""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import unittest
from contextlib import suppress

import pywikibot
from tests.aspects import DefaultSiteTestCase, TestCase, require_modules


class TestTkdialog(TestCase):

    """Test Tkdialog."""

    net = True

    def testTkdialog(self):
        """Test Tk dialog."""
        try:
            box = Tkdialog('foo', 'tests/data/MP_sounds.png', 'MP_sounds.png')
            box.show_dialog()
        except ImportError as e:
            pywikibot.warning(e)


class TestTkinter(DefaultSiteTestCase):

    """Test Tkinter."""

    net = True

    def testTkinter(self):
        """Test Tkinter window."""
        root = tkinter.Tk()
        root.resizable(width=tkinter.FALSE, height=tkinter.FALSE)
        root.title('pywikibot GUI')
        page = pywikibot.Page(pywikibot.Site(), 'Main Page')
        content = page.get()
        myapp = EditBoxWindow(root)
        myapp.bind('<Control-d>', myapp.debug)
        v = myapp.edit(content, highlight=page.title())
        self.assertIsNone(v)


@require_modules('tkinter')
def setUpModule():
    """Skip tests if tkinter is not installed. Otherwise import it."""
    global EditBoxWindow, Tkdialog, tkinter
    import tkinter
    from pywikibot.userinterfaces.gui import EditBoxWindow, Tkdialog


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
