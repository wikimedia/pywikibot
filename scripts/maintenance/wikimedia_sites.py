# -*- coding: utf-8  -*-
"""
This script checks the language list of each Wikimedia multiple-language site
against the language lists
"""
#
# (C) xqt, 2009-2014
# (C) Pywikibot team, 2008-2014
#
# Distributed under the terms of the MIT license.
#
__version__ = '$Id$'
#

import re
import codecs
import urllib
from xml.etree import cElementTree

import pywikibot
from pywikibot.site import Family

URL = 'http://wikistats.wmflabs.org/api.php?action=dump&table=%s&format=xml'

familiesDict = {
    'anarchopedia': 'anarchopedias',
    'wikibooks':    'wikibooks',
    'wikinews':     'wikinews',
    'wikipedia':    'wikipedias',
    'wikiquote':    'wikiquotes',
    'wikisource':   'wikisources',
    'wikiversity':  'wikiversity',
    'wikivoyage':   'wikivoyage',
    'wiktionary':   'wiktionaries',
}

exceptions = ['www']


def update_family(families):
    if not families:
        families = familiesDict.keys()
    for family in families:
        pywikibot.output('\nChecking family %s:' % family)

        original = Family(family).languages_by_size
        obsolete = Family(family).obsolete

        feed = urllib.urlopen(URL % familiesDict[family])
        tree = cElementTree.parse(feed)

        new = []
        for field in tree.findall('row/field'):
            if field.get('name') == 'prefix':
                code = field.text
                if not (code in obsolete or code in exceptions):
                    new.append(code)
                continue

        # put the missing languages to the right place
        missing = original != new and set(original) - set(new)
        if missing:
            pywikibot.output(u"WARNING: ['%s'] not listed at wikistats."
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
            text = u'        self.languages_by_size = [\r\n'
            line = ' ' * 11
            for code in new:
                if len(line) + len(code) <= 76:
                    line += u" '%s'," % code
                else:
                    text += u'%s\r\n' % line
                    line = ' ' * 11
                    line += u" '%s'," % code
            text += u'%s\r\n' % line
            text += u'        ]'
            pywikibot.output(text)
            family_file_name = 'pywikibot/families/%s_family.py' % family
            family_file = codecs.open(family_file_name, 'r', 'utf8')
            family_text = family_file.read()
            old = re.findall(ur'(?msu)^ {8}self.languages_by_size.+?\]',
                             family_text)[0]
            family_text = family_text.replace(old, text)
            family_file = codecs.open(family_file_name, 'w', 'utf8')
            family_file.write(family_text)
            family_file.close()


if __name__ == '__main__':
    fam = []
    for arg in pywikibot.handleArgs():
        if arg in familiesDict.keys() and arg not in fam:
            fam.append(arg)
    update_family(fam)
