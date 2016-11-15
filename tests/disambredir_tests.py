# -*- coding: utf-8 -*-
"""
DisambigurationRedirectBot test.

These tests write to the wiki.
"""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

__version__ = '$Id$'
#

import pywikibot

from scripts import disambredir

from tests.aspects import unittest
from tests.bot_tests import FakeSaveBotTestCase, TWNBotTestCase
from tests.utils import fixed_generator


class TestDisambigurationRedirectBot(FakeSaveBotTestCase, TWNBotTestCase):

    """
    Test cases for DisambigurationRedirectBot.

    It patches the bot instances in such a way that there is no user interaction
    required and it can be run autonomously. It also does not actually write to
    the wiki.
    """

    family = 'wikipedia'
    code = 'test'

    def _patch_create_callback(self, choice):
        """
        Patch _create_callback in the Bot instance.

        It still creates a InteractiveReplace instance but returns another
        function which only calls 'handle_answer' from that InteractiveReplace
        instance if the link matches.
        """
        def _patched_creator(old, new):
            """Create the own callback callable."""
            def _patched_callback(link, text, groups, rng):
                """Return the result from handle_answer."""
                if callback._old == link:
                    callback._current_match = (link, text, groups, rng)
                    answer = callback.handle_answer(choice)
                    callback._current_match = None
                    return answer
                else:
                    return None

            callback = original(old, new)
            return _patched_callback

        original = self.bot._create_callback
        self.bot._create_callback = _patched_creator

    @classmethod
    def setUpClass(cls):
        """Initialize page variable."""
        super(TestDisambigurationRedirectBot, cls).setUpClass()
        # Patch the page to be independent of the actual site
        cls.page = pywikibot.Page(cls.site, 'User:BobBot/Test disambig')
        cls.page.linkedPages = fixed_generator(
            [pywikibot.Page(cls.site, 'User:BobBot/Redir'),
             pywikibot.Page(cls.site, 'User:BobBot/Redir2'),
             pywikibot.Page(cls.site, 'Main Page')])

    def bot_save(self, page, *args, **kwargs):
        """Check if the page matches."""
        self.assertIs(page, self.page)
        return super(TestDisambigurationRedirectBot, self).bot_save(
            page, *args, **kwargs)

    def setUp(self):
        """Set up the test page."""
        super(TestDisambigurationRedirectBot, self).setUp()
        self.page.text = ('[[User:BobBot/Redir#Foo|Bar]]\n'
                          '[[User:BobBot/Redir|Baz]]\n'
                          '[[User:BobBot/Redir2]]\n'
                          '[[user:BobBot/Redir2]]\n'
                          '[[Main Page|Label]]\n')
        self.bot = disambredir.DisambiguationRedirectBot(generator=[self.page])

    def test_unchanged(self):
        """Test no change."""
        # No changes needed, won't call the save method
        self.assert_saves = 0
        self._patch_create_callback('n')
        self.bot.run()
        self.assertEqual(self.page.text,
                         '[[User:BobBot/Redir#Foo|Bar]]\n'
                         '[[User:BobBot/Redir|Baz]]\n'
                         '[[User:BobBot/Redir2]]\n'
                         '[[user:BobBot/Redir2]]\n'
                         '[[Main Page|Label]]\n')

    def test_unlink(self):
        """Test unlinking."""
        self._patch_create_callback('u')
        self.bot.run()
        self.assertEqual(self.page.text,
                         'Bar\nBaz\nUser:BobBot/Redir2\nuser:BobBot/Redir2\n'
                         '[[Main Page|Label]]\n')

    def test_replace_target(self):
        """Test replacing just target page."""
        self._patch_create_callback('t')
        self.bot.run()
        self.assertEqual(self.page.text,
                         '[[Main Page#Foo|Bar]]\n'
                         '[[Main Page|Baz]]\n'
                         '[[Main Page|User:BobBot/Redir2]]\n'
                         '[[Main Page|user:BobBot/Redir2]]\n'
                         '[[Main Page|Label]]\n')

    def test_replace_label(self):
        """Test replacing target and label."""
        self._patch_create_callback('l')
        self.bot.run()
        self.assertEqual(self.page.text,
                         '[[Main Page#Foo|Main Page]]\n'
                         '[[Main Page]]\n'
                         '[[Main Page|Main Page#What we do on this wiki]]\n'
                         '[[Main Page|Main Page#What we do on this wiki]]\n'
                         '[[Main Page|Label]]\n')

    def test_replace_section(self):
        """Test replacing target including section."""
        self._patch_create_callback('s')
        self.bot.run()
        self.assertEqual(self.page.text,
                         '[[Main Page|Bar]]\n'
                         '[[Main Page|Baz]]\n'
                         '[[Main Page#What we do on this wiki|User:BobBot/Redir2]]\n'
                         '[[Main Page#What we do on this wiki|user:BobBot/Redir2]]\n'
                         '[[Main Page|Label]]\n')

    def test_replace_all(self):
        """Test replacing target including section and label."""
        self._patch_create_callback('c')
        self.bot.run()
        self.assertEqual(self.page.text,
                         '[[Main Page]]\n'
                         '[[Main Page]]\n'
                         '[[Main Page#What we do on this wiki]]\n'
                         '[[Main Page#What we do on this wiki]]\n'
                         '[[Main Page|Label]]\n')


if __name__ == '__main__':  # pragma: no cover
    try:
        unittest.main()
    except SystemExit:
        pass
