#!/usr/bin/env python3
"""Script that adds new wikis to the codes set in Wikimedia family files.

Usage:

    python pwb.py addwikis [-family:<family>] {<wiki>}


.. versionadded:: 9.2
"""
#
# (C) Pywikibot team, 2024
#
# Distributed under the terms of the MIT license.
#
from __future__ import annotations

import re
import sys
from pathlib import Path

import pywikibot
from pywikibot.family import Family


# supported families by this script
families_list = [
    'wikibooks',
    'wikinews',
    'wikipedia',
    'wikiquote',
    'wikisource',
    'wikiversity',
    'wikivoyage',
    'wiktionary',
]


def update_family(family, wikis):
    """Update codes set in family file."""
    joined_wikis = "', '".join(wikis)
    pywikibot.info(f"Adding '{joined_wikis}' to {family} family...\n")

    original = Family.load(family).codes
    new_codes = set()
    for wiki in list(wikis):
        if wiki in original:
            pywikibot.warning(f'{wiki!r} is alread in Family.codes; ignoring.')
        else:
            new_codes.add(wiki)

    if not new_codes:
        pywikibot.info('No wikis to add.')
        return

    # combine new codes set
    new = sorted(original | new_codes)
    pywikibot.info("The lists don't match, the new list is:\n")
    text = '    codes = {\n'
    line = ' ' * 7
    for code in new:
        if len(line) + len(code) >= 76:
            text += line + '\n'
            line = ' ' * 7
        line += f" '{code}',"
    text += line + '\n'
    text += '    }'
    pywikibot.info(text)

    # update codes
    filepath = Path(f'pywikibot/families/{family}_family.py')
    family_text = filepath.read_text(encoding='utf8')
    family_text = re.sub(r'(?ms)^ {4}codes = \{.+?\}',
                         text, family_text, count=1)
    filepath.write_text(family_text, encoding='utf8')


def main(*args: str) -> None:
    """Script entry point to handle args."""
    if not args:
        args = sys.argv[1:]
        sys.argv = [sys.argv[0]]

    family = 'wikipedia'
    wikis = []
    for arg in args:
        if arg.startswith('-family'):
            family = arg.split(':')[1]
        elif arg == 'help':
            pywikibot.show_help()
            return
        else:
            wikis.append(arg)

    if not wikis:
        pywikibot.bot.suggest_help(
            additional_text='No wiki is specified to be added.')
    elif family not in families_list:
        pywikibot.bot.suggest_help(
            additional_text=f'Script cannot be used for {family} family.')
    else:
        update_family(family, wikis)


if __name__ == '__main__':
    main()
