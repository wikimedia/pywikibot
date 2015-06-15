# -*- coding: utf-8  -*-
"""Bot tests."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#
import sys

import pywikibot
import pywikibot.bot

from tests.aspects import unittest, DefaultSiteTestCase, SiteAttributeTestCase


class TestBotTreatExit(object):

    """Mixin to provide handling for treat and exit."""

    def _treat(self, pages, post_treat=None):
        """
        Get tests which are executed on each treat.

        It uses pages as an iterator and compares the page given to the page
        returned by pages iterator. It checks that the bot's _site and site
        attributes are set to the page's site. If _treat_site is set with a Site
        it compares it to that one too.

        Afterwards it calls post_treat so it's possible to do additional checks.
        """
        def treat(page):
            self.assertEqual(page, next(self._page_iter))
            self.assertIsNotNone(self.bot._site)
            self.assertEqual(self.bot.site, self.bot._site)
            if self._treat_site:
                self.assertEqual(self.bot._site, self._treat_site)
            self.assertEqual(page.site, self.bot.site)
            if post_treat:
                post_treat(page)
        self._page_iter = iter(pages)
        return treat

    def _treat_page(self, pages=True, post_treat=None):
        """
        Adjust to CurrentPageBot signature.

        It uses almost the same logic as _treat but returns a wrapper function
        which itself calls the function returned by _treat.

        The pages may be set to True which sill use _treat_generator as the
        source for the pages.
        """
        def treat_page():
            treat(self.bot.current_page)

        if pages is True:
            pages = self._treat_generator()
        treat = self._treat(pages, post_treat)
        return treat_page

    def _exit(self, treated, written=0, exception=None):
        """Get tests which are executed on exit."""
        def exit():
            exc = sys.exc_info()[0]
            if exc is AssertionError:
                # When an AssertionError happened we shouldn't do these
                # assertions as they are invalid anyway and hide the actual
                # failed assertion
                return
            self.assertEqual(self.bot._treat_counter, treated)
            self.assertEqual(self.bot._save_counter, written)
            if exception:
                self.assertIs(exc, exception)
            else:
                self.assertIsNone(exc)
                self.assertRaises(StopIteration, next, self._page_iter)
        return exit


class TestDrySiteBot(TestBotTreatExit, SiteAttributeTestCase):

    """Tests for the BaseBot subclasses."""

    dry = True

    sites = {
        'de': {
            'family': 'wikipedia',
            'code': 'de'
        },
        'en': {
            'family': 'wikipedia',
            'code': 'en'
        }
    }

    def _generator(self):
        """Generic generator."""
        yield pywikibot.Page(self.de, 'Page 1')
        yield pywikibot.Page(self.en, 'Page 2')
        yield pywikibot.Page(self.de, 'Page 3')
        yield pywikibot.Page(self.en, 'Page 4')

    def test_Bot(self):
        """Test normal Bot class."""
        # Assert no specific site
        self._treat_site = False
        self.bot = pywikibot.bot.Bot(generator=self._generator())
        self.bot.treat = self._treat(self._generator())
        self.bot.exit = self._exit(4)
        self.bot.run()

    def test_CurrentPageBot(self):
        """Test normal Bot class."""
        def post_treat(page):
            self.assertIs(self.bot.current_page, page)
        # Assert no specific site
        self._treat_site = False
        self.bot = pywikibot.bot.CurrentPageBot(generator=self._generator())
        self.bot.treat_page = self._treat_page(self._generator(), post_treat)
        self.bot.exit = self._exit(4)
        self.bot.run()

    def test_Bot_ValueError(self):
        """Test normal Bot class with a ValueError in treat."""
        def post_treat(page):
            if page.title() == 'Page 3':
                raise ValueError('Whatever')

        self._treat_site = False
        self.bot = pywikibot.bot.Bot(generator=self._generator())
        self.bot.treat = self._treat([pywikibot.Page(self.de, 'Page 1'),
                                      pywikibot.Page(self.en, 'Page 2'),
                                      pywikibot.Page(self.de, 'Page 3')],
                                     post_treat)
        self.bot.exit = self._exit(2, exception=ValueError)
        self.assertRaises(ValueError, self.bot.run)

    def test_Bot_KeyboardInterrupt(self):
        """Test normal Bot class with a KeyboardInterrupt in treat."""
        def post_treat(page):
            if page.title() == 'Page 3':
                raise KeyboardInterrupt('Whatever')

        self._treat_site = False
        self.bot = pywikibot.bot.Bot(generator=self._generator())
        self.bot.treat = self._treat([pywikibot.Page(self.de, 'Page 1'),
                                      pywikibot.Page(self.en, 'Page 2'),
                                      pywikibot.Page(self.de, 'Page 3')],
                                     post_treat)

        # TODO: sys.exc_info is empty in Python 3
        if sys.version_info[0] > 2:
            exc = None
        else:
            exc = KeyboardInterrupt
        self.bot.exit = self._exit(2, exception=exc)
        self.bot.run()


# TODO: This could be written as dry tests probably by faking the important
# properties
class LiveBotTestCase(TestBotTreatExit, DefaultSiteTestCase):

    """Test bot classes which need to check the Page object live."""

    def _treat_generator(self):
        """Yield the current page until it's None."""
        while self._current_page:
            yield self._current_page

    def _missing_generator(self):
        """Yield pages and the last one does not exist."""
        self._count = 1
        self._current_page = list(self.site.allpages(total=1))[0]
        yield self._current_page
        while self._current_page.exists():
            self._count += 1
            self._current_page = pywikibot.Page(
                self.site, self._current_page.title() + 'X')
            yield self._current_page
        self._current_page = None

    def _exit(self, treated=None, written=0, exception=None):
        """Set the number of treated pages to _count."""
        def exit():
            t = self._count if treated is None else treated
            super(LiveBotTestCase, self)._exit(t, written, exception)()
        return exit

    def test_ExistingPageBot(self):
        """Test ExistingPageBot class."""
        def post_treat(page):
            """Verify the page exists."""
            self.assertTrue(page.exists())

        self._treat_site = False
        self.bot = pywikibot.bot.ExistingPageBot(
            generator=self._missing_generator())
        self.bot.treat_page = self._treat_page(post_treat=post_treat)
        self.bot.exit = self._exit()
        self.bot.run()

    def test_CreatingPageBot(self):
        """Test CreatingPageBot class."""
        # This doesn't verify much (e.g. it could yield the first existing page)
        # but the assertion in post_treat should verify that the page is valid
        def treat_generator():
            """Yield just one current page (the last one)."""
            yield self._current_page

        def post_treat(page):
            """Verify the page is missing."""
            self.assertFalse(page.exists())

        self._treat_site = False
        self.bot = pywikibot.bot.CreatingPageBot(
            generator=self._missing_generator())
        self.bot.treat_page = self._treat_page(treat_generator(), post_treat)
        self.bot.exit = self._exit()
        self.bot.run()


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
