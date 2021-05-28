#!/usr/bin/python
"""Script that updates interwiki sorting order in family.py file."""
#
# (C) Pywikibot team, 2020-2021
#
# Distributed under the terms of the MIT license.
#
import codecs
import re

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
    pywikibot.output('\nReading {} sorting order from\nfrom {}...'
                     .format(list_name, page.title(with_ns=False)))

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
        pywikibot.output('The lists match!')
        return

    pywikibot.output("The lists don't match, the new list is:")
    text = '    {} = [\n'.format(list_name)
    line = ' ' * 7
    for code in new:
        if len(line) + len(code) >= 76:
            text += line + '\n'
            line = ' ' * 7
        line += " '{}',".format(code)
    text += line + '\n'
    text += '    ]'
    pywikibot.output(text)
    family_file_name = 'pywikibot/family.py'
    with codecs.open(family_file_name, 'r', 'utf8') as family_file:
        family_text = family_file.read()
    family_text = re.sub(r'(?ms)^ {4}%s.+?\]' % list_name,
                         text, family_text, 1)
    with codecs.open(family_file_name, 'w', 'utf8') as family_file:
        family_file.write(family_text)


def main():
    """Main entry function."""
    site = pywikibot.Site('meta', 'meta')
    for list_name, page_name in pages.items():
        page = pywikibot.Page(site, page_name, ns=site.namespaces.MEDIAWIKI)
        update_family(list_name, page)


if __name__ == '__main__':
    main()
