#!/usr/bin/env python3
#
# (C) Pywikibot team, 2026
#
# Distributed under the terms of the MIT license.
#
"""Tests for the make_i18n_dict maintenance script."""
from __future__ import annotations

import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch

from scripts.maintenance import make_i18n_dict
from tests.aspects import TestCase


class MakeI18nDictTestCase(TestCase):

    """Test :class:`make_i18n_dict.i18nBot`."""

    net = False

    def test_init_with_class(self) -> None:
        """Test initializing the bot with a class from a script."""
        script_class = SimpleNamespace(message={})
        script_module = SimpleNamespace(ScriptClass=script_class)

        with patch.object(make_i18n_dict, 'import_module',
                          return_value=script_module) as import_module:
            bot = make_i18n_dict.i18nBot(
                'sample.ScriptClass', 'message')

        import_module.assert_called_once_with('scripts.sample')
        self.assertIs(bot.script, script_class)
        self.assertEqual(bot.messages, {'message': 'message'})

    def test_to_json_creates_and_updates_file(self) -> None:
        """Test creating directories and updating an existing JSON file."""
        bot = object.__new__(make_i18n_dict.i18nBot)
        bot.scriptname = 'sample'
        bot.dict = {'en': {'sample-first': 'first'}}

        with TemporaryDirectory() as directory:
            with patch.object(make_i18n_dict.config, 'base_dir', directory):
                bot.to_json()

                file_path = Path(directory, 'scripts/i18n/sample/en.json')
                data = json.loads(file_path.read_text(encoding='utf-8'))
                data['@metadata']['authors'].extend(['mahveotm', 'xqt'])
                file_path.write_text(json.dumps(data), encoding='utf-8')

                bot.dict = {'en': {'sample-second': 'second'}}
                bot.to_json()

            data = json.loads(file_path.read_text(encoding='utf-8'))

        self.assertEqual(data, {
            '@metadata': {'authors': ['mahveotm', 'xqt']},
            'sample-first': 'first',
            'sample-second': 'second',
        })


if __name__ == '__main__':
    unittest.main()
