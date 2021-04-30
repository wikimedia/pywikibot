"""Tests for the Tk UI."""
#
# (C) Pywikibot team, 2008-2021
#
# Distributed under the terms of the MIT license.
#
import os
import unittest
from contextlib import suppress

import pywikibot
from tests.aspects import DefaultSiteTestCase, TestCase


if os.environ.get('PYWIKIBOT_TEST_GUI', '0') == '1':
    import tkinter

    from pywikibot.userinterfaces.gui import EditBoxWindow, Tkdialog


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


def setUpModule():  # noqa: N802
    """Skip Travis tests if PYWIKIBOT_TEST_GUI variable is not set."""
    if os.environ.get('PYWIKIBOT_TEST_GUI', '0') != '1':
        raise unittest.SkipTest('Tkinter tests are disabled on Travis-CI')


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
