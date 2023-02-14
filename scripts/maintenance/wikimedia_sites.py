#!/usr/bin/env python3
"""Script that updates the language lists in Wikimedia family files.

Usage:

    python pwb.py wikimedia_sites [ {<family>} ]

"""
#
# (C) Pywikibot team, 2008-2022
#
# Distributed under the terms of the MIT license.
#
import re
from pathlib import Path

import pywikibot
from pywikibot.data import wikistats
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

exceptions = {
    'wikiversity': ['beta']
}


def update_family(families):
    """Update family files."""
    ws = wikistats.WikiStats()
    for family in families or families_list:
        pywikibot.info(f'\nChecking family {family}:')

        original = Family.load(family).languages_by_size
        for code in exceptions.get(family, []):
            if code in original:
                original.remove(code)
        obsolete = Family.load(family).obsolete

        new = []
        table = ws.languages_by_size(family)
        for code in table:
            if not (code in obsolete or code in exceptions.get(family, [])):
                new.append(code)

        # put the missing languages to the right place
        missing = original != new and set(original) - set(new)
        if missing:
            pywikibot.warning("['{}'] not listed at wikistats."
                              .format("', '".join(missing)))
            index = {}
            for code in missing:
                index[original.index(code)] = code
            i = len(index) - 1
            for key in sorted(index.keys(), reverse=True):
                new.insert(key - i, index[key])
                i -= 1

        if original == new:
            pywikibot.info('The lists match!')
            continue

        pywikibot.info("The lists don't match, the new list is:")
        text = '    languages_by_size = [\n'
        line = ' ' * 7
        for code in new:
            if len(line) + len(code) >= 76:
                text += line + '\n'
                line = ' ' * 7
            line += f" '{code}',"
        text += line + '\n'
        text += '    ]'
        pywikibot.info(text)

        filepath = Path(f'pywikibot/families/{family}_family.py')
        family_text = filepath.read_text(encoding='utf8')
        family_text = re.sub(r'(?ms)^ {4}languages_by_size.+?\]',
                             text, family_text, 1)
        filepath.write_text(family_text, encoding='utf8')


if __name__ == '__main__':
    fam = set()
    for arg in pywikibot.handle_args():
        if arg in families_list:
            fam.add(arg)
    update_family(fam)
