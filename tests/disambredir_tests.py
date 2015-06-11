# -*- coding: utf-8  -*-
"""
DisambigurationRedirectBot test.

These tests write to the wiki.
"""
#
# (C) Pywikibot team, 2015
#
# Distributed under the terms of the MIT license.
#
from __future__ import unicode_literals

__version__ = '$Id$'
#

import pywikibot

from scripts import disambredir

from tests.aspects import unittest, TestCase
from tests.utils import fixed_generator


class TestDisambigurationRedirectBot(TestCase):

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
                    return callback.handle_answer(choice, link)
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
        cls.page = pywikibot.Page(cls.site, 'User:BobBot/Test disambig')

    def setUp(self):
        """Set up the test page."""
        def _save_page(*args, **kwargs):
            self.assertIs(args[0], self.page)
            self.save_called = True
            return  # avert actually saving

        super(TestDisambigurationRedirectBot, self).setUp()
        self.page.text = ('[[User:BobBot/Redir#Foo|Bar]]\n'
                          '[[User:BobBot/Redir|Baz]]\n'
                          '[[Main Page|Label]]\n')
        self.bot = disambredir.DisambiguationRedirectBot(generator=[self.page])
        self.bot.options['always'] = True
        # Patch the page and bot to not actually save anything
        self.page.linkedPages = fixed_generator(
            [pywikibot.Page(self.site, 'User:BobBot/Redir'),
             pywikibot.Page(self.site, 'Main Page')])
        self.save_called = False
        self.bot._save_page = _save_page

    def test_unchanged(self):
        """Test no change."""
        self._patch_create_callback('n')
        self.assertFalse(self.save_called)
        self.bot.run()
        self.assertEqual(self.page.text,
                         '[[User:BobBot/Redir#Foo|Bar]]\n'
                         '[[User:BobBot/Redir|Baz]]\n'
                         '[[Main Page|Label]]\n')
        # No changes needed, won't call the save method
        self.assertFalse(self.save_called)

    def test_unlink(self):
        """Test unlinking."""
        self._patch_create_callback('u')
        self.assertFalse(self.save_called)
        self.bot.run()
        self.assertEqual(self.page.text,
                         'Bar\nBaz\n[[Main Page|Label]]\n')
        self.assertTrue(self.save_called)

    def test_replace_target(self):
        """Test replacing just target page."""
        self._patch_create_callback('t')
        self.assertFalse(self.save_called)
        self.bot.run()
        self.assertEqual(self.page.text,
                         '[[Main Page#Foo|Bar]]\n'
                         '[[Main Page|Baz]]\n'
                         '[[Main Page|Label]]\n')
        self.assertTrue(self.save_called)

    def test_replace_all(self):
        """Test replacing target and label."""
        self._patch_create_callback('l')
        self.assertFalse(self.save_called)
        self.bot.run()
        self.assertEqual(self.page.text,
                         '[[Main Page#Foo|Main Page]]\n'
                         '[[Main Page]]\n'
                         '[[Main Page|Label]]\n')
        self.assertTrue(self.save_called)


if __name__ == '__main__':
    try:
        unittest.main()
    except SystemExit:
        pass
