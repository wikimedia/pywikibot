#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Script that updates the language lists in Wikimedia family files.

Usage:

    python pwb.py wikimedia_sites [ {<family>} ]

"""
#
# (C) xqt, 2009-2017
# (C) Pywikibot team, 2008-2017
#
# Distributed under the terms of the MIT license.
#
from __future__ import absolute_import, unicode_literals

import codecs
import re

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

exceptions = ['-', 'mul']


def update_family(families):
    """Update family files."""
    ws = wikistats.WikiStats()
    for family in families or families_list:
        pywikibot.output('\nChecking family %s:' % family)

        original = Family.load(family).languages_by_size
        for code in exceptions:
            if code in original:
                original.remove(code)
        obsolete = Family.load(family).obsolete

        new = []
        table = ws.languages_by_size(family)
        for code in table:
            if not (code in obsolete or code in exceptions):
                new.append(code)

        # put the missing languages to the right place
        missing = original != new and set(original) - set(new)
        if missing:
            pywikibot.warning("['%s'] not listed at wikistats."
                              % "', '".join(missing))
            index = {}
            for code in missing:
                index[original.index(code)] = code
            i = len(index) - 1
            for key in sorted(index.keys(), reverse=True):
                new.insert(key - i, index[key])
                i -= 1

        if original == new:
            pywikibot.output(u'The lists match!')
        else:
            pywikibot.output(u"The lists don't match, the new list is:")
            text = '    languages_by_size = [\n'
            line = ' ' * 7
            for code in new:
                if len(line) + len(code) < 76:
                    line += u" '%s'," % code
                else:
                    text += '%s\n' % line
                    line = ' ' * 7
                    line += u" '%s'," % code
            text += '%s\n' % line
            text += '    ]'
            pywikibot.output(text)
            family_file_name = 'pywikibot/families/%s_family.py' % family
            with codecs.open(family_file_name, 'r', 'utf8') as family_file:
                family_text = family_file.read()
            family_text = re.sub(r'(?msu)^ {4}languages_by_size.+?\]',
                                 text, family_text, 1)
            with codecs.open(family_file_name, 'w', 'utf8') as family_file:
                family_file.write(family_text)


if __name__ == '__main__':
    fam = set()
    for arg in pywikibot.handle_args():
        if arg in families_list:
            fam.add(arg)
    update_family(fam)
