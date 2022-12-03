#!/usr/bin/python3
"""Script that updates interwiki sorting order in family.py file."""
#
# (C) Pywikibot team, 2020-2022
#
# Distributed under the terms of the MIT license.
#
import re
from pathlib import Path

import pywikibot
from pywikibot.family import Family


# MediaWiki page names for interwiki sorting order
pages = {
    'alphabetic':
        'Interwiki config-sorting order-native-languagename',
    'alphabetic_revised':
        'Interwiki_config-sorting_order-native-languagename-firstword',
}


def update_family(list_name, page):
    """Update family.py file."""
    pywikibot.info(f'\nReading {list_name} sorting order from\n'
                   f'{page.title(with_ns=False)!r}...')

    original = getattr(Family, list_name)
    new = page.text.split()

    # put the missing languages to the right place
    missing = original != new and set(original) - set(new)
    if missing:
        pywikibot.warning("['{}'] not listed at meta."
                          .format("', '".join(missing)))
        index = {}
        for code in missing:
            index[original.index(code)] = code
        i = len(index) - 1
        for key in index:
            new.insert(key - i, index[key])
            i -= 1

    if original == new:
        pywikibot.info('The lists match!')
        return

    pywikibot.info("The lists don't match, the new list is:")
    text = f'    {list_name} = [\n'
    line = ' ' * 7
    for code in new:
        if len(line) + len(code) >= 76:
            text += line + '\n'
            line = ' ' * 7
        line += f" '{code}',"
    text += line + '\n'
    text += '    ]'
    pywikibot.info(text)
    filepath = Path('pywikibot/family.py')
    family_text = filepath.read_text(encoding='utf8')
    family_text = re.sub(r'(?ms)^ {4}%s.+?\]' % list_name,
                         text, family_text, 1)
    filepath.write_text(family_text, encoding='utf8')


def main():
    """Main entry function."""
    site = pywikibot.Site('meta')
    for list_name, page_name in pages.items():
        page = pywikibot.Page(site, page_name, ns=site.namespaces.MEDIAWIKI)
        update_family(list_name, page)


if __name__ == '__main__':
    main()
