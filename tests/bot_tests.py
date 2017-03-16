# -*- coding: utf-8 -*-
"""Bot tests."""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#
import sys

import pywikibot
import pywikibot.bot

from pywikibot import i18n
from pywikibot.tools import PY2

from tests.aspects import (
    unittest, DefaultSiteTestCase, SiteAttributeTestCase, TestCase,
)


class TWNBotTestCase(TestCase):

    """Verify that i18n is available."""

    @classmethod
    def setUpClass(cls):
        """Verify that the translations are available."""
        if not i18n.messages_available():
            raise unittest.SkipTest("i18n messages package '%s' not available."
                                    % i18n._messages_package_name)
        super(TWNBotTestCase, cls).setUpClass()


class FakeSaveBotTestCase(TestCase):

    """
    An abstract test case which patches the bot class to not actually write.

    It redirects the bot's _save_page to it's own C{bot_save} method. Currently
    userPut, put_current and user_edit_entity call it. By default it'll call
    the original method but replace the function called to actually save the
    page by C{page_save}. It patches the bot class as soon as this class'
    attribute bot is defined. It also sets the bot's 'always' option to True to
    avoid user interaction.

    The C{bot_save} method compares the save counter before the call and asserts
    that it has increased by one after the call. It also stores locally in
    C{save_called} if C{page_save} has been called. If C{bot_save} or
    C{page_save} are implemented they should call super's method at some point
    to make sure these assertions work. At C{tearDown} it checks that the pages
    are saved often enough. The attribute C{default_assert_saves} defines the
    number of saves which must happen and compares it to the difference using
    the save counter. It is possible to define C{assert_saves} after C{setUp} to
    overwrite the default value for certain tests. By default the number of
    saves it asserts are 1. Additionally C{save_called} increases by 1 on each
    call of C{page_save} and should be equal to C{assert_saves}.

    This means if the bot class actually does other writes, like using
    L{pywikibot.page.Page.save} manually, it'll still write.
    """

    @property
    def bot(self):
        """Get the current bot."""
        return self._bot

    @bot.setter
    def bot(self, value):
        """Set and patch the current bot."""
        assert value._save_page != self.bot_save, 'bot may not be patched.'
        self._bot = value
        self._bot.options['always'] = True
        self._original = self._bot._save_page
        self._bot._save_page = self.bot_save
        self._old_counter = self._bot._save_counter

    def setUp(self):
        """Set up test by reseting the counters."""
        super(FakeSaveBotTestCase, self).setUp()
        self.assert_saves = getattr(self, 'default_assert_saves', 1)
        self.save_called = 0

    def tearDown(self):
        """Tear down by asserting the counters."""
        self.assertEqual(self._bot._save_counter,
                         self._old_counter + self.assert_saves)
        self.assertEqual(self.save_called, self.assert_saves)
        super(FakeSaveBotTestCase, self).tearDown()

    def bot_save(self, page, func, *args, **kwargs):
        """Handle when bot's userPut was called."""
        self.assertGreaterEqual(self._bot._save_counter, 0)
        old_counter = self._bot._save_counter
        old_local_cnt = self.save_called
        result = self._original(page, self.page_save, *args, **kwargs)
        self.assertEqual(self._bot._save_counter, old_counter + 1)
        self.assertEqual(self.save_called, old_local_cnt + 1)
        self.assertGreater(self._bot._save_counter, self._old_counter)
        return result

    def page_save(self, *args, **kwargs):
        """Handle when bot calls the page's save method."""
        self.save_called += 1


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
            if self._treat_site is None:
                self.assertFalse(hasattr(self.bot, 'site'))
                self.assertFalse(hasattr(self.bot, '_site'))
            else:
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
                # Cannot use assertRaisesRegex. Python 2.6 issue. See T158519.
                self.assertRaises(StopIteration, next, self._page_iter)
        return exit


class TestDrySiteBot(TestBotTreatExit, SiteAttributeTestCase):

    """Tests for the BaseBot subclasses."""

    CANT_SET_ATTRIBUTE_RE = 'can\'t set attribute'
    NOT_IN_TREAT_RE = 'Requesting the site not while in treat is not allowed.'
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

    def test_SingleSiteBot_automatic(self):
        """Test SingleSiteBot class with no predefined site."""
        self._treat_site = self.de
        self.bot = pywikibot.bot.SingleSiteBot(site=None,
                                               generator=self._generator())
        self.bot.treat = self._treat([pywikibot.Page(self.de, 'Page 1'),
                                      pywikibot.Page(self.de, 'Page 3')])
        self.bot.exit = self._exit(2)
        self.bot.run()
        self.assertEqual(self.bot.site, self._treat_site)

    def test_SingleSiteBot_specific(self):
        """Test SingleSiteBot class with predefined site."""
        self._treat_site = self.en
        self.bot = pywikibot.bot.SingleSiteBot(site=self.en,
                                               generator=self._generator())
        self.bot.treat = self._treat([pywikibot.Page(self.en, 'Page 2'),
                                      pywikibot.Page(self.en, 'Page 4')])
        self.bot.exit = self._exit(2)
        self.bot.run()
        self.assertEqual(self.bot.site, self._treat_site)

    def test_MultipleSitesBot(self):
        """Test MultipleSitesBot class."""
        # Assert no specific site
        self._treat_site = False
        self.bot = pywikibot.bot.MultipleSitesBot(generator=self._generator())
        with self.assertRaisesRegex(AttributeError, self.CANT_SET_ATTRIBUTE_RE):
            self.bot.site = self.de
        with self.assertRaisesRegex(ValueError, self.NOT_IN_TREAT_RE):
            self.bot.site
        if PY2:
            # The exc_info still contains the AttributeError :/
            sys.exc_clear()
        self.bot.treat = self._treat(self._generator())
        self.bot.exit = self._exit(4)
        self.bot.run()
        with self.assertRaisesRegex(ValueError, self.NOT_IN_TREAT_RE):
            self.bot.site
        if PY2:
            # The exc_info still contains the AttributeError :/
            sys.exc_clear()

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
        self._treat_site = None
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
        self.assertRaisesRegex(ValueError, 'Whatever', self.bot.run)

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
        if not PY2:
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

        self._treat_site = None
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

        self._treat_site = None
        self.bot = pywikibot.bot.CreatingPageBot(
            generator=self._missing_generator())
        self.bot.treat_page = self._treat_page(treat_generator(), post_treat)
        self.bot.exit = self._exit()
        self.bot.run()


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
