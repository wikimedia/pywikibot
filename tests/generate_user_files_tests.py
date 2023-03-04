#!/usr/bin/env python3
"""Test generate_user_files script."""
#
# (C) Pywikibot team, 2018-2023
#
# Distributed under the terms of the MIT license.
#
import re
import unittest
from contextlib import suppress

from pywikibot.scripts import generate_user_files as guf
from tests.aspects import TestCase


class TestGenerateUserFiles(TestCase):

    """Test generate_user_files.py functionality."""

    dry = True

    def test_ask_for_dir_change(self):
        """Test ask_for_dir_change function."""
        userfile, passfile = guf.ask_for_dir_change(force=True)
        self.assertIsInstance(userfile, bool)
        self.assertIsInstance(passfile, bool)

    def test_base_names(self):
        """Test basename constants."""
        self.assertTrue(guf.USER_BASENAME.endswith('.py'))
        self.assertTrue(guf.PASS_BASENAME.endswith('.py'))

    def test_config_test(self):
        """Test config text strings."""
        args = {'main_family': '', 'main_code': '', 'usernames': '',
                'botpasswords': ''}
        config_text = guf.SMALL_CONFIG.format_map(args)
        self.assertEqual(config_text,
                         re.sub('{[a-z_]+}', '', guf.SMALL_CONFIG))
        args['config_text'] = ''
        config_text = guf.EXTENDED_CONFIG.format_map(args)
        self.assertEqual(config_text,
                         re.sub('{[a-z_]+}', '', guf.EXTENDED_CONFIG))
        config_text = guf.PASSFILE_CONFIG.format(botpasswords='')
        self.assertEqual(config_text,
                         re.sub('{[a-z_]+}', '', guf.PASSFILE_CONFIG))

    def test_file_exists(self):
        """Test file_exists function."""
        self.assertFalse(guf.file_exists('This file does not exist'))
        self.assertTrue(guf.file_exists('pwb.py'))

    def test_default_get_site_and_lang(self):
        """Test get_site_and_lang function with defaults."""
        family, code, user = guf.get_site_and_lang(force=True)
        self.assertEqual(family, 'wikipedia')
        self.assertEqual(code, 'en')
        self.assertIsNone(user)

    def test_get_site_and_lang(self):
        """Test get_site_and_lang function with parameters."""
        family, code, user = guf.get_site_and_lang(
            default_family='wikisource', default_lang='foo',
            default_username='bar',
            force=True)
        self.assertEqual(family, 'wikisource')
        self.assertEqual(code, 'en')
        self.assertEqual(user, 'bar')

    def test_parse_sections(self):
        """Test parse_sections regex."""
        sections = guf.parse_sections()
        self.assertGreater(len(sections), 10)
        first = sections[0]
        last = sections[-1]
        self.assertEqual('ACCOUNT SETTINGS', first.head)
        self.assertIn(first.head, first.section)
        self.assertIn(first.info[:10], first.section)
        self.assertEqual('FURTHER SETTINGS', last.head)
        self.assertIn(last.head, last.section)
        self.assertIn(last.info[:10], last.section)

    def test_copy_sections_not_found(self):
        """Test copy_sections function for sections not in config text."""
        config_text = guf.copy_sections(force=True, default='a')
        for section in guf.DISABLED_SECTIONS | guf.OBSOLETE_SECTIONS:
            self.assertNotIn(section, config_text)

    def test_copy_sections_found(self):
        """Test copy_sections function for sections found in config text."""
        config_text = guf.copy_sections(force=True, default='a')
        self.assertIsNotNone(config_text)
        for section in guf.SCRIPT_SECTIONS:
            self.assertIn(section, config_text)
        lines = config_text.splitlines()
        self.assertGreater(len(lines), 200)

    def test_copy_sections_none(self):
        """Test read_sections function."""
        config_text = guf.copy_sections(force=True)
        self.assertEqual(config_text, '')


if __name__ == '__main__':  # pragma: no cover
    with suppress(SystemExit):
        unittest.main()
