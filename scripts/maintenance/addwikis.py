#!/usr/bin/env python3
#
# (C) Pywikibot team, 2024-2026
#
# Distributed under the terms of the MIT license.
#
"""Script that adds new wikis to the codes set in Wikimedia family files.

Usage:

    python pwb.py addwikis [-family:<fam>] {<wiki>} {-family:<fam> {<wiki>}}


Example:

    :code:`python pwb.py addwikis foo -family:wikisource bar baz`

    adds code ``foo`` to the default (wikipedia) family, and codes ``bar``
    and ``baz`` to wikisource.


.. version-added:: 9.2
.. version-changed:: 10.4
   The options ``-h``, ``-help`` and ``--help`` display the help message.
.. version-deprecated:: 10.4
   The ``help`` option
.. version-changed:: 11.0
   Multiple families can be given with one run. The difference is shown
   instead of the new list.
.. version-changed:: 11.3
   wikinews is no longer supported by this script because all wikinews
   sites are closed. Also update
   :attr:`family.WikimediaFamily.known_codes`.

"""
from __future__ import annotations

import re
import sys
from collections import defaultdict
from pathlib import Path

import pywikibot
from pywikibot.exceptions import ArgumentDeprecationWarning
from pywikibot.family import Family
from pywikibot.tools import issue_deprecation_warning


# supported families by this script
FAMILIES_LIST = [
    'wikibooks',
    'wikipedia',
    'wikiquote',
    'wikisource',
    'wikiversity',
    'wikivoyage',
    'wiktionary',
]


def combine_codes(codes: set[str], /, *, attr='codes', style='{}') -> str:
    """Combine codes and return a formatted Python assignment block.

    .. version-added:: 11.3
    """
    new = sorted(codes)
    opening, closing = style
    text = f'    {attr} = {opening}\n'
    line = ' ' * 7
    for code in new:
        if len(line) + len(code) >= 76:
            text += line + '\n'
            line = ' ' * 7
        line += f" '{code}',"
    text += line + '\n'
    text += f'    {closing}'
    return text


def update_known_codes(families: list[str]) -> None:
    """Collect all codes from all families and update Family.known_codes.

    .. version-added:: 11.3
    """
    pywikibot.info()
    family = Family.load(families[0])
    if not isinstance(family, pywikibot.family.WikimediaFamily):
        pywikibot.info(f'{family} is not a WikimediaFamily')
        return

    original: set[str] = set(family.known_codes)
    new_codes: set[str] = set(family.codes)

    for family_name in families[1:]:
        new_codes.update(Family.load(family_name).codes)

    new_codes.discard('mul')

    if new_codes <= original:
        pywikibot.info('No codes to add to known_codes list.')
        return

    pywikibot.info('Updating known_codes list:\n')
    text = combine_codes(original | new_codes, attr='known_codes', style='[]')
    filepath = Path('pywikibot/family.py')
    old_family_text = filepath.read_text(encoding='utf8')
    new_family_text = re.sub(r'(?ms)^ {4}known_codes = \[.+?\]',
                             text, old_family_text, count=1)
    pywikibot.showDiff(old_family_text, new_family_text)
    filepath.write_text(new_family_text, encoding='utf8')


def update_family(family_name: str, wikis: set) -> None:
    """Update codes set in family file."""
    joined_wikis = "', '".join(wikis)
    pywikibot.info(f"Adding '{joined_wikis}' to {family_name} family...\n")

    family = Family.load(family_name)
    original = family.codes
    new_codes = set()
    for wiki in list(wikis):
        if wiki in original:
            pywikibot.warning(
                f'{wiki!r} is already in Family.codes; ignoring.')
        else:
            new_codes.add(wiki)

    # cleanup cache
    family._families.clear()
    module = type(family).__module__
    del sys.modules[module]

    if not new_codes:
        pywikibot.info('No wikis to add.')
        return

    pywikibot.info("The lists don't match, the updated list is:\n")
    text = combine_codes(original | new_codes)
    filepath = Path(f'pywikibot/families/{module}.py')
    old_family_text = filepath.read_text(encoding='utf8')
    new_family_text = re.sub(r'(?ms)^ {4}codes = \{.+?\}',
                             text, old_family_text, count=1)
    pywikibot.showDiff(old_family_text, new_family_text)
    filepath.write_text(new_family_text, encoding='utf8')


def main(*args: str) -> None:
    """Script entry point to handle args."""
    if not args:
        args = sys.argv[1:]
        sys.argv = [sys.argv[0]]

    current_family = 'wikipedia'
    wikis = defaultdict(set)
    for arg in args:
        if arg.startswith('-family'):
            current_family = arg.split(':')[1]
        elif arg in ('help', '-h', '-help', '--help'):
            if arg == 'help':
                issue_deprecation_warning(
                    "'help' option",
                    "'-h', '-help' or '--help'",
                    since='10.4.0',
                    warning_class=ArgumentDeprecationWarning
                )
            pywikibot.show_help()
            return
        else:
            wikis[current_family].add(arg)

    if not wikis:
        pywikibot.bot.suggest_help(
            additional_text='No wiki is specified to be added.')

    for family, codes in wikis.items():
        if family not in FAMILIES_LIST:
            pywikibot.bot.suggest_help(
                additional_text=f'Script cannot be used for {family} family.')
        else:
            update_family(family, codes)

    update_known_codes(FAMILIES_LIST)


if __name__ == '__main__':
    main()
